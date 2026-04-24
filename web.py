import io, datetime, uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

# ==========================================
# 1. 初始化设置 (必须放在代码最前面)
# ==========================================
st.set_page_config(page_title="Invoice Generator", layout="wide")

# 确保 items 列表在页面加载的第一时间就存在
if 'items' not in st.session_state:
    st.session_state['items'] = [{"description": "", "quantity": 1.0, "unit_price": 0.0}]

# ==========================================
# 2. PDF 生成核心函数
# ==========================================
def generate_pdf(data):
    items = data.get("items", [])
    currency = "USD"
    invoice_no = "INV-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm

    s_bold = ParagraphStyle('bold', parent=styles['Normal'], fontSize=10, fontName="Helvetica-Bold")
    s_th = ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")
    s_td = ParagraphStyle('td', parent=styles['Normal'], fontSize=9)
    s_td_r = ParagraphStyle('td_r', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
    s_tot = ParagraphStyle('tot', parent=styles['Normal'], fontSize=12, fontName="Helvetica-Bold", alignment=TA_RIGHT, textColor=colors.HexColor("#4472C4"))

    story = []
    story.append(Paragraph("INVOICE", ParagraphStyle('title', parent=styles['Normal'], fontSize=26, textColor=colors.HexColor("#4472C4"))))
    story.append(Spacer(1, 10))

    party_data = [[
        [Paragraph("FROM", s_bold), Paragraph(data.get("issuer_name", ""), s_td), Paragraph(data.get("issuer_address", ""), s_td)],
        [Paragraph("BILL TO", s_bold), Paragraph(data.get("recipient_name", ""), s_td), Paragraph(data.get("recipient_address", ""), s_td)]
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 15))

    table_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph("Price", s_th), Paragraph("Amount", s_th)]]
    total_amt = 0
    for idx, item in enumerate(items, 1):
        q = float(item.get("quantity", 0))
        p = float(item.get("unit_price", 0))
        amt = q * p
        total_amt += amt
        table_data.append([str(idx), Paragraph(item.get("description", ""), s_td), f"{q:g}", f"{p:,.2f}", f"{amt:,.2f}"])

    item_table = Table(table_data, colWidths=[W*0.05, W*0.5, W*0.1, W*0.15, W*0.2])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4472C4")),
        ('GRID', (0,1), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 10))
    
    # 修复了之前的括号闭合问题
    story.append(Table([[Paragraph("TOTAL", s_tot), Paragraph(f"{currency} {total_amt:,.2f}", s_tot)]], colWidths=[W*0.7, W*0.3]))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# ==========================================
# 3. 网页界面布局
# ==========================================
st.title("📑 发票在线生成器")
st.write("请填写信息并点击生成 PDF。")

# 卖家和买家信息
col1, col2 = st.columns(2)
with col1:
    i_name = st.text_input("您的名称", "My Company", key="issuer_name")
    i_addr = st.text_area("您的地址", "Singapore", key="issuer_addr")
with col2:
    r_name = st.text_input("客户名称", "Client Name", key="recipient_name")
    r_addr = st.text_area("客户地址", "Client Office", key="recipient_addr")

st.write("---")
st.subheader("📦 发票明细")

# 再次确保 items 存在（双重保险）
if "items" in st.session_state:
    for i, item in enumerate(st.session_state.items):
        c1, c2, c3 = st.columns([3, 1, 1])
        st.session_state.items[i]["description"] = c1.text_input(f"项目 #{i+1} 描述", value=item["description"], key=f"d_{i}")
        st.session_state.items[i]["quantity"] = c2.number_input(f"数量", value=float(item["quantity"]), key=f"q_{i}")
        st.session_state.items[i]["unit_price"] = c3.number_input(f"单价", value=float(item["unit_price"]), key=f"p_{i}")

# 添加行按钮
if st.button("➕ 添加一行"):
    st.session_state.items.append({"description": "", "quantity": 1.0, "unit_price": 0.0})
    st.rerun()

st.write("---")

# 生成 PDF 按钮
if st.button("🚀 生成 PDF", type="primary"):
    # 确保数据被正确获取
    data_to_save = {
        "issuer_name": i_name,
        "issuer_address": i_addr,
        "recipient_name": r_name,
        "recipient_address": r_addr,
        "items": st.session_state.items
    }
    
    try:
        pdf_buf, inv_no = generate_pdf(data_to_save)
        st.success(f"发票 {inv_no} 已成功生成！")
        st.download_button(
            label="📥 点击下载发票 PDF",
            data=pdf_buf,
            file_name=f"Invoice_{inv_no}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"生成过程中出现错误: {e}")
