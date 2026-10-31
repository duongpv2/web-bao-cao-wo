import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. Cấu hình giao diện trang web toàn màn hình
st.set_page_config(
    page_title="Hệ Thống Quản Lý & Điều Hành Work Order",
    layout="wide"
)

# 2. Tiêu đề hệ thống
st.markdown("### **Viettel Construction** | **TTKV3** — HỆ THỐNG QUẢN LÝ & ĐIỀU HÀNH WORK ORDER")
st.caption("Theo dõi, phân tích và quản lý tiến độ thực hiện Work Order theo thời gian thực từ dữ liệu hệ thống.")
st.write("☀️ **Chào buổi chiều, duongpv2**")
st.divider()

# 3. Tải dữ liệu (Ưu tiên đọc file 'Web.xlsx' có sẵn trong repo, hoặc cho phép upload file mới)
@st.cache_data
def load_data():
    try:
        # Đọc file Web.xlsx có sẵn trên GitHub (header nằm ở dòng thứ 2, index=1)
        df = pd.read_excel('Web.xlsx', header=1)
        return df, "Đã tải dữ liệu mặc định từ tệp Web.xlsx trên hệ thống."
    except Exception as e:
        return None, f"Chưa tìm thấy file Web.xlsx mặc định. Vui lòng tải file lên."

df, load_msg = load_data()

# Tùy chọn cho phép người dùng upload file mới nếu muốn
uploaded_file = st.sidebar.file_uploader("📂 Tải lên file Excel báo cáo mới", type=["xlsx", "csv"])
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, header=1, engine="calamine")
    st.sidebar.success("Đã tải file thành công!")
elif df is None:
    st.info(load_msg)
    uploaded = st.file_uploader("Tải lên file Web.xlsx để tiếp tục", type=["xlsx", "csv"])
    if uploaded is not None:
        df = pd.read_excel(uploaded, header=1, engine="calamine")
        st.rerun()
    st.stop()

# 4. Xử lý và tính toán các chỉ số KPI tổng quan
total_wo = len(df)
# Phân loại trạng thái dựa trên cột 'Trạng thái'
dong_count = len(df[df['Trạng thái'] == 'Đóng']) if 'Trạng thái' in df.columns else 0
dang_xu_ly = total_wo - dong_count

# Tính số lượng quá hạn (dựa trên cột 'Quá hạn' hoặc 'Số ngày quá hạn')
if 'Quá hạn' in df.columns:
    quahan_count = int(df['Quá hạn'].sum())
else:
    quahan_count = 0

# Tính tổng tiền phạt
total_penalty = df['Tổng tiền phạt'].sum() if 'Tổng tiền phạt' in df.columns else 0

# Hiển thị các khối thẻ KPI (Metric Cards)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Tổng WO", value=f"{total_wo:,}")
with col2:
    st.metric(label="WO Đang Tồn", value=f"{dang_xu_ly:,}")
with col3:
    st.metric(label="WO Đã Đóng", value=f"{dong_count:,}")
with col4:
    st.metric(label="WO Quá Hạn", value=f"{quahan_count:,}", delta="Cần xử lý", delta_color="inverse")
with col5:
    st.metric(label="Tổng Tiền Phạt", value=f"{total_penalty:,.0f} đ")

st.markdown("---")

# 5. Thanh công cụ lọc tương tác thông minh (Filter Bar)
st.subheader("🔍 Bộ lọc và Tra cứu chi tiết (Drill-down)")
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    trung_tam_list = ["Tất cả"] + sorted(df['Trung tâm'].dropna().unique().tolist()) if 'Trung tâm' in df.columns else ["Tất cả"]
    selected_tt = st.selectbox("🏢 Chọn Trung tâm", trung_tam_list)

with f_col2:
    trang_thai_list = ["Tất cả"] + sorted(df['Trạng thái'].dropna().unique().tolist()) if 'Trạng thái' in df.columns else ["Tất cả"]
    selected_tthai = st.selectbox("📌 Chọn Trạng thái", trang_thai_list)

with f_col3:
    search_keyword = st.text_input("🔎 Tìm kiếm nhanh (Mã công việc, Nhân viên, Mã trạm)...")

# Áp dụng bộ lọc lên DataFrame
df_filtered = df.copy()
if selected_tt != "Tất cả":
    df_filtered = df_filtered[df_filtered['Trung tâm'] == selected_tt]
if selected_tthai != "Tất cả":
    df_filtered = df_filtered[df_filtered['Trạng thái'] == selected_tthai]
if search_keyword:
    mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False, na=False)).any(axis=1)
    df_filtered = df_filtered[mask]

st.info(f"Hiển thị **{len(df_filtered):,}** / {total_wo:,} bản ghi sau khi lọc.")

# 6. Hiển thị bảng dữ liệu chi tiết
st.dataframe(df_filtered, use_container_width=True, height=400)

# 7. Nút Xuất Excel trực quan
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df_filtered.to_excel(writer, index=False, sheet_name='BaoCao_WO')
excel_data = output.getvalue()

st.download_button(
    label="📥 Xuất Bảng Dữ Liệu Đã Lọc Ra File Excel",
    data=excel_data,
    file_name="BaoCao_WO_ChiTiet.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("---")

# 8. Phần Biểu đồ trực quan hóa dữ liệu (Charts)
st.subheader("📈 Biểu đồ thống kê trực quan")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    if 'Trung tâm' in df.columns and 'Trạng thái' in df.columns:
        st.markdown("**Tổng mức WO theo Trung tâm & Trạng thái**")
        fig_bar = px.histogram(df, x="Trung tâm", color="Trạng thái", barmode="stack")
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    if 'Loại công việc' in df.columns:
        st.markdown("**Top 10 loại công việc phổ biến**")
        top_loai_cv = df['Loại công việc'].value_counts().head(10).reset_index()
        top_loai_cv.columns = ['Loại công việc', 'Số lượng']
        fig_pie = px.pie(top_loai_cv, names='Loại công việc', values='Số lượng', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)