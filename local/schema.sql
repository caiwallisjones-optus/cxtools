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
  activeproject TEXT
);

CREATE TABLE project (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  owner_name TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  shortname TEXT NOT NULL,
  instancename TEXT NOT NULL,
  buid  TEXT NOT NULL,
  description TEXT NULL,
  ttsvoice TEXT NOT NULL,
  deploymenttype TEXT NOT NULL,
  userkey TEXT NULL,
  usersecret TEXT NULL,
  connected BOOLEAN,
  lastconnected DATETIME,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE audio (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  filename TEXT NOT NULL,
  wording TEXT,
  isSystem BOOLEAN NOT NULL DEFAULT TRUE,
  localSize INTEGER NOT NULL,
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
  FOREIGN KEY (callFlowAction_id) REFERENCES callFlowAction (id)

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
  FOREIGN KEY (callFlow_id) REFERENCES callFlow (id)
  FOREIGN KEY (callFlowAction_id) REFERENCES callFlowAction (id)
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
  external_id INTEGER,
  is_synced BOOLEAN,
  name TEXT,
  description TEXT,
  FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE skill (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  is_synced BOOLEAN,
  external_id INTEGER,
  skillPrefix TEXT,
  name TEXT,
  description TEXT,
  FOREIGN KEY (project_id) REFERENCES project (id)
);


-- INDEX
 
-- TRIGGER
 
-- VIEW

INSERT INTO user (username,password) VALUES (
  'demo@demo.com',
  'password'
);
