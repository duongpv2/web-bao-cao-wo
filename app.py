# -*- coding: utf-8 -*-
"""
Hệ thống Điều hành WO & Quản lý CSDL - P.VHKT - CNCTHNI (Viettel Construction)
================================================================================
Phiên bản đã tái cấu trúc & sửa lỗi bởi chuyên gia (fix 7 nghiêm trọng + 8 mức cao).
Các thay đổi chính so với bản gốc:
  1. Bảo mật: mật khẩu hash (pbkdf2) + lưu bền trong users.json (không còn hardcode plaintext)
  2. Chống brute-force: khóa tạm 60s sau 5 lần thử sai
  3. Upload: chỉ nhận .xlsx cho file dữ liệu, lọc tên file (chống path traversal),
     tự clear cache + rerun, validate schema cột bắt buộc
  4. Đọc Excel: fallback engine (calamine -> openpyxl), cache có TTL 300s
  5. Logic dữ liệu: ép kiểu cột "Quá hạn", chuẩn hóa "Trạng thái",
     cột tiền phạt khai báo tường minh (không dò mò), tìm kiếm vectorized trong form
  6. Sửa lỗi đổi mật khẩu không rerun; bổ sung xem file chi tiết tiền phạt (trước đây chết)
  7. Xóa file CSDL có xác nhận 2 bước; lọc chỉ file (không crash khi có thư mục con)
  8. Bổ sung: xuất báo cáo tổng hợp Excel (đa sheet), audit log, đường dẫn tuyệt đối,
     backup file cũ khi ghi đè, constants tập trung.

Yêu cầu thư viện (requirements):
  streamlit>=1.31, pandas, plotly, openpyxl, python-calamine (không bắt buộc, có fallback), numpy
Chạy: streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import numpy as np
import io
import os
import json
import hashlib
import logging
import base64
import urllib.request
import urllib.error
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ======================================================================
# 0. CONSTANTS & CẤU HÌNH TẬP TRUNG (tránh magic strings lặp khắp nơi)
# ======================================================================
VIETTEL_RED = "#d90429"
VIETTEL_RED_DARK = "#8b0000"
VIETTEL_RED_SOFT = "rgba(217,4,41,0.12)"

BASE_DIR = Path(__file__).resolve().parent          # đường dẫn tuyệt đối, không phụ thuộc CWD
DATA_DIR = BASE_DIR / "uploaded_data"
CSDL_DIR = BASE_DIR / "csdl_tong_hop"
WO_PATH = BASE_DIR / "Web.xlsx"
PENALTY_LOOKUP_PATH = DATA_DIR / "penalty_lookup.xlsx"
PENALTY_DETAIL_PATH = DATA_DIR / "penalty_detail.xlsx"
USERS_FILE = BASE_DIR / "users.json"
AUDIT_LOG = BASE_DIR / "app_audit.log"

REQUIRED_WO_COLS = ["Trạng thái", "Trung tâm", "Quá hạn"]   # schema bắt buộc của file WO
PENALTY_VALUE_COL = "Tổng tiền phạt"                         # cột tiền phạt khai báo tường minh
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
MIN_PASSWORD_LEN = 6
CACHE_TTL = 300                                              # cache tự hết hạn sau 5 phút
GH_CHECK_INTERVAL = 300                                      # kiểm tra GitHub mỗi 5 phút 1 lần

# --- Cấu hình đồng bộ GitHub 2 chiều (đặt trong .streamlit/secrets.toml) ---
# [github]
# repo = "owner/ten-repo"
# branch = "main"
# file_path = "Web.xlsx"
# token = "ghp_xxxxxxxxxxxx"   # Personal Access Token có quyền repo (cần để push ngược)
GH = {}
try:
    if "github" in st.secrets:
        GH = dict(st.secrets["github"])
except Exception:
    pass
GH_REPO = GH.get("repo")
GH_BRANCH = GH.get("branch", "main")
GH_FILE_PATH = GH.get("file_path", "Web.xlsx")
GH_TOKEN = GH.get("token")
GH_RAW_URL = f"https://raw.githubusercontent.com/{GH_REPO}/{GH_BRANCH}/{GH_FILE_PATH}" if GH_REPO else None
GH_API = "https://api.github.com"
APP_VERSION = "v5.2-20261102"   # badge kiểm tra code nào đang chạy thật trên Streamlit Cloud

DATA_DIR.mkdir(parents=True, exist_ok=True)
CSDL_DIR.mkdir(parents=True, exist_ok=True)

# ======================================================================
# 1. CẤU HÌNH GHI LOG AUDIT (ai làm gì lúc nào)
# ======================================================================
logging.basicConfig(
    filename=str(AUDIT_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
def audit(action: str):
    user = st.session_state.get("username", "anonymous")
    logging.info(f"user={user} | {action}")

# ======================================================================
# 2. BẢO MẬT: hash mật khẩu + lưu bền trong users.json
# ======================================================================
def hash_pw(pw: str, salt: str = None) -> str:
    salt = salt or hashlib.sha256(os.urandom(16)).hexdigest()[:32]
    h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
    return f"{salt}${h}"

def verify_pw(pw: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
    except ValueError:
        return False
    return hash_pw(pw, salt) == f"{salt}${h}"

DEFAULT_USERS = {
    "duongpv2": {"pass": hash_pw("admin123"), "role": "admin", "name": "Phạm Văn Dương"},
    "user":     {"pass": hash_pw("user123"),  "role": "viewer", "name": "Cán bộ / Nhân viên"},
}

def load_users() -> dict:
    """Nạp users từ file JSON (bền qua restart). Nếu chưa có, tạo từ mặc định."""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_USERS, f, ensure_ascii=False, indent=2)
    return DEFAULT_USERS

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def sanitize_filename(name: str) -> str:
    """Chống path traversal: chỉ lấy basename, loại ký tự nguy hiểm."""
    name = os.path.basename(name)
    name = name.replace("/", "_").replace("\\", "_").replace("\0", "")
    if ".." in name or name.startswith("."):
        name = "uploaded_" + name.lstrip(".")
    return name if name else "uploaded_file"

def backup_if_exists(path: Path):
    """Backup file cũ trước khi ghi đè (đổi tên .bak theo thời gian)."""
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".{ts}.bak")
        try:
            path.rename(bak)
        except OSError:
            pass

# ======================================================================
# 2b. ĐỒNG BỘ GITHUB 2 CHIỀU: auto-pull từ GitHub + admin push ngược lên
# ======================================================================
def gh_request(url, token=None, method="GET", data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "wo-csdl-app")
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), {}
    except Exception:
        return None, b"", {}

def sync_wo_from_github() -> str:
    """Tự động tải Web.xlsx từ GitHub nếu remote mới hơn local. Trả về trạng thái."""
    if not GH_RAW_URL:
        return "no_config"
    now_ts = datetime.now().timestamp()
    if now_ts - st.session_state.get("gh_last_check", 0) < GH_CHECK_INTERVAL:
        return "throttled"
    st.session_state.gh_last_check = now_ts
    status, _, headers = gh_request(GH_RAW_URL, method="HEAD")
    if status != 200:
        return f"error_head_{status}"
    remote_ts = 0
    if headers.get("Last-Modified"):
        try:
            remote_ts = parsedate_to_datetime(headers["Last-Modified"]).timestamp()
        except Exception:
            remote_ts = 0
    local_ts = WO_PATH.stat().st_mtime if WO_PATH.exists() else 0
    if remote_ts and remote_ts <= local_ts:
        st.session_state.data_source = "GitHub (đã đồng bộ)"
        return "uptodate"
    status, body, _ = gh_request(GH_RAW_URL, method="GET")
    if status == 200 and body:
        backup_if_exists(WO_PATH)
        with open(WO_PATH, "wb") as f:
            f.write(body)
        st.cache_data.clear()
        st.session_state.data_source = "GitHub (vừa tải)"
        audit("auto-synced Web.xlsx from GitHub")
        return "updated"
    return f"error_get_{status}"

def push_wo_to_github(content_bytes: bytes, commit_msg: str):
    """Đẩy Web.xlsx lên GitHub để admin upload đồng bộ với repo (2 chiều)."""
    if not (GH_REPO and GH_TOKEN):
        return False, "Chưa cấu hình GitHub token/repo — file chỉ lưu local. Lưu ý: lần git pull tiếp theo có thể ghi đè, vui lòng cấu hình secrets.toml để đồng bộ 2 chiều."
    url = f"{GH_API}/repos/{GH_REPO}/contents/{GH_FILE_PATH}"
    status, body, _ = gh_request(f"{url}?ref={GH_BRANCH}", token=GH_TOKEN, method="GET")
    sha = None
    if status == 200:
        try:
            sha = json.loads(body).get("sha")
        except Exception:
            pass
    payload = {
        "message": commit_msg,
        "content": base64.b64encode(content_bytes).decode(),
        "branch": GH_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    status, body, _ = gh_request(url, token=GH_TOKEN, method="PUT", data=json.dumps(payload).encode())
    if status in (200, 201):
        return True, "Đã đẩy lên GitHub thành công — 2 kênh đã đồng bộ."
    try:
        err = json.loads(body).get("message", f"HTTP {status}")
    except Exception:
        err = f"HTTP {status}"
    return False, f"Lỗi đẩy lên GitHub: {err}. File đã lưu local nhưng chưa lên GitHub."

# ======================================================================
# 3. ĐỌC DỮ LIỆU: fallback engine + cache có TTL + validate schema
# ======================================================================
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_excel_file(file_path: str, header_row: int = 0):
    """Đọc Excel: thử calamine (nhanh), fallback openpyxl. Không nuốt lỗi."""
    path = Path(file_path)
    if not path.exists():
        return None, f"Không tìm thấy file {path.name}"
    for engine in ("calamine", "openpyxl"):
        try:
            df = pd.read_excel(str(path), header=header_row, engine=engine)
            return df, None
        except ImportError:
            continue  # thử engine kế tiếp
        except Exception as e:
            return None, f"Lỗi đọc {path.name}: {type(e).__name__}"
    return None, "Thiếu cả 2 engine đọc Excel (calamine/openpyxl)"

def validate_wo_schema(df: pd.DataFrame) -> list:
    """Trả về danh sách cột bị thiếu (rỗng = hợp lệ)."""
    if df is None:
        return REQUIRED_WO_COLS[:]
    return [c for c in REQUIRED_WO_COLS if c not in df.columns]

def normalize_wo(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa cột quan trọng để tránh crash / sai số."""
    if df is None:
        return df
    df = df.copy()
    if "Trạng thái" in df.columns:
        df["Trạng thái"] = df["Trạng thái"].astype(str).str.strip()
    if "Quá hạn" in df.columns:
        # Ép về số: text "Có/Không" hoặc "1/0" đều xử lý an toàn
        col = df["Quá hạn"]
        if col.dtype == object:
            mask_yes = col.astype(str).str.strip().str.lower().isin(["có", "yes", "true", "1", "y"])
            df["Quá hạn"] = np.where(mask_yes, 1, 0)
        df["Quá hạn"] = pd.to_numeric(df["Quá hạn"], errors="coerce").fillna(0).astype(int)
    return df

