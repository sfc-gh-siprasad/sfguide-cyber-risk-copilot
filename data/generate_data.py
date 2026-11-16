"""Deterministic synthetic data for the Cyber Risk Copilot example.

Run: python3 data/generate_data.py
Writes CSVs to data/ and the Snowflake load script to sql/02_data.sql.
Everything is invented; the same seed always yields the same numbers.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SQL = ROOT / "sql"
AS_OF = date(2026, 11, 1)
rng = random.Random(20261101)

TEAMS = [
    ("T01", "Core Banking Platform", "Retail Banking"),
    ("T02", "Digital Channels", "Retail Banking"),
    ("T03", "Payments Engineering", "Payments"),
    ("T04", "Card Services", "Payments"),
    ("T05", "Wealth Technology", "Wealth"),
    ("T06", "Corporate Banking Systems", "Corporate"),
    ("T07", "Cloud Platform", "Shared Platform"),
    ("T08", "Data and Analytics", "Shared Platform"),
]

SERVICE_NAMES = [
    ("Online Banking Portal", "Retail Banking", 1, "T02"),
    ("Mobile Banking App", "Retail Banking", 1, "T02"),
    ("Core Ledger", "Retail Banking", 1, "T01"),
    ("Account Opening", "Retail Banking", 2, "T02"),
    ("Branch Teller Platform", "Retail Banking", 2, "T01"),
    ("Real-Time Payments Hub", "Payments", 1, "T03"),
    ("Wire Transfer Gateway", "Payments", 1, "T03"),
    ("ACH Processing", "Payments", 2, "T03"),
    ("Card Authorization", "Payments", 1, "T04"),
    ("Card Dispute Portal", "Payments", 3, "T04"),
    ("Advisor Workstation", "Wealth", 2, "T05"),
    ("Client Portfolio Portal", "Wealth", 2, "T05"),
    ("Trade Order Router", "Wealth", 1, "T05"),
    ("Commercial Lending Origination", "Corporate", 2, "T06"),
    ("Treasury Management Portal", "Corporate", 1, "T06"),
    ("Trade Finance Platform", "Corporate", 2, "T06"),
    ("Identity Provider", "Shared Platform", 1, "T07"),
    ("API Gateway", "Shared Platform", 1, "T07"),
    ("Container Platform", "Shared Platform", 2, "T07"),
    ("Enterprise Data Platform", "Shared Platform", 2, "T08"),
    ("Reporting and BI", "Shared Platform", 3, "T08"),
    ("Customer Notification Service", "Retail Banking", 3, "T02"),
    ("Fraud Decision Service", "Payments", 1, "T04"),
    ("Document Management", "Shared Platform", 3, "T08"),
]

ASSET_TYPES = ["Virtual Machine", "Container Image", "Database", "API Endpoint", "Load Balancer", "Storage Bucket"]
ENVIRONMENTS = ["Production", "Production", "Production", "Staging", "Development"]
SOURCES = ["Vulnerability Scanner", "Cloud Posture Scanner", "External Exposure Scan"]

FINDING_TITLES = [
    ("Outdated TLS configuration", "Medium"),
    ("Remote code execution in web framework", "Critical"),
    ("Privilege escalation in OS kernel", "High"),
    ("Exposed administrative interface", "High"),
    ("Missing security patch for database engine", "High"),
    ("Storage bucket allows public read", "Critical"),
    ("Weak password policy on service account", "Medium"),
    ("Container image uses end-of-life base image", "Medium"),
    ("Deserialization flaw in message library", "Critical"),
    ("Unauthenticated API endpoint", "High"),
    ("Cross-site scripting in customer portal", "Medium"),
    ("Certificate expiring within 30 days", "Low"),
    ("Verbose error messages disclose stack traces", "Low"),
    ("Open management port reachable from internet", "High"),
    ("Missing HTTP security headers", "Low"),
    ("SQL injection in reporting query", "Critical"),
    ("Insecure direct object reference", "High"),
    ("Outdated open-source dependency with known flaw", "Medium"),
]

SLA_DAYS = {"Critical": 7, "High": 30, "Medium": 90, "Low": 180}
CVSS_BASE = {"Critical": 9.3, "High": 7.8, "Medium": 5.4, "Low": 3.1}

POLICIES = [
    ("Vulnerability Remediation Standard", "Remediation",
     "Critical findings must be remediated within 7 days of discovery. High findings within 30 days, Medium within 90 days, and Low within 180 days. Findings on internet-facing assets or with a known exploit are treated one severity level higher for deadline purposes. Remediation is complete only when a follow-up scan confirms the fix."),
    ("Risk Exception Process", "Exceptions",
     "A remediation exception may be requested when a fix cannot be applied within the deadline. Requests need a business justification, a compensating control, an owner, and an expiry date of no more than 90 days. Critical exceptions require approval from the Chief Information Security Officer delegate. Expired exceptions return the finding to Open status."),
    ("Asset Ownership Standard", "Governance",
     "Every production asset must map to a business service and an owning team in the asset inventory. Assets with no owner are escalated to the platform team after 14 days and reported in the monthly posture review. Ownership changes must be recorded within 5 business days."),
    ("Internet Exposure Policy", "Exposure",
     "Internet-facing assets must be registered, placed behind a web application firewall, and scanned weekly. Administrative interfaces must never be reachable from the internet. Any newly discovered internet-facing asset without a registered owner is treated as shadow IT and escalated within 2 business days."),
    ("Critical Service Prioritization Guide", "Prioritization",
     "Tier 1 services support customer-facing money movement or authentication and receive priority remediation capacity. When capacity is limited, order work by: known exploited findings on Tier 1 services, then internet-facing Critical findings, then remaining Critical and High findings by age."),
    ("Security Metrics Definitions", "Reporting",
     "Open Critical findings counts findings with status Open or In Progress and severity Critical. SLA breach rate is overdue open findings divided by all open findings. Mean age is the average number of days since a finding was opened, measured at the reporting date. Metrics exclude findings in Development environments unless stated."),
    ("Cloud Storage Configuration Standard", "Configuration",
     "Storage buckets must block public access by default, enforce encryption at rest, and log access. Public read access requires an approved exception. Buckets holding customer data must also have versioning and retention enabled."),
    ("Container Image Hygiene", "Configuration",
     "Container images must use a supported base image, be rebuilt at least monthly, and be scanned before deployment. Images with Critical findings may not be promoted to production. End-of-life base images must be replaced within 60 days."),
    ("Third-Party Component Management", "Remediation",
     "Open-source and vendor components must be tracked in an inventory. Components with a known exploited flaw must be upgraded or mitigated within 14 days. Teams own the update path for components they deploy."),
    ("Monthly Posture Review", "Governance",
     "Security leadership reviews posture monthly. The review covers open Critical and High findings, SLA breach rate by business service, aging findings over 90 days, unowned assets, and active exceptions. Owners of services with rising residual risk present a remediation plan."),
]


def d(x):
    return x.isoformat() if x else ""


def build():
    services = []
    for i, (name, lob, tier, team) in enumerate(SERVICE_NAMES, 1):
        services.append({"service_id": f"S{i:03d}", "service_name": name, "line_of_business": lob,
                         "tier": tier, "owner_team_id": team})
    svc_by_id = {s["service_id"]: s for s in services}

    assets = []
    n = 0
    for s in services:
        count = rng.randint(6, 14) if s["tier"] == 1 else rng.randint(5, 10)
        for _ in range(count):
            n += 1
            atype = rng.choice(ASSET_TYPES)
            env = rng.choice(ENVIRONMENTS)
            internet = atype in ("API Endpoint", "Load Balancer") and rng.random() < 0.75 or rng.random() < 0.08
            owner = s["owner_team_id"] if rng.random() > 0.05 else ""
            assets.append({
                "asset_id": f"A{n:04d}",
                "asset_name": f"{atype.split()[0].lower()}-{n:04d}",
                "asset_type": atype,
                "environment": env,
                "internet_facing": str(internet).upper(),
                "service_id": s["service_id"],
                "owner_team_id": owner,
                "criticality": min(5, max(1, 6 - s["tier"] * 1 + rng.choice([-1, 0, 0, 1]))),
            })

    findings = []
    for fid in range(1, 1401):
        a = rng.choice(assets)
        title, sev = rng.choice(FINDING_TITLES)
        if rng.random() < 0.18:
            sev = rng.choice(["Critical", "High", "Medium", "Low"])
        opened = AS_OF - timedelta(days=int(rng.triangular(1, 400, 25)))
        due = opened + timedelta(days=SLA_DAYS[sev])
        exploit = rng.random() < (0.35 if sev in ("Critical", "High") else 0.1)
        kev = exploit and rng.random() < 0.35
        r = rng.random()
        if r < 0.58:
            status, resolved = "Resolved", opened + timedelta(days=rng.randint(2, SLA_DAYS[sev] + 40))
            if resolved > AS_OF:
                status, resolved = "Open", None
        elif r < 0.68:
            status, resolved = "In Progress", None
        elif r < 0.72:
            status, resolved = "Exception", None
        else:
            status, resolved = "Open", None
        cvss = round(min(10.0, max(1.0, CVSS_BASE[sev] + rng.uniform(-0.8, 0.7))), 1)
        findings.append({
            "finding_id": f"F{fid:05d}",
            "asset_id": a["asset_id"],
            "title": title,
            "severity": sev,
            "cvss_score": cvss,
            "exploit_available": str(exploit).upper(),
            "known_exploited": str(kev).upper(),
            "status": status,
            "source": rng.choice(SOURCES),
            "opened_date": d(opened),
            "due_date": d(due),
            "resolved_date": d(resolved),
        })
    return services, assets, findings


def write_csv(name, rows):
    with open(DATA / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def sql_val(v):
    if v == "" or v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if v in ("TRUE", "FALSE"):
        return v
    return "'" + str(v).replace("'", "''") + "'"


def insert_block(table, rows, cols, date_cols=()):
    out = []
    for i in range(0, len(rows), 200):
        chunk = rows[i:i + 200]
        vals = []
        for r in chunk:
            items = []
            for c in cols:
                v = r[c]
                s = sql_val(v)
                if c in date_cols and s != "NULL":
                    s = f"TO_DATE({s})"
                items.append(s)
            vals.append("(" + ", ".join(items) + ")")
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n" + ",\n".join(vals) + ";")
    return "\n\n".join(out)


def main():
    services, assets, findings = build()
    teams = [{"team_id": t, "team_name": n, "line_of_business": l} for t, n, l in TEAMS]
    write_csv("teams.csv", teams)
    write_csv("services.csv", services)
    write_csv("assets.csv", assets)
    write_csv("findings.csv", findings)
    pol = [{"doc_id": f"P{i:02d}", "title": t, "category": c, "content": body}
           for i, (t, c, body) in enumerate(POLICIES, 1)]
    write_csv("policies.csv", pol)

    parts = ["-- Generated by data/generate_data.py. Synthetic data only.",
             "-- Run after 01_setup.sql. Context: role CYBER_COPILOT_ROLE, schema CYBER_RISK_COPILOT.DATA.",
             "USE ROLE CYBER_COPILOT_ROLE;", "USE SCHEMA CYBER_RISK_COPILOT.DATA;", "",
             insert_block("TEAMS", teams, ["team_id", "team_name", "line_of_business"]),
             insert_block("SERVICES", services, ["service_id", "service_name", "line_of_business", "tier", "owner_team_id"]),
             insert_block("ASSETS", assets, ["asset_id", "asset_name", "asset_type", "environment", "internet_facing",
                                             "service_id", "owner_team_id", "criticality"]),
             insert_block("FINDINGS", findings, ["finding_id", "asset_id", "title", "severity", "cvss_score",
                                                 "exploit_available", "known_exploited", "status", "source",
                                                 "opened_date", "due_date", "resolved_date"],
                          date_cols=("opened_date", "due_date", "resolved_date")),
             insert_block("POLICY_DOCS", pol, ["doc_id", "title", "category", "content"])]
    (SQL / "02_data.sql").write_text("\n\n".join(parts) + "\n")
    print(f"teams={len(teams)} services={len(services)} assets={len(assets)} findings={len(findings)} policies={len(pol)}")


if __name__ == "__main__":
    main()
