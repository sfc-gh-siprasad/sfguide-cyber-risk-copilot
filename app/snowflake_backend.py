"""Live mode: same app against Snowflake on the synthetic data from sql/.

Local run:  SNOWFLAKE_CONNECTION_NAME=<your connection> streamlit run app/streamlit_app.py
Streamlit in Snowflake: the active Snowpark session is used automatically.
"""

import json
import os

import pandas as pd

DB, SCHEMA = "CYBER_RISK_COPILOT", "DATA"
ROLE, WAREHOUSE = "CYBER_COPILOT_ROLE", "CYBER_COPILOT_WH"
AGENT = "CYBER_RISK_COPILOT_AGENT"
MODE_LABEL = "Live: Snowflake"

SAMPLE_QUESTIONS = [
    "Which Tier 1 services have the most open critical findings?",
    "What is our SLA breach rate for internet-facing assets?",
    "Which teams have the most overdue findings?",
    "What does policy say about remediation deadlines for known exploited findings?",
]


class LiveUnavailable(Exception):
    pass


def _session():
    """Return (kind, handle). Snowpark session inside Snowflake, connector locally."""
    try:
        from snowflake.snowpark.context import get_active_session
        return "snowpark", get_active_session()
    except Exception:
        pass
    try:
        import snowflake.connector
    except ImportError as exc:
        raise LiveUnavailable("Install snowflake-connector-python to use live mode.") from exc
    name = os.environ.get("SNOWFLAKE_CONNECTION_NAME")
    if not name:
        raise LiveUnavailable("Set SNOWFLAKE_CONNECTION_NAME to a connection in your Snowflake config.")
    try:
        conn = snowflake.connector.connect(connection_name=name, role=ROLE, warehouse=WAREHOUSE,
                                           database=DB, schema=SCHEMA)
    except Exception as exc:
        raise LiveUnavailable(f"Could not connect with '{name}': {exc}") from exc
    return "connector", conn


def query(sql: str) -> pd.DataFrame:
    kind, h = _session()
    if kind == "snowpark":
        return h.sql(sql).to_pandas()
    cur = h.cursor()
    try:
        cur.execute(sql)
        return cur.fetch_pandas_all()
    finally:
        cur.close()


def load_frames() -> dict:
    frames = {}
    for n in ("findings", "assets", "services", "teams"):
        df = query(f"SELECT * FROM {DB}.{SCHEMA}.{n}")
        df.columns = [c.lower() for c in df.columns]
        frames[n] = df
    p = query(f"SELECT * FROM {DB}.{SCHEMA}.POLICY_DOCS")
    p.columns = [c.lower() for c in p.columns]
    frames["policies"] = p
    return frames


def semantic_view_kpis() -> dict:
    """Headline numbers computed by the semantic view, not by the app."""
    df = query(
        f"SELECT * FROM SEMANTIC_VIEW({DB}.{SCHEMA}.CYBER_POSTURE "
        "METRICS findings.open_findings, findings.open_critical_findings, findings.sla_breach_rate, "
        "findings.avg_open_age_days)")
    r = df.iloc[0]
    r.index = [c.lower() for c in r.index]
    return {"open_findings": int(r["open_findings"]), "open_critical": int(r["open_critical_findings"]),
            "sla_breach_rate": float(r["sla_breach_rate"]), "avg_open_age_days": float(r["avg_open_age_days"])}


def _rest_call(body: dict):
    """POST to the Cortex Agents run endpoint using the active session."""
    path = f"/api/v2/databases/{DB}/schemas/{SCHEMA}/agents/{AGENT}:run"
    kind, h = _session()
    if kind == "snowpark":
        import _snowflake
        resp = _snowflake.send_snow_api_request("POST", path, {}, {}, body, None, 60000)
        if resp.get("status", 200) >= 400:
            raise LiveUnavailable(f"Agent call failed: {resp.get('content')}")
        return resp.get("content")
    import requests
    url = f"https://{h.host}{path}"
    headers = {"Authorization": f'Snowflake Token="{h.rest.token}"', "Content-Type": "application/json",
               "Accept": "application/json"}
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=120)
    if r.status_code >= 400:
        raise LiveUnavailable(f"Agent call failed ({r.status_code}): {r.text[:300]}")
    return r.text


def _parse(content) -> dict:
    """Pull text, SQL, result tables and cited sources from an agent response."""
    text, sql, table, sources = [], None, None, []
    events = []
    if isinstance(content, str):
        try:
            events = [json.loads(content)]
        except json.JSONDecodeError:
            for block in content.split("\n\n"):
                for line in block.splitlines():
                    if line.startswith("data:") and "[DONE]" not in line:
                        try:
                            events.append(json.loads(line[5:].strip()))
                        except json.JSONDecodeError:
                            pass
    else:
        events = content if isinstance(content, list) else [content]

    def walk(node):
        nonlocal sql, table
        if isinstance(node, dict):
            t = node.get("type")
            if t == "text" and isinstance(node.get("text"), str):
                text.append(node["text"])
            if "sql" in node and isinstance(node["sql"], str):
                sql = node["sql"]
            rs = node.get("result_set")
            if isinstance(rs, dict) and rs.get("data") is not None:
                cols = [c["name"] for c in rs.get("resultSetMetaData", {}).get("rowType", [])]
                table = pd.DataFrame(rs["data"], columns=cols or None)
            for k, v in node.items():
                if k not in ("result_set",):
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for ev in events:
        walk(ev.get("data", ev) if isinstance(ev, dict) else ev)
    return {"text": "".join(text).strip(), "sql": sql, "table": table, "sources": sources}


def ask(question: str, df=None, frames=None) -> dict:
    body = {"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}], "stream": False}
    parsed = _parse(_rest_call(body))
    return {"answer": parsed["text"] or "The agent returned no text.", "table": parsed["table"],
            "sources": parsed["sources"], "sql": parsed["sql"], "chart": None, "mocked": False}