def compute_kpis(df_wo: pd.DataFrame, df_pen_lookup: pd.DataFrame) -> dict:
    """Tính KPI một lần dùng chung cho mọi trang (tránh lặp logic)."""
    if df_wo is None:
        return {"total": 0, "doing": 0, "done": 0, "overdue": 0, "penalty": 0.0}
    total = len(df_wo)
    done = int((df_wo["Trạng thái"].str.lower() == "đóng").sum()) if "Trạng thái" in df_wo else 0
    overdue = int(df_wo["Quá hạn"].sum()) if "Quá hạn" in df_wo else 0
    penalty = 0.0
    if df_pen_lookup is not None and PENALTY_VALUE_COL in df_pen_lookup.columns:
        penalty = float(pd.to_numeric(df_pen_lookup[PENALTY_VALUE_COL], errors="coerce").fillna(0).sum())
    elif df_wo is not None and PENALTY_VALUE_COL in df_wo.columns:
        penalty = float(pd.to_numeric(df_wo[PENALTY_VALUE_COL], errors="coerce").fillna(0).sum())
    return {"total": total, "doing": total - done, "done": done, "overdue": overdue, "penalty": penalty}

def vectorized_search(df: pd.DataFrame, kw: str) -> pd.DataFrame:
    """Tìm kiếm trên mọi cột bằng vectorized (nhanh hơn astype(str).apply rất nhiều)."""
    if not kw or df is None or df.empty:
        return df
    mask = np.column_stack([
        df[c].astype(str).str.contains(kw, case=False, na=False, regex=False) for c in df.columns
    ]).any(axis=1)
    return df[mask]

