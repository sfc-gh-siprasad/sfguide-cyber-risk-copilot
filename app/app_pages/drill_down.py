import streamlit as st

import analytics
import common

ctx = common.context()
df = ctx["df"]

st.title("Services and findings")
st.caption("Choose a service to see its highest-priority open findings. Ordering uses a simple illustrative score.")

with st.container(horizontal=True, vertical_alignment="bottom"):
    tiers = st.pills("Service tier", [1, 2, 3], selection_mode="multi", default=[1, 2, 3],
                     format_func=lambda t: f"Tier {t}", key="tiers")
    lobs = sorted(df["line_of_business"].dropna().unique())
    selected_lobs = st.multiselect("Line of business", lobs, default=lobs, key="lobs")

svc = analytics.by_service(df)
svc = svc[svc["tier"].isin(tiers or [1, 2, 3]) & svc["line_of_business"].isin(selected_lobs)].reset_index(drop=True)

with st.container(border=True):
    st.subheader("Services")
    st.dataframe(
        svc, hide_index=True,
        alt="Services with open findings, sorted by open critical findings",
        column_config={
            "service_name": "Service", "tier": "Tier", "line_of_business": "Line of business", "team_name": "Owning team",
            "open_findings": "Open", "open_critical": "Critical", "overdue": "Overdue",
            "avg_age_days": st.column_config.NumberColumn("Avg age (days)", format="%.0f"),
            "sla_breach_rate": st.column_config.ProgressColumn("SLA breach rate", min_value=0, max_value=1, format="percent"),
        },
    )

if svc.empty:
    st.info("No services match the filters.", icon=":material/filter_alt_off:")
    st.stop()

name = st.selectbox("Show findings for", svc["service_name"].tolist(), key="svc_pick")
sub = df[df["service_name"] == name]
with st.container(border=True):
    st.subheader(f"Highest-priority open findings: {name}")
    q = analytics.priority_queue(sub, limit=15)
    st.dataframe(
        q, hide_index=True, alt=f"Priority queue of open findings for {name}",
        column_config={
            "finding_id": "Finding", "title": "Title", "severity": "Severity", "service_name": None, "tier": None,
            "asset_name": "Asset", "internet_facing": "Internet-facing", "known_exploited": "Known exploited",
            "due_date": st.column_config.DateColumn("Due"), "team_name": "Owner",
            "priority_score": st.column_config.NumberColumn("Priority score"),
        },
    )
