import io, datetime, uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

# --- 1. 预设 HoYoverse 信息 ---
HYV_INFO = {
    "name": "HoYoverse Pte. Ltd.",
    "address": "Singapore (HQ), North Bridge Road" # 你可以在这里修改为精确地址
}

# --- 2. 核心 PDF 渲染函数 (严格遵循原 Flask 逻辑) ---
def generate_pdf(data):
    items = data.get("items", [])
    currency = data.get("currency", "USD")
    invoice_no = "INV-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm

    def style(name="Normal", **kw):
        return ParagraphStyle(name + str(id(kw)), parent=styles[name], **kw)

    # 还原原版样式
    s_title = style(fontSize=26, textColor=colors.HexColor("#4472C4"), leading=32)
    s_label = style(fontSize=8,  textColor=colors.HexColor("#888888"), leading=11)
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
            [Paragraph("Invoice Date", s_label), Paragraph(invoice_date, s_value if 's_value' in locals() else s_td)],
            [Paragraph("Due Date", s_label),     Paragraph(data.get("due_date", "-"), s_td)],
            [Paragraph("Terms", s_label),        Paragraph(data.get("terms", "-"), s_td)],
        ], colWidths=[30*mm, 48*mm])
    ]]
    story.append(Table(header_data, colWidths=[W*0.5, W*0.5]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4472C4"), spaceAfter=10))

    # Bill From / To
    party_data = [[
        [Paragraph("FROM", s_bank_h), Paragraph(data.get("issuer_name", ""), s_bold), Paragraph(data.get("issuer_address", ""), s_small)],
        [Paragraph("BILL TO", s_bank_h), Paragraph(data.get("recipient_name", ""), s_bold), Paragraph(data.get("recipient_address", ""), s_small)],
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 10))

    # Items Table (列宽比例 5%, 45%, 12%, 18%, 20%)
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
    
    # Total & Bank Info (保持原版逻辑)
    story.append(Spacer(1, 6))
    story.append(Table([[Paragraph("TOTAL", s_tot_l), Paragraph(f"{currency} {total_amt:,.2f}", s_tot_r)]], colWidths=[W*0.75, W*0.25], style=TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#EEF2FF"))])))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CCCCCC"), spaceAfter=8))
    story.append(Paragraph("Banking Information", s_bank_h))
    bank_data = [[Paragraph(k, s_label), Paragraph(v, s_bank)] for k, v in [
        ("Account Name", data.get("b_name", "")), ("Account Number", data.get("b_acc", "")),
        ("Bank Name", data.get("b_bank", "")), ("SWIFT Code", data.get("b_swift", "")), ("Bank Address", data.get("b_addr", ""))
    ]]
    story.append(Table(bank_data, colWidths=[W*0.32, W*0.68]))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# --- 3. 网页主程序 (含动态加行与场景切换) ---
st.set_page_config(page_title="HYV Invoice Tool", layout="wide")

# 初始化 Session State
if 'items' not in st.session_state:
    st.session_state.items = [{"desc": "", "qty": 1.0, "price": 0.0}]

# 操作函数
def add_row(): st.session_state.items.append({"desc": "", "qty": 1.0, "price": 0.0})
def del_row(): 
    if len(st.session_state.items) > 1: st.session_state.items.pop()

st.title("📑 HoYoverse 往来账单生成器")

# 场景选择
scene = st.radio("选择业务场景：", ["Bill To HoYoverse (向 HYV 请款)", "Bill From HoYoverse (由 HYV 开票)"], horizontal=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("甲方信息 (From)")
    if scene == "Bill From HoYoverse (由 HYV 开票)":
        i_name = st.text_input("名称", HYV_INFO["name"])
        i_addr = st.text_area("地址", HYV_INFO["address"])
    else:
        i_name = st.text_input("名称", "Your Company Name")
        i_addr = st.text_area("地址", "Your Local Address")
with col2:
    st.subheader("乙方信息 (To)")
    if scene == "Bill To HoYoverse (向 HYV 请款)":
        r_name = st.text_input("客户名称", HYV_INFO["name"])
        r_addr = st.text_area("客户地址", HYV_INFO["address"])
    else:
        r_name = st.text_input("客户名称", "Client Name")
        r_addr = st.text_area("客户地址", "Client Address")

st.divider()
st.subheader("📦 费用明细")
for i, item in enumerate(st.session_state.items):
    c1, c2, c3 = st.columns([3, 1, 1])
    st.session_state.items[i]["desc"] = c1.text_input(f"描述 #{i+1}", value=item["desc"], key=f"d{i}")
    st.session_state.items[i]["qty"] = c2.number_input(f"数量", value=float(item["qty"]), key=f"q{i}")
    st.session_state.items[i]["price"] = c3.number_input(f"单价", value=float(item["price"]), key=f"p{i}")

c1, c2, _ = st.columns([1, 1, 3])
c1.button("➕ 添加行", on_click=add_row)
c2.button("➖ 减少行", on_click=del_row)

st.divider()
st.subheader("🏦 收款银行信息")
b1, b2 = st.columns(2)
bank_payload = {
    "b_name": b1.text_input("Beneficiary Name"), "b_acc": b1.text_input("Account Number"),
    "b_bank": b2.text_input("Bank Name"), "b_swift": b2.text_input("SWIFT Code"), "b_addr": b2.text_area("Bank Address")
}

if st.button("🚀 生成 PDF", type="primary", use_container_width=True):
    full_data = {**bank_payload, "issuer_name": i_name, "issuer_address": i_addr, 
                 "recipient_name": r_name, "recipient_address": r_addr, 
                 "items": st.session_state.items, "currency": "USD"}
    buf, name = generate_pdf(full_data)
    st.success(f"发票已生成！")
    st.download_button("📥 下载文件", data=buf, file_name=f"{name}.pdf", mime="application/pdf")
