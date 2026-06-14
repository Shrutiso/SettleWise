import streamlit as st
import pandas as pd
import os

from services.anomaly_detector import detect_anomalies
from services.import_service import run_full_import
from utils.helpers import inject_css, require_auth, sidebar_branding, get_page_config

st.set_page_config(**get_page_config("Import Data"))

inject_css()
sidebar_branding()
require_auth()


# =====================================================
# CUSTOM STYLES
# =====================================================

st.markdown("""
<style>

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.08));
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px;
    padding: 18px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99,102,241,0.15);
}

div.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 600;
    font-size: 16px;
    transition: all 0.3s ease;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    box-shadow: 0 8px 25px rgba(99,102,241,0.3);
    transform: translateY(-1px);
}

.import-success {
    background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(52,211,153,0.08));
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
}

.import-warning {
    background: linear-gradient(135deg, rgba(245,158,11,0.1), rgba(251,191,36,0.08));
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
}

.severity-high {
    color: #ef4444;
    font-weight: 700;
}

.severity-medium {
    color: #f59e0b;
    font-weight: 600;
}

.severity-low {
    color: #10b981;
    font-weight: 500;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# PAGE HEADER
# =====================================================

st.title("📂 Import Expenses CSV")

st.markdown("""
Upload your exported expense CSV file. The system will automatically:
- **Validate** all data fields
- **Detect** anomalies and data quality issues
- **Import** clean records into the database
- **Skip** rows with critical errors
""")

st.divider()


# =====================================================
# FILE UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Upload an expenses CSV with columns: date, description, paid_by, amount, currency, split_type, split_with, split_details, notes"
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    anomalies = detect_anomalies(df)

    high_count = len(
        [a for a in anomalies if a["severity"] == "HIGH"]
    )

    medium_count = len(
        [a for a in anomalies if a["severity"] == "MEDIUM"]
    )

    low_count = len(
        [a for a in anomalies if a["severity"] == "LOW"]
    )

    st.success(f"✅ **{uploaded_file.name}** loaded successfully")

    # =====================================================
    # KPI CARDS
    # =====================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "📄 Total Records",
            len(df)
        )

    with col2:
        st.metric(
            "⚠️ Anomalies",
            len(anomalies)
        )

    with col3:
        st.metric(
            "🔴 High",
            high_count
        )

    with col4:
        st.metric(
            "🟡 Medium",
            medium_count
        )

    with col5:
        st.metric(
            "🟢 Low",
            low_count
        )

    st.divider()

    # =====================================================
    # CSV PREVIEW
    # =====================================================

    st.subheader("📋 CSV Data Preview")

    st.dataframe(
        df,
        width="stretch",
        height=300,
    )

    st.divider()

    # =====================================================
    # ANOMALIES TABLE
    # =====================================================

    st.subheader("⚠️ Detected Anomalies")

    if anomalies:

        anomaly_df = pd.DataFrame(anomalies)

        # Color-code severity
        def highlight_severity(val):
            if val == "HIGH":
                return "color: #ef4444; font-weight: bold"
            elif val == "MEDIUM":
                return "color: #f59e0b; font-weight: bold"
            elif val == "LOW":
                return "color: #10b981; font-weight: bold"
            return ""

        styled_df = anomaly_df.style.map(
            highlight_severity,
            subset=["severity"]
        )

        st.dataframe(
            styled_df,
            width="stretch",
            height=300,
        )

    else:
        st.success("✅ No anomalies detected — data is clean!")

    st.divider()

    # =====================================================
    # IMPORT SECTION
    # =====================================================

    st.subheader("🚀 Import to Database")

    if high_count > 0:
        st.warning(
            f"⚠️ **{high_count} HIGH severity anomalies** detected. "
            f"These rows will be **skipped** during import. "
            f"Remaining {len(df) - high_count} rows will be imported."
        )
    else:
        st.success(
            "✅ All validation checks passed. Ready to import!"
        )

    # Prevent double-import using session state
    import_key = f"imported_{uploaded_file.name}_{len(df)}"

    if import_key not in st.session_state:
        st.session_state[import_key] = False

    if st.session_state[import_key]:

        st.markdown("""
        <div class="import-success">
            <h3>✅ Data Already Imported</h3>
            <p>This file has already been imported in this session.
            Upload a different file or refresh to re-import.</p>
        </div>
        """, unsafe_allow_html=True)

    else:

        if st.button(
            "🚀 Import Data to Database",
            width="stretch",
            type="primary",
        ):

            with st.spinner("Importing data... This may take a moment."):

                # Reset the file pointer
                uploaded_file.seek(0)
                df_fresh = pd.read_csv(uploaded_file)

                result = run_full_import(
                    df_fresh,
                    uploaded_file.name
                )

            if result["success"]:

                st.session_state[import_key] = True

                st.balloons()

                st.markdown("""
                <div class="import-success">
                    <h3>✅ Import Completed Successfully!</h3>
                </div>
                """, unsafe_allow_html=True)

                # Results metrics
                r1, r2, r3, r4 = st.columns(4)

                with r1:
                    st.metric(
                        "📥 Total Rows",
                        result["total_rows"]
                    )

                with r2:
                    st.metric(
                        "✅ Imported",
                        result["imported_rows"]
                    )

                with r3:
                    st.metric(
                        "⏭️ Skipped",
                        result["skipped_rows"]
                    )

                with r4:
                    st.metric(
                        "⚠️ Anomalies Saved",
                        result["anomaly_count"]
                    )

                st.info(
                    "💡 Head to the **Dashboard** to see your data, "
                    "or visit **Balances** to calculate who owes whom."
                )

            else:

                st.error(
                    f"❌ Import failed: {result.get('error', 'Unknown error')}"
                )

                st.info(
                    "Please check your CSV format and try again."
                )