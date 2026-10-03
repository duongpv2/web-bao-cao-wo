import streamlit as st
import extra_streamlit_components as stx

st.set_page_config(page_title="Hệ thống Báo cáo WO", layout="wide")

# --- QUẢN LÝ COOKIE DỂ GIỮ ĐĂNG NHẬP KHI F5 ---
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# Đọc quyền Admin từ cookie trình duyệt
user_role = cookie_manager.get(cookie="user_role")

if "role" not in st.session_state:
    st.session_state["role"] = user_role if user_role else "viewer"

# Cập nhật session nếu cookie có giá trị
if user_role == "admin":
    st.session_state["role"] = "admin"

# --- GIAO DIỆN MENU BÊN TRÁI ---
st.sidebar.title("🔐 HỆ THỐNG")

# 1. KHU VỰC ĐĂNG NHẬP / ĐĂNG XUẤT ADMIN
if st.session_state["role"] != "admin":
    with st.sidebar.expander("🔑 Đăng nhập Quản trị (Dành riêng cho Admin)"):
        username = st.text_input("Tài khoản", key="login_user")
        password = st.text_input("Mật khẩu", type="password", key="login_pass")
        
        if st.button("Đăng nhập Admin"):
            if username == "admin" and password == "123456":  # Thay mật khẩu Admin của bạn ở đây
                st.session_state["role"] = "admin"
                cookie_manager.set("user_role", "admin", key="set_role")
                st.success("Đăng nhập Admin thành công!")
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu Admin!")
else:
    st.sidebar.success("Xin chào: ADMIN (Quản trị viên)")
    if st.sidebar.button("Đăng xuất Admin"):
        st.session_state["role"] = "viewer"
        cookie_manager.delete("user_role", key="del_role")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📌 CHỨC NĂNG")

# 2. PHÂN QUYỀN MENU CHỨC NĂNG
# Nếu là Admin -> Cho phép chọn cả 2 trang (Xem & Upload)
# Nếu là User bình thường -> Chỉ hiển thị trang Xem / Tra cứu
if st.session_state["role"] == "admin":
    menu_list = ["📊 Dashboard & Tra Cứu", "⚙️ Quản Trị (Upload Dữ Liệu Tỉnh)"]
else:
    menu_list = ["📊 Dashboard & Tra Cứu"]

menu_option = st.sidebar.radio("Chọn trang:", menu_list)

# --- NỘI DUNG CHÍNH (BÊN PHẢI) ---

if menu_option == "📊 Dashboard & Tra Cứu":
    st.title("📈 Báo Cáo & Tra Cứu Dữ Liệu Work Order")
    st.info("Trang tra cứu công khai cho tất cả cán bộ / nhân viên.")
    
    # [Đặt đoạn code hiển thị bảng/biểu đồ dữ liệu WO của bạn ở đây]
    st.write("Dữ liệu báo cáo WO và biểu đồ KPI sẽ hiển thị tại đây cho tất cả mọi người cùng xem.")

elif menu_option == "⚙️ Quản Trị (Upload Dữ Liệu Tỉnh)":
    # Bảo vệ lớp 2: Kiểm tra lại quyền Admin trước khi hiển thị khung upload
    if st.session_state["role"] == "admin":
        st.title("⚙️️ Quản Trị & Upload Dữ Liệu")
        st.warning("⚠️ Khu vực này chỉ dành cho Admin để cập nhật file Excel dữ liệu mới.")
        
        uploaded_file = st.file_uploader("Tải file Excel báo cáo WO mới lên:", type=["xlsx", "xls"])
        if uploaded_file is not None:
            st.success("Tải file báo cáo thành công! Dữ liệu trên hệ thống đã được cập nhật.")
    else:
        st.error("⛔ Bạn không có quyền truy cập vào chức năng này!")