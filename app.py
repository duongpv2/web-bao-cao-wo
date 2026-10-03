import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Hệ thống Báo cáo WO", layout="wide")

# --- XỬ LÝ SESSIONSTORAGE (GIỮ ĐĂNG NHẬP KHI F5, MẤT KHI TẮT TAB) ---
logged_in_storage = streamlit_js_eval(js_expressions='sessionStorage.getItem("is_logged_in")', key='get_login')

if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

if logged_in_storage == "true":
    st.session_state["is_logged_in"] = True

# --- GIAO DIỆN MENU BÊN TRÁI ---
st.sidebar.title("🔐 HỆ THỐNG")

if not st.session_state["is_logged_in"]:
    # 1. CHƯA ĐĂNG NHẬP
    username = st.sidebar.text_input("Tên đăng nhập")
    password = st.sidebar.text_input("Mật khẩu", type="password")
    
    if st.sidebar.button("Đăng nhập"):
        if username == "admin" and password == "123456":  # Thay mật khẩu của bạn tại đây
            st.session_state["is_logged_in"] = True
            streamlit_js_eval(js_expressions='sessionStorage.setItem("is_logged_in", "true")', key='set_login')
            st.rerun()
        else:
            st.sidebar.error("Sai tài khoản hoặc mật khẩu!")
            
    # Hiển thị thông báo ở màn hình chính khi chưa đăng nhập
    st.info("👉 Vui lòng đăng nhập ở menu bên trái để sử dụng hệ thống.")

else:
    # 2. ĐÃ ĐĂNG NHẬP THÀNH CÔNG
    st.sidebar.success("Xin chào: ADMIN")
    
    if st.sidebar.button("Đăng xuất"):
        st.session_state["is_logged_in"] = False
        streamlit_js_eval(js_expressions='sessionStorage.removeItem("is_logged_in")', key='remove_login')
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("CHỨC NĂNG")
    
    # Menu chọn trang
    menu_option = st.sidebar.radio(
        "Chọn chức năng:",
        ["📊 Dashboard & Tra Cứu", "⚙️ Quản Trị (Upload Dữ Liệu Tỉnh)"]
    )
    
    # --- HIỂN THỊ NỘI DUNG MÀN HÌNH CHÍNH BÊN PHẢI ---
    if menu_option == "📊 Dashboard & Tra Cứu":
        st.title("📈 Tra Cứu Dữ Liệu Work Order")
        # Đặt code hiển thị bảng/biểu đồ báo cáo WO của bạn ở đây...
        st.write("Nội dung báo cáo WO sẽ hiển thị ở đây.")
        
    elif menu_option == "⚙️ Quản Trị (Upload Dữ Liệu Tỉnh)":
        st.title("⚙️ Quản Trị Dữ Liệu")
        uploaded_file = st.file_uploader("Tải file Excel báo cáo WO mới lên:", type=["xlsx", "xls"])
        if uploaded_file is not None:
            st.success("Tải file lên thành công!")