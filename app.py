import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. Cấu hình trang & Theme
st.set_page_config(
    page_title="Báo Cáo & Tra Cứu Work Order",
    page_icon="📊",
    layout="wide"
)

# 2. Trang trí giao diện bằng Custom CSS (Làm đẹp thẻ KPI, bảng & Nút bấm)
st.markdown("""
    <style>
    /* Nền tổng thể nhẹ nhàng */
    .stApp {
        background-color: #f8f9fa;
    }
    /* Style cho các thẻ KPI */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #495057;
    }
    /* Đổi màu tiêu đề */
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #d90429;
        margin-bottom: 5px;
    }
    .sub-header {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# Header giao diện
st.markdown('<div class="main-header">🔴 VIETTEL CONSTRUCTION | TTKV3</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">HỆ THỐNG ĐIỀU HÀNH & PHÂN TÍCH DỮ LIỆU WORK ORDER</div>', unsafe_allow_html=True)

# 3. Đọc dữ liệu
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('Web.xlsx', header=1)
        return df
    except Exception:
        return None

df = load_data()

# Cho phép Upload file ở Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Viettel_logo_2021.svg/1200px-Viettel_logo_2021.svg.png", width=150)
st.sidebar.title("⚙️ Cấu hình hệ thống")
uploaded_file = st.sidebar.file_uploader("📂 Tải lên báo cáo mới (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, header=1, engine="calamine")
elif df is None:
    st.warning("⚠️ Không tìm thấy file dữ liệu mặc định Web.xlsx. Vui lòng tải file lên thanh bên trái!")
    st.stop()

# 4. Thống kê KPI cốt lõi
total_wo = len(df)
dong_count = len(df[df['Trạng thái'] == 'Đóng']) if 'Trạng thái' in df.columns else 0
dang_xu_ly = total_wo - dong_count
quahan_count = int(df['Quá hạn'].sum()) if 'Quá hạn' in df.columns else 0
total_penalty = df['Tổng tiền phạt'].sum() if 'Tổng tiền phạt' in df.columns else 0

# Khối KPI trực quan (Cards)
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("📦 Tổng WO", f"{total_wo:,}")
kpi2.metric("⏳ Đang Thực Hiện", f"{dang_xu_ly:,}")
kpi3.metric("✅ Đã Đóng", f"{dong_count:,}")
kpi4.metric("⚠️ Quá Hạn", f"{quahan_count:,}", delta="Cần xử lý", delta_color="inverse")
kpi5.metric("💸 Tổng Phạt", f"{total_penalty:,.0f} đ")

st.markdown("<br>", unsafe_allow_html=True)

# 5. Phân chia Tab chức năng
tab1, tab2, tab3 = st.tabs(["📊 Biểu Đồ & Thống Kê", "📋 Tra Cứu Chi Tiết (Drill-Down)", "💰 Chi Tiết Tiền Phạt"])

with tab1:
    st.subheader("Visual Analytics")
    c1, c2 = st.columns(2)
    with c1:
        if 'Trung tâm' in df.columns and 'Trạng thái' in df.columns:
            st.markdown("**Phân bổ WO theo Trung tâm**")
            fig_bar = px.histogram(df, x="Trung tâm", color="Trạng thái", barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2)
            fig_bar.update_layout(xaxis_tickangle=-45, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        if 'Loại công việc' in df.columns:
            st.markdown("**Top 10 Nhóm công việc chiếm tỷ trọng cao nhất**")
            top_loai = df['Loại công việc'].value_counts().head(10).reset_index()
            top_loai.columns = ['Loại công việc', 'Số lượng']
            fig_pie = px.pie(top_loai, names='Loại công việc', values='Số lượng', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("Bộ lọc thông minh")
    f1, f2, f3 = st.columns(3)
    with f1:
        selected_tt = st.selectbox("🏢 Trung tâm:", ["Tất cả"] + sorted(df['Trung tâm'].dropna().unique().tolist()))
    with f2:
        selected_tthai = st.selectbox("📌 Trạng thái WO:", ["Tất cả"] + sorted(df['Trạng thái'].dropna().unique().tolist()))
    with f3:
        search_kw = st.text_input("🔎 Tìm kiếm nhanh:")

    df_filtered = df.copy()
    if selected_tt != "Tất cả":
        df_filtered = df_filtered[df_filtered['Trung tâm'] == selected_tt]
    if selected_tthai != "Tất cả":
        df_filtered = df_filtered[df_filtered['Trạng thái'] == selected_tthai]
    if search_kw:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_kw, case=False, na=False)).any(axis=1)
        df_filtered = df_filtered[mask]

    st.markdown(f"Đang hiển thị **{len(df_filtered):,}** dòng dữ liệu.")
    st.dataframe(df_filtered, use_container_width=True, height=450)

    # Nút xuất Excel
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
    st.subheader("Thống kê tiền phạt vi phạm")
    if 'Tiền phạt FT' in df.columns and 'Tiền phạt CD' in df.columns:
        pf1, pf2 = st.columns(2)
        with pf1:
            st.markdown("**Top 10 Trung tâm có tổng tiền phạt cao nhất**")
            penalty_by_tt = df.groupby('Trung tâm')['Tổng tiền phạt'].sum().reset_index().sort_values(by='Tổng tiền phạt', ascending=False).head(10)
            fig_pen = px.bar(penalty_by_tt, x='Trung tâm', y='Tổng tiền phạt', text_auto='.2s', color='Tổng tiền phạt', color_continuous_scale='Reds')
            st.plotly_chart(fig_pen, use_container_width=True)
        with pf2:
            st.markdown("**Bảng tổng hợp phạt theo Nhân viên**")
            if 'Nhân viên thực hiện' in df.columns:
                pen_nv = df.groupby(['Nhân viên thực hiện', 'Trung tâm'])['Tổng tiền phạt'].sum().reset_index().sort_values(by='Tổng tiền phạt', ascending=False)
                st.dataframe(pen_nv, use_container_width=True, height=350)