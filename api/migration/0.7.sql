-- #165 setup developer payment details
ALTER TABLE "user" 
	ADD COLUMN paypal_email VARCHAR(256) NULL;
