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

# --- 核心 PDF 生成逻辑 ---
def generate_pdf(data):
    items = data.get("items", [])
    currency = data.get("currency", "USD")
    # 生成唯一发票编号
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

    # 定义 PDF 内部样式
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
    
    # 1. Header (标题与基本信息)
    header_data = [[
        Paragraph("INVOICE", s_title),
        Table([
            [Paragraph("Invoice No.", s_label),  Paragraph(invoice_no, s_bold)],
            [Paragraph("Invoice Date", s_label), Paragraph(invoice_date, s_value)],
            [Paragraph("Due Date", s_label),     Paragraph(data.get("due_date") or "-", s_value)],
            [Paragraph("Terms", s_label),        Paragraph(data.get("terms") or "Net 30", s_value)],
        ], colWidths=[30*mm, 48*mm])
    ]]
    story.append(Table(header_data, colWidths=[W*0.5, W*0.5]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4472C4"), spaceAfter=10))

    # 2. FROM / BILL TO (双方地址)
    party_data = [[
        [Paragraph("FROM", s_bank_h), Paragraph(data.get("issuer_name", ""), s_bold), Paragraph(data.get("issuer_address", ""), s_small)],
        [Paragraph("BILL TO", s_bank_h), Paragraph(data.get("recipient_name", ""), s_bold), Paragraph(data.get("recipient_address", ""), s_small)],
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 10))

    # 3. Items Table (明细表格)
    table_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph(f"Price", s_th), Paragraph(f"Amount", s_th)]]
    for idx, item in enumerate(items, 1):
        q = parse_num(item.get("quantity", 0))
        p = parse_num(item.get("unit_price", 0))
        table_data.append([
            str(idx), 
            Paragraph(item.get("description", ""), s_td), 
            Paragraph(f"{q:g}", s_td_r), 
            Paragraph(f"{p:,.2f}", s_td_r), 
            Paragraph(f"{q*p:,.2f}", s_td_r)
        ])
    
    story.append(Table(table_data, colWidths=[W*0.05, W*0.45, W*0.12, W*0.18, W*0.20], style=TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,1), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ])))

    # 4. Total (总额)
    story.append(Spacer(1, 10))
    story.append(Table([[Paragraph("TOTAL", s_tot_l), Paragraph(f"{currency} {total:,.2f}", s_tot_r)]], 
                       colWidths=[W*0.75, W*0.25],
                       style=TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F3F6FF")), ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)])))
    
    # 5. Banking Information (银行信息)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("Banking Information", s_bank_h))
    story.append(Spacer(1, 5))
    bank_info = [
        f"<b>Beneficiary:</b> {data.get('beneficiary_name', '-')}",
        f"<b>Account Number:</b> {data.get('bank_account_number', '-')}",
        f"<b>Bank Name:</b> {data.get('bank_name', '-')}",
        f"<b>SWIFT Code:</b> {data.get('swift_code', '-')}"
    ]
    for line in bank_info:
        story.append(Paragraph(line, s_bank))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# --- Streamlit 界面逻辑 ---
st.set_page_config(page_title="Professional Invoice Generator", layout="wide")

# 初始化 Session State (防止报错的关键)
if 'items' not in st.session_state:
    st.session_state.items = [{"description": "", "quantity": 1, "unit_price": 0.0}]

def add_item():
    st.session_state.items.append({"description": "", "quantity": 1, "unit_price": 0.0})

st.title("📑 在线发票生成器")
st.info("填写下方信息即可生成专业 PDF 发票。本工具由 Python & Streamlit 驱动。")

# 第一部分：主体信息
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("卖家信息 (From)")
        issuer_name = st.text_input("公司/个人名称", "My Company Name")
        issuer_address = st.text_area("详细地址", "123 Business Street, Singapore")
    with col2:
        st.subheader("买家信息 (Bill To)")
        recipient_name = st.text_input("客户名称", "Client Company")
        recipient_address = st.text_area("客户地址", "456 Client Avenue, Office 01")

# 第二部分：明细信息
st.markdown("---")
st.subheader("📦 发票明细")
for i, _ in enumerate(list(st.session_state.items)):
    c1, c2, c3 = st.columns([3, 1, 1])
    st.session_state.items[i]["description"] = c1.text_input(f"项目描述 #{i+1}", key=f"desc_{i}")
    st.session_state.items[i]["quantity"] = c2.number_input(f"数量", value=1.0, step=1.0, key=f"qty_{i}")
    st.session_state.items[i]["unit_price"] = c3.number_input(f"单价", value=0.0, step=0.01, key=f"price_{i}")

st.button("➕ 添加一行项目", on_click=add_item)

# 第三部分：额外参数与收款
st.markdown("---")
with st.container():
    c1, c2, c3 = st.columns(3)
    currency = c1.selectbox("币种", ["USD", "SGD", "CNY", "EUR", "GBP"])
    due_date = c2.text_input("截止日期", value=(datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
    terms = c3.text_input("支付条款", "Net 30 Days")

st.subheader("🏦 收款银行信息")
b_col1, b_col2 = st.columns(2)
beneficiary_name = b_col1.text_input("开户名 (Beneficiary Name)")
bank_account_number = b_col1.text_input("账号 (Account Number)")
bank_name = b_col2.text_input("银行名称 (Bank Name)")
swift_code = b_col2.text_input("SWIFT Code")

# 第四部分：生成与下载
st.markdown("---")
if st.button("🚀 生成并预览 PDF", type="primary", use_container_width=True):
    # 组装数据
    final_data = {
        "issuer_name": issuer_name,
        "issuer_address": issuer_address,
        "recipient_name": recipient_name,
        "recipient_address": recipient_address,
        "currency": currency,
        "due_date": due_date,
        "terms": terms,
        "beneficiary_name": beneficiary_name,
        "bank_account_number": bank_account_number,
        "bank_name": bank_name,
        "swift_code": swift_code,
        "items": st.session_state.items
    }
    
    try:
        pdf_buf, inv_no = generate_pdf(final_data)
        st.success(f"成功！发票编号: {inv_no}")
        st.download_button(
            label="📥 点击下载 PDF 发票",
            data=pdf_buf,
            file_name=f"Invoice_{inv_no}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"生成失败: {e}")
