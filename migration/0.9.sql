-- add developer payment email
ALTER TABLE "user" 
	ADD COLUMN password_hash VARCHAR(128) NULL;

