import streamlit as st
import pandas as pd

# Cấu hình giao diện rộng
st.set_page_config(page_title="Báo Cáo & Tra Cứu Dữ Liệu Work Order", layout="wide")

st.markdown("## 📊 Báo Cáo & Tra Cứu Dữ Liệu Work Order")
st.info("Trang tra cứu dữ liệu tự động từ hệ thống báo cáo.")

# --- PHẦN 1: TẢI HOẶC ĐỌC DỮ LIỆU EXCEL ---
# Cho phép người dùng tải file Excel báo cáo lên web
uploaded_file = st.file_uploader("Tải lên file Excel báo cáo WO (Định dạng .xlsx hoặc .csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Đọc file Excel bằng Pandas
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="calamine")
    
    st.success(f"Đã tải thành công file dữ liệu! Tổng số dòng: {len(df):,}")

    # --- PHẦN 2: TỰ ĐỘNG TÍNH TOÁN CÁC CHỈ SỐ KPI ---
    total_wo = len(df)
    # Ví dụ lọc các dòng quá hạn (giả sử cột trạng thái là 'Trạng thái')
    # total_quahan = len(df[df['Trạng thái'] == 'Quá hạn'])
    
    # Hiển thị các khối chỉ số KPI lên web
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Tổng số lượng WO", value=f"{total_wo:,}")
    with col2:
        st.metric(label="WO Hoàn Thành", value="--") # Thay bằng logic tính toán thực tế của bạn
    with col3:
        st.metric(label="WO Quá Hạn", value="--", delta="Cần xử lý", delta_color="inverse")

    st.divider()

    # --- PHẦN 3: BẢNG DỮ LIỆU TRA CỨU & LỌC (DRILL-DOWN) ---
    st.subheader("📋 Chi tiết dữ liệu Work Order")
    
    # Thanh tìm kiếm nhanh
    search_keyword = st.text_input("🔍 Tìm kiếm nhanh theo mã trạm hoặc nhân viên:")
    
    df_display = df.copy()
    if search_keyword:
        # Lọc dữ liệu chứa từ khóa ở mọi cột chữ
        mask = df_display.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False)).any(axis=1)
        df_display = df_display[mask]

    # Hiển thị bảng tương tác
    st.dataframe(df_display, use_container_width=True)

    # --- PHẦN 4: NÚT TẢI XUỐNG FILE KẾT QUẢ (EXPORT EXCEL) ---
    st.download_button(
        label="📥 Tải xuống bảng dữ liệu đã lọc (Excel)",
        data=df_display.to_csv(index=False).encode('utf-8-sig'),
        file_name="BaoCao_WO_DaXuLy.csv",
        mime="text/csv"
    )

else:
    st.warning("⚠️ Vui lòng tải lên file Excel báo cáo ở khung bên trên để hiển thị dữ liệu và biểu đồ.")