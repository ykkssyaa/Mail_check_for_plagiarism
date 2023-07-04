import email
import imaplib
from email.header import decode_header
import base64
from bs4 import BeautifulSoup
import re

#  Сохранение зависимостей -  pip freeze > requirements.txt

# TODO: сделать через настраиваемый корфиг
mail_pass = "m78pQdtJQ9vn6UAJPEUa"
username = "mr.ender.03@mail.ru"
imap_server = "imap.mail.ru"
imap_port = 993

# Подключение к почте
imap = imaplib.IMAP4_SSL(host=imap_server, port=imap_port)
imap.login(username, mail_pass)


def main():
    select_resp = imap.select("INBOX")
    mails_count = int(select_resp[1][0])

    # TODO: Проверка на корректность подключения
    print(f"Start - Status:<{select_resp[0]}>, mails count:{mails_count}")

    res, msg = imap.fetch(b'853', '(RFC822)')
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


if __name__ == '__main__':
    main()





