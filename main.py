#! /usr/bin/env python
# -*- coding: windows-1251 -*-
import email
import imaplib
from email.header import decode_header
from datetime import datetime, timedelta

import emailHandler

#  ���������� ������������ -  pip freeze > requirements.txt

# TODO: ������� ����� ������������� ������
mail_pass = "m78pQdtJQ9vn6UAJPEUa"
username = "mr.ender.03@mail.ru"
imap_server = "imap.mail.ru"
imap_port = 993
doc_dir = "F:\\IT\\AntiPlagiat"
valid_file_extensions = ["docx", "pdf"]

DAYS_COUNT = 7

# TODO: ������
# ����������� � �����
imap = imaplib.IMAP4_SSL(host=imap_server, port=imap_port)
imap.login(username, mail_pass)


def m_main():
    select_resp = imap.select("INBOX")
    mails_count = int(select_resp[1][0])

    # TODO: �������� �� ������������ �����������
    print(f"Start - Status:<{select_resp[0]}>, mails count:{mails_count}")

    res, msg = imap.fetch(b'858', '(RFC822)')
    msg = email.message_from_bytes(msg[0][1])

    # ���� ���������, �������� � ���� ������, ������ ���� � ������� � ������ datetime
    letter_date = email.utils.parsedate_tz(msg["Date"])
    letter_id = msg["Message-ID"]  # ���� ������
    letter_from = msg["Return-path"]

    print(f"Date: {letter_date}, ID: {letter_id}, FROM: {letter_from}\n")

    # TODO: �������� �� ������ ��������
    header = decode_header(msg["Subject"])[0][0].decode()  # ������������� �������� ������
    print(header)

    for part in msg.walk():

        if part.get_content_disposition() == 'attachment':
            print(decode_header(part.get_filename())[0][0].decode())  # ��������� �������� �����

            with open(decode_header(part.get_filename())[0][0].decode(), "wb") as f:
                f.write(part.get_payload(decode=True))  # ���������� �����


def main_menu():
    print("����:")
    print("1. �������� ����� �� ��������� ������")  # TODO: �����������
    print("2. �������� ������������� ����� �� ��������� ������")  # TODO: �����������
    print("3. �������� ������������� ����� �� ��������� N ����")  # TODO: �����������
    print("4. ������ � �������")
    print("0. �����")

    return input("��� �����: ")


def config_info():
    pass  # TODO: �����������


def isFileValid(filename: str):
    for extension in valid_file_extensions:
        if extension in filename:
            return True
    return False


# �������� ������ �� ������ � ���������� �����������
def deleteNotValidFiles(attachment):
    for i in range(len(attachment)):
        if not isFileValid(attachment[i][0]):
            attachment.pop(i)

    return attachment


# ��������� ���� ������ � ���� ���������
def message_processing(msg):
    date = email.utils.parsedate_tz(msg["Date"])

    present = datetime.now()
    date = datetime(date[0], date[1], date[2])

    if (present - date).days > DAYS_COUNT:
        raise NameError("End processing")

    title = ""

    try:
        title = (decode_header(msg["Subject"])[0][0].decode())
    except AttributeError:
        title = (decode_header(msg["Subject"])[0][0])
    except TypeError:
        title = "��� ����"
    except UnicodeDecodeError:
        title = decode_header(msg["Subject"])[0][0].decode("windows-1251")
    except:
        title = "������ ��������� ����"

    return [date.date(), title]


# ������ �� ���� �������, ������� ���� �������� � ������� ������
def check_mail_last_week(flag: str):
    try:
        with emailHandler.MailBox(flag) as mail:
            for msg_num in range(1, len(mail.emails) + 1):
                try:
                    # �������� � ������ �������� � ������ � �������� �����������
                    attachment = deleteNotValidFiles(mail.get_attachment(-msg_num))
                    if len(attachment) == 0:  # ���� �������� ���, ��������� ������
                        continue

                    # �������� ���� ������ � ���� ���������
                    date, title = message_processing(mail.fetch_message(-msg_num))
                    print(title, attachment[0][0])

                    # TODO: �������� ������ ���� � ������ �� ���������
                    # TODO: ������ ������ �� ���������, ���� ���� ��� ������� �� ��������, ��������� ��� � ��������� �����
                    # TODO: ��������� ������ �� �����������
                    # TODO: ���������� ������� ������ � �������
                    # TODO: ����� ����� � ���� ������������ ������

                except NameError:
                    break

    except NameError as err:
        print(err.name)


# ������� �������
def main():
    # TODO: Hello messages - config data
    print("")

    while True:
        user_input = main_menu()

        match user_input:
            case '1':
                check_mail_last_week("ALL")
            case '2':
                check_mail_last_week("UNSEEN")
            case '3':
                pass
            case '0':
                exit(0)


if __name__ == '__main__':
    main()
    exit(0)