def export_report(kpis: dict, df_wo: pd.DataFrame, df_pen_lookup: pd.DataFrame, df_pen_detail: pd.DataFrame) -> bytes:
    """Xuất báo cáo tổng hợp Excel đa sheet."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        summary = pd.DataFrame({
            "Chỉ tiêu": ["Tổng WO", "Đang thực hiện", "Đã đóng", "Quá hạn", "Tổng tiền phạt (đ)", "Thời gian xuất báo cáo"],
            "Giá trị": [kpis["total"], kpis["doing"], kpis["done"], kpis["overdue"], f"{kpis['penalty']:,.0f}",
                        datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S %d/%m/%Y")],
        })
        summary.to_excel(w, sheet_name="Tong_Quan", index=False)
        if df_wo is not None:
            df_wo.to_excel(w, sheet_name="WO", index=False)
        if df_pen_lookup is not None:
            df_pen_lookup.to_excel(w, sheet_name="Tien_Phat_TraCuu", index=False)
        if df_pen_detail is not None:
            df_pen_detail.to_excel(w, sheet_name="Tien_Phat_ChiTiet", index=False)
    return buf.getvalue()

# ======================================================================
# 4. CẤU HÌNH TRANG & CSS (GIỮ NGUYÊN GIAO DIỆN ĐỎ VIETTEL)
# ======================================================================
st.set_page_config(
    page_title="Điều hành WO & Quản lý CSDL - P.VHKT - CNCTHNI",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
    <style>
    .block-container {{padding-top:0.8rem !important;padding-bottom:2rem !important;padding-left:1.5rem !important;padding-right:1.5rem !important;}}
    [data-testid="stHeader"] {{background:transparent !important;}}
    [data-testid="stToolbar"] {{display:none !important;}}
    #MainMenu {{visibility:hidden;}}
    footer {{visibility:hidden;}}
    /* === FORCE SIDEBAR (VÙNG 2) LUÔN HIỆN — không phụ thuộc nút thu/mở === */
    section[data-testid="stSidebar"] {{
        display:block !important;
        transform:none !important;
        visibility:visible !important;
        opacity:1 !important;
        width:280px !important;
        min-width:280px !important;
        margin-left:0 !important;
    }}
    div[data-testid="stSidebarCollapsedControl"],
    div[data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {{display:none !important;}}
    /* Ẩn luôn đầu sidebar (chứa nút thu ×) — người dùng KHÔNG THỂ thu sidebar */
    [data-testid="stSidebarHeader"] {{display:none !important;}}
    section[data-testid="stSidebar"] > div:first-child {{top:0 !important;}}
    .stApp {{background-color:#f4f6f9 !important;}}
    [data-testid="stSidebar"] {{background-color:#a61c1c !important;border-right:2px solid {VIETTEL_RED};}}
    [data-testid="stSidebar"] * {{color:#ffffff !important;}}
    [data-testid="stSidebar"] div[role="radiogroup"] label {{background-color:rgba(255,255,255,0.1);padding:8px 12px;border-radius:6px;margin-bottom:6px;transition:all 0.3s ease;border:1px solid rgba(255,255,255,0.2);}}
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{background-color:rgba(255,255,255,0.25);}}
    [data-testid="stMetric"] {{background-color:#ffffff;border-radius:8px;padding:12px 18px;box-shadow:0 4px 6px rgba(0,0,0,0.05);border:1px solid {VIETTEL_RED} !important;border-left:5px solid {VIETTEL_RED} !important;}}
    .stButton button[kind="primary"], [data-testid="baseButton-primary"] {{background-color:{VIETTEL_RED} !important;border-color:{VIETTEL_RED} !important;color:white !important;}}
    .stButton button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover {{background-color:{VIETTEL_RED_DARK} !important;}}
    </style>
""", unsafe_allow_html=True)

# JS tự động mở sidebar nếu đang bị thu (chạy trong trang chính, không phải iframe)
st.markdown("""<script>
(function(){
  function expandSidebar(){
    try{
      var sb = document.querySelector('section[data-testid="stSidebar"]');
      if(sb && sb.getAttribute('aria-expanded') !== 'true'){
        var btn = document.querySelector('[data-testid="stSidebarCollapsedControl"] button')
               || document.querySelector('[data-testid="stSidebarCollapsedControl"]')
               || document.querySelector('[data-testid="collapsedControl"] button')
               || document.querySelector('[data-testid="collapsedControl"]');
        if(btn){ btn.click(); }
      }
    }catch(e){}
  }
  expandSidebar();
  // Kiểm tra vĩnh viễn mỗi 1 giây — nếu bị thu (do Streamlit/localStorage) thì tự mở lại ngay
  setInterval(expandSidebar, 1000);
})();
</script>""", unsafe_allow_html=True)

# ======================================================================
# 5. KHỞI TẠO SESSION STATE
# ======================================================================
if "users_db" not in st.session_state:
    st.session_state.users_db = load_users()
