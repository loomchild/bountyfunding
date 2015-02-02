-- add developer payment email
ALTER TABLE "user" 
	ADD COLUMN paypal_email VARCHAR(256) NULL;

-- add issue owner
ALTER TABLE "issue"
	ADD COLUMN owner_id INTEGER NULL;

