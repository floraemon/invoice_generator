import io, datetime, uuid
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

# --- 1. HoYoverse 预设信息 ---
HYV_DETAILS = {
    "name": "HoYoverse Pte. Ltd.",
    "address": "12/F, North Bridge Road, Singapore" # 建议此处根据实际需求细化
}

# --- 2. 核心 PDF 渲染 (100% 还原原版 Flask 逻辑与列宽) ---
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

    # 严格还原原版颜色与字体参数
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
            [Paragraph("Invoice Date", s_label), Paragraph(invoice_date, s_td)],
            [Paragraph("Due Date", s_label),     Paragraph(data.get("due_date", "-"), s_td)],
            [Paragraph("Terms", s_label),        Paragraph(data.get("terms", "-"), s_td)],
        ], colWidths=[30*mm, 48*mm])
    ]]
    story.append(Table(header_data, colWidths=[W*0.5, W*0.5]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4472C4"), spaceAfter=10))

    # FROM / TO 布局
    party_data = [[
        [Paragraph("FROM", s_bank_h), Paragraph(data.get("from_name", ""), s_bold), Paragraph(data.get("from_addr", ""), s_small)],
        [Paragraph("BILL TO", s_bank_h), Paragraph(data.get("to_name", ""), s_bold), Paragraph(data.get("to_addr", ""), s_small)],
    ]]
    story.append(Table(party_data, colWidths=[W*0.5, W*0.5]))
    story.append(Spacer(1, 10))

    # 表格明细 (严格列宽: 5%, 45%, 12%, 18%, 20%)
    table_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph("Unit Price", s_th), Paragraph("Amount", s_th)]]
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
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ])))
    
    # 合计
    story.append(Spacer(1, 6))
    story.append(Table([[Paragraph("TOTAL", s_tot_l), Paragraph(f"{currency} {total_amt:,.2f}", s_tot_r)]], colWidths=[W*0.75, W*0.25], style=TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#EEF2FF"))])))

    # 银行信息
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CCCCCC"), spaceAfter=8))
    story.append(Paragraph("Banking Information", s_bank_h))
    bank_info = [
        ("Account Name", data.get("b_name", "")), ("Account Number", data.get("b_acc", "")),
        ("Bank Name", data.get("b_bank", "")), ("SWIFT Code", data.get("b_swift", "")), ("Bank Address", data.get("b_addr", ""))
    ]
    bank_data = [[Paragraph(k, s_label), Paragraph(v, s_bank)] for k, v in bank_info]
    story.append(Table(bank_data, colWidths=[W*0.32, W*0.68]))

    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# --- 3. Streamlit 页面逻辑 ---
st.set_page_config(page_title="Invoice Master", layout="wide")

# 关键：改名以彻底避免 'method' object is not iterable 错误
if 'inv_rows' not in st.session_state:
    st.session_state['inv_rows'] = [{"desc": "", "qty": 1.0, "price": 0.0}]

def add_row(): st.session_state['inv_rows'].append({"desc": "", "qty": 1.0, "price": 0.0})
def del_row(): 
    if len(st.session_state['inv_rows']) > 1: st.session_state['inv_rows'].pop()

st.title("📑 HoYoverse 往来账单管理系统")

# 场景一键切换
scene = st.radio("业务方向：", ["Bill To HoYoverse", "Bill From HoYoverse"], horizontal=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("甲方 (From)")
    if scene == "Bill From HoYoverse":
        f_name = st.text_input("Name", HYV_DETAILS["name"], key="fn_hyv")
        f_addr = st.text_area("Address", HYV_DETAILS["address"], key="fa_hyv")
    else:
        f_name = st.text_input("Name", "Your Company", key="fn_custom")
        f_addr = st.text_area("Address", "Your Address", key="fa_custom")

with col2:
    st.subheader("乙方 (Bill To)")
    if scene == "Bill To HoYoverse":
        t_name = st.text_input("Customer Name", HYV_DETAILS["name"], key="tn_hyv")
        t_addr = st.text_area("Customer Address", HYV_DETAILS["address"], key="ta_hyv")
    else:
        t_name = st.text_input("Customer Name", "Client Name", key="tn_custom")
        t_addr = st.text_area("Customer Address", "Client Address", key="ta_custom")

st.divider()
st.subheader("📦 费用明细")

# 使用新变量名进行循环，确保不会产生 method 冲突
for i, row in enumerate(st.session_state['inv_rows']):
    c1, c2, c3 = st.columns([3, 1, 1])
    st.session_state['inv_rows'][i]["desc"] = c1.text_input(f"描述 #{i+1}", value=row["desc"], key=f"desc_field_{i}")
    st.session_state['inv_rows'][i]["qty"] = c2.number_input(f"数量", value=float(row["qty"]), key=f"qty_field_{i}")
    st.session_state['inv_rows'][i]["price"] = c3.number_input(f"单价", value=float(row["price"]), key=f"price_field_{i}")

col_btn1, col_btn2, _ = st.columns([1, 1, 5])
col_btn1.button("➕ 添加行", on_click=add_row)
col_btn2.button("➖ 删除行", on_click=del_row)

st.divider()
st.subheader("🏦 收款信息及条款")
b1, b2 = st.columns(2)
due_date = b1.text_input("截止日期 (Due Date)", (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
terms = b1.text_input("支付条款 (Terms)", "Net 30 Days")
b_name = b2.text_input("Beneficiary Name")
b_acc = b2.text_input("Account Number")
b_bank = b1.text_input("Bank Name")
b_swift = b2.text_input("SWIFT Code")
b_addr = st.text_area("Bank Address")

if st.button("🚀 生成并预览 PDF", type="primary", use_container_width=True):
    pdf_data = {
        "from_name": f_name, "from_addr": f_addr,
        "to_name": t_name, "to_addr": t_addr,
        "due_date": due_date, "terms": terms,
        "b_name": b_name, "b_acc": b_acc, "b_bank": b_bank, "b_swift": b_swift, "b_addr": b_addr,
        "items": st.session_state['inv_rows'], "currency": "USD"
    }
    buf, name = generate_pdf(pdf_data)
    st.success(f"已生成: {name}")
    st.download_button("📥 下载发票", data=buf, file_name=f"{name}.pdf", mime="application/pdf")
