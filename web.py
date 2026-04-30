import io, datetime, uuid, os
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT

# ==========================================
# 0. 多语言配置 (Multi-language Dictionary)
# ==========================================
LANG_DICT = {
    "English": {
        "sys_title": "🛡️ System Access Control",
        "login_label": "Enter Name / Office Email",
        "pwd_label": "Access Password",
        "login_btn": "Enter System",
        "auth_err_name": "❌ Audit requirement: Please register identity.",
        "auth_err_pwd": "❌ Incorrect password.",
        "op_user": "👤 Operator:",
        "logout": "Logout",
        "app_title": "📑 Invoice Automation System",
        "scene_label": "Business Scenario:",
        "from_sec": "FROM (Party A) *",
        "to_sec": "BILL TO (Party B) *",
        "items_sec": "📦 Line Items *",
        "desc": "Description",
        "qty": "Qty",
        "price": "Unit Price",
        "add_row": "➕ Add Row",
        "del_row": "➖ Remove Row",
        "bank_sec": "🏦 Terms & Banking *",
        "terms": "Terms",
        "due_date": "Due Date",
        "acc_name": "Account Name",
        "acc_num": "Account Number",
        "bank_name": "Bank Name",
        "swift": "SWIFT Code",
        "bank_addr": "Bank Address",
        "gen_pdf": "🚀 Generate PDF",
        "err_fill": "❌ Error: Please fill in all required fields.",
        "success": "Ready!",
        "download": "📥 Download PDF"
    },
    "中文": {
        "sys_title": "🛡️ 系统访问控制",
        "login_label": "请输入您的姓名 / 办公邮箱",
        "pwd_label": "访问密码",
        "login_btn": "进入系统",
        "auth_err_name": "❌ 审计要求：请先登记您的身份。",
        "auth_err_pwd": "❌ 密码错误。",
        "op_user": "👤 当前操作员:",
        "logout": "登出系统",
        "app_title": "📑 发票自动化生成系统",
        "scene_label": "业务场景：",
        "from_sec": "甲方 (From) *",
        "to_sec": "乙方 (Bill To) *",
        "items_sec": "📦 费用明细 *",
        "desc": "描述",
        "qty": "数量",
        "price": "单价",
        "add_row": "➕ 添加行",
        "del_row": "➖ 减少行",
        "bank_sec": "🏦 条款与银行 *",
        "terms": "条款 (Terms)",
        "due_date": "到期日 (Due Date)",
        "acc_name": "账户名称",
        "acc_num": "银行账号",
        "bank_name": "银行名称",
        "swift": "SWIFT 代码",
        "bank_addr": "银行地址",
        "gen_pdf": "🚀 生成 PDF",
        "err_fill": "❌ 错误：请填写必填项。",
        "success": "已就绪！",
        "download": "📥 下载 PDF"
    }
}

