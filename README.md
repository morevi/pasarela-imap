
# TODO:

## Code quality

- [x] simplify controller functions RECV and OTHERS

## Security

- [x] check email before leaving black
- [x] ensure HTTPS

## IMAP Pasarela

- [x] basic auth
- [x] dirs
- [x] delete
- [x] mark as unseen
- [x] mails
	- [x] av on body and attachments
	- [x] store attachments and give link under auth
	- [x] return body and attachments links
	- [x] on link dl the attachment
- [x] log auth and posible errors: av, auth

## QoL tasks

- [x] pagination (hardcoded), limit and page number

## Web interface

- [x] choose framework for easier development
- [x] login component
- [x] site mock
- [x] interactions
	- [x] after login display dirs
	- [x] on dir get mails
	- [x] on mail get mail body and links
	- [x] on link dl file
	- [x] on delete delete mail
	- [x] on unseen mark mail unseen
