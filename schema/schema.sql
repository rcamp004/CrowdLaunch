CREATE TABLE component_design(component_design_id INTEGER PRIMARY KEY,operator_id INTEGER REFERENCES operator,family_name TEXT,variant TEXT,component_type TEXT,parent_design_id INTEGER REFERENCES component_design,reusable INTEGER,criticality REAL,notes TEXT);

CREATE TABLE condition_observation(observation_id INTEGER PRIMARY KEY AUTOINCREMENT,launch_id TEXT REFERENCES launch,observed_utc TEXT,domain TEXT,metric TEXT,value_numeric REAL,value_text TEXT,unit TEXT,state TEXT,severity TEXT,source_url TEXT,confidence TEXT);

CREATE TABLE failure_causality(upstream_failure_event_id INTEGER REFERENCES failure_event,downstream_failure_event_id INTEGER REFERENCES failure_event,relationship TEXT,confidence REAL,PRIMARY KEY(upstream_failure_event_id,downstream_failure_event_id,relationship));

CREATE TABLE failure_event(failure_event_id INTEGER PRIMARY KEY AUTOINCREMENT,launch_id TEXT REFERENCES launch,attempt_id INTEGER REFERENCES launch_attempt,component_design_id INTEGER REFERENCES component_design,flight_phase TEXT,state_before TEXT,state_after TEXT,failure_mode TEXT,mechanism TEXT,root_cause TEXT,root_cause_status TEXT,mission_effect TEXT,severity TEXT,source_url TEXT,confidence TEXT);

CREATE TABLE ingestion_run(run_id INTEGER PRIMARY KEY AUTOINCREMENT,started_utc TEXT,completed_utc TEXT,source_name TEXT,rows_seen INTEGER,rows_inserted INTEGER,rows_updated INTEGER,status TEXT,notes TEXT);

CREATE TABLE launch(launch_id TEXT PRIMARY KEY,operator_id INTEGER REFERENCES operator,external_id TEXT,mission_name TEXT,vehicle_name TEXT,platform_family_id INTEGER REFERENCES platform_family,mission_type TEXT,launch_site TEXT,planned_utc TEXT,actual_utc TEXT,status TEXT,success INTEGER,landing_recorded INTEGER,booster_flight_no INTEGER,source_url TEXT,source_asof TEXT,ingest_status TEXT);

CREATE TABLE launch_attempt(attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,launch_id TEXT REFERENCES launch,attempt_number INTEGER,scheduled_utc TEXT,outcome TEXT,countdown_reached_sec INTEGER,cause_class TEXT,cause_detail TEXT,affected_component_design_id INTEGER REFERENCES component_design,automatic_abort INTEGER,recycle_hours REAL,source_url TEXT,confidence TEXT,UNIQUE(launch_id,attempt_number));

CREATE TABLE operator(operator_id INTEGER PRIMARY KEY,name TEXT UNIQUE,abbrev TEXT,country TEXT);

CREATE TABLE platform_component(platform_family_id INTEGER REFERENCES platform_family,component_design_id INTEGER REFERENCES component_design,quantity REAL,role TEXT,interface_class TEXT,valid_from TEXT,valid_to TEXT,PRIMARY KEY(platform_family_id,component_design_id,role));

CREATE TABLE platform_family(platform_family_id INTEGER PRIMARY KEY,operator_id INTEGER REFERENCES operator, name TEXT,generation TEXT,first_flight_date TEXT,active INTEGER);

CREATE TABLE source_registry(source_id INTEGER PRIMARY KEY AUTOINCREMENT,source_name TEXT,domain TEXT,url TEXT,cadence TEXT,authority_rank INTEGER,license_notes TEXT,fields_supported TEXT,last_checked_utc TEXT,notes TEXT);

CREATE TABLE underwriting_snapshot(snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,launch_id TEXT REFERENCES launch,asof_utc TEXT,insured_value_usd REAL,p_hardware_go REAL,p_team_go REAL,p_weather_go REAL,p_range_security_go REAL,p_launch_window REAL,p_success_given_launch REAL,p_total_loss REAL,p_partial_loss REAL,partial_loss_severity REAL,pure_risk_rate REAL,uncertainty_load REAL,capital_load REAL,expense_profit_load REAL,indicated_rate REAL,decision TEXT,model_version TEXT);

CREATE VIEW v_component_heritage AS
SELECT cd.component_design_id, cd.family_name, cd.variant, cd.component_type,
COUNT(DISTINCT l.launch_id) known_launches,
SUM(CASE WHEN l.success=1 THEN 1 ELSE 0 END) known_successes,
SUM(CASE WHEN fe.failure_event_id IS NOT NULL THEN 1 ELSE 0 END) known_failure_events
FROM component_design cd
LEFT JOIN platform_component pc ON pc.component_design_id=cd.component_design_id
LEFT JOIN launch l ON l.platform_family_id=pc.platform_family_id
LEFT JOIN failure_event fe ON fe.component_design_id=cd.component_design_id AND fe.launch_id=l.launch_id
GROUP BY cd.component_design_id;
