import io, datetime, uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

# 设置页面
st.set_page_config(page_title="Invoice Generator")

def generate_pdf(issuer, recipient, items):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # 标题
    story.append(Paragraph("INVOICE", ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor("#4472C4"))))
    story.append(Spacer(1, 20))
    
    # 双方信息
    data = [[f"FROM:\n{issuer}", f"BILL TO:\n{recipient}"]]
    t = Table(data, colWidths=[90*mm, 90*mm])
    t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('FONTSIZE', (0,0), (-1,-1), 10)]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # 明细表格头
    table_data = [["Description", "Qty", "Price", "Amount"]]
    total = 0
    for item in items:
        if item[0]: # 只有描述不为空才添加
            q, p = float(item[1]), float(item[2])
            amt = q * p
            total += amt
            table_data.append([item[0], f"{q:g}", f"{p:,.2f}", f"{amt:,.2f}"])
    
    it = Table(table_data, colWidths=[80*mm, 20*mm, 35*mm, 35*mm])
    it.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4472C4")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT')
    ]))
    story.append(it)
    
    # 总计
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"TOTAL AMOUNT: USD {total:,.2f}", ParagraphStyle('Total', parent=styles['Normal'], fontSize=14, alignment=TA_RIGHT, fontName="Helvetica-Bold")))
    
    doc.build(story)
    buf.seek(0)
    return buf

# --- 网页界面 ---
st.title("📑 极简发票生成器")
st.write("如果你看到这个界面，说明我们成功了！")

col1, col2 = st.columns(2)
issuer = col1.text_area("您的公司信息", "My Company\nSingapore")
recipient = col2.text_area("客户公司信息", "Client Name\nUSA")

st.subheader("发票明细 (填写下方 3 行)")
item1_desc = st.text_input("项目 1 描述", "Consulting Service")
c1, c2 = st.columns(2)
item1_qty = c1.number_input("项目 1 数量", value=1.0)
item1_price = c2.number_input("项目 1 单价", value=100.0)

st.write("---")
item2_desc = st.text_input("项目 2 描述 (可选)", "")
c3, c4 = st.columns(2)
item2_qty = c3.number_input("项目 2 数量", value=0.0)
item2_price = c4.number_input("项目 2 单价", value=0.0)

if st.button("🚀 生成 PDF 发票", type="primary"):
    items_list = [
        [item1_desc, item1_qty, item1_price],
        [item2_desc, item2_qty, item2_price]
    ]
    try:
        pdf_out = generate_pdf(issuer, recipient, items_list)
        st.success("发票生成成功！")
        st.download_button("📥 下载 PDF", data=pdf_out, file_name="invoice.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"发生错误: {e}")
