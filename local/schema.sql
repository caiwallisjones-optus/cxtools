DROP TABLE IF EXISTS user;

CREATE TABLE config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT UNIQUE NOT NULL,
  value TEXT
);

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  active_project INTEGER
);

CREATE TABLE project (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  short_name TEXT NOT NULL,
  instance_name TEXT NOT NULL,
  bu_id  TEXT NOT NULL,
  description TEXT NULL,
  tts_voice TEXT NOT NULL,
  deployment_type TEXT NOT NULL,
  user_key TEXT NULL,
  user_secret TEXT NULL,
  connected BOOLEAN,
  last_connected DATETIME,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE audio (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  isSystem BOOLEAN NOT NULL DEFAULT FALSE,
  localSize INTEGER NOT NULL DEFAULT 0,
  isSynced BOOLEAN NOT NULL DEFAULT FALSE,
  lastSync TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES user (id)
);

CREATE TABLE queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT,
  skills TEXT, 
  queuehoo INTEGER ,
  prequeehooactions TEXT,
  queehooactions TEXT,
  unattendedemail TEXT,
  FOREIGN KEY (project_id) REFERENCES project (id),
  FOREIGN KEY (queuehoo) REFERENCES hoo (id)
);

CREATE TABLE queueAction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  queue_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  param1 INTEGER NOT NULL,
  param2 INTEGER NOT NULL,
  step_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (queue_id) REFERENCES queue (id)
);

CREATE TABLE queuextendedvariables (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  queue_id INTEGER NOT NULL,
  variable TEXT NOT NULL,
  value TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (queue_id) REFERENCES queue (id)
);

CREATE TABLE callFlow (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT,
  description TEXT,
  poc_list TEXT,
  callFlowAction_id INTEGER, 
  FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE callFlowAction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  callFlow_id INTEGER NOT NULL,
  parent_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  action TEXT NOT NULL,
  params TEXT,
  FOREIGN KEY (callFlow_id) REFERENCES callFlow (id)
);

CREATE TABLE callFlowResponse (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  callFlow_id INTEGER NOT NULL,
  callFlowAction_id INTEGER NOT NULL,
  response TEXT NOT NULL,
  callFlowNextAction_id INTEGER, 
  FOREIGN KEY (callFlow_id) REFERENCES callFlow (id),
  FOREIGN KEY (callFlowAction_id) REFERENCES callFlowAction (id),
  FOREIGN KEY (callFlowNextAction_id) REFERENCES callFlowAction (id)
);

CREATE TABLE poc (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  external_id INTEGER,
  is_synced BOOLEAN,
  name TEXT,
  description TEXT,
  FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE hoo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT,
  description TEXT,
  external_id INTEGER,
  is_synced BOOLEAN,
  FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE skill (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT,
  description TEXT,
  is_synced BOOLEAN,
  external_id INTEGER,
  skill_campaign TEXT DEFAULT "Default",
  skill_type TEXT DEFAULT "Voice",
  FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE deployment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  action TEXT,
  action_object TEXT,
  description TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  success_state BOOLEAN,
  FOREIGN KEY (project_id) REFERENCES project (id)
);


-- INDEX
 
-- TRIGGER
 
-- VIEW

INSERT INTO user (username,password) VALUES (
  'demo@demo.com',
  'password'
);
