import imaplib
import email
from email.header import decode_header


class MailBox:
    def __init__(self, flag: str, SMTP_SERVER, SMTP_PORT, USER, PASSWORD):

        self.SMTP_SERVER = SMTP_SERVER
        self.SMTP_PORT = SMTP_PORT
        self.USER = USER
        self.PASSWORD = PASSWORD

        self.imap = imaplib.IMAP4_SSL(host=self.SMTP_SERVER, port=self.SMTP_PORT)
        self.imap.login(self.USER, self.PASSWORD)
        self.flag = flag

    def __enter__(self):
        self.emails = self._get_messages_with_flag(self.flag)
        return self

    def __exit__(self,  exp_type, exp_value, exp_tr):
        self.imap.close()
        self.imap.logout()

    def fetch_message(self, num=0):
        status, data = self.imap.fetch(self.emails[num], '(RFC822)')

        if status != 'OK':
            raise NameError("Error with searching mail")

        _, bytes_data = data[0]
        email_message = email.message_from_bytes(bytes_data)
        return email_message

    def get_attachment(self, num=0):
        res = []
        for part in self.fetch_message(num).walk():
            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                continue
            if part.get_filename():

                try:
                    res.append([decode_header(part.get_filename())[0][0].decode(),
                                part.get_payload(decode=True).strip()])
                except:
                    res.append([part.get_filename(), part.get_payload(decode=True).strip()])

        return res

    def _get_messages_with_flag(self, flag="ALL", count=-1):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, flag)

        if status != 'OK':
            raise NameError("Error with parsing email")

        res = data[0].split()

        if len(res) < count or count == -1:
            return res

        return res[:count]

