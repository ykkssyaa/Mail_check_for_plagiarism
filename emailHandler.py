import imaplib
import email


class MailBox:
    SMTP_SERVER = "imap.mail.ru"
    SMTP_PORT = 993
    USER = "mr.ender.03@mail.ru"
    PASSWORD = "m78pQdtJQ9vn6UAJPEUa"

    def __init__(self):
        self.imap = imaplib.IMAP4_SSL(host=self.SMTP_SERVER, port=self.SMTP_PORT)
        self.imap.login(self.USER, self.PASSWORD)

    def __enter__(self):
        self.emails = self._get_all_messages()

    def __exit__(self):
        self.imap.close()
        self.imap.logout()

    def fetch_message(self, num=-1):
        status, data = self.imap.fetch(self.emails[num], '(RFC822)')

        if status != 'OK':
            raise NameError("Error with searching mail")

        _, bytes_data = data[0]
        email_message = email.message_from_bytes(bytes_data)
        return email_message

    def get_attachment(self, num=-1):
        for part in self.fetch_message(num).walk():
            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                continue
            if part.get_filename():
                return [part.get_filename(), part.get_payload(decode=True).strip()]

    def _get_all_messages(self, count=-1):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')

        if status != 'OK':
            raise NameError("Error with parsing email")

        res = data[0].split()

        if len(res) < count:
            return res

        return res[:count]

    def _get_unseen_messages(self, count=-1):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'UNSEEN')

        if status != 'OK':
            raise NameError("Error with parsing email")

        res = data[0].split()

        if len(res) < count:
            return res

        return res[:count]
