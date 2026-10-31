import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import io
import os
from datetime import datetime, timezone, timedelta

# 1. Cấu hình giao diện trang web toàn màn hình
st.set_page_config(
    page_title="Điều hành WO & Quản lý CSDL - P.VHKT - CNCTHNI",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thư mục lưu trữ dữ liệu
DATA_DIR = "uploaded_data"
CSDL_DIR = "csdl_tong_hop"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CSDL_DIR, exist_ok=True)

# 2. Quản lý trạng thái phiên đăng nhập và điều hướng (Giữ nguyên khi F5)
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "duongpv2": {"pass": "admin123", "role": "admin", "name": "Phạm Văn Dương"},
        "user": {"pass": "user123", "role": "viewer", "name": "Cán bộ / Nhân viên"}
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.name = ""

if "current_page" not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"

if "action_view" not in st.session_state:
    st.session_state.action_view = "normal"

# 3. CSS Tùy chỉnh giao diện: Vùng 1 & Vùng 2 màu đỏ Viettel, Vùng 3 nền sáng sạch sẽ
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    [data-testid="stHeader"] {
        display: none;
    }
    /* Tổng thể ứng dụng nền sáng trung tính cho vùng nội dung */
    .stApp {
        background-color: #f4f6f9 !important;
    }
    /* VÙNG 2: Sidebar (Menu điều hướng) mang màu đỏ Viettel đặc trưng */
    [data-testid="stSidebar"] {
        background-color: #a61c1c !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    /* Tùy chỉnh radio button trong sidebar dễ nhìn hơn */
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 6px;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }
    /* Thẻ KPI và nội dung vùng chính */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 12px 18px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #d90429;
    }
    /* Nút bấm chủ đạo */
    .stButton button[kind="primary"] {
        background-color: #d90429 !important;
        border-color: #d90429 !important;
        color: white !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #8b0000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# MÀN HÌNH ĐĂNG NHẬP
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 20px; background: #ffffff; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 6px solid #d90429;">
                <div style="font-family: sans-serif; font-size: 28px; font-weight: 900; color: #d90429; letter-spacing: -0.5px;">viettel</div>
                <div style="font-family: sans-serif; font-size: 15px; font-weight: 600; color: #212529; letter-spacing: 0.5px; margin-top: -4px;">construction</div>
                <h4 style="color: #d90429; font-weight: 800; margin: 15px 0 2px 0;">P.VHKT - CNCTHNI</h4>
                <p style="color: #6c757d; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Hệ thống Điều hành & Quản lý CSDL</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### **Đăng nhập hệ thống**")
            st.caption("Vui lòng nhập thông tin tài khoản để tiếp tục")
            
            input_user = st.text_input("Tài khoản đăng nhập", placeholder="Nhập tên đăng nhập (VD: duongpv2)...")
            input_pass = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
            
            submit_login = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")
            
            if submit_login:
                if input_user in st.session_state.users_db and st.session_state.users_db[input_user]["pass"] == input_pass:
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.session_state.role = st.session_state.users_db[input_user]["role"]
                    st.session_state.name = st.session_state.users_db[input_user]["name"]
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("⚠️ Sai tài khoản hoặc mật khẩu. Vui lòng kiểm tra lại!")
        
        st.markdown("""
            <div style="text-align: center; margin-top: 15px; font-size: 12px; color: #555;">
                💡 <i>Mặc định: Quản trị (duongpv2 / admin123) | Nhân viên (user / user123)</i>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# GIAO DIỆN CHÍNH (3 VÙNG CHUẨN DOANH NGHIỆP)
# ==========================================

# --- VÙNG 1: HEADER ---
col_h1, col_h2, col_h3 = st.columns([2.5, 2, 1.5])
with col_h1:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; background: linear-gradient(90deg, #d90429 0%, #a61c1c 100%); padding: 12px 18px; border-radius: 8px; box-shadow: 0 4px 10px rgba(217, 4, 4, 0.2); color: white;">
            <div style="line-height: 1.1;">
                <span style="font-family: sans-serif; font-size: 18px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px;">viettel</span>
                <span style="font-family: sans-serif; font-size: 10px; font-weight: 600; color: #ffcccc; display: block; letter-spacing: 0.5px;">construction</span>
            </div>
            <div style="border-left: 2px solid rgba(255,255,255,0.4); padding-left: 12px;">
                <p style="color: #ffffff; font-size: 13px; font-weight: 800; margin: 0;">P.VHKT - CNCTHNI</p>
                <span style="color: #ffcccc; font-size: 10px; font-weight: 600;">Điều hành WO & CSDL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_h2:
    # Đồng hồ chạy trực tiếp thời gian thực bằng JavaScript theo giờ VN (UTC+7)
    clock_html = """
    <div style="text-align: center; padding-top: 6px;">
        <div id="live-clock" style="font-size: 13px; color: #ffffff; background: #a61c1c; padding: 10px 15px; border-radius: 8px; display: inline-block; font-weight: 700; box-shadow: 0 4px 8px rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.2);">
            📅 Đang đồng bộ thời gian...
        </div>
    </div>
    <script>
    function updateClock() {
        const now = new Date();
        const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
        const vnTime = new Date(utc + (3600000 * 7));
        
        const day = String(vnTime.getDate()).padStart(2, '0');
        const month = String(vnTime.getMonth() + 1).padStart(2, '0');
        const year = vnTime.getFullYear();
        const hours = String(vnTime.getHours()).padStart(2, '0');
        const minutes = String(vnTime.getMinutes()).padStart(2, '0');
        const seconds = String(vnTime.getSeconds()).padStart(2, '0');
        
        const timeString = `📅 ${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
        const elem = document.getElementById('live-clock');
        if (elem) {
            elem.innerText = timeString;
        }
    }
    setInterval(updateClock, 1000);
    updateClock();
    </script>
    """
    components.html(clock_html, height=45)

with col_h3:
    role_label = "ADMIN" if st.session_state.role == "admin" else "USER"
    with st.popover(f"👤 {st.session_state.name} ({role_label})", use_container_width=True):
        st.markdown(f"**Tài khoản:** `{st.session_state.username}`")
        st.markdown(f"**Phân quyền:** `{role_label}`")
        st.markdown("---")
        if st.button("🔐 Đổi mật khẩu cá nhân", use_container_width=True):
            st.session_state.action_view = "change_pass"
            st.rerun()
        if st.button("🚪 Đăng xuất hệ thống", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.action_view = "normal"
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Xử lý giao diện đổi mật khẩu
if st.session_state.action_view == "change_pass":
    st.markdown("""
        <div style="background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <h3 style="color: #d90429;">🔐 Thay đổi mật khẩu tài khoản</h3>
    """, unsafe_allow_html=True)
    with st.form("form_change_password"):
        old_p = st.text_input("Mật khẩu cũ", type="password")
        new_p = st.text_input("Mật khẩu mới", type="password")
        confirm_p = st.text_input("Xác nhận mật khẩu mới", type="password")
        
        c_sub1, c_sub2 = st.columns(2)
        btn_update = c_sub1.form_submit_button("Xác nhận thay đổi", type="primary")
        btn_back = c_sub2.form_submit_button("Quay lại trang chính")
        
        if btn_update:
            cur_user = st.session_state.username
            if old_p == st.session_state.users_db[cur_user]["pass"]:
                if new_p and new_p == confirm_p:
                    st.session_state.users_db[cur_user]["pass"] = new_p
                    st.success("Đổi mật khẩu thành công! Vui lòng ghi nhớ mật khẩu mới.")
                    st.session_state.action_view = "normal"
                else:
                    st.error("Mật khẩu mới không khớp hoặc bị để trống.")
            else:
                st.error("Mật khẩu cũ không chính xác.")
        if btn_back:
            st.session_state.action_view = "normal"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- VÙNG 2: SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 15px 0; border-bottom: 2px solid rgba(255,255,255,0.3); margin-bottom: 15px;">
            <span style="font-family: sans-serif; font-size: 18px; font-weight: 900; color: #ffffff;">viettel</span>
            <span style="font-family: sans-serif; font-size: 11px; font-weight: 600; color: #ffcccc; display: block;">construction</span>
            <h5 style="color: #ffffff; margin: 8px 0 0 0; font-weight: 800;">QUẢN LÝ ĐIỀU HÀNH</h5>
        </div>
    """, unsafe_allow_html=True)
    
    menu_options = ["📊 Dashboard", "📋 Dữ liệu WO", "💰 Dữ liệu tiền phạt", "🗂️ CSDL tổng hợp"]
    
    selected_menu = st.radio(
        "Chọn chức năng:",
        menu_options,
        index=menu_options.index(st.session_state.current_page) if st.session_state.current_page in menu_options else 0,
        label_visibility="collapsed"
    )
    st.session_state.current_page = selected_menu

# --- HÀM ĐỌC DỮ LIỆU ---
@st.cache_data
def load_excel_file(file_path, header_row=0):
    try:
        if os.path.exists(file_path):
            return pd.read_excel(file_path, header=header_row, engine="calamine")
    except Exception:
        pass
    return None

wo_path = "Web.xlsx"
penalty_lookup_path = os.path.join(DATA_DIR, "penalty_lookup.xlsx")
penalty_detail_path = os.path.join(DATA_DIR, "penalty_detail.xlsx")

df_wo = load_excel_file(wo_path, header_row=1)
df_pen_lookup = load_excel_file(penalty_lookup_path, header_row=0)

# --- VÙNG 3: HIỂN THỊ NỘI DUNG ---
with st.container():
    if st.session_state.current_page == "📊 Dashboard":
        st.subheader("📊 Tổng Quan Chỉ Số Work Order & Tài Chính")
        
        if df_wo is not None:
            total_wo = len(df_wo)
            dong_count = len(df_wo[df_wo['Trạng thái'] == 'Đóng']) if 'Trạng thái' in df_wo.columns else 0
            dang_xu_ly = total_wo - dong_count
            quahan_count = int(df_wo['Quá hạn'].sum()) if 'Quá hạn' in df_wo.columns else 0
            
            total_unit_penalty = 0
            if df_pen_lookup is not None:
                for col in df_pen_lookup.columns:
                    if 'phạt' in str(col).lower() or 'tiền' in str(col).lower():
                        try:
                            total_unit_penalty = pd.to_numeric(df_pen_lookup[col], errors='coerce').sum()
                            break
                        except:
                            pass
            if total_unit_penalty == 0 and df_wo is not None and 'Tổng tiền phạt' in df_wo.columns:
                total_unit_penalty = df_wo['Tổng tiền phạt'].sum()

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("📦 Tổng WO", f"{total_wo:,}")
            k2.metric("⏳ Đang Thực Hiện", f"{dang_xu_ly:,}")
            k3.metric("✅ Đã Đóng", f"{dong_count:,}")
            k4.metric("⚠️ Quá Hạn", f"{quahan_count:,}", delta="Cần xử lý", delta_color="inverse")
            k5.metric("💸 Tổng Tiền Phạt Đơn Vị", f"{total_unit_penalty:,.0f} đ")
            
            st.markdown("---")
            
            bc1, bc2 = st.columns(2)
            with bc1:
                if 'Trung tâm' in df_wo.columns and 'Trạng thái' in df_wo.columns:
                    st.markdown("**Phân bổ Work Order theo Trung tâm**")
                    fig_b = px.histogram(df_wo, x="Trung tâm", color="Trạng thái", barmode="stack", color_discrete_sequence=px.colors.sequential.Reds_r)
                    fig_b.update_layout(xaxis_tickangle=-45, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_b, use_container_width=True)
            with bc2:
                if 'Loại công việc' in df_wo.columns:
                    st.markdown("**Top 10 Loại công việc phổ biến**")
                    top_l = df_wo['Loại công việc'].value_counts().head(10).reset_index()
                    top_l.columns = ['Loại công việc', 'Số lượng']
                    fig_p = px.pie(top_l, names='Loại công việc', values='Số lượng', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                    st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.warning("⚠️ Chưa tìm thấy tệp dữ liệu `Web.xlsx`.")

    elif st.session_state.current_page == "📋 Dữ liệu WO":
        st.subheader("📋 Dashboard Tổng Hợp & Tra Cứu Dữ Liệu Work Order (Drill-Down)")
        
        if st.session_state.role == "admin":
            with st.expander("⚙️ [Admin] Tải lên file dữ liệu Web.xlsx mới"):
                up_wo = st.file_uploader("Chọn file Excel WO (.xlsx)", type=["xlsx", "csv"], key="upload_wo")
                if up_wo is not None:
                    with open(wo_path, "wb") as f:
                        f.write(up_wo.getbuffer())
                    st.success("Đã cập nhật file Web.xlsx thành công! Hãy F5 tải lại trang.")
                    
        if df_wo is not None:
            tot_wo = len(df_wo)
            cl_dong = len(df_wo[df_wo['Trạng thái'] == 'Đóng']) if 'Trạng thái' in df_wo.columns else 0
            cl_qh = int(df_wo['Quá hạn'].sum()) if 'Quá hạn' in df_wo.columns else 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Tổng WO hiển thị", f"{tot_wo:,}")
            m2.metric("WO Đã Đóng", f"{cl_dong:,}")
            m3.metric("WO Quá Hạn", f"{cl_qh:,}")
            
            st.markdown("---")
            
            st.markdown("#### 🔍 Bộ lọc và Tra cứu chi tiết (Drill-Down)")
            f1, f2, f3 = st.columns(3)
            with f1:
                sel_tt = st.selectbox("🏢 Trung tâm:", ["Tất cả"] + sorted(df_wo['Trung tâm'].dropna().unique().tolist()))
            with f2:
                sel_tts = st.selectbox("📌 Trạng thái WO:", ["Tất cả"] + sorted(df_wo['Trạng thái'].dropna().unique().tolist()))
            with f3:
                kw = st.text_input("🔎 Tìm kiếm nhanh:")
                
            df_f = df_wo.copy()
            if sel_tt != "Tất cả":
                df_f = df_f[df_f['Trung tâm'] == sel_tt]
            if sel_tts != "Tất cả":
                df_f = df_f[df_f['Trạng thái'] == sel_tts]
            if kw:
                mask = df_f.astype(str).apply(lambda x: x.str.contains(kw, case=False, na=False)).any(axis=1)
                df_f = df_f[mask]
                
            st.markdown(f"Đang hiển thị **{len(df_f):,}** / {len(df_wo):,} bản ghi sau khi lọc.")
            st.dataframe(df_f, use_container_width=True, height=420)
            
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df_f.to_excel(writer, index=False, sheet_name='WO_DaLoc')
            st.download_button("📥 Tải xuống file Excel đã lọc", data=buf.getvalue(), file_name="BaoCao_WO_DaLoc.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        else:
            st.warning("Chưa có dữ liệu Work Order.")

    elif st.session_state.current_page == "💰 Dữ liệu tiền phạt":
        st.subheader("💰 Quản Lý & Tra Cứu Dữ Liệu Tiền Phạt")
        
        if st.session_state.role == "admin":
            st.markdown("#### ⚙️ Khu vực quản trị tải lên file tiền phạt")
            col_up1, col_up2 = st.columns(2)
            with col_up1:
                st.markdown("**1. File Chi Tiết Tiền Phạt Các Tháng (CSDL)**")
                up_detail = st.file_uploader("Tải file chi tiết tiền phạt", type=["xlsx", "csv"], key="up_pen_detail")
                if up_detail is not None:
                    with open(penalty_detail_path, "wb") as f:
                        f.write(up_detail.getbuffer())
                    st.success("Đã lưu file Chi tiết tiền phạt!")
            with col_up2:
                st.markdown("**2. File Đã Tính Toán (Cho Người Dùng Tra Cứu)**")
                up_lookup = st.file_uploader("Tải file tra cứu tiền phạt", type=["xlsx", "csv"], key="up_pen_lookup")
                if up_lookup is not None:
                    with open(penalty_lookup_path, "wb") as f:
                        f.write(up_lookup.getbuffer())
                    st.success("Đã lưu file Tra cứu tiền phạt! Hãy F5 để xem.")
            st.markdown("---")
            
        st.markdown("#### 🔍 Bảng Tra Cứu Dữ Liệu Tiền Phạt Đơn Vị")
        if df_pen_lookup is not None:
            search_pen = st.text_input("🔎 Tìm kiếm thông tin phạt:")
            df_p_show = df_pen_lookup.copy()
            if search_pen:
                mask_p = df_p_show.astype(str).apply(lambda x: x.str.contains(search_pen, case=False, na=False)).any(axis=1)
                df_p_show = df_p_show[mask_p]
                
            st.dataframe(df_p_show, use_container_width=True, height=400)
            
            buf_p = io.BytesIO()
            with pd.ExcelWriter(buf_p, engine='openpyxl') as writer:
                df_p_show.to_excel(writer, index=False, sheet_name='TienPhat')
            st.download_button("📥 Tải xuống file Báo cáo tiền phạt", data=buf_p.getvalue(), file_name="BaoCao_TienPhat.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        else:
            st.info("Chưa có file tra cứu tiền phạt được tải lên hệ thống.")

    elif st.session_state.current_page == "🗂️ CSDL tổng hợp":
        st.subheader("🗂️ Kho Lưu Trữ CSDL Tổng Hợp")
        st.caption("Quản lý tất cả các tệp cơ sở dữ liệu gốc, file tổng hợp phục vụ công tác điều hành và báo cáo.")
        
        if st.session_state.role == "admin":
            st.markdown("#### ⚙️ [Admin] Tải lên CSDL mới vào kho lưu trữ (Chọn nhiều file cùng lúc)")
            up_csdl_files = st.file_uploader("Chọn một hoặc nhiều file cơ sở dữ liệu (.xlsx, .csv, .zip)", type=["xlsx", "csv", "zip", "rar"], accept_multiple_files=True, key="up_csdl_files")
            if up_csdl_files:
                for up_csdl in up_csdl_files:
                    save_path = os.path.join(CSDL_DIR, up_csdl.name)
                    with open(save_path, "wb") as f:
                        f.write(up_csdl.getbuffer())
                st.success(f"Đã tải lên và lưu thành công **{len(up_csdl_files)}** file vào kho CSDL tổng hợp!")
                st.rerun()
                
        st.markdown("#### 📁 Danh sách các tệp CSDL đang lưu trữ trên hệ thống:")
        files_in_csdl = os.listdir(CSDL_DIR)
        
        if files_in_csdl:
            for idx, file_name in enumerate(files_in_csdl):
                file_full_path = os.path.join(CSDL_DIR, file_name)
                file_size_kb = os.path.getsize(file_full_path) / 1024
                
                c_f1, c_f2, c_f3 = st.columns([3, 1, 1])
                with c_f1:
                    st.write(f"📄 **{file_name}** `({file_size_kb:.1f} KB)`")
                with c_f2:
                    with open(file_full_path, "rb") as f_dl:
                        st.download_button(
                            label="📥 Tải xuống",
                            data=f_dl,
                            file_name=file_name,
                            key=f"dl_csdl_{idx}"
                        )
                with c_f3:
                    if st.session_state.role == "admin":
                        if st.button("🗑️ Xóa", key=f"del_csdl_{idx}"):
                            os.remove(file_full_path)
                            st.success(f"Đã xóa {file_name}")
                            st.rerun()
        else:
            st.info("Kho lưu trữ CSDL tổng hợp hiện đang trống.")

<ElicitationsGroup>
</ElicitationsGroup>