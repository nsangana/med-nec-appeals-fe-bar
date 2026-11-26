-- FE Bar lineage: bronze -> silver -> gold -> grounding -> appeals_output (plus worklist_serving / review_state_uc when they exist).
-- Source: system.access.table_lineage (table-level edges, last 30 days). Read-only.
-- Edge count per hop first, then the edges themselves.
SELECT source_table_full_name, target_table_full_name, COUNT(*) AS edge_events, MAX(event_time) AS last_seen
FROM system.access.table_lineage
WHERE event_date >= current_date() - 30
  AND target_table_catalog = 'appeals_hackathon_catalog'
  AND target_table_schema = 'fe_bar_appeals'
  AND source_table_catalog = 'appeals_hackathon_catalog'
  AND source_table_schema = 'fe_bar_appeals'
GROUP BY source_table_full_name, target_table_full_name
ORDER BY target_table_full_name, source_table_full_name;
