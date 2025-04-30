DROP TABLE IF EXISTS user;

CREATE TABLE config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT UNIQUE NOT NULL,
  value TEXT
);

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uid TEXT UNIQUE DEFAULT (lower(hex(randomblob(16)))) NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  mfa_seed TEXT,
  session_id TEXT,
  default_scope INTEGER NOT NULL DEFAULT id,
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
  extendedattributes TEXT,
  FOREIGN KEY (project_id) REFERENCES project (id),
  FOREIGN KEY (queuehoo) REFERENCES hoo (id)
);

CREATE TABLE queueAction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  queue_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  param1 TEXT NOT NULL,
  param2 TEXT NOT NULL,
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
  daily_pattern TEXT,
  callback_pattern TEXT,
  holiday_pattern TEXT,
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

CREATE TABLE tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT UNIQUE NOT NULL,
  task_started_at DATETIME DEFAULT NOW,
  task_is_active BOOLEAN,
  task_description TEXT,
  task_status_description TEXT,
  task_status TEXT
);

--This will be a list of roles that can be assigned
CREATE TABLE role (
id INTEGER PRIMARY KEY AUTOINCREMENT,
uid TEXT DEFAULT (lower(hex(randomblob(16)))) ,
name TEXT UNIQUE NOT NULL,
description TEXT
);

--This will be a list of permissions that we can check against
CREATE TABLE permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT DEFAULT (lower(hex(randomblob(16)))),
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

--This will map permissions to roles
CREATE TABLE role_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   
    uid TEXT DEFAULT (lower(hex(randomblob(16)))) ,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Role(id),
    FOREIGN KEY (permission_id) REFERENCES permission(id)
);

--This will map users to roles
CREATE TABLE user_role (
id INTEGER PRIMARY KEY AUTOINCREMENT,
uid TEXT DEFAULT (lower(hex(randomblob(16)))) ,
user_id int NOT NULL,
role_id int NOT NULL,
FOREIGN KEY (user_id) REFERENCES user (id),
FOREIGN KEY (role_id) REFERENCES role (id)
);


INSERT INTO role (name, description) VALUES ('Impersonation', 'Application Administrator'); 
INSERT INTO role (name, description) VALUES ('Administrator', 'Administrator');
INSERT INTO role (name, description) VALUES ('Power User', 'Access to deploy projects');
INSERT INTO role (name, description) VALUES ('User', 'No access to projects or deployments');

INSERT INTO permission (name, description) VALUES ('PROJECT', 'Access the project page'); 
INSERT INTO permission (name, description) VALUES ('AUDIO', 'Access the audio page'); 
INSERT INTO permission (name, description) VALUES ('CALLFLOW', 'Access the call flows page'); 
INSERT INTO permission (name, description) VALUES ('QUEUE', 'Access the queue page'); 
INSERT INTO permission (name, description) VALUES ('ENTRYPOINT', 'Access the ENTRY POINT page'); 
INSERT INTO permission (name, description) VALUES ('HOO', 'Access the hours of operation page'); 
INSERT INTO permission (name, description) VALUES ('SKILL', 'Access the skill page'); 
INSERT INTO permission (name, description) VALUES ('DEPLOYMENT', 'Access the deployment page'); 
INSERT INTO permission (name, description) VALUES ('ADMIN', 'Access the administrator page'); 
INSERT INTO permission (name, description) VALUES ('ADMIN.USER.CREATE', 'Create a new user');
INSERT INTO permission (name, description) VALUES ('ADMIN.USER.DELETE', 'Delete a user');
INSERT INTO permission (name, description) VALUES ('ADMIN.USER.EDIT', 'Edit an existing user');
INSERT INTO permission (name, description) VALUES ('ADMIN.SCOPE.ALL', 'Can see and modify access to all projects');
INSERT INTO permission (name, description) VALUES ('ADMIN.SCOPE.ASSIGN', 'Can assign accessible projects to other users');


-- Attach permissions for Impersonation
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'ADMIN';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'ADMIN.USER.CREATE';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'ADMIN.USER.DELETE';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'ADMIN.USER.EDIT';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'ADMIN.SCOPE.ALL';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'ADMIN.SCOPE.ASSIGN';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'PROJECT';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'AUDIO';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'CALLFLOW';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'QUEUE';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'ENTRYPOINT';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'HOO';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'SKILL';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Impersonation' AND p.name = 'DEPLOYMENT';

-- Attach permissions for Administrator
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'PROJECT';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'AUDIO';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'CALLFLOW';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'QUEUE';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'ENTRYPOINT';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'HOO';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'SKILL';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Administrator' AND p.name = 'DEPLOYMENT';

-- Attach permissions to for Power User
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Power User' AND p.name = 'PROJECT';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Power User' AND p.name = 'AUDIO';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Power User' AND p.name = 'CALLFLOW';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Power User' AND p.name = 'QUEUE';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Power User' AND p.name = 'ENTRYPOINT';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Power User' AND p.name = 'HOO';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'Power User' AND p.name = 'SKILL';

-- Attach permissions to for User
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'User' AND p.name = 'AUDIO';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'User' AND p.name = 'CALLFLOW';
INSERT INTO role_permission (role_id, permission_id) 
SELECT r.id, p.id FROM role r, permission p WHERE r.name = 'User' AND p.name = 'QUEUE';

-- Create 1:1 scope as admin for all existing users
INSERT INTO user_role (user_id, role_id)
SELECT u.id, r.id FROM user u, role r WHERE r.name = 'Administrator';

-- Add impersonation user to system
INSERT INTO user (username,password) VALUES (
  'administrator@cxtools.cco.com.au',
  'P@ssword123'
);
--Assign impersonation role to new admin user
INSERT INTO user_role (user_id, role_id)
SELECT u.id, r.id FROM user u, role r WHERE r.name = 'Impersonation' AND u.username = 'administrator@cxtools.cco.com.au' ;

-- Add demo user to system
INSERT INTO user (username,password) VALUES (
  'demo@demo.com',
  'password'
);
--Assign role to new demo user
INSERT INTO user_role (user_id, role_id)
SELECT u.id, r.id FROM user u, role r WHERE r.name = 'Administrator' AND u.username = 'demo@demo.com.au' ;

UPDATE config SET value = '0_0_0_15' where key ='version'