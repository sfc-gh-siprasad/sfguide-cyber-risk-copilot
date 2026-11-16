-- Cyber Risk Copilot: Cortex Search service over policy documents, and the Cortex Agent.
USE ROLE CYBER_COPILOT_ROLE;
USE WAREHOUSE CYBER_COPILOT_WH;
USE SCHEMA CYBER_RISK_COPILOT.DATA;

CREATE OR REPLACE CORTEX SEARCH SERVICE POLICY_SEARCH
  ON content
  ATTRIBUTES title, category
  WAREHOUSE = CYBER_COPILOT_WH
  TARGET_LAG = '1 day'
  AS (SELECT doc_id, title, category, content FROM POLICY_DOCS);

CREATE OR REPLACE AGENT CYBER_RISK_COPILOT_AGENT
  COMMENT = 'Answers cyber posture questions with governed numbers and cited policy text (synthetic example).'
  PROFILE = '{"display_name": "Cyber Risk Copilot", "color": "blue"}'
  FROM SPECIFICATION
  $$
  orchestration:
    budget:
      seconds: 60
      tokens: 16000
  instructions:
    response: "Be concise. Lead with the number or answer, then one sentence of context. When a policy applies, quote it briefly and name the policy title. State that data is synthetic when asked about real systems."
    orchestration: "Use cyber_data for counts, rates, rankings and trends about findings, assets, services and teams. Use policy_search for questions about standards, deadlines, exceptions and how things should be done. Use both when a question needs a number and the rule behind it."
    sample_questions:
      - question: "Which Tier 1 services have the most open critical findings?"
      - question: "What is our SLA breach rate for internet-facing assets?"
      - question: "What does policy say about remediation deadlines for known exploited findings?"
  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "cyber_data"
        description: "Answers questions about vulnerability findings, assets, business services and owning teams using the CYBER_POSTURE semantic view."
    - tool_spec:
        type: "cortex_search"
        name: "policy_search"
        description: "Searches cyber policy and standards documents: remediation deadlines, exceptions, ownership, exposure, and metric definitions."
    - tool_spec:
        type: "data_to_chart"
        name: "data_to_chart"
        description: "Creates charts from query results."
  tool_resources:
    cyber_data:
      semantic_view: "CYBER_RISK_COPILOT.DATA.CYBER_POSTURE"
      execution_environment:
        type: "warehouse"
        warehouse: "CYBER_COPILOT_WH"
    policy_search:
      name: "CYBER_RISK_COPILOT.DATA.POLICY_SEARCH"
      max_results: "4"
      title_column: "title"
      id_column: "doc_id"
  $$;
