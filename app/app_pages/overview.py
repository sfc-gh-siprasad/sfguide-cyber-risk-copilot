import streamlit as st

import analytics
import common

ctx = common.context()
df = ctx["df"]

st.title("Cyber posture overview")
st.caption("As of 1 November 2026 · open means status Open or In Progress")

k = analytics.kpis(df)
badge_note = "Sample data"
if ctx["live"]:
    try:
        sv = ctx["backend"].semantic_view_kpis()
        k.update(sv)
        badge_note = "Headline numbers computed by a Snowflake semantic view"
    except Exception:
        badge_note = "Snowflake data (semantic view query unavailable)"
st.badge(badge_note, icon=":material/database:", color="blue" if ctx["live"] else "gray")

with st.container(horizontal=True):
    st.metric("Open findings", f"{k['open_findings']:,}", border=True)
    st.metric("Open critical", f"{k['open_critical']:,}", border=True)
    st.metric("SLA breach rate", f"{k['sla_breach_rate']:.1%}", border=True,
              help="Overdue open findings divided by all open findings")
    st.metric("Average open age", f"{k['avg_open_age_days']:.0f} days", border=True)
    st.metric("Internet-facing, open", f"{k['internet_facing_open']:,}", border=True)
    st.metric("Known exploited, open", f"{k['known_exploited_open']:,}", border=True)

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Open findings by severity")
        sev = analytics.by_severity(df).rename(columns={"severity": "Severity", "open_findings": "Open", "overdue": "Overdue"})
        st.bar_chart(sev, x="Severity", y=["Open", "Overdue"], stack=False, x_label="", y_label="Findings",
                     alt="Open and overdue findings by severity")
with right:
    with st.container(border=True):
        st.subheader("Opened and resolved by month")
        st.line_chart(analytics.monthly_trend(df), x="month", y=["Opened", "Resolved"], x_label="", y_label="Findings",
                      alt="Findings opened and resolved per month over the last 12 months")

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("How old are open findings?")
        ag = analytics.aging_buckets(df)
        ag = ag.rename(columns={"bucket": "Age", "severity": "Severity"})
        st.bar_chart(ag, x="Age", y="Open findings", color="Severity", stack=True, x_label="",
                     alt="Open findings by age bucket and severity")
with right:
    with st.container(border=True):
        st.subheader("Services with the most open critical findings")
        top = analytics.by_service(df).head(8)[["service_name", "tier", "open_critical", "overdue", "sla_breach_rate"]]
        st.dataframe(
            top, hide_index=True, alt="Top services by open critical findings",
            column_config={
                "service_name": "Service", "tier": "Tier", "open_critical": "Open critical", "overdue": "Overdue",
                "sla_breach_rate": st.column_config.ProgressColumn("SLA breach rate", min_value=0, max_value=1, format="percent"),
            },
        )
