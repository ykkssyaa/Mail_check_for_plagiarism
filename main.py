#! /usr/bin/env python
# -*- coding: windows-1251 -*-
import email
import imaplib
import os
from email.header import decode_header
from datetime import datetime, timedelta
import urllib.request

import emailHandler
import antiPlagiatAPI

#  ���������� ������������ -  pip freeze > requirements.txt

# TODO: ������� ����� ������������� ������
mail_pass = "m78pQdtJQ9vn6UAJPEUa"
username = "mr.ender.03@mail.ru"
imap_server = "imap.mail.ru"
imap_port = 993
doc_dir = "F:\\IT\\AntiPlagiat"
valid_file_extensions = ["docx", "pdf"]

DAYS_COUNT = 7


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
    print("config_info �� �����������!")


# �������� �����, ���������� �� � ���� ����������.
# ���������� �� ������ ���������� ����������
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
    link, fullreport = antiPlagiatAPI.check_report(file_dir+file_name)

    AuthorName = (fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].Surname + "_"
                 + fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].OtherNames).replace(" ", "_").replace(".", "")

    report_dir = file_dir.replace("temp", AuthorName)
    report_name = report_dir + "\\reportOF"\
                  + file_name[:file_name.rfind(".")]\
                  + ".pdf"

    os.makedirs(os.path.dirname(report_dir), exist_ok=True)
    urllib.request.urlretrieve(link, report_name)

    os.replace(file_dir+file_name, report_dir+file_name)

    # TODO: ����� ����� � ���� ������������ ������


# ������ �� ������, ��� ������� ���������� �������� �����. ���������� ������������, ��� ���������
def attachments_list_processing(attachments):
    if len(attachments) == 0:
        print("attachments is empty")
        return

    res = []  # ���������� ���� ������ �� ������, ��� ������� ������������

    for i, file in enumerate(attachments):
        print(f"{i + 1}.\n ���� ������: {file[0]} \n ���� ��������� {file[1]}\n �������� ����� {file[2][0]}\n")
        user_choice = input("��������� ������ ����? (1-��, STOP - ���������� ������ ����������)\n >> ")

        if user_choice == '1':
            res.append(file)
        elif user_choice == "STOP":
            break

    for file in res:
        file_processing(file)


# ������ �� ���� �������, ������� ���� �������� � ������� ������
def check_mail_last_week(flag: str):
    try:
        with emailHandler.MailBox(flag) as mail:
            attachments = []  # ������ �� ���������

            for msg_num in range(1, len(mail.emails) + 1):
                try:
                    # �������� � ������ �������� � ������ � �������� �����������
                    attachment = deleteNotValidFiles(mail.get_attachment(-msg_num))
                    if len(attachment) == 0:  # ���� �������� ���, ��������� ������
                        continue

                    # �������� ���� ������ � ���� ���������
                    date, title = message_processing(mail.fetch_message(-msg_num))
                    # print(title, attachment[0][0])

                    # �������� �������� � ������ �� ���������
                    for i in attachment:
                        attachments.append([title, date, i])

                except NameError:  # ��� ������ �� ��������� ���� ������ ������(������ ������), ��������� �����������

                    # �������� �� ������ �� ��������� � ���������� ������������, ����� ����� ����� ���������
                    break

        attachments_list_processing(attachments)

    except NameError as err:
        print(err.name)


# ������� �������
def main():

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
