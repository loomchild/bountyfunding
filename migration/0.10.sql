-- add account to user
ALTER TABLE user 
	ADD COLUMN account_id INTEGER NULL REFERENCES account(account_id);

CREATE UNIQUE INDEX idx_user_project_id_account_id ON users(project_id, account_id);
CREATE INDEX idx_user_account_id ON users(account_id);

-- add account to sponsorship
ALTER TABLE sponsorship 
	ADD COLUMN account_id INTEGER NULL REFERENCES account(account_id);
	ALTER COLUMN user_id INTEGER NULL REFERENCES user(user_id);


