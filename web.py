import io, datetime, uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

# --- 1. 核心 PDF 生成逻辑 (完整保留你的专业样式) ---
def generate_pdf(data):
    items = data.get("items", [])
    currency = "USD"
    invoice_no = "INV-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm

    # 样式定义 (Navy Blue 风格)
    s_title = ParagraphStyle('title', parent=styles['Normal'], fontSize=26, textColor=colors.HexColor("#4472C4"), leading=32)
    s_bold = ParagraphStyle('bold', parent=styles['Normal'], fontSize=10, fontName="Helvetica-Bold")
    s_label = ParagraphStyle('label', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    s_th = ParagraphStyle('th', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")
    s_td = ParagraphStyle('td', parent=styles['Normal'], fontSize=9)
    s_td_r = ParagraphStyle('td_r', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
    s_tot = ParagraphStyle('tot', parent=styles['Normal'], fontSize=12, fontName="Helvetica-Bold", alignment=TA_RIGHT, textColor=colors.HexColor("#4472C4"))

    story = []
    # 标题
    story.append(Paragraph("INVOICE", s_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4472C4"), spaceAfter=10))

    # FROM / BILL TO (左右布局)
    party_data = [[
        [Paragraph("FROM", s_bold), Paragraph(data.get("i_name", ""), s_td), Paragraph(data.get("i_addr", ""), s_td)],
        [Paragraph("BILL TO", s_bold), Paragraph(data.get("r_name", ""), s_td), Paragraph(data.get("r_addr", ""), s_td)]
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 15))

    # 表格
    table_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph("Price", s_th), Paragraph("Amount", s_th)]]
    total_amt = 0
    for idx, item in enumerate(items, 1):
        if item['desc']: # 只处理有内容的项目
            q, p = float(item['qty']), float(item['price'])
            amt = q * p
            total_amt += amt
            table_data.append([str(idx), Paragraph(item['desc'], s_td), f"{q:g}", f"{p:,.2f}", f"{amt:,.2f}"])

    if len(table_data) > 1:
        it = Table(table_data, colWidths=[W*0.05, W*0.5, W*0.1, W*0.15, W*0.2])
        it.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4472C4")),
            ('GRID', (0,1), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(it)
    
    story.append(Spacer(1, 10))
    story.append(Table([[Paragraph("TOTAL", s_tot), Paragraph(f"{currency} {total_amt:,.2f}", s_tot)]], colWidths=[W*0.7, W*0.3]))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# --- 2. 网页界面 (回归初衷) ---
st.set_page_config(page_title="Professional Invoice Gen", layout="wide")
st.title("📑 专业发票生成器")

# 地址栏
col1, col2 = st.columns(2)
with col1:
    st.subheader("卖家信息 (Bill From)")
    i_name = st.text_input("您的公司/个人名称", "My Company Name")
    i_addr = st.text_area("您的详细地址", "Singapore, North Bridge Road")
with col2:
    st.subheader("客户信息 (Bill To)")
    r_name = st.text_input("客户公司名称", "Client Company Name")
    r_addr = st.text_area("客户详细地址", "Customer Office, USA")

st.write("---")
st.subheader("📦 发票项目明细")

# 预设 5 行，彻底规避动态 Session 报错
items_to_send = []
for i in range(5):
    c1, c2, c3 = st.columns([3, 1, 1])
    d = c1.text_input(f"项目 #{i+1} 描述", key=f"d_{i}")
    q = c2.number_input(f"数量", value=1.0, key=f"q_{i}")
    p = c3.number_input(f"单价", value=0.0, key=f"p_{i}")
    if d: # 如果描述不为空，才加入生成列表
        items_to_send.append({"desc": d, "qty": q, "price": p})

st.write("---")
if st.button("🚀 生成专业 PDF 发票", type="primary"):
    if not items_to_send:
        st.warning("请至少填写一个项目的描述！")
    else:
        final_data = {
            "i_name": i_name, "i_addr": i_addr,
            "r_name": r_name, "r_addr": r_addr,
            "items": items_to_send
        }
        try:
            pdf_buf, inv_no = generate_pdf(final_data)
            st.success(f"发票 {inv_no} 已生成")
            st.download_button("📥 下载 PDF 文件", data=pdf_buf, file_name=f"{inv_no}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"生成失败: {e}")
