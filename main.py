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

#  Сохранение зависимостей -  pip freeze > requirements.txt

# TODO: сделать через настраиваемый корфиг
mail_pass = "m78pQdtJQ9vn6UAJPEUa"
username = "mr.ender.03@mail.ru"
imap_server = "imap.mail.ru"
imap_port = 993
doc_dir = "F:\\IT\\AntiPlagiat"
valid_file_extensions = ["docx", "pdf"]

DAYS_COUNT = 7


def main_menu():
    print("Меню:")
    print("1. Просмотр писем за последнюю неделю")
    print("2. Просмотр непрочитанных писем за последнюю неделю")
    print("3. Просмотр непрочитанных писем за последние N дней")  # TODO: реализовать
    print("4. Данные в конфиге")
    print("0. Выход")

    return input("Ваш выбор: ")


# TODO: реализовать
def config_info():
    print("config_info не реализована!")


# Проверка файла, допустимое ли у него расширение.
# Проходимся по списку допустимых расширений
def isFileValid(filename: str):
    for extension in valid_file_extensions:
        if extension in filename:
            return True
    return False


# Удаление файлов из списка с невалидным расширением
def deleteNotValidFiles(attachment):
    for i in range(len(attachment)):
        if not isFileValid(attachment[i][0]):
            attachment.pop(i)

    return attachment


# Получение темы письма и даты получения
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
        title = "Без Темы"
    except UnicodeDecodeError:
        title = decode_header(msg["Subject"])[0][0].decode("windows-1251")
    except:
        title = "Ошибка получения темы"

    return [date.date(), title]


# Скачивание файла в заданную директорию
def download_file(file):
    new_dir = doc_dir + "\\" + "temp\\"

    os.makedirs(os.path.dirname(new_dir), exist_ok=True)  # Создание папок, если их нет

    # Запись в файл(скачивание файла)
    with open(new_dir + file[2][0], "wb") as f:
        f.write(file[2][1])

    return new_dir


# Обработка файла
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

    # TODO: Общий отчет о всех обработанных файлах


# Проход по списку, где указаны пройденные проверку файлы. Спрашиваем пользователя, что проверить
def attachments_list_processing(attachments):
    if len(attachments) == 0:
        print("attachments is empty")
        return

    res = []  # Записываем сюда только те письма, что одобрил пользователь

    for i, file in enumerate(attachments):
        print(f"{i + 1}.\n Тема письма: {file[0]} \n Дата получения {file[1]}\n Название файла {file[2][0]}\n")
        user_choice = input("Сохранить данный файл? (1-да, STOP - обработать только одобренные)\n >> ")

        if user_choice == '1':
            res.append(file)
        elif user_choice == "STOP":
            break

    for file in res:
        file_processing(file)


# Проход по всем письмам, которые были получены в течение недели
def check_mail_last_week(flag: str):
    try:
        with emailHandler.MailBox(flag) as mail:
            attachments = []  # Список на одобрение

            for msg_num in range(1, len(mail.emails) + 1):
                try:
                    # Считываю с письма вложения и удаляю с ненужным расширением
                    attachment = deleteNotValidFiles(mail.get_attachment(-msg_num))
                    if len(attachment) == 0:  # Если вложений нет, пропускаю письмо
                        continue

                    # Считываю тему письма и дату получения
                    date, title = message_processing(mail.fetch_message(-msg_num))
                    # print(title, attachment[0][0])

                    # Добавляю вложение в список на одобрение
                    for i in attachment:
                        attachments.append([title, date, i])

                except NameError:  # Как только на обработку идут старые письма(старше недели), обработка завершается

                    # Проходим по списку на одобрение и спрашиваем пользователя, какие файлы нужно проверить
                    break

        attachments_list_processing(attachments)

    except NameError as err:
        print(err.name)


# Главная функция
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
