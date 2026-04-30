# ==========================================
# 0. 多语言配置 (新增警告注释字段)
# ==========================================
LANG_DICT = {
    "English": {
        "app_title": "📑 Invoice Creation System",
        "warning_box": "NOTE: This format is only applicable for generating non-Singapore GST Invoices.", # 新增
        # ... 其他字段保持不变
        "sys_title": "🛡️ System Access Control",
        "login_label": "Enter Name / Office Email",
        "pwd_label": "Access Password",
        "login_btn": "Enter System",
        "auth_err_name": "❌ Audit requirement: Please register identity.",
        "auth_err_pwd": "❌ Incorrect password.",
        "op_user": "👤 Operator:",
        "logout": "Logout",
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
        "app_title": "📑 发票自动化生成系统",
        "warning_box": "注意：本格式仅适用于生成非新加坡GST Invoice。", # 新增
        # ... 其他字段保持不变
        "sys_title": "🛡️ 系统访问控制",
        "login_label": "请输入您的姓名 / 办公邮箱",
        "pwd_label": "访问密码",
        "login_btn": "进入系统",
        "auth_err_name": "❌ 审计要求：请先登记您的身份。",
        "auth_err_pwd": "❌ 密码错误。",
        "op_user": "👤 当前操作员:",
        "logout": "登出系统",
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

# --- 页面逻辑部分 (web.py) ---

# 页面标题
st.title(L["app_title"])

# 新增：在大标题下增加注释框
st.warning(L["warning_box"]) 

# 场景切换
scene = st.radio(L["scene_label"], ["Bill To HYV", "Bill From HYV"], horizontal=True)
# ... 后续代码保持一致
