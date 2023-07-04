import email
import imaplib
from email.header import decode_header

import emailHandler

#  Сохранение зависимостей -  pip freeze > requirements.txt

# TODO: сделать через настраиваемый корфиг
mail_pass = "m78pQdtJQ9vn6UAJPEUa"
username = "mr.ender.03@mail.ru"
imap_server = "imap.mail.ru"
imap_port = 993

# Подключение к почте
imap = imaplib.IMAP4_SSL(host=imap_server, port=imap_port)
imap.login(username, mail_pass)

filename = "file.docx"

def main():
    select_resp = imap.select("INBOX")
    mails_count = int(select_resp[1][0])

    # TODO: Проверка на корректность подключения
    print(f"Start - Status:<{select_resp[0]}>, mails count:{mails_count}")

    res, msg = imap.fetch(b'858', '(RFC822)')
    msg = email.message_from_bytes(msg[0][1])

    # дата получения, приходит в виде строки, дальше надо её парсить в формат datetime
    letter_date = email.utils.parsedate_tz(msg["Date"])
    letter_id = msg["Message-ID"]  # айди письма
    letter_from = msg["Return-path"]

    print(f"Date: {letter_date}, ID: {letter_id}, FROM: {letter_from}\n")

    # TODO: Проверка на пустое название
    header = decode_header(msg["Subject"])[0][0].decode()  # Декодирование названия письма
    print(header)

    for part in msg.walk():

        if part.get_content_disposition() == 'attachment':
            print(decode_header(part.get_filename())[0][0].decode())  # Получение названия файла

            with open(filename, "wb") as f:
                f.write(part.get_payload(decode=True))  # Сохранение файла


if __name__ == '__main__':
    # main()
    mail = emailHandler.MailBox()
    mail.__enter__()

    msg = mail.fetch_message()
    title = decode_header(msg["Subject"])[0][0].decode()
    print(title)

    with open(filename, "wb") as f:
        f.write(mail.get_attachment()[1])

    mail.__exit__()








