import streamlit as st
import pandas as pd
import os

# 1. Cấu hình tiêu đề trang Web
st.set_page_config(
    page_title="Hệ Thống Báo Cáo & Tra Cứu WO", 
    page_icon="📊", 
    layout="wide"
)

# 2. Xử lý Đăng nhập & Phân quyền
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.sidebar.title("🔑 ĐĂNG NHẬP HỆ THỐNG")
    username = st.sidebar.text_input("Tên đăng nhập")
    password = st.sidebar.text_input("Mật khẩu", type="password")
    
    if st.sidebar.button("Đăng nhập"):
        # Tài khoản mẫu (Sau này có thể đổi lại)
        if username == "admin" and password == "123456":
            st.session_state["authenticated"] = True
            st.session_state["role"] = "admin"
            st.rerun()
        elif username == "user" and password == "123456":
            st.session_state["authenticated"] = True
            st.session_state["role"] = "user"
            st.rerun()
        else:
            st.sidebar.error("Tài khoản hoặc mật khẩu không đúng!")
            
    st.info("👈 Vui lòng đăng nhập ở menu bên trái. (Tài khoản thử nghiệm: admin / 123456)")

else:
    # HIỂN THỊ GIAO DIỆN SAU KHI ĐĂNG NHẬP
    st.sidebar.success(f"Xin chào: {st.session_state.get('role').upper()}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state["authenticated"] = False
        st.rerun()

    menu = st.sidebar.radio("CHỨC NĂNG", ["📊 Dashboard & Tra Cứu", "⚙️️ Quản Trị (Upload Dữ Liệu Tĩnh)"])

    # ----------------------------------------------------
    # HÌNH THỨC 1: DASHBOARD & TRA CỨU DỮ LIỆU
    # ----------------------------------------------------
    if menu == "📊 Dashboard & Tra Cứu":
        st.title("📊 Báo Cáo Dashboard & Tra Cứu Dữ Liệu")
        
        mang = st.selectbox("Chọn mảng dữ liệu:", ["Điều hành WO", "VHKT Cố định rộng", "KPI Tiền phạt"])
        data_file = f"data_{mang}.csv"
        
        if os.path.exists(data_file):
            df = pd.read_csv(data_file)
            
            # Khung tìm kiếm
            st.subheader("🔍 Tìm kiếm nhanh")
            search_term = st.text_input("Nhập Mã WO hoặc từ khóa cần tra cứu:")
            
            if search_term:
                df_filtered = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]
            else:
                df_filtered = df
                
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tổng số bản ghi", len(df_filtered))
            with col2:
                st.metric("Trạng thái dữ liệu", "Sẵn sàng")

            st.dataframe(df_filtered, use_container_width=True)
        else:
            st.warning(f"Mảng **{mang}** chưa có dữ liệu. Hãy sang trang Quản Trị để tải file Excel lên!")

    # ----------------------------------------------------
    # HÌNH THỨC 2: DỮ LIỆU TĨNH DO ADMIN UPLOAD ĐỊNH KỲ
    # ----------------------------------------------------
    elif menu == "⚙️ Quản Trị (Upload Dữ Liệu Tĩnh)":
        if st.session_state.get("role") != "admin":
            st.error("⚠️ Trang này chỉ dành cho tài khoản Quản trị (ADMIN)!")
        else:
            st.title("⚙️ Trang Quản Trị - Upload Dữ Liệu Định Kỳ")
            
            mang_up = st.selectbox("Chọn mảng cập nhật:", ["Điều hành WO", "VHKT Cố định rộng", "KPI Tiền phạt"])
            uploaded_file = st.file_uploader("Chọn file Excel (.xlsx) hoặc CSV từ máy:", type=["xlsx", "csv"])
            
            if uploaded_file is not None:
                if uploaded_file.name.endswith(".xlsx"):
                    df_up = pd.read_excel(uploaded_file)
                else:
                    df_up = pd.read_csv(uploaded_file)
                
                # Lưu file dữ liệu
                df_up.to_csv(f"data_{mang_up}.csv", index=False)
                st.success(f"🎉 Đã cập nhật thành công dữ liệu cho mảng **{mang_up}**!")