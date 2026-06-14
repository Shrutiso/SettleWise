import streamlit as st
from database.database import init_db
from utils.helpers import inject_css, sidebar_branding
from services.auth_service import signup, login, seed_demo_user

# Initialize database tables
init_db()
seed_demo_user()

st.set_page_config(
    page_title="SettleWise",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------- LOAD GLOBAL CSS -------
inject_css()

# ------- SIDEBAR BRANDING -------
sidebar_branding()


# =====================================================
# AUTH STATE CHECK
# =====================================================

if not st.session_state.get("authenticated"):

    # ------- AUTH HERO -------
    st.markdown("""
    <div style="text-align: center; padding: 30px 20px 20px 20px;">
        <div style="font-size: 56px; margin-bottom: 16px;">💰</div>
        <h1 style="
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 48px;
            font-weight: 800;
            margin: 0 0 8px 0;
            letter-spacing: -1px;
        ">SettleWise</h1>
        <p style="
            color: #94a3b8;
            font-size: 18px;
            font-weight: 400;
            margin-bottom: 24px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
            line-height: 1.6;
        ">
            Smart expense management for groups.<br/>
            Import data, detect anomalies, calculate balances,<br/>
            and generate optimized settlement recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ------- LOGIN / SIGNUP TABS -------
    tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab_login:
        st.markdown("""
        <div class="glass-card" style="max-width: 440px; margin: 20px auto; padding: 30px; border-radius: 16px;">
            <h3 style="margin-top: 0; margin-bottom: 24px; text-align: center; font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Welcome Back</h3>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            login_username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )
            login_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            login_submitted = st.form_submit_button(
                "🔑 Log In",
                use_container_width=True,
                type="primary"
            )

            if login_submitted:
                success, message, user_data = login(
                    login_username, login_password
                )
                if success:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user_data["id"]
                    st.session_state["user_name"] = user_data["full_name"]
                    st.session_state["user_email"] = user_data["email"]
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user_data["full_name"]
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_signup:
        st.markdown("""
        <div class="glass-card" style="max-width: 440px; margin: 20px auto; padding: 30px; border-radius: 16px;">
            <h3 style="margin-top: 0; margin-bottom: 24px; text-align: center; font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Create Account</h3>
        """, unsafe_allow_html=True)

        with st.form("signup_form", clear_on_submit=True):
            signup_username = st.text_input(
                "Username",
                placeholder="e.g. Rohan, Priya",
                key="signup_username"
            )
            signup_password = st.text_input(
                "Password",
                type="password",
                placeholder="Minimum 8 characters",
                key="signup_password"
            )
            signup_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="signup_confirm"
            )
            signup_submitted = st.form_submit_button(
                "📝 Create Account",
                use_container_width=True,
                type="primary"
            )

            if signup_submitted:
                if signup_password != signup_confirm:
                    st.error("❌ Passwords do not match.")
                else:
                    success, message, user_data = signup(
                        signup_username, signup_password
                    )
                    if success:
                        st.success(f"✅ {message} You can now log in.")
                    else:
                        st.error(f"❌ {message}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ------- FOOTER -------
    st.markdown("""
    <div style="
        text-align: center;
        padding: 30px 0 10px 0;
        color: #475569;
        font-size: 12px;
    ">
        SettleWise • Smart Expense Settlement Platform • Built with Streamlit
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# =====================================================
# AUTHENTICATED LANDING PAGE
# =====================================================

# ------- HERO SECTION -------
st.markdown("""
<div style="
    text-align: center;
    padding: 40px 20px 30px 20px;
">
    <div style="font-size: 56px; margin-bottom: 16px;">💰</div>
    <h1 style="
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 48px;
        font-weight: 800;
        margin: 0 0 8px 0;
        letter-spacing: -1px;
    ">SettleWise</h1>
    <p style="
        color: #94a3b8;
        font-size: 18px;
        font-weight: 400;
        margin-bottom: 32px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    ">
        Smart expense management for groups.<br/>
        Import data, detect anomalies, calculate balances,<br/>
        and generate optimized settlement recommendations.
    </p>
</div>
""", unsafe_allow_html=True)


# ------- FEATURE CARDS -------
col1, col2, col3, col4 = st.columns(4)

features = [
    {
        "icon": "📂",
        "title": "Import & Validate",
        "desc": "Upload CSV files with automatic anomaly detection and data cleaning"
    },
    {
        "icon": "📊",
        "title": "Live Dashboard",
        "desc": "Real-time KPIs, spending trends, and AI-powered insights"
    },
    {
        "icon": "⚖️",
        "title": "Balance Engine",
        "desc": "Calculate who owes whom with support for multiple split types"
    },
    {
        "icon": "🤝",
        "title": "Smart Settlements",
        "desc": "Optimized payment recommendations that minimize transactions"
    },
]

for col, feat in zip([col1, col2, col3, col4], features):
    with col:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{feat['icon']}</div>
            <div class="feature-title">{feat['title']}</div>
            <div class="feature-desc">{feat['desc']}</div>
        </div>
        """, unsafe_allow_html=True)


st.markdown("<br/>", unsafe_allow_html=True)
st.divider()


# ------- QUICK STATS FROM DATABASE -------
from database.database import SessionLocal
from database.models import Expense, User, Anomaly, Settlement, ImportLog

db = SessionLocal()

try:
    total_expenses = db.query(Expense).count()
    total_users = db.query(User).count()
    total_anomalies = db.query(Anomaly).count()
    total_settlements = db.query(Settlement).count()
    total_imports = db.query(ImportLog).count()

    if total_expenses > 0 or total_users > 0:

        st.subheader("📈 Quick Overview")

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric("💰 Expenses", total_expenses)

        with c2:
            st.metric("👥 Members", total_users)

        with c3:
            st.metric("⚠️ Anomalies", total_anomalies)

        with c4:
            st.metric("🤝 Settlements", total_settlements)

        with c5:
            st.metric("📥 Imports", total_imports)

    else:

        st.markdown("""
        <div style="
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(139,92,246,0.04));
            border: 1px dashed rgba(99,102,241,0.2);
            border-radius: 16px;
            margin: 20px 0;
        ">
            <p style="font-size: 32px; margin-bottom: 8px;">🚀</p>
            <h3 style="color: #e2e8f0; margin-bottom: 8px;">Get Started</h3>
            <p style="color: #94a3b8; font-size: 14px;">
                Navigate to <strong>📂 Import Data</strong> in the sidebar to upload your first expense CSV.
            </p>
        </div>
        """, unsafe_allow_html=True)

finally:
    db.close()


# ------- FOOTER -------
st.markdown("""
<div style="
    text-align: center;
    padding: 30px 0 10px 0;
    color: #475569;
    font-size: 12px;
">
    SettleWise • Smart Expense Settlement Platform • Built with Streamlit
</div>
""", unsafe_allow_html=True)