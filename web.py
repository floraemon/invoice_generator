import io, datetime, uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

# --- 1. 核心 PDF 生成函数 ---
def generate_pdf(data):
    items = data.get("items", [])
    currency = data.get("currency", "USD")
    invoice_no = "INV-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm

    # 样式定义
    s_bold = ParagraphStyle('bold', parent=styles['Normal'], fontSize=10, fontName="Helvetica-Bold")
    s_th = ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")
    s_td = ParagraphStyle('td', parent=styles['Normal'], fontSize=9)
    s_td_r = ParagraphStyle('td_r', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
    s_tot = ParagraphStyle('tot', parent=styles['Normal'], fontSize=12, fontName="Helvetica-Bold", alignment=TA_RIGHT, textColor=colors.HexColor("#4472C4"))

    story = []
    story.append(Paragraph("INVOICE", ParagraphStyle('title', parent=styles['Normal'], fontSize=26, textColor=colors.HexColor("#4472C4"))))
    story.append(Spacer(1, 10))

    # 地址信息表
    party_data = [[
        [Paragraph("FROM", s_bold), Paragraph(data.get("issuer_name", ""), s_td), Paragraph(data.get("issuer_address", ""), s_td)],
        [Paragraph("BILL TO", s_bold), Paragraph(data.get("recipient_name", ""), s_td), Paragraph(data.get("recipient_address", ""), s_td)]
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 15))

    # 明细表
    table_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph("Price", s_th), Paragraph("Amount", s_th)]]
    total_amt = 0
    for idx, item in enumerate(items, 1):
        q, p = float(item.get("quantity", 0)), float(item.get("unit_price", 0))
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
    
    # 总计 (这里之前漏了括号，现在补上了)
    story.append(Spacer(1, 10))
    story.append(Table([[Paragraph("TOTAL", s_tot), Paragraph(f"{currency} {total_amt:,.2f}", s_tot)]], colWidths=[W*0.7, W*0.3]))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# --- 2. Streamlit 网页界面 ---
st.set_page_config(page_title="Invoice Generator")

if 'items' not in st.session_state:
    st.session_state.items = [{"description": "", "quantity": 1.0, "unit_price": 0.0}]

st.title("📑 发票在线生成器")

col1, col2 = st.columns(2)
with col1:
    i_name = st.text_input("您的名称", "My Company")
    i_addr = st.text_area("您的地址", "Singapore")
with col2:
    r_name = st.text_input("客户名称", "Client Name")
    r_addr = st.text_area("客户地址", "Client Office")

st.write("---")
for i, item in enumerate(st.session_state.items):
    c1, c2, c3 = st.columns([3, 1, 1])
    st.session_state.items[i]["description"] = c1.text_input(f"描述 #{i+1}", key=f"d_{i}")
    st.session_state.items[i]["quantity"] = c2.number_input(f"数量", value=1.0, key=f"q_{i}")
    st.session_state.items[i]["unit_price"] = c3.number_input(f"单价", value=0.0, key=f"p_{i}")

if st.button("➕ 添加行"):
    st.session_state.items.append({"description": "", "quantity": 1.0, "unit_price": 0.0})
    st.rerun()

st.write("---")
if st.button("🚀 生成 PDF", type="primary"):
    data = {"issuer_name": i_name, "issuer_address": i_addr, "recipient_name": r_name, "recipient_address": r_addr, "items": st.session_state.items}
    pdf_buf, inv_no = generate_pdf(data)
    st.success(f"发票 {inv_no} 已生成!")
    st.download_button("📥 下载发票", data=pdf_buf, file_name=f"{inv_no}.pdf", mime="application/pdf")