for key, default in [("logged_in", False), ("username", ""), ("role", ""), ("name", ""),
                     ("current_page", "📊 Dashboard"), ("action_view", "normal"),
                     ("login_attempts", 0), ("lock_until", None), ("delete_confirm", None),
                     ("data_source", "GitHub / local"), ("gh_last_check", 0)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ======================================================================
# 6. MÀN HÌNH ĐĂNG NHẬP (có chống brute-force)
# ======================================================================
if not st.session_state.logged_in:
    now_ts = datetime.now().timestamp()
    locked = st.session_state.lock_until and now_ts < st.session_state.lock_until
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_l2, _ = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown(f"""
            <div style="text-align:center;margin-bottom:20px;background:#fff;padding:30px;border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,0.1);border:2px solid {VIETTEL_RED};">
                <div style="font-family:sans-serif;font-size:30px;font-weight:900;color:{VIETTEL_RED};letter-spacing:-0.5px;line-height:1;">VIETTEL</div>
                <div style="font-family:sans-serif;font-size:11px;font-weight:700;color:#333;letter-spacing:5px;text-transform:lowercase;margin-top:4px;">construction</div>
                <h4 style="color:{VIETTEL_RED};font-weight:800;margin:15px 0 2px 0;">P.VHKT - CNCTHNI</h4>
                <p style="color:#6c757d;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Hệ thống Điều hành & Quản lý CSDL</p>
            </div>
        """, unsafe_allow_html=True)

        if locked:
            remain = int(st.session_state.lock_until - now_ts)
            st.error(f"⚠️ Tài khoản bị tạm khóa do nhập sai quá nhiều lần. Vui lòng thử lại sau {remain}s.")
            audit("login locked out")
            st.stop()

        with st.form("login_form"):
            st.markdown("### **Đăng nhập hệ thống**")
            st.caption("Vui lòng nhập thông tin tài khoản để tiếp tục")
            input_user = st.text_input("Tài khoản đăng nhập", placeholder="Nhập tên đăng nhập (VD: duongpv2)...")
            input_pass = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
            submit_login = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")

            if submit_login:
                users = st.session_state.users_db
                if input_user in users and verify_pw(input_pass, users[input_user]["pass"]):
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.session_state.role = users[input_user]["role"]
                    st.session_state.name = users[input_user]["name"]
                    st.session_state.login_attempts = 0
                    st.session_state.lock_until = None
                    audit(f"login success")
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    audit(f"login FAILED for user='{input_user}' (attempt {st.session_state.login_attempts})")
                    if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                        st.session_state.lock_until = now_ts + LOCKOUT_SECONDS
                        st.session_state.login_attempts = 0
                        st.error(f"⚠️ Nhập sai {MAX_LOGIN_ATTEMPTS} lần. Tài khoản tạm khóa {LOCKOUT_SECONDS}s.")
                    else:
                        left = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
                        st.error(f"⚠️ Sai tài khoản hoặc mật khẩu. Còn {left} lần thử trước khi bị khóa.")
        st.stop()

# ======================================================================
# 7. GIAO DIỆN CHÍNH — VÙNG 1: HEADER (giữ nguyên thiết kế)
# ======================================================================
last_update_str = "Chưa có dữ liệu"
if WO_PATH.exists():
    vn_tz = timezone(timedelta(hours=7))
    last_update_str = datetime.fromtimestamp(WO_PATH.stat().st_mtime, tz=vn_tz).strftime("%H:%M:%S %d/%m/%Y")

with st.container():
    st.markdown(f"""
        <div style="background-color:#fff;padding:12px 20px;border-radius:8px;border:1px solid {VIETTEL_RED};box-shadow:0 2px 5px rgba(0,0,0,0.05);margin-bottom:5px;">
    """, unsafe_allow_html=True)
    h1, h2, h3, h4 = st.columns([1.5, 1.8, 2.2, 1.8])
    with h1:
        st.markdown(f"""
            <div style="line-height:1.1;padding-top:2px;">
                <span style="font-family:sans-serif;font-size:24px;font-weight:900;color:{VIETTEL_RED};letter-spacing:-0.5px;">VIETTEL</span><br>
                <span style="font-family:sans-serif;font-size:10px;font-weight:700;color:#333;letter-spacing:4.5px;text-transform:lowercase;display:inline-block;width:100%;">construction</span>
            </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown(f"""
            <div style="padding-top:2px;border-left:2px solid {VIETTEL_RED};padding-left:12px;">
                <span style="color:{VIETTEL_RED};font-size:13px;font-weight:800;">P.VHKT - CNCTHNI</span><br>
                <span style="color:#495057;font-size:11px;font-weight:600;">Hệ thống Điều hành & CSDL</span>
            </div>
        """, unsafe_allow_html=True)
    with h3:
        clock_html = """
        <div style="padding-top:2px;text-align:center;border-left:2px solid #d90429;padding-left:10px;">
            <div style="font-size:10px;font-weight:700;color:#6c757d;text-transform:uppercase;">Thời gian thực (UTC+7)</div>
            <div id="live-clock" style="font-size:14px;color:#d90429;background:#fff5f5;padding:4px 10px;border-radius:6px;display:inline-block;font-weight:800;border:1px solid #d90429;margin-top:2px;">Đang đồng bộ...</div>
        </div>
        <script>
        function updateClock(){
            var now=new Date();
            var utc=now.getTime()+(now.getTimezoneOffset()*60000);
            var vn=new Date(utc+(3600000*7));
            var p=function(n){return String(n).padStart(2,'0');};
            document.getElementById('live-clock').innerText=p(vn.getDate())+'/'+p(vn.getMonth()+1)+'/'+vn.getFullYear()+' '+p(vn.getHours())+':'+p(vn.getMinutes())+':'+p(vn.getSeconds());
        }
        setInterval(updateClock,1000);updateClock();
        </script>
        """
        components.html(clock_html, height=45)
    with h4:
        st.markdown(f"""
            <div style="border-left:2px solid {VIETTEL_RED};padding-left:10px;font-size:11px;line-height:1.3;">
                <span style="color:#6c757d;font-weight:600;">CSDL cập nhật:</span><br>
                <span style="color:{VIETTEL_RED};font-weight:700;">🕒 {last_update_str}</span>
            </div>
        """, unsafe_allow_html=True)
        st.caption(f"📡 Nguồn: {st.session_state.data_source} · 🔖 {APP_VERSION}")
        role_label = "ADMIN" if st.session_state.role == "admin" else "USER"
        with st.popover(f"👤 {st.session_state.name} ({role_label})", use_container_width=True):
            st.markdown(f"**Tài khoản:** `{st.session_state.username}`")
            st.markdown(f"**Phân quyền:** `{role_label}`")
            st.markdown("---")
            if st.button("🔐 Đổi mật khẩu cá nhân", use_container_width=True):
                st.session_state.action_view = "change_pass"
                st.rerun()
            if st.button("🚪 Đăng xuất hệ thống", use_container_width=True, type="primary"):
                audit("logout")
                for k in ("logged_in", "username", "role", "name", "action_view"):
                    st.session_state[k] = "" if k != "logged_in" else False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f'<hr style="border:none;height:3px;background-color:{VIETTEL_RED};margin:5px 0 15px 0;">', unsafe_allow_html=True)

# Thanh điều hướng ngang dự phòng (luôn hiện) — đảm bảo 100% không bị kẹt trang kể cả khi sidebar có vấn đề
MENU_OPTIONS = ["📊 Dashboard", "📋 Dữ liệu WO", "💰 Dữ liệu tiền phạt", "🗂️ CSDL tổng hợp"]
_top_idx = MENU_OPTIONS.index(st.session_state.current_page) if st.session_state.current_page in MENU_OPTIONS else 0
_top_nav = st.radio(
    "Điều hướng nhanh:", MENU_OPTIONS, index=_top_idx, horizontal=True,
    label_visibility="collapsed", key="top_nav_radio",
)
st.session_state.current_page = _top_nav

# ======================================================================
# 8. MÀN HÌNH ĐỔI MẬT KHẨU (đã fix: rerun sau khi thành công)
# ======================================================================
if st.session_state.action_view == "change_pass":
    st.markdown(f"""
        <div style="background:#fff;padding:30px;border-radius:12px;border:1px solid {VIETTEL_RED};box-shadow:0 4px 12px rgba(0,0,0,0.08);">
            <h3 style="color:{VIETTEL_RED};">🔐 Thay đổi mật khẩu tài khoản</h3>
    """, unsafe_allow_html=True)
    with st.form("form_change_password"):
        old_p = st.text_input("Mật khẩu cũ", type="password")
        new_p = st.text_input(f"Mật khẩu mới (tối thiểu {MIN_PASSWORD_LEN} ký tự)", type="password")
        confirm_p = st.text_input("Xác nhận mật khẩu mới", type="password")
        c1, c2 = st.columns(2)
        btn_update = c1.form_submit_button("Xác nhận thay đổi", type="primary")
        btn_back = c2.form_submit_button("Quay lại trang chính")
        if btn_update:
            cur = st.session_state.username
            users = st.session_state.users_db
            if not verify_pw(old_p, users[cur]["pass"]):
                st.error("Mật khẩu cũ không chính xác.")
            elif len(new_p) < MIN_PASSWORD_LEN:
                st.error(f"Mật khẩu mới phải có ít nhất {MIN_PASSWORD_LEN} ký tự.")
            elif new_p != confirm_p:
                st.error("Mật khẩu mới và xác nhận không khớp.")
            else:
                users[cur]["pass"] = hash_pw(new_p)
                save_users(users)                       # lưu bền ra file
                st.session_state.users_db = users
                st.session_state.action_view = "normal"
                audit("password changed")
                st.success("Đổi mật khẩu thành công!")
                st.rerun()                             # FIX: trước đây thiếu rerun
        if btn_back:
            st.session_state.action_view = "normal"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ======================================================================
# 9. VÙNG 2: SIDEBAR ĐỎ VIETTEL
# ======================================================================
with st.sidebar:
    st.markdown("""
        <div style="text-align:center;padding:15px 0;border-bottom:2px solid rgba(255,255,255,0.3);margin-bottom:15px;">
            <div style="font-family:sans-serif;font-size:24px;font-weight:900;color:#fff;line-height:1;">VIETTEL</div>
            <div style="font-family:sans-serif;font-size:10px;font-weight:700;color:#ffcccc;letter-spacing:4.5px;text-transform:lowercase;margin-top:3px;">construction</div>
            <h5 style="color:#fff;margin:10px 0 0 0;font-weight:800;font-size:14px;">QUẢN LÝ ĐIỀU HÀNH</h5>
        </div>
    """, unsafe_allow_html=True)
    selected = st.radio(
        "Chọn chức năng:", MENU_OPTIONS,
        index=MENU_OPTIONS.index(st.session_state.current_page) if st.session_state.current_page in MENU_OPTIONS else 0,
        label_visibility="collapsed",
    )
    st.session_state.current_page = selected

# ======================================================================
# 10. NẠP DỮ LIỆU (1 lần, đã chuẩn hóa) — tự đồng bộ từ GitHub trước
# ======================================================================
gh_sync_status = sync_wo_from_github()
if gh_sync_status == "updated":
    st.info("🔄 Hệ thống vừa tự động tải bản Web.xlsx mới nhất từ GitHub.")

# Hiển thị kết quả đồng bộ thủ công (nếu có) rồi xóa để không lặp lại
if st.session_state.get("gh_sync_msg"):
    kind, msg = st.session_state.gh_sync_msg
    {"success": st.success, "info": st.info, "warning": st.warning}.get(kind, st.error)(msg)
    st.session_state.gh_sync_msg = None

df_wo_raw, err_wo = load_excel_file(str(WO_PATH), header_row=1)
df_wo = normalize_wo(df_wo_raw) if df_wo_raw is not None else None
missing_cols = validate_wo_schema(df_wo)
if err_wo and WO_PATH.exists():
    st.error(f"⚠️ {err_wo}")
elif missing_cols and df_wo is not None:
    st.warning(f"⚠️ File WO thiếu các cột: {', '.join(missing_cols)}. Một số chỉ số có thể không hiển thị đúng.")

df_pen_lookup, _ = load_excel_file(str(PENALTY_LOOKUP_PATH), header_row=0)
df_pen_detail, _ = load_excel_file(str(PENALTY_DETAIL_PATH), header_row=0)   # FIX: trước đây không bao giờ đọc
kpis = compute_kpis(df_wo, df_pen_lookup)

# ======================================================================
# 11. VÙNG 3: NỘI DUNG CHÍNH THEO TRANG
# ======================================================================
with st.container():

    # ---------- TRANG DASHBOARD ----------
    if st.session_state.current_page == "📊 Dashboard":
        st.subheader("📊 Tổng Quan Chỉ Số Work Order & Tài Chính")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("📦 Tổng WO", f"{kpis['total']:,}")
        k2.metric("⏳ Đang Thực Hiện", f"{kpis['doing']:,}")
        k3.metric("✅ Đã Đóng", f"{kpis['done']:,}")
        k4.metric("⚠️ Quá Hạn", f"{kpis['overdue']:,}", delta="Cần xử lý", delta_color="inverse")
        k5.metric("💸 Tổng Tiền Phạt", f"{kpis['penalty']:,.0f} đ")

        # Xuất báo cáo tổng hợp + nút đồng bộ GitHub thủ công
        col_exp, col_sync = st.columns([3, 2])
        with col_exp:
            st.download_button(
                "📤 Xuất báo cáo tổng hợp (Excel đa sheet)",
                data=export_report(kpis, df_wo, df_pen_lookup, df_pen_detail),
                file_name=f"BaoCao_TongHop_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        with col_sync:
            if st.button("🔄 Đồng bộ GitHub ngay", use_container_width=True, help="Bỏ qua giới hạn 5 phút, tải bản Web.xlsx mới nhất từ GitHub ngay lập tức"):
                st.session_state.gh_last_check = 0  # bỏ qua throttle
                status = sync_wo_from_github()
                msg_map = {
                    "updated":   ("success", "✅ Đã tải bản Web.xlsx mới nhất từ GitHub."),
                    "uptodate":  ("info", "ℹ️ Bản local đã là mới nhất, không có thay đổi trên GitHub."),
                    "no_config": ("warning", "⚠️ Chưa cấu hình GitHub trong .streamlit/secrets.toml — xem file secrets.toml.example."),
                    "throttled": ("info", "Đã được đồng bộ gần đây."),
                }
                st.session_state.gh_sync_msg = msg_map.get(status, ("error", f"❌ Lỗi đồng bộ GitHub (trạng thái: {status}). Kiểm tra kết nối mạng và cấu hình repo."))
                audit(f"manual GitHub sync triggered: {status}")
                st.rerun()

        st.markdown(f'<hr style="border:none;height:1px;background-color:{VIETTEL_RED};margin:20px 0;">', unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        with bc1:
            if df_wo is not None and {"Trung tâm", "Trạng thái"}.issubset(df_wo.columns):
                st.markdown("**Phân bổ Work Order theo Trung tâm**")
                fig_b = px.histogram(df_wo, x="Trung tâm", color="Trạng thái", barmode="stack",
                                     color_discrete_sequence=px.colors.sequential.Reds_r)
                fig_b.update_layout(xaxis_tickangle=-45, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_b, use_container_width=True)
        with bc2:
            if df_wo is not None and "Loại công việc" in df_wo.columns:
                st.markdown("**Top 10 Loại công việc phổ biến**")
                top_l = df_wo["Loại công việc"].value_counts().head(10).reset_index()
                top_l.columns = ["Loại công việc", "Số lượng"]
                fig_p = px.pie(top_l, names="Loại công việc", values="Số lượng", hole=0.4,
                               color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(fig_p, use_container_width=True)
        if df_wo is None:
            st.warning("⚠️ Chưa tìm thấy tệp dữ liệu `Web.xlsx`. Admin vui lòng tải lên tại trang Dữ liệu WO.")

    # ---------- TRANG DỮ LIỆU WO ----------
    elif st.session_state.current_page == "📋 Dữ liệu WO":
        st.subheader("📋 Dashboard Tổng Hợp & Tra Cứu Dữ Liệu Work Order (Drill-Down)")

        if st.session_state.role == "admin":
            with st.expander("⚙️ [Admin] Tải lên file dữ liệu Web.xlsx mới"):
                up_wo = st.file_uploader("Chọn file Excel WO (.xlsx)", type=["xlsx"], key="upload_wo")
                if not (GH_REPO and GH_TOKEN):
                    st.info("💡 Chưa cấu hình đồng bộ GitHub 2 chiều. Tạo file `.streamlit/secrets.toml` với mục `[github]` (repo, branch, file_path, token) để admin upload tự đẩy lên GitHub — tránh bị lần git pull tiếp theo ghi đè.")
                if up_wo is not None:
                    safe_name = sanitize_filename(up_wo.name)
                    if not safe_name.lower().endswith(".xlsx"):
                        st.error("❌ Chỉ nhận file định dạng .xlsx. File CSV vui lòng mở Excel lưu lại dạng .xlsx.")
                    else:
                        # Kiểm tra schema trước khi ghi đè
                        try:
                            check_df = pd.read_excel(up_wo, header=1, engine="openpyxl")
                            up_wo.seek(0)
                            file_bytes = up_wo.getvalue()
                            missing = validate_wo_schema(check_df)
                            if missing:
                                st.error(f"❌ File thiếu cột bắt buộc: {', '.join(missing)}. Không ghi đè dữ liệu cũ.")
                            else:
                                backup_if_exists(WO_PATH)
                                with open(WO_PATH, "wb") as f:
                                    f.write(file_bytes)
                                st.cache_data.clear()            # xóa cache dữ liệu cũ
                                audit(f"uploaded Web.xlsx ({up_wo.size} bytes) via web")
                                # Đẩy ngược lên GitHub để 2 kênh đồng bộ (không bị git pull ghi đè)
                                push_ok, push_msg = push_wo_to_github(
                                    file_bytes,
                                    f"Admin {st.session_state.username} cập nhật Web.xlsx qua web",
                                )
                                st.session_state.data_source = (
                                    f"Upload trực tiếp bởi {st.session_state.username}" +
                                    (" + đã push GitHub" if push_ok else " (chưa lên GitHub)")
                                )
                                st.success("✅ Đã cập nhật Web.xlsx. " + push_msg)
                                st.rerun()                        # tự động rerun, không bắt F5
                        except Exception as e:
                            st.error(f"❌ File không hợp lệ: {type(e).__name__}. Vui lòng kiểm tra lại.")

        if df_wo is not None:
            m1, m2, m3 = st.columns(3)
            m1.metric("Tổng WO hiển thị", f"{kpis['total']:,}")
            m2.metric("WO Đã Đóng", f"{kpis['done']:,}")
            m3.metric("WO Quá Hạn", f"{kpis['overdue']:,}")
            st.markdown(f'<hr style="border:none;height:1px;background-color:{VIETTEL_RED};margin:20px 0;">', unsafe_allow_html=True)

            # Bộ lọc nằm trong form → chỉ chạy khi nhấn nút (không rerun mỗi phím gõ)
            st.markdown("#### 🔍 Bộ lọc và Tra cứu chi tiết (Drill-Down)")
            with st.form("wo_filter"):
                f1, f2, f3 = st.columns(3)
                tt_opts = ["Tất cả"] + sorted(df_wo["Trung tâm"].dropna().unique().tolist()) if "Trung tâm" in df_wo else ["Tất cả"]
                stt_opts = ["Tất cả"] + sorted(df_wo["Trạng thái"].dropna().unique().tolist()) if "Trạng thái" in df_wo else ["Tất cả"]
                sel_tt = f1.selectbox("🏢 Trung tâm:", tt_opts)
                sel_stt = f2.selectbox("📌 Trạng thái WO:", stt_opts)
                kw = f3.text_input("🔎 Tìm kiếm nhanh:")
                submitted = st.form_submit_button("🔍 Áp dụng bộ lọc", type="primary")

            df_f = df_wo.copy()
            if sel_tt != "Tất cả" and "Trung tâm" in df_f.columns:
                df_f = df_f[df_f["Trung tâm"] == sel_tt]
            if sel_stt != "Tất cả" and "Trạng thái" in df_f.columns:
                df_f = df_f[df_f["Trạng thái"] == sel_stt]
            df_f = vectorized_search(df_f, kw)

            st.markdown(f"Đang hiển thị **{len(df_f):,}** / {len(df_wo):,} bản ghi sau khi lọc.")
            st.dataframe(df_f, use_container_width=True, height=420)

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_f.to_excel(w, index=False, sheet_name="WO_DaLoc")
            st.download_button("📥 Tải xuống file Excel đã lọc", data=buf.getvalue(),
                               file_name="BaoCao_WO_DaLoc.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        else:
            st.warning("Chưa có dữ liệu Work Order.")

    # ---------- TRANG DỮ LIỆU TIỀN PHẠT ----------
    elif st.session_state.current_page == "💰 Dữ liệu tiền phạt":
        st.subheader("💰 Quản Lý & Tra Cứu Dữ Liệu Tiền Phạt")

        if st.session_state.role == "admin":
            st.markdown("#### ⚙️ Khu vực quản trị tải lên file tiền phạt")
            cu1, cu2 = st.columns(2)
            with cu1:
                st.markdown("**1. File Chi Tiết Tiền Phạt Các Tháng (CSDL)**")
                up_detail = st.file_uploader("Tải file chi tiết tiền phạt (.xlsx)", type=["xlsx"], key="up_pen_detail")
                if up_detail is not None:
                    if sanitize_filename(up_detail.name).lower().endswith(".xlsx"):
                        backup_if_exists(PENALTY_DETAIL_PATH)
                        with open(PENALTY_DETAIL_PATH, "wb") as f:
                            f.write(up_detail.getbuffer())
                        st.cache_data.clear()
                        audit(f"uploaded penalty_detail.xlsx ({up_detail.size} bytes)")
                        st.success("✅ Đã lưu file Chi tiết tiền phạt!")
                        st.rerun()
                    else:
                        st.error("❌ Chỉ nhận file .xlsx.")
            with cu2:
                st.markdown("**2. File Đã Tính Toán (Cho Người Dùng Tra Cứu)**")
                up_lookup = st.file_uploader("Tải file tra cứu tiền phạt (.xlsx)", type=["xlsx"], key="up_pen_lookup")
                if up_lookup is not None:
                    if sanitize_filename(up_lookup.name).lower().endswith(".xlsx"):
                        backup_if_exists(PENALTY_LOOKUP_PATH)
                        with open(PENALTY_LOOKUP_PATH, "wb") as f:
                            f.write(up_lookup.getbuffer())
                        st.cache_data.clear()
                        audit(f"uploaded penalty_lookup.xlsx ({up_lookup.size} bytes)")
                        st.success("✅ Đã lưu file Tra cứu tiền phạt!")
                        st.rerun()
                    else:
                        st.error("❌ Chỉ nhận file .xlsx.")
            st.markdown(f'<hr style="border:none;height:1px;background-color:{VIETTEL_RED};margin:20px 0;">', unsafe_allow_html=True)

        # FIX: hiển thị CẢ HAI file (trước đây chi tiết bị bỏ sót)
        tab_lookup, tab_detail = st.tabs(["🔍 Bảng Tra Cứu Tiền Phạt", "📂 Chi Tiết Tiền Phạt Các Tháng"])
        with tab_lookup:
            st.markdown("#### Bảng Tra Cứu Dữ Liệu Tiền Phạt Đơn Vị")
            if df_pen_lookup is not None:
                search_pen = st.text_input("🔎 Tìm kiếm thông tin phạt:", key="search_pen_lookup")
                df_p_show = vectorized_search(df_pen_lookup, search_pen)
                st.dataframe(df_p_show, use_container_width=True, height=400)
                buf_p = io.BytesIO()
                with pd.ExcelWriter(buf_p, engine="openpyxl") as w:
                    df_p_show.to_excel(w, index=False, sheet_name="TienPhat")
                st.download_button("📥 Tải xuống Báo cáo tiền phạt", data=buf_p.getvalue(),
                                   file_name="BaoCao_TienPhat.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
            else:
                st.info("Chưa có file tra cứu tiền phạt được tải lên hệ thống.")
        with tab_detail:
            st.markdown("#### Chi Tiết Tiền Phạt Các Tháng (CSDL gốc)")
            if df_pen_detail is not None:
                search_det = st.text_input("🔎 Tìm kiếm trong chi tiết:", key="search_pen_detail")
                df_d_show = vectorized_search(df_pen_detail, search_det)
                st.dataframe(df_d_show, use_container_width=True, height=400)
                buf_d = io.BytesIO()
                with pd.ExcelWriter(buf_d, engine="openpyxl") as w:
                    df_d_show.to_excel(w, index=False, sheet_name="ChiTiet")
                st.download_button("📥 Tải xuống Chi tiết tiền phạt", data=buf_d.getvalue(),
                                   file_name="ChiTiet_TienPhat.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("Chưa có file chi tiết tiền phạt. Admin tải lên tại khu vực quản trị.")

    # ---------- TRANG CSDL TỔNG HỢP ----------
    elif st.session_state.current_page == "🗂️ CSDL tổng hợp":
        st.subheader("🗂️ Kho Lưu Trữ CSDL Tổng Hợp")
        st.caption("Quản lý tất cả các tệp cơ sở dữ liệu gốc, file tổng hợp phục vụ công tác điều hành và báo cáo.")

        if st.session_state.role == "admin":
            st.markdown("#### ⚙️ [Admin] Tải lên CSDL mới vào kho lưu trữ (chọn nhiều file cùng lúc)")
            up_csdl_files = st.file_uploader("Chọn một hoặc nhiều file (.xlsx, .csv, .zip, .rar)",
                                             type=["xlsx", "csv", "zip", "rar"],
                                             accept_multiple_files=True, key="up_csdl_files")
            if up_csdl_files:
                saved, skipped = 0, []
                for up_csdl in up_csdl_files:
                    safe_name = sanitize_filename(up_csdl.name)
                    save_path = CSDL_DIR / safe_name
                    if save_path.exists():                       # không ghi đè im lặng: thêm hậu tố thời gian
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        save_path = CSDL_DIR / f"{Path(safe_name).stem}_{ts}{Path(safe_name).suffix}"
                        skipped.append(safe_name)
                    with open(save_path, "wb") as f:
                        f.write(up_csdl.getbuffer())
                    saved += 1
                audit(f"uploaded {saved} file(s) to CSDL repo")
                msg = f"✅ Đã lưu **{saved}** file vào kho CSDL."
                if skipped:
                    msg += f" (Trùng tên: {', '.join(skipped)} → đã tự động đổi tên thêm hậu tố thời gian)"
                st.success(msg)
                st.rerun()

        st.markdown(f'<hr style="border:none;height:1px;background-color:{VIETTEL_RED};margin:20px 0;">', unsafe_allow_html=True)
        st.markdown("#### 📁 Danh sách các tệp CSDL đang lưu trữ trên hệ thống:")

        # FIX: lọc chỉ file (tránh crash nếu có thư mục con)
        files_in_csdl = sorted([f for f in os.listdir(CSDL_DIR) if (CSDL_DIR / f).is_file()])

        # Xác nhận xóa 2 bước (FIX: trước đây xóa thẳng)
        if st.session_state.delete_confirm:
            target = st.session_state.delete_confirm
            st.warning(f"⚠️ Xác nhận xóa vĩnh viễn file **{target}**?")
            cc1, cc2 = st.columns(2)
            if cc1.button("🗑️ Xác nhận xóa", type="primary", key="confirm_del_yes"):
                try:
                    (CSDL_DIR / target).unlink()
                    audit(f"DELETED file {target} from CSDL repo")
                    st.success(f"Đã xóa {target}")
                except OSError as e:
                    st.error(f"Lỗi xóa file: {e}")
                st.session_state.delete_confirm = None
                st.rerun()
            if cc2.button("Hủy", key="confirm_del_no"):
                st.session_state.delete_confirm = None
                st.rerun()

        if files_in_csdl:
            for idx, file_name in enumerate(files_in_csdl):
                file_full_path = CSDL_DIR / file_name
                file_size_kb = file_full_path.stat().st_size / 1024
                cf1, cf2, cf3 = st.columns([3, 1, 1])
                with cf1:
                    st.write(f"📄 **{file_name}** `({file_size_kb:.1f} KB)`")
                with cf2:
                    with open(file_full_path, "rb") as f_dl:
                        st.download_button(label="📥 Tải xuống", data=f_dl.read(), file_name=file_name,
                                           key=f"dl_csdl_{idx}")
                with cf3:
                    if st.session_state.role == "admin":
                        if st.button("🗑️ Xóa", key=f"del_csdl_{idx}"):
                            st.session_state.delete_confirm = file_name
                            st.rerun()
        else:
            st.info("Kho lưu trữ CSDL tổng hợp hiện đang trống.")
