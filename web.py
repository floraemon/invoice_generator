import io, datetime, uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

# --- 1. 完全还原你最初代码中的 PDF 渲染逻辑 ---
def generate_pdf(data):
    items = data.get("items", [])
    currency = data.get("currency", "USD")
    # 生成发票号和日期（原代码逻辑）
    invoice_no = "INV-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm

    # 样式定义 (100% 还原原代码中的样式名和参数)
    def style(name="Normal", **kw):
        return ParagraphStyle(name + str(id(kw)), parent=styles[name], **kw)

    s_title = style(fontSize=26, textColor=colors.HexColor("#4472C4"), leading=32)
    s_label = style(fontSize=8,  textColor=colors.HexColor("#888888"), leading=11)
    s_value = style(fontSize=10, textColor=colors.HexColor("#222222"), leading=14)
    s_bold  = style(fontSize=10, textColor=colors.HexColor("#222222"), leading=14, fontName="Helvetica-Bold")
    s_th    = style(fontSize=9,  textColor=colors.white, fontName="Helvetica-Bold", leading=12)
    s_td    = style(fontSize=9,  textColor=colors.HexColor("#333333"), leading=12)
    s_td_r  = style(fontSize=9,  textColor=colors.HexColor("#333333"), leading=12, alignment=TA_RIGHT)
    s_tot_l = style(fontSize=11, textColor=colors.HexColor("#4472C4"), fontName="Helvetica-Bold", leading=14, alignment=TA_RIGHT)
    s_tot_r = style(fontSize=13, textColor=colors.HexColor("#4472C4"), fontName="Helvetica-Bold", leading=16, alignment=TA_RIGHT)
    s_bank_h = style(fontSize=9,  textColor=colors.HexColor("#4472C4"), fontName="Helvetica-Bold", leading=13)
    s_bank   = style(fontSize=9,  textColor=colors.HexColor("#444444"), leading=13)
    s_small  = style(fontSize=8,  textColor=colors.HexColor("#888888"), leading=12)

    story = []
    
    # Header (还原原代码布局)
    header_data = [[
        Paragraph("INVOICE", s_title),
        Table([
            [Paragraph("Invoice No.", s_label),  Paragraph(invoice_no, s_bold)],
            [Paragraph("Invoice Date", s_label), Paragraph(invoice_date, s_value)],
            [Paragraph("Due Date", s_label),     Paragraph(data.get("due_date", "-"), s_value)],
            [Paragraph("Terms", s_label),        Paragraph(data.get("terms", "-"), s_value)],
        ], colWidths=[30*mm, 48*mm])
    ]]
    story.append(Table(header_data, colWidths=[W*0.5, W*0.5]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4472C4"), spaceAfter=10))

    # FROM / BILL TO
    party_data = [[
        [Paragraph("FROM", s_bank_h), Paragraph(data.get("issuer_name", ""), s_bold), Paragraph(data.get("issuer_address", ""), s_small)],
        [Paragraph("BILL TO", s_bank_h), Paragraph(data.get("recipient_name", ""), s_bold), Paragraph(data.get("recipient_address", ""), s_small)],
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 10))

    # 明细表 (原代码 colWidths: [5%, 45%, 12%, 18%, 20%])
    table_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph(f"Unit Price", s_th), Paragraph(f"Amount", s_th)]]
    total_amt = 0
    for idx, item in enumerate(items, 1):
        q, p = float(item.get("qty", 0)), float(item.get("price", 0))
        amt = q * p
        total_amt += amt
        table_data.append([str(idx), Paragraph(item.get("desc", ""), s_td), f"{q:g}", f"{p:,.2f}", f"{amt:,.2f}"])

    story.append(Table(table_data, colWidths=[W*0.05, W*0.45, W*0.12, W*0.18, W*0.20], style=TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4472C4")),
        ("GRID", (0,1), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("ALIGN", (2,0), (-1,-1), "RIGHT"),
    ])))
    
    # Total
    story.append(Spacer(1, 6))
    story.append(Table([[Paragraph("TOTAL", s_tot_l), Paragraph(f"{currency} {total_amt:,.2f}", s_tot_r)]], colWidths=[W*0.75, W*0.25], 
                       style=TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#EEF2FF"))])))

    # 银行信息 (完全还原原代码底部样式)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CCCCCC"), spaceAfter=8))
    story.append(Paragraph("Banking Information", s_bank_h))
    bank_rows = [
        ("Account Name", data.get("beneficiary_name", "")),
        ("Account Number", data.get("bank_account", "")),
        ("Bank Name", data.get("bank_name", "")),
        ("SWIFT Code", data.get("swift_code", "")),
        ("Bank Address", data.get("bank_addr", ""))
    ]
    bank_data = [[Paragraph(k, s_label), Paragraph(v, s_bank)] for k, v in bank_rows]
    story.append(Table(bank_data, colWidths=[W*0.32, W*0.68]))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# --- 2. 网页界面布局 ---
st.set_page_config(page_title="Professional Invoice Gen", layout="wide")
st.title("📑 发票生成系统")

# 分栏填写基本信息
col1, col2 = st.columns(2)
with col1:
    st.subheader("甲方信息 (From)")
    issuer_name = st.text_input("您的名称", "Issuer Company Ltd")
    issuer_address = st.text_area("您的地址", "Singapore Address")
    terms = st.text_input("支付条款", "Net 30")
with col2:
    st.subheader("乙方信息 (Bill To)")
    recipient_name = st.text_input("客户名称", "Client Name")
    recipient_address = st.text_area("客户地址", "Global Avenue, USA")
    due_date = st.text_input("截止日期", "2026-05-24")

st.divider()
st.subheader("📦 发票明细")
items_to_send = []
# 预设 5 行以保证稳定性，不使用动态 session 状态
for i in range(5):
    c1, c2, c3 = st.columns([3, 1, 1])
    d = c1.text_input(f"描述 #{i+1}", key=f"d_{i}")
    q = c2.number_input(f"数量", value=1.0, key=f"q_{i}")
    p = c3.number_input(f"单价", value=0.0, key=f"p_{i}")
    if d: items_to_send.append({"desc": d, "qty": q, "price": p})

st.divider()
st.subheader("🏦 银行收款信息")
b1, b2 = st.columns(2)
beneficiary_name = b1.text_input("收款人全称")
bank_account = b1.text_input("银行账号")
bank_name = b2.text_input("银行名称")
swift_code = b2.text_input("SWIFT Code")
bank_addr = b2.text_area("银行地址")

if st.button("🚀 生成 PDF", type="primary"):
    payload = {
        "issuer_name": issuer_name, "issuer_address": issuer_address,
        "recipient_name": recipient_name, "recipient_address": recipient_address,
        "terms": terms, "due_date": due_date,
        "beneficiary_name": beneficiary_name, "bank_account": bank_account,
        "bank_name": bank_name, "swift_code": swift_code, "bank_addr": bank_addr,
        "items": items_to_send, "currency": "USD"
    }
    buf, name = generate_pdf(payload)
    st.success(f"发票 {name} 已就绪")
    st.download_button("📥 下载发票", data=buf, file_name=f"{name}.pdf", mime="application/pdf")
