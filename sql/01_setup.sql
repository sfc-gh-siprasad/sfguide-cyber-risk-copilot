-- Cyber Risk Copilot: setup. Creates ONLY the objects below; nothing existing is changed.
--   Role       CYBER_COPILOT_ROLE   (least privilege for the example)
--   Warehouse  CYBER_COPILOT_WH     (XSMALL, 60s auto-suspend)
--   Database   CYBER_RISK_COPILOT   (schema DATA)
-- Part A needs a role that can create roles, warehouses and databases (e.g. ACCOUNTADMIN).
-- Part B runs as the least-privilege demo role.
-- Synthetic data only. Not production or compliance advice.

-- ---------- Part A: admin ----------
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS CYBER_COPILOT_ROLE;

CREATE WAREHOUSE IF NOT EXISTS CYBER_COPILOT_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS CYBER_RISK_COPILOT;
CREATE SCHEMA IF NOT EXISTS CYBER_RISK_COPILOT.DATA;

GRANT USAGE, OPERATE ON WAREHOUSE CYBER_COPILOT_WH TO ROLE CYBER_COPILOT_ROLE;
GRANT OWNERSHIP ON DATABASE CYBER_RISK_COPILOT TO ROLE CYBER_COPILOT_ROLE COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA CYBER_RISK_COPILOT.DATA TO ROLE CYBER_COPILOT_ROLE COPY CURRENT GRANTS;
-- Cortex Analyst, Search and Agents run on Snowflake-hosted models.
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE CYBER_COPILOT_ROLE;
-- Let the signed-in user use the role.
SET me = (SELECT CURRENT_USER());
GRANT ROLE CYBER_COPILOT_ROLE TO USER IDENTIFIER($me);

-- ---------- Part B: demo role ----------
USE ROLE CYBER_COPILOT_ROLE;
USE WAREHOUSE CYBER_COPILOT_WH;
USE SCHEMA CYBER_RISK_COPILOT.DATA;

CREATE OR REPLACE TABLE TEAMS (
  team_id STRING PRIMARY KEY, team_name STRING, line_of_business STRING);

CREATE OR REPLACE TABLE SERVICES (
  service_id STRING PRIMARY KEY, service_name STRING, line_of_business STRING,
  tier NUMBER, owner_team_id STRING);

CREATE OR REPLACE TABLE ASSETS (
  asset_id STRING PRIMARY KEY, asset_name STRING, asset_type STRING, environment STRING,
  internet_facing BOOLEAN, service_id STRING, owner_team_id STRING, criticality NUMBER);

CREATE OR REPLACE TABLE FINDINGS (
  finding_id STRING PRIMARY KEY, asset_id STRING, title STRING, severity STRING,
  cvss_score NUMBER(3,1), exploit_available BOOLEAN, known_exploited BOOLEAN,
  status STRING, source STRING, opened_date DATE, due_date DATE, resolved_date DATE);

CREATE OR REPLACE TABLE POLICY_DOCS (
  doc_id STRING PRIMARY KEY, title STRING, category STRING, content STRING);
