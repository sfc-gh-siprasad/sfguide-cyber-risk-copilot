-- Cyber Risk Copilot: cleanup. Removes everything the setup created.
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS CYBER_RISK_COPILOT;   -- tables, semantic view, search service, agent
DROP WAREHOUSE IF EXISTS CYBER_COPILOT_WH;
DROP ROLE IF EXISTS CYBER_COPILOT_ROLE;
-- If you deployed the Streamlit app, it lives in CYBER_RISK_COPILOT and is dropped with the database.
