"""
Shared Helpers – Eliminates boilerplate across all pages.

Provides:
- inject_css() – loads global.css once
- require_auth() – checks session state and stops page if not logged in
- get_page_config() – returns standard st.set_page_config kwargs
"""

import streamlit as st
import os


def get_css_path():
    """Get absolute path to global.css from project root."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(project_root, "styles", "global.css")


def inject_css():
    """Load and inject global.css into the current page."""
    css_path = get_css_path()
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )


def require_auth():
    """
    Check if the user is authenticated.
    If not, display a message and stop the page.
    """
    if not st.session_state.get("authenticated"):
        st.warning("🔒 Please log in to access this page.")
        st.info("Go to the **Home** page to log in or sign up.")
        st.stop()


def get_page_config(title_suffix=None):
    """
    Return standard page config dict.
    Usage: st.set_page_config(**get_page_config("Dashboard"))
    """
    page_title = "SettleWise"
    if title_suffix:
        page_title = f"SettleWise | {title_suffix}"

    return {
        "page_title": page_title,
        "page_icon": "💰",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
    }


def sidebar_branding():
    """Render sidebar branding with logo and tagline."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="font-size: 42px; margin-bottom: 4px;">💰</div>
            <h1 style="
                background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 26px;
                font-weight: 800;
                margin: 0;
                letter-spacing: -0.5px;
            ">SettleWise</h1>
            <p style="
                color: #94a3b8;
                font-size: 12px;
                margin-top: 4px;
                letter-spacing: 1px;
                text-transform: uppercase;
            ">Smart Expense Settlement</p>
        </div>
        """, unsafe_allow_html=True)

        # Logout button
        if st.session_state.get("authenticated"):
            user_name = st.session_state.get("user_name", "User")
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 8px 12px;
                background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.05));
                border: 1px solid rgba(99,102,241,0.15);
                border-radius: 12px;
                margin-bottom: 12px;
            ">
                <span style="color: #94a3b8; font-size: 12px;">Logged in as</span><br/>
                <span style="color: #e2e8f0; font-weight: 600; font-size: 14px;">{user_name}</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚪 Logout", use_container_width=True):
                for key in ["authenticated", "user_id", "user_name", "user_email", "logged_in", "username"]:
                    st.session_state.pop(key, None)
                st.rerun()

        st.divider()
