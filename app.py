import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. Cấu hình trang
st.set_page_config(
    page_title="CƠ SỞ DỮ LIỆU & Điều Hành WO",
    page_icon="🔴",
    layout="wide"
)

# 2. Khởi tạo danh sách tài khoản trong st.session_state (nếu chưa có)
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "duongpv2": {"pass": "admin123", "role": "admin", "name": "Duongpv2 Quản trị viên"},
        "user": {"pass": "user123", "role": "viewer", "name": "Cán bộ / Nhân viên"}
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.name = ""

# 3. Giao diện CSS tùy chỉnh (Tone đỏ Viettel sang trọng)
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
    }
    /* Khung đăng nhập trung tâm */
    .login-container {
        max-width: 420px;
        margin: 80px auto;
        padding: 40px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(217, 4, 4, 0.15);
        border-top: 5px solid #d90429;
    }
    /* Tiêu đề ứng dụng */
    .main-header {
        font-size: 24px;
        font-weight: 700;
        color: #d90429;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 13px;
        color: #6c757d;
        margin-bottom: 20px;
    }
    /* Thẻ KPI */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        border: 1px solid #e9ecef;
        border-left: 4px solid #d90429;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# PHẦN 1: MÀN HÌNH ĐĂNG NHẬP (LOGIN SCREEN)
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #d90429; font-weight: 800; margin-bottom: 0;">VIETTEL CONSTRUCTION</h2>
                <p style="color: #555; font-size: 14px; font-weight: 500;">CƠ SỞ DỮ LIỆU & Điều Hành WO</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### **Đăng nhập hệ thống**")
            st.caption("Vui lòng nhập thông tin tài khoản để tiếp tục")
            
            input_user = st.text_input("Tài khoản đăng nhập", placeholder="Nhập tên đăng nhập...")
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
                💡 <i>Mặc định: Admin (admin / admin123) | Nhân viên (user / user123)</i>
            </div>
        """, unsafe_allow_html=True)
        
    st.stop()  # Dừng code bên dưới nếu chưa đăng nhập

# ==========================================
# PHẦN 2: GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP
# ==========================================

# Sidebar thông tin tài khoản & menu
with st.sidebar:
    st.markdown("### 🔴 VIETTEL CONSTRUCTION")
    st.info(f"👤 **Xin chào:** {st.session_state.name}\n\n🔑 **Quyền hạn:** `{st.session_state.role.upper()}`")
    
    st.markdown("---")
    
    # Khu vực Đổi mật khẩu
    with st.expander("🔐 Đổi mật khẩu tài khoản"):
        with st.form("change_pass_form"):
            old_p = st.text_input("Mật khẩu cũ", type="password")
            new_p = st.text_input("Mật khẩu mới", type="password")
            confirm_p = st.text_input("Xác nhận mật khẩu mới", type="password")
            btn_change = st.form_submit_button("Cập nhật mật khẩu")
            
            if btn_change:
                cur_user = st.session_state.username
                if old_p == st.session_state.users_db[cur_user]["pass"]:
                    if new_p and new_p == confirm_p:
                        st.session_state.users_db[cur_user]["pass"] = new_p
                        st.success("Đổi mật khẩu thành công! Hãy nhớ mật khẩu mới cho lần đăng nhập sau.")
                    else:
                        st.error("Mật khẩu mới không khớp hoặc để trống.")
                else:
                    st.error("Mật khẩu cũ không chính xác.")

    # Nút Đăng xuất
    if st.button("🚪 Đăng xuất hệ thống", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# Tiêu đề trang chính
st.markdown('<div class="main-header">🔴 CƠ SỞ DỮ LIỆU & Điều Hành WO</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Báo cáo, tra cứu dữ liệu và phân tích chỉ số chuyên sâu theo thời gian thực.</div>', unsafe_allow_html=True)

# 3. Tải dữ liệu (Ưu tiên đọc Web.xlsx có sẵn)
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('Web.xlsx', header=1)
        return df
    except Exception:
        return None

df = load_data()

# 4. CHỈ QUẢN TRỊ VIÊN (ADMIN) MỚI CÓ QUYỀN UPLOAD/THAY ĐỔI DỮ LIỆU
if st.session_state.role == "admin":
    with st.sidebar:
        st.markdown("---")
        st.subheader("⚙️ Quản trị dữ liệu (Admin)")
        uploaded_file = st.file_uploader("📂 Tải lên báo cáo Web.xlsx mới", type=["xlsx", "csv"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file, header=1, engine="calamine")
            st.success("Đã cập nhật dữ liệu mới thành công!")
else:
    if df is None:
        st.warning("⚠️ Hệ thống chưa có dữ liệu. Vui lòng liên hệ Quản trị viên (Admin) để cập nhật tệp Web.xlsx.")
        st.stop()

if df is None:
    st.warning("⚠️ Không tìm thấy file dữ liệu mặc định Web.xlsx trên hệ thống.")
    st.stop()

# 5. Thống kê KPI cốt lõi
total_wo = len(df)
dong_count = len(df[df['Trạng thái'] == 'Đóng']) if 'Trạng thái' in df.columns else 0
dang_xu_ly = total_wo - dong_count
quahan_count = int(df['Quá hạn'].sum()) if 'Quá hạn' in df.columns else 0
total_penalty = df['Tổng tiền phạt'].sum() if 'Tổng tiền phạt' in df.columns else 0

# Hiển thị các khối thẻ KPI
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("📦 Tổng WO", f"{total_wo:,}")
kpi2.metric("⏳ Đang Thực Hiện", f"{dang_xu_ly:,}")
kpi3.metric("✅ Đã Đóng", f"{dong_count:,}")
kpi4.metric("⚠️ Quá Hạn", f"{quahan_count:,}", delta="Cần xử lý", delta_color="inverse")
kpi5.metric("💸 Tổng Phạt", f"{total_penalty:,.0f} đ")

st.markdown("<br>", unsafe_allow_html=True)

# 6. Phân chia Tab chức năng giao diện quản trị
tab1, tab2, tab3 = st.tabs(["📊 Biểu Đồ & Thống Kê", "📋 Tra Cứu Chi Tiết (Drill-Down)", "💰 Chi Tiết Tiền Phạt"])

with tab1:
    st.subheader("📈 Phân tích trực quan dữ liệu Work Order")
    c1, c2 = st.columns(2)
    with c1:
        if 'Trung tâm' in df.columns and 'Trạng thái' in df.columns:
            st.markdown("**Phân bổ WO theo Trung tâm & Trạng thái**")
            fig_bar = px.histogram(df, x="Trung tâm", color="Trạng thái", barmode="stack", color_discrete_sequence=px.colors.sequential.Reds_r)
            fig_bar.update_layout(xaxis_tickangle=-45, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        if 'Loại công việc' in df.columns:
            st.markdown("**Top 10 Loại công việc chiếm tỷ trọng cao nhất**")
            top_loai = df['Loại công việc'].value_counts().head(10).reset_index()
            top_loai.columns = ['Loại công việc', 'Số lượng']
            fig_pie = px.pie(top_loai, names='Loại công việc', values='Số lượng', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("🔍 Bộ lọc tương tác thông minh")
    f1, f2, f3 = st.columns(3)
    with f1:
        selected_tt = st.selectbox("🏢 Trung tâm:", ["Tất cả"] + sorted(df['Trung tâm'].dropna().unique().tolist()))
    with f2:
        selected_tthai = st.selectbox("📌 Trạng thái WO:", ["Tất cả"] + sorted(df['Trạng thái'].dropna().unique().tolist()))
    with f3:
        search_kw = st.text_input("🔎 Tìm kiếm nhanh (Mã công việc, nhân viên...):")

    df_filtered = df.copy()
    if selected_tt != "Tất cả":
        df_filtered = df_filtered[df_filtered['Trung tâm'] == selected_tt]
    if selected_tthai != "Tất cả":
        df_filtered = df_filtered[df_filtered['Trạng thái'] == selected_tthai]
    if search_kw:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_kw, case=False, na=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    st.markdown(f"Đang hiển thị **{len(df_filtered):,}** / {total_wo:,} bản ghi dữ liệu.")
    st.dataframe(df_filtered, use_container_width=True, height=450)

    # Nút xuất Excel (Cả Admin và User đều được phép tải file về)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Data_WO')
    st.download_button(
        label="📥 Tải file Excel chi tiết (Đã lọc)",
        data=buffer.getvalue(),
        file_name="BaoCao_WO_DaLoc.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with tab3:
    st.subheader("💸 Thống kê tiền phạt vi phạm")
    if 'Tổng tiền phạt' in df.columns:
        pf1, pf2 = st.columns(2)
        with pf1:
            st.markdown("**Top 10 Trung tâm có tổng tiền phạt cao nhất**")
            penalty_by_tt = df.groupby('Trung tâm')['Tổng tiền phạt'].sum().reset_index().sort_values(by='Tổng tiền phạt', ascending=False).head(10)
            fig_pen = px.bar(penalty_by_tt, x='Trung tâm', y='Tổng tiền phạt', text_auto='.2s', color='Tổng tiền phạt', color_continuous_scale='Reds')
            st.plotly_chart(fig_pen, use_container_width=True)
        with pf2:
            st.markdown("**Bảng tổng hợp phạt theo Nhân viên thực hiện**")
            if 'Nhân viên thực hiện' in df.columns:
                pen_nv = df.groupby(['Nhân viên thực hiện', 'Trung tâm'])['Tổng tiền phạt'].sum().reset_index().sort_values(by='Tổng tiền phạt', ascending=False)
                st.dataframe(pen_nv, use_container_width=True, height=350)