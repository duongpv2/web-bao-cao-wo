import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
from datetime import datetime

# 1. Cấu hình giao diện trang web toàn màn hình
st.set_page_config(
    page_title="Điều hành WO & Quản lý CSDL - P.VHKT - CNCTHNI",
    page_icon="🔴",
    layout="wide"
)

# Thư mục lưu trữ dữ liệu tải lên cục bộ
DATA_DIR = "uploaded_data"
os.makedirs(DATA_DIR, exist_ok=True)

# 2. Khởi tạo phiên làm việc (Session State) cho tài khoản
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

# Trạng thái mở popup menu tài khoản & modal đổi mật khẩu
if "show_user_menu" not in st.session_state:
    st.session_state.show_user_menu = False
if "show_change_pass_modal" not in st.session_state:
    st.session_state.show_change_pass_modal = False

# 3. CSS Tùy chỉnh giao diện (Tone đỏ Viettel sang trọng & thu gọn khoảng trắng)
st.markdown("""
    <style>
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    [data-testid="stHeader"] {
        display: none;
    }
    .stApp {
        background-color: #f4f6f9;
    }
    /* Vùng 1: Header chuyên nghiệp tích hợp Logo */
    .header-container {
        background: linear-gradient(90deg, #d90429 0%, #ef233c 100%);
        padding: 10px 20px;
        border-radius: 8px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(217, 4, 4, 0.2);
    }
    .header-title {
        font-size: 17px;
        font-weight: 700;
        margin: 0;
    }
    .header-info {
        font-size: 13px;
        opacity: 0.95;
    }
    /* Thẻ KPI */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 12px 18px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        border: 1px solid #e9ecef;
        border-left: 4px solid #d90429;
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
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #d90429; font-weight: 800; margin-bottom: 0;">VIETTEL CONSTRUCTION</h2>
                <p style="color: #555; font-size: 14px; font-weight: 500;">P.VHKT - CNCTHNI</p>
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
            <div style="text-align: center; margin-top: 15px; font-size: 12px; color: #888;">
                💡 <i>Mặc định: Quản trị (duongpv2 / admin123) | Nhân viên (user / user123)</i>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# GIAO DIỆN CHÍNH (3 VÙNG)
# ==========================================

# --- VÙNG 1: HEADER (Logo, P.VHKT - CNCTHNI, Giờ thực tế, Thông tin tài khoản click mở Menu) ---
current_time_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

col_h1, col_h2, col_h3 = st.columns([0.6, 2.4, 2])
with col_h1:
    # Chèn Logo Viettel Construction chuẩn từ URL
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Viettel_logo_2021.svg/1200px-Viettel_logo_2021.svg.png", width=120)
with col_h2:
    st.markdown(f"""
        <div style="padding-top: 5px;">
            <p class="header-title" style="color: #d90429; font-size: 16px; font-weight: 800; margin:0;">VIETTEL CONSTRUCTION | P.VHKT - CNCTHNI</p>
            <span style="color: #555; font-size: 13px; font-weight: 600;">Điều hành WO & Quản lý CSDL</span>
        </div>
    """, unsafe_allow_html=True)
with col_h3:
    st.markdown(f"""
        <div style="text-align: right; padding-top: 5px;">
            <div style="font-size: 12px; color: #444;">📅 <b>{current_time_str}</b></div>
        </div>
    """, unsafe_allow_html=True)

# Khung tài khoản với menu tương tác click
col_acc1, col_acc2 = st.columns([5, 1])
with col_acc2:
    role_label = "(ADMIN)" if st.session_state.role == "admin" else "(USER)"
    if st.button(f"👤 {st.session_state.name} {role_label} ▼", use_container_width=True):
        st.session_state.show_user_menu = not st.session_state.show_user_menu

# Hiển thị Menu tài khoản (Đổi mật khẩu / Đăng xuất) khi click
if st.session_state.show_user_menu:
    with st.container():
        st.markdown("""
            <div style="background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #ddd; float: right; width: 220px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); z-index: 999; margin-bottom: 10px;">
        """, unsafe_allow_html=True)
        if st.button("🔐 Đổi mật khẩu cá nhân", use_container_width=True):
            st.session_state.show_change_pass_modal = True
            st.session_state.show_user_menu = False
            st.rerun()
        if st.button("🚪 Đăng xuất hệ thống", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.show_user_menu = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Popup Modal đổi mật khẩu
if st.session_state.show_change_pass_modal:
    with st.expander("🔐 Hộp thoại đổi mật khẩu", expanded=True):
        with st.form("modal_change_pass"):
            old_p = st.text_input("Mật khẩu cũ", type="password")
            new_p = st.text_input("Mật khẩu mới", type="password")
            confirm_p = st.text_input("Xác nhận mật khẩu mới", type="password")
            c_sub1, c_sub2 = st.columns(2)
            btn_up_pass = c_sub1.form_submit_button("Xác nhận đổi")
            btn_cancel = c_sub2.form_submit_button("Đóng")
            
            if btn_up_pass:
                cur_user = st.session_state.username
                if old_p == st.session_state.users_db[cur_user]["pass"]:
                    if new_p and new_p == confirm_p:
                        st.session_state.users_db[cur_user]["pass"] = new_p
                        st.success("Đổi mật khẩu thành công!")
                        st.session_state.show_change_pass_modal = False
                    else:
                        st.error("Mật khẩu mới không khớp hoặc trống.")
                else:
                    st.error("Mật khẩu cũ không chính xác.")
            if btn_cancel:
                st.session_state.show_change_pass_modal = False
                st.rerun()

st.divider()

# --- VÙNG 2: SIDEBAR (Menu chức năng điều hướng) ---
with st.sidebar:
    st.markdown("### 🗂️ MENU ĐIỀU HƯỚNG")
    menu_selection = st.radio(
        "Chọn chức năng:",
        ["📊 Dashboard", "📋 Dữ liệu WO", "💰 Dữ liệu tiền phạt", "🗂️ CSDL tổng hợp"],
        label_visibility="collapsed"
    )


# --- HÀM HỖ TRỢ ĐỌC DỮ LIỆU ---
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


# --- VÙNG 3: HIỂN THỊ NỘI DUNG THEO MỤC CHỌN Ở VÙNG 2 ---

if menu_selection == "📊 Dashboard":
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


elif menu_selection == "📋 Dữ liệu WO":
    st.subheader("📋 Dashboard Tổng Hợp & Tra Cứu Dữ Liệu Work Order (Drill-Down)")
    
    # Cho phép Admin upload file mới
    if st.session_state.role == "admin":
        with st.expander("⚙️ [Admin] Tải lên file dữ liệu Web.xlsx mới"):
            up_wo = st.file_uploader("Chọn file Excel WO (.xlsx)", type=["xlsx", "csv"], key="upload_wo")
            if up_wo is not None:
                with open(wo_path, "wb") as f:
                    f.write(up_wo.getbuffer())
                st.success("Đã cập nhật file Web.xlsx thành công! Hãy F5 tải lại trang.")
                
    if df_wo is not None:
        # 1. Hiển thị Dashboard thu gọn ngay trong mục Dữ liệu WO
        tot_wo = len(df_wo)
        cl_dong = len(df_wo[df_wo['Trạng thái'] == 'Đóng']) if 'Trạng thái' in df_wo.columns else 0
        cl_qh = int(df_wo['Quá hạn'].sum()) if 'Quá hạn' in df_wo.columns else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng WO hiển thị", f"{tot_wo:,}")
        m2.metric("WO Đã Đóng", f"{cl_dong:,}")
        m3.metric("WO Quá Hạn", f"{cl_qh:,}")
        
        st.markdown("---")
        
        # 2. Khung Drill-down bộ lọc và Tra cứu Excel
        st.markdown("#### 🔍 Bộ lọc và Tra cứu chi tiết")
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
        st.download_button("📥 Tải xuống file Excel đã lọc", data=buf.getvalue(), file_name="BaoCao_WO_DaLoc.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("Chưa có dữ liệu Work Order.")


elif menu_selection == "💰 Dữ liệu tiền phạt":
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
        st.download_button("📥 Tải xuống file Báo cáo tiền phạt", data=buf_p.getvalue(), file_name="BaoCao_TienPhat.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Chưa có file tra cứu tiền phạt được tải lên hệ thống.")


elif menu_selection == "🗂️ CSDL tổng hợp":
    st.subheader("🗂️ Kho Lưu Trữ CSDL Tổng Hợp")
    st.caption("Quản lý tất cả các tệp cơ sở dữ liệu gốc, file tổng hợp phục vụ công tác điều hành và báo cáo.")
    
    CSDL_DIR = "csdl_tong_hop"
    os.makedirs(CSDL_DIR, exist_ok=True)
    
    if st.session_state.role == "admin":
        st.markdown("#### ⚙️ [Admin] Tải lên CSDL mới vào kho lưu trữ")
        up_csdl = st.file_uploader("Chọn file cơ sở dữ liệu (.xlsx, .csv, .zip)", type=["xlsx", "csv", "zip", "rar"], key="up_csdl_files")
        if up_csdl is not None:
            save_path = os.path.join(CSDL_DIR, up_csdl.name)
            with open(save_path, "wb") as f:
                f.write(up_csdl.getbuffer())
            st.success(f"Đã lưu thành công file `{up_csdl.name}` vào kho CSDL tổng hợp!")
            
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