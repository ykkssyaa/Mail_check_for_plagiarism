#! /usr/bin/env python
# -*- coding: windows-1251 -*-
import email
import imaplib
import os
import time
from email.header import decode_header
from datetime import datetime, timedelta
import urllib.request

import emailHandler
import antiPlagiatAPI

#  ���������� ������������ -  pip freeze > requirements.txt

# TODO: ������� ����� ������������� ������
doc_dir = ""   # �����, ���� ��������� ��������� ����� � ������ � ���
valid_file_extensions = [".docx", ".pdf"]  # ���������� ���������� ������, ������ ��� ����� ���������� ������ �����

DAYS_COUNT = 7

SMTP_SERVER = "imap.mail.ru"  # IMAP ������ �����, ������ ��� mail.ru
SMTP_PORT = 993  # IMAP ���� ����������� � �����, ����� �� ������
USER = ""  # ����� �����
PASSWORD = ""  # ������ ��� �����


def main_menu():
    print("����:")
    print("1. �������� ����� �� ��������� ������")
    print("2. �������� ������������� ����� �� ��������� ������")
    print("3. �������� ������������� ����� �� ��������� N ����")  # TODO: �����������
    print("4. ������ � �������")
    print("0. �����")

    return input("��� �����: ")


# TODO: �����������
def config_info():
    time.sleep(200)
    print("\n\n")
    print(f"�����: {USER}")
    print(f"������: {'*'*len(PASSWORD)}")
    print(f"IMAP ������ ��������� �����: {SMTP_SERVER}")
    print(f"IMAP ���� �������� �����: {SMTP_PORT}")
    print(f"���������� ��� ��������� ������ � ������� � ���: {doc_dir}")
    print(f"����������� ���������� ������({len(valid_file_extensions)}): ")
    for i in valid_file_extensions:
        print(i, end="\t")

    print("\n\n")
    time.sleep(200)

    antiPlagiatAPI.get_tariff_info()
    print("\n\n")
    time.sleep(200)


# �������� �����, ���������� �� � ���� ����������.
# ���������� �� ������ ���������� ����������
def isFileValid(filename: str):
    for extension in valid_file_extensions:
        if extension in os.path.splitext(filename):
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


# ���������� ����� � �������� ����������
def download_file(file):
    new_dir = doc_dir + "\\" + "temp\\"

    os.makedirs(os.path.dirname(new_dir), exist_ok=True)  # �������� �����, ���� �� ���

    # ������ � ����(���������� �����)
    with open(new_dir + file[2][0], "wb") as f:
        f.write(file[2][1])

    return new_dir


# ��������� �����
def file_processing(file):
    file_name = file[2][0]

    file_dir = download_file(file)
    try:
        link, fullreport = antiPlagiatAPI.check_report(file_dir + file_name)
    except Exception:
        return
    try:
        AuthorName = (fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].Surname + "_"
                  + fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].OtherNames).replace(" ", "_").replace(".", "")
    except Exception:
        AuthorName = "���_�����"

    if len(AuthorName) == 0:
        AuthorName = "���_�����"

    report_dir = file_dir.replace("temp", AuthorName)
    report_name = report_dir + "\\report_of_" \
                  + file_name[:file_name.rfind(".")] \
                  + ".pdf"

    os.makedirs(os.path.dirname(report_dir), exist_ok=True)
    urllib.request.urlretrieve(link, report_name)

    os.replace(file_dir + file_name, report_dir + file_name)

    print(f"���� {file_name} � ������� ��������� � {report_dir}\n\n")


# ������ �� ������, ��� ������� ���������� �������� �����. ���������� ������������, ��� ���������
def attachments_list_processing(attachments):
    if len(attachments) == 0:
        return

    res = []  # ���������� ���� ������ �� ������, ��� ������� ������������

    for i, file in enumerate(attachments):
        print(f"{i + 1} �� {len(attachments)}\n "
              f"\t���� ������: {file[0]} \n "
              f"\t���� ��������� {file[1]}\n "
              f"\t�������� ����� {file[2][0]}\n")

        user_choice = input("��������� ������ ����? "
                            "\n(1-��, s - ���������� ��� ����������, a - ���������� ��� ����������)\n >> ")

        if user_choice == '1':
            res.append(file)
        elif user_choice == "s":
            break
        elif user_choice == "a":
            for f in attachments[i:]:
                res.append(f)
            break

    print(f"\n\n��������� {len(res)} �����")
    i = 1
    for file in res:
        print(f"������ �{i}")
        i += 1
        file_processing(file)


# ������ �� ���� �������, ������� ���� �������� � ������� ������
def check_mail_last_week(flag: str):
    try:
        # ����������� � �����
        with emailHandler.MailBox(flag, SMTP_SERVER, SMTP_PORT, USER, PASSWORD) as mail:
            attachments = []  # ������ �������� �� ���������

            print("\n\n����������� � " + mail.USER)
            print("���������� ����������� ��������� �����...\n\n")

            c = 0
            for msg_num in range(1, len(mail.emails) + 1):
                try:
                    # �������� � ������ �������� � ������ � �������� �����������
                    attachment = deleteNotValidFiles(mail.get_attachment(-msg_num))
                    c += 1
                    if len(attachment) == 0:  # ���� �������� ���, ��������� ������
                        continue

                    # �������� ���� ������ � ���� ���������
                    date, title = message_processing(mail.fetch_message(-msg_num))

                    # �������� �������� � ������ �� ���������
                    for i in attachment:
                        attachments.append([title, date, i])

                except NameError:  # ��� ������ �� ��������� ���� ������ ������(������ ������), ��������� �����������
                    break

            print(f"����� {len(attachments)} �������� �� {c-1 if c > 1 else 0} ������������� �����")

        # �������� �� ������ �� ��������� � ���������� ������������, ����� ����� ����� ���������
        attachments_list_processing(attachments)

    except NameError as err:
        print(err.name)


# ������� �������
def main():
    while True:
        user_input = main_menu()

        match user_input:
            case '1':
                DAYS_COUNT = 7
                check_mail_last_week("ALL")
            case '2':
                DAYS_COUNT = 7
                check_mail_last_week("UNSEEN")
            case '3':
                DAYS_COUNT = int(input("������� ���������� ����:\nN = "))
                check_mail_last_week("UNSEEN")
            case '4':
                config_info()
            case '0':
                exit(0)


if __name__ == '__main__':
    try:
        main()
    finally:
        temp_dir = doc_dir + "\\" + "temp\\"
        lst = os.listdir(temp_dir)

        if len(lst) == 0:
            exit(0)

        for i in lst:
            if os.path.isfile(i):
                os.remove(temp_dir + i)

    exit(0)