# ==========================================
# 1. 审计日志与身份校验逻辑
# ==========================================
def write_audit_log(visitor):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] Login Success: User -> {visitor}"
    print(log_msg) 
    try:
        with open("access_log.txt", "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except:
        pass

def check_manual_auth():
    if "auth_success" not in st.session_state:
        st.session_state["auth_success"] = False
        st.session_state["visitor_name"] = ""
    
    # 语言选择初始化
    if "lang" not in st.session_state:
        st.session_state["lang"] = "English"

    if st.session_state["auth_success"]:
        return True

    # 登录界面的语言切换
    sel_lang = st.radio("Language / 语言", ["English", "中文"], horizontal=True)
    st.session_state["lang"] = sel_lang
    L = LANG_DICT[sel_lang]

    st.title(L["sys_title"])
    st.markdown("---")
    reg_name = st.text_input(L["login_label"], placeholder="e.g. Zhang San")
    reg_password = st.text_input(L["pwd_label"], type="password")
    
    if st.button(L["login_btn"], use_container_width=True, type="primary"):
        system_password = st.secrets.get("password", "888") # 默认密码
        if not reg_name:
            st.error(L["auth_err_name"])
        elif reg_password != system_password:
            st.error(L["auth_err_pwd"])
        else:
            write_audit_log(reg_name)
            st.session_state["auth_success"] = True
            st.session_state["visitor_name"] = reg_name
            st.rerun()
    return False

if not check_manual_auth():
    st.stop()

# 快捷引用当前语言包
L = LANG_DICT[st.session_state["lang"]]

# --- 侧边栏专属审计模块 ---
st.sidebar.selectbox("🌐 Language / 语言", ["English", "中文"], key="lang")
st.sidebar.markdown(f"**{L['op_user']}**\n{st.session_state['visitor_name']}")
admin_command = st.sidebar.text_input("🔑 Admin Entry", type="password")
if admin_command == "831228":
    st.sidebar.markdown("### Logs")
    if os.path.exists("access_log.txt"):
        with open("access_log.txt", "r", encoding="utf-8") as f:
            st.sidebar.text_area("Logs Data", f.read(), height=300)

if st.sidebar.button(L["logout"]):
    st.session_state["auth_success"] = False
    st.rerun()

# ==========================================
# 2. 业务配置 (HYV 官方法定资料)
# ==========================================
HYV_DETAILS = {
    "name": "COGNOSPHERE PTE. LTD.",
    "address": "1 One-North Crescent, #06-01/02, Razer Sea HQ, Singapore 138538"
}

# ==========================================
# 3. PDF 生成函数 (保持英文，通常发票使用英文)
# ==========================================
def generate_pdf(data):
    items = data.get("items", [])
    currency = "USD"
    invoice_no = "INV-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm

    def style(name="Normal", **kw):
        return ParagraphStyle(name + str(id(kw)), parent=styles[name], **kw)

    s_title = style(fontSize=26, textColor=colors.HexColor("#4472C4"), leading=32)
    s_label = style(fontSize=8,  textColor=colors.HexColor("#888888"), leading=11)
    s_bold  = style(fontSize=10, textColor=colors.HexColor("#222222"), leading=14, fontName="Helvetica-Bold")
    s_th    = style(fontSize=9,  textColor=colors.white, fontName="Helvetica-Bold", leading=12)
    s_td    = style(fontSize=9,  textColor=colors.HexColor("#333333"), leading=12)
    s_bank_h = style(fontSize=9,  textColor=colors.HexColor("#4472C4"), fontName="Helvetica-Bold", leading=13)
    s_bank   = style(fontSize=9,  textColor=colors.HexColor("#444444"), leading=13)
    s_small  = style(fontSize=8,  textColor=colors.HexColor("#888888"), leading=12)
    s_tot_l = style(fontSize=11, textColor=colors.HexColor("#4472C4"), fontName="Helvetica-Bold", leading=14, alignment=TA_RIGHT)
    s_tot_r = style(fontSize=13, textColor=colors.HexColor("#4472C4"), fontName="Helvetica-Bold", leading=16, alignment=TA_RIGHT)

    story = []
    h_table = Table([[Paragraph("INVOICE", s_title), Table([[Paragraph("Invoice No.", s_label),  Paragraph(invoice_no, s_bold)], [Paragraph("Invoice Date", s_label), Paragraph(invoice_date, s_td)], [Paragraph("Due Date", s_label), Paragraph(data.get("due_date", "-"), s_td)], [Paragraph("Terms", s_label), Paragraph(data.get("terms", "-"), s_td)]], colWidths=[30*mm, 48*mm])]], colWidths=[W*0.5, W*0.5])
    h_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(h_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4472C4"), spaceAfter=10))

    p_table = Table([[ [Paragraph("FROM", s_bank_h), Spacer(1, 2), Paragraph(data.get("from_name", ""), s_bold), Paragraph(data.get("from_addr", ""), s_small)], [Paragraph("BILL TO", s_bank_h), Spacer(1, 2), Paragraph(data.get("to_name", ""), s_bold), Paragraph(data.get("to_addr", ""), s_small)] ]], colWidths=[W*0.5, W*0.5])
    p_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
    story.append(p_table)
    story.append(Spacer(1, 15))

    t_data = [[Paragraph("#", s_th), Paragraph("Description", s_th), Paragraph("Qty", s_th), Paragraph("Unit Price", s_th), Paragraph("Amount", s_th)]]
    total = 0
    for idx, item in enumerate(items, 1):
        q, p = float(item.get("qty", 0)), float(item.get("price", 0))
        amt = q * p
        total += amt
        t_data.append([str(idx), Paragraph(item.get("desc", ""), s_td), f"{q:g}", f"{p:,.2f}", f"{amt:,.2f}"])

    main_table = Table(t_data, colWidths=[W*0.05, W*0.45, W*0.12, W*0.18, W*0.20])
    main_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4472C4")), ("GRID", (0,1), (-1,-1), 0.3, colors.HexColor("#DDDDDD")), ("ALIGN", (2,0), (-1,-1), "RIGHT"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("BOTTOMPADDING", (0,0), (-1,-1), 6), ("TOPPADDING", (0,0), (-1,-1), 6)]))
    story.append(main_table)
    
    story.append(Spacer(1, 6))
    tot_table = Table([[Paragraph("TOTAL", s_tot_l), Paragraph(f"{currency} {total:,.2f}", s_tot_r)]], colWidths=[W*0.75, W*0.25])
    tot_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#EEF2FF")), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)]))
    story.append(tot_table)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CCCCCC"), spaceAfter=8))
    story.append(Paragraph("Banking Information", s_bank_h))
    b_rows = [[Paragraph(k, s_label), Paragraph(v, s_bank)] for k, v in [("Account Name", data.get("b_name", "")), ("Account Number", data.get("b_acc", "")), ("Bank Name", data.get("b_bank", "")), ("SWIFT Code", data.get("b_swift", "")), ("Bank Address", data.get("b_addr", ""))]]
    b_table = Table(b_rows, colWidths=[W*0.32, W*0.68])
    b_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(b_table)
    doc.build(story)
    buf.seek(0)
    return buf, invoice_no

# ==========================================
# 4. 页面布局与逻辑
# ==========================================
st.set_page_config(page_title="HYV Invoice Manager", layout="wide")

if 'inv_rows' not in st.session_state:
    st.session_state['inv_rows'] = [{"desc": "", "qty": 1.0, "price": 0.0}]

def add_row(): st.session_state['inv_rows'].append({"desc": "", "qty": 1.0, "price": 0.0})
def del_row(): 
    if len(st.session_state['inv_rows']) > 1: st.session_state['inv_rows'].pop()

st.title(L["app_title"])

# 场景切换
scene = st.radio(L["scene_label"], ["Bill To HYV", "Bill From HYV"], horizontal=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader(L["from_sec"])
    if scene == "Bill From HYV":
        f_name = st.text_input("Name", value=HYV_DETAILS["name"], key=f"f_n_hyv_{scene}")
        f_addr = st.text_area("Address", value=HYV_DETAILS["address"], key=f"f_a_hyv_{scene}")
    else:
        f_name = st.text_input("Name", value="", key=f"f_n_cust_{scene}")
        f_addr = st.text_area("Address", value="", key=f"f_a_cust_{scene}")

with col2:
    st.subheader(L["to_sec"])
    if scene == "Bill To HYV":
        t_name = st.text_input("Customer Name", value=HYV_DETAILS["name"], key=f"t_n_hyv_{scene}")
        t_addr = st.text_area("Customer Address", value=HYV_DETAILS["address"], key=f"t_a_hyv_{scene}")
    else:
        t_name = st.text_input("Customer Name", value="", key=f"t_n_cust_{scene}")
        t_addr = st.text_area("Customer Address", value="", key=f"t_a_cust_{scene}")

st.divider()
st.subheader(L["items_sec"])
for i, row in enumerate(st.session_state['inv_rows']):
    c1, c2, c3 = st.columns([3, 1, 1])
    st.session_state['inv_rows'][i]["desc"] = c1.text_input(f"{L['desc']} #{i+1}", value=row["desc"], key=f"d_{i}")
    st.session_state['inv_rows'][i]["qty"] = c2.number_input(L["qty"], value=float(row["qty"]), min_value=0.01, key=f"q_{i}")
    st.session_state['inv_rows'][i]["price"] = c3.number_input(L["price"], value=float(row["price"]), min_value=0.0, key=f"p_{i}")

col_btn1, col_btn2, _ = st.columns([1, 1, 4])
with col_btn1: st.button(L["add_row"], on_click=add_row, use_container_width=True)
with col_btn2: st.button(L["del_row"], on_click=del_row, use_container_width=True)

st.divider()
st.subheader(L["bank_sec"])
b_col1, b_col2 = st.columns(2)
terms = b_col1.text_input(L["terms"], "Net 45 Days")
due_date = b_col1.text_input(L["due_date"], (datetime.date.today() + datetime.timedelta(days=45)).strftime("%Y-%m-%d"))
b_name = b_col2.text_input(L["acc_name"])
b_acc = b_col2.text_input(L["acc_num"])
b_bank = b_col1.text_input(L["bank_name"])
b_swift = b_col2.text_input(L["swift"])
b_addr = st.text_area(L["bank_addr"])

if st.button(L["gen_pdf"], type="primary", use_container_width=True):
    if not f_name or not f_addr or not t_name or not t_addr or not b_name or not b_acc:
        st.error(L["err_fill"])
    else:
        payload = {
            "from_name": f_name, "from_addr": f_addr, "to_name": t_name, "to_addr": t_addr,
            "due_date": due_date, "terms": terms, "b_name": b_name, "b_acc": b_acc,
            "b_bank": b_bank, "b_swift": b_swift, "b_addr": b_addr,
            "items": st.session_state['inv_rows']
        }
        buf, name = generate_pdf(payload)
        st.success(L["success"])
        st.download_button(L["download"], data=buf, file_name=f"{name}.pdf", mime="application/pdf", use_container_width=True)
