-- #165 Additional step for developer to set-up Payment Gateway account

-- add developer payment email
ALTER TABLE "user" 
	ADD COLUMN paypal_email VARCHAR(256) NULL;

-- add issue owner
ALTER TABLE "issue"
	ADD COLUMN owner_id INTEGER NULL;

-- add payment recipient
ALTER TABLE "payment"
	ADD COLUMN recipient_id INTEGER NOT NULL;
