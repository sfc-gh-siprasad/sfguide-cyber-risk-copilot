"""Shared analytics. Mock and live modes both feed DataFrames through here."""

from datetime import date

import pandas as pd

AS_OF = pd.Timestamp(date(2026, 11, 1))
OPEN_STATUSES = ("Open", "In Progress")
SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]


def prepare(frames: dict) -> pd.DataFrame:
    """Join findings to assets, services and teams and add derived columns."""
    f = frames["findings"].copy()
    for col in ("opened_date", "due_date", "resolved_date"):
        f[col] = pd.to_datetime(f[col])
    a, s, t = frames["assets"], frames["services"], frames["teams"]
    df = (
        f.merge(a.rename(columns={"owner_team_id": "asset_owner_team_id"}), on="asset_id", how="left")
        .merge(s, on="service_id", how="left")
        .merge(t.rename(columns={"line_of_business": "team_lob"}), left_on="owner_team_id", right_on="team_id", how="left")
    )
    for col in ("internet_facing", "exploit_available", "known_exploited"):
        df[col] = df[col].astype(str).str.upper().eq("TRUE")
    df["is_open"] = df["status"].isin(OPEN_STATUSES)
    df["is_overdue"] = df["is_open"] & (df["due_date"] < AS_OF)
    df["open_age_days"] = (AS_OF - df["opened_date"]).dt.days.where(df["is_open"])
    df["is_open_critical"] = df["is_open"] & (df["severity"] == "Critical")
    df["tier_label"] = "Tier " + df["tier"].astype(str)
    return df


def kpis(df: pd.DataFrame) -> dict:
    open_df = df[df["is_open"]]
    n_open = len(open_df)
    return {
        "open_findings": n_open,
        "open_critical": int(open_df["severity"].eq("Critical").sum()),
        "sla_breach_rate": float(open_df["is_overdue"].mean()) if n_open else 0.0,
        "avg_open_age_days": float(open_df["open_age_days"].mean()) if n_open else 0.0,
        "internet_facing_open": int(open_df["internet_facing"].sum()),
        "known_exploited_open": int(open_df["known_exploited"].sum()),
    }


def by_service(df: pd.DataFrame) -> pd.DataFrame:
    o = df[df["is_open"]]
    g = o.groupby(["service_name", "tier", "line_of_business", "team_name"], dropna=False)
    out = g.agg(
        open_findings=("finding_id", "count"),
        open_critical=("is_open_critical", "sum"),
        overdue=("is_overdue", "sum"),
        avg_age_days=("open_age_days", "mean"),
    ).reset_index()
    out["sla_breach_rate"] = (out["overdue"] / out["open_findings"]).round(3)
    out["avg_age_days"] = out["avg_age_days"].round(1)
    out["open_critical"] = out["open_critical"].astype(int)
    out["overdue"] = out["overdue"].astype(int)
    return out.sort_values(["open_critical", "overdue", "open_findings"], ascending=False).reset_index(drop=True)


def by_severity(df: pd.DataFrame) -> pd.DataFrame:
    o = df[df["is_open"]]
    out = o.groupby("severity").agg(open_findings=("finding_id", "count"), overdue=("is_overdue", "sum")).reset_index()
    out["severity"] = pd.Categorical(out["severity"], SEVERITY_ORDER, ordered=True)
    return out.sort_values("severity").reset_index(drop=True)


def by_team(df: pd.DataFrame) -> pd.DataFrame:
    o = df[df["is_open"]]
    out = o.groupby("team_name", dropna=False).agg(
        open_findings=("finding_id", "count"), overdue=("is_overdue", "sum"),
        open_critical=("is_open_critical", "sum"),
    ).reset_index()
    out["team_name"] = out["team_name"].fillna("Unowned")
    return out.sort_values(["overdue", "open_findings"], ascending=False).reset_index(drop=True)


def aging_buckets(df: pd.DataFrame) -> pd.DataFrame:
    o = df[df["is_open"]].copy()
    bins = [-1, 30, 90, 180, 10_000]
    labels = ["0-30 days", "31-90 days", "91-180 days", "Over 180 days"]
    o["bucket"] = pd.cut(o["open_age_days"], bins=bins, labels=labels)
    out = o.groupby(["bucket", "severity"], observed=False).size().reset_index(name="Open findings")
    return out


def monthly_trend(df: pd.DataFrame, months: int = 12) -> pd.DataFrame:
    start = (AS_OF - pd.DateOffset(months=months)).replace(day=1)
    opened = df[df["opened_date"] >= start].groupby(df["opened_date"].dt.to_period("M")).size()
    resolved = df[df["resolved_date"].notna() & (df["resolved_date"] >= start)].groupby(
        df["resolved_date"].dt.to_period("M")).size()
    last_full = (AS_OF - pd.DateOffset(months=1)).to_period("M")
    idx = pd.period_range(start.to_period("M"), last_full, freq="M")
    out = pd.DataFrame({"month": idx.to_timestamp(),
                        "Opened": opened.reindex(idx, fill_value=0).values,
                        "Resolved": resolved.reindex(idx, fill_value=0).values})
    return out


def priority_queue(df: pd.DataFrame, limit: int = 15) -> pd.DataFrame:
    o = df[df["is_open"]].copy()
    sev_w = o["severity"].map({"Critical": 40, "High": 25, "Medium": 10, "Low": 3})
    o["priority_score"] = (
        sev_w + o["known_exploited"] * 25 + o["exploit_available"] * 10 + o["internet_facing"] * 15
        + (6 - o["tier"]) * 4 + o["is_overdue"] * 10
    )
    cols = ["finding_id", "title", "severity", "service_name", "tier", "asset_name", "internet_facing",
            "known_exploited", "due_date", "team_name", "priority_score"]
    return o.sort_values("priority_score", ascending=False).head(limit)[cols].reset_index(drop=True)
