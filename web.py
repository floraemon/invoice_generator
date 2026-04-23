import io
import datetime
import uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

# --- 核心 PDF 生成逻辑 (保留你的原逻辑) ---
def generate_pdf(data):
    items = data.get("items", [])
    currency = data.get("currency", "USD")
    invoice_no = "INV-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    def parse_num(v):
        try: return float(v)
        except: return 0.0
    
    total = sum(parse_num(i.get("quantity", 0)) * parse_num(i.get("unit_price", 0)) for i in items)
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm
    )
    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm
    
    def style(name="Normal", **kw):
        return ParagraphStyle(name + str(id(kw)), parent=styles[name], **kw)

    # 样式定义
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
    # Header
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

    # Parties
    party_data = [[
        [Paragraph("FROM", s_bank_h), Paragraph(data.get("issuer_name", ""), s_bold), Paragraph(data.get("issuer_address", ""), s_small)],
        [Paragraph("BILL TO", s_bank_h), Paragraph(data.get("recipient_name", ""), s_bold), Paragraph(data.get("recipient_address", ""), s_small)],
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 10))

    # Items Table
    table_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph(f"Price", s_th), Paragraph(f"Amount", s_th)]]
    for idx, item in enumerate(items, 1):
        q, p = parse_num(item.get("quantity")), parse_num(item.get("unit_price"))
        table_data.append([str(idx), item.get("description"), f"{q:g}", f"{p:,.2f}", f"{q*p:,.2f}"])
    
    story.append(Table(table_data, colWidths=[W*0.05, W*0.45, W*0.12, W*0.18, W*0.20], style=TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,1), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("ALIGN", (2,0), (-1,-1), "RIGHT")
    ])))

    # Total
    story.append(Spacer(1, 10))
    story.append(Table([[Paragraph("TOTAL", s_tot_l), Paragraph(f"{currency} {total:,.2f}", s_tot_r)]], colWidths=[W*0.75, W*0.25]))
    
    # Bank Info
    story.append(Spacer(1, 20))
    story.append(Paragraph("Banking Information", s_bank_h))
    bank_rows = [
        ("Account Name", data.get("beneficiary_name")),
        ("Account Number", data.get("bank_account_number")),
        ("Bank Name", data.get("bank_name")),
        ("SWIFT Code", data.get("swift_code"))
    ]
    for k, v in bank_rows:
        story.append(Paragraph(f"<b>{k}:</b> {v}", s_bank))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# --- Streamlit 网页界面 ---
st.set_page_config(page_title="专业发票生成器", layout="wide")

st.title("📑 在线发票生成工具")
st.write("填写下方信息，一键生成专业的 PDF 发票")

col1, col2 = st.columns(2)

with col1:
    st.subheader("基本信息")
    issuer_name = st.text_input("您的公司/个人名称", "My Company")
    issuer_address = st.text_area("您的地址", "Singapore, North Bridge Road")
    currency = st.selectbox("币种", ["USD", "SGD", "CNY", "EUR"])

with col2:
    st.subheader("客户信息")
    recipient_name = st.text_input("客户名称", "Client Name")
    recipient_address = st.text_area("客户地址", "Customer Building, Suite 101")

st.divider()
st.subheader("发票明细")

# 动态添加物品行
if 'items' not in st.session_state:
    st.session_state.items = [{"description": "", "quantity": 1, "unit_price": 0.0}]

def add_item():
    st.session_state.items.append({"description": "", "quantity": 1, "unit_price": 0.0})

for i, item in enumerate(st.session_state.items):
    c1, c2, c3 = st.columns([3, 1, 1])
    st.session_state.items[i]["description"] = c1.text_input(f"项目描述 #{i+1}", item["description"], key=f"desc_{i}")
    st.session_state.items[i]["quantity"] = c2.number_input(f"数量", value=float(item["quantity"]), key=f"qty_{i}")
    st.session_state.items[i]["unit_price"] = c3.number_input(f"单价", value=float(item["unit_price"]), key=f"price_{i}")

st.button("➕ 添加项目", on_click=add_item)

st.divider()
st.subheader("银行收款信息")
b_col1, b_col2 = st.columns(2)
bank_data = {
    "beneficiary_name": b_col1.text_input("开户名"),
    "bank_account_number": b_col1.text_input("账号"),
    "bank_name": b_col2.text_input("银行名称"),
    "swift_code": b_col2.text_input("SWIFT Code"),
    "issuer_name": issuer_name,
    "issuer_address": issuer_address,
    "recipient_name": recipient_name,
    "recipient_address": recipient_address,
    "currency": currency,
    "items": st.session_state.items
}

if st.button("🚀 生成并预览 PDF", type="primary"):
    pdf_buf, inv_no = generate_pdf(bank_data)
    st.success(f"发票 {inv_no} 已生成！")
    st.download_button(
        label="📥 点击下载 PDF 发票",
        data=pdf_buf,
        file_name=f"Invoice_{inv_no}.pdf",
        mime="application/pdf"
    )