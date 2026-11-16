-- Cyber Risk Copilot: semantic view for Cortex Analyst.
-- Reporting date is fixed at 2026-11-01 so results match the screenshots.
USE ROLE CYBER_COPILOT_ROLE;
USE WAREHOUSE CYBER_COPILOT_WH;
USE SCHEMA CYBER_RISK_COPILOT.DATA;

CREATE OR REPLACE SEMANTIC VIEW CYBER_POSTURE
  TABLES (
    findings AS FINDINGS PRIMARY KEY (finding_id)
      COMMENT = 'One row per security finding on an asset (synthetic).',
    assets AS ASSETS PRIMARY KEY (asset_id)
      COMMENT = 'Technology assets that findings are raised against.',
    services AS SERVICES PRIMARY KEY (service_id)
      COMMENT = 'Business services. Tier 1 is the most critical.',
    teams AS TEAMS PRIMARY KEY (team_id)
      COMMENT = 'Teams that own services.'
  )
  RELATIONSHIPS (
    findings_to_assets AS findings (asset_id) REFERENCES assets,
    assets_to_services AS assets (service_id) REFERENCES services,
    services_to_teams AS services (owner_team_id) REFERENCES teams
  )
  FACTS (
    findings.is_open AS IFF(status IN ('Open', 'In Progress'), 1, 0)
      COMMENT = '1 when the finding is still open or in progress',
    findings.is_open_critical AS IFF(status IN ('Open', 'In Progress') AND severity = 'Critical', 1, 0),
    findings.is_overdue AS IFF(status IN ('Open', 'In Progress') AND due_date < DATE '2026-11-01', 1, 0)
      COMMENT = '1 when an open finding is past its remediation due date',
    findings.open_age_days AS IFF(status IN ('Open', 'In Progress'), DATEDIFF('day', opened_date, DATE '2026-11-01'), NULL)
      COMMENT = 'Days since an open finding was opened'
  )
  DIMENSIONS (
    findings.severity AS severity WITH SYNONYMS = ('risk level', 'criticality of finding'),
    findings.status AS status,
    findings.title AS title WITH SYNONYMS = ('vulnerability', 'issue'),
    findings.source AS source,
    findings.known_exploited AS known_exploited WITH SYNONYMS = ('actively exploited'),
    findings.exploit_available AS exploit_available,
    findings.opened_date AS opened_date,
    findings.due_date AS due_date,
    assets.asset_name AS asset_name,
    assets.asset_type AS asset_type,
    assets.environment AS environment,
    assets.internet_facing AS internet_facing WITH SYNONYMS = ('externally exposed', 'public facing'),
    services.service_name AS service_name WITH SYNONYMS = ('application', 'business service'),
    services.tier AS tier WITH SYNONYMS = ('service tier'),
    services.line_of_business AS line_of_business WITH SYNONYMS = ('LOB', 'business line'),
    teams.team_name AS team_name WITH SYNONYMS = ('owner', 'owning team')
  )
  METRICS (
    findings.total_findings AS COUNT(findings.finding_id),
    findings.open_findings AS SUM(findings.is_open)
      COMMENT = 'Findings with status Open or In Progress',
    findings.open_critical_findings AS SUM(findings.is_open_critical)
      COMMENT = 'Open or in-progress findings with severity Critical',
    findings.overdue_findings AS SUM(findings.is_overdue),
    findings.sla_breach_rate AS SUM(findings.is_overdue) / NULLIF(SUM(findings.is_open), 0)
      COMMENT = 'Overdue open findings divided by all open findings',
    findings.avg_open_age_days AS AVG(findings.open_age_days)
  )
  COMMENT = 'Cyber posture: findings, assets, services and owners. Synthetic data.'
  AI_SQL_GENERATION 'Open findings means status Open or In Progress. Use the metrics open_findings, open_critical_findings and sla_breach_rate instead of rebuilding them. The reporting date is 2026-11-01. Round rates to 2 decimals.';
