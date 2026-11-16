import streamlit as st

import common

st.set_page_config(page_title="Cyber Risk Copilot", page_icon=":material/shield:", layout="wide")

with st.sidebar:
    st.title(":material/shield: Cyber Risk Copilot")
    st.segmented_control(
        "Data source",
        [common.SAMPLE, common.LIVE],
        default=common.default_mode(),
        key="mode",
        help="Sample data runs with no Snowflake account. Snowflake mode reads the tables created by sql/.",
    )
    ctx = common.context()
    if st.session_state.get("mode") == common.LIVE and not ctx["live"]:
        st.error(f"Snowflake mode is unavailable: {st.session_state.get('live_error', 'unknown error')}", icon=":material/error:")
        st.caption("Showing sample data instead.")
    st.caption(
        "Synthetic data. Illustrative logic, not production, security, or compliance advice. "
        "Not an official Snowflake product."
    )

pages = [
    st.Page("app_pages/overview.py", title="Posture overview", icon=":material/dashboard:", default=True),
    st.Page("app_pages/drill_down.py", title="Services and findings", icon=":material/table_view:"),
    st.Page("app_pages/copilot.py", title="Ask the copilot", icon=":material/chat:"),
]
st.navigation(pages).run()
