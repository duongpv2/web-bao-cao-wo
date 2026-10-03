import streamlit as st
from streamlit_js_eval import streamlit_js_eval, set_cookie, get_cookie

# --- KHỞI TẠO BỘ NHỚ TRÌNH DUYỆT (sessionStorage) ---
# Đọc trạng thái đăng nhập từ sessionStorage của trình duyệt
logged_in_storage = streamlit_js_eval(js_expressions='sessionStorage.getItem("is_logged_in")', key='get_login')

if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = (logged_in_storage == "true")

# Sync trạng thái nếu sessionStorage thay đổi
if logged_in_storage == "true":
    st.session_state["is_logged_in"] = True

# --- GIAO DIỆN HỆ THỐNG ---
st.sidebar.title("🔐 HỆ THỐNG")

if not st.session_state["is_logged_in"]:
    # Giao diện khi CHƯA đăng nhập
    username = st.sidebar.text_input("Tên đăng nhập")
    password = st.sidebar.text_input("Mật khẩu", type="password")
    
    if st.sidebar.button("Đăng nhập"):
        if username == "admin" and password == "123456": # Hoặc mật khẩu của bạn
            st.session_state["is_logged_in"] = True
            # Lưu trạng thái vào sessionStorage của trình duyệt
            streamlit_js_eval(js_expressions='sessionStorage.setItem("is_logged_in", "true")', key='set_login')
            st.rerun()
        else:
            st.sidebar.error("Sai tài khoản hoặc mật khẩu!")
else:
    # Giao diện khi ĐÃ đăng nhập
    st.sidebar.success("Xin chào: ADMIN")
    
    if st.sidebar.button("Đăng xuất"):
        st.session_state["is_logged_in"] = False
        # Xóa trạng thái khỏi sessionStorage khi ấn Đăng xuất
        streamlit_js_eval(js_expressions='sessionStorage.removeItem("is_logged_in")', key='remove_login')
        st.rerun()

    st.sidebar.markdown("---")
    # Các chức năng Quản trị / Upload file của bạn bên dưới...