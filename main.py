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

#  Сохранение зависимостей -  pip freeze > requirements.txt

# TODO: сделать через настраиваемый корфиг
doc_dir = ""   # Папка, куда сохранять скачанные файлы и отчеты к ним
valid_file_extensions = [".docx", ".pdf"]  # Допустимые расширения файлов, именно они будут отбираться внутри писем

DAYS_COUNT = 7

SMTP_SERVER = "imap.mail.ru"  # IMAP сервер почты, указан для mail.ru
SMTP_PORT = 993  # IMAP порт подключения к почте, лучше не менять
USER = ""  # Адрес почты
PASSWORD = ""  # Пароль для почты


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
    time.sleep(200)
    print("\n\n")
    print(f"Адрес: {USER}")
    print(f"Пароль: {'*'*len(PASSWORD)}")
    print(f"IMAP сервер почтового ящика: {SMTP_SERVER}")
    print(f"IMAP порт почтоого ящика: {SMTP_PORT}")
    print(f"Директория для скачанных файлов и отчетов к ним: {doc_dir}")
    print(f"Разрешенные расширения файлов({len(valid_file_extensions)}): ")
    for i in valid_file_extensions:
        print(i, end="\t")

    print("\n\n")
    time.sleep(200)

    antiPlagiatAPI.get_tariff_info()
    print("\n\n")
    time.sleep(200)


# Проверка файла, допустимое ли у него расширение.
# Проходимся по списку допустимых расширений
def isFileValid(filename: str):
    for extension in valid_file_extensions:
        if extension in os.path.splitext(filename):
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
    try:
        link, fullreport = antiPlagiatAPI.check_report(file_dir + file_name)
    except Exception:
        return
    try:
        AuthorName = (fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].Surname + "_"
                  + fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].OtherNames).replace(" ", "_").replace(".", "")
    except Exception:
        AuthorName = "Без_Имени"

    if len(AuthorName) == 0:
        AuthorName = "Без_Имени"

    report_dir = file_dir.replace("temp", AuthorName)
    report_name = report_dir + "\\report_of_" \
                  + file_name[:file_name.rfind(".")] \
                  + ".pdf"

    os.makedirs(os.path.dirname(report_dir), exist_ok=True)
    urllib.request.urlretrieve(link, report_name)

    os.replace(file_dir + file_name, report_dir + file_name)

    print(f"Файл {file_name} с отчетом сохранены в {report_dir}\n\n")


# Проход по списку, где указаны пройденные проверку файлы. Спрашиваем пользователя, что проверить
def attachments_list_processing(attachments):
    if len(attachments) == 0:
        return

    res = []  # Записываем сюда только те письма, что одобрил пользователь

    for i, file in enumerate(attachments):
        print(f"{i + 1} из {len(attachments)}\n "
              f"\tТема письма: {file[0]} \n "
              f"\tДата получения {file[1]}\n "
              f"\tНазвание файла {file[2][0]}\n")

        user_choice = input("Сохранить данный файл? "
                            "\n(1-да, s - обработать уже одобренные, a - обработать все оставшиеся)\n >> ")

        if user_choice == '1':
            res.append(file)
        elif user_choice == "s":
            break
        elif user_choice == "a":
            for f in attachments[i:]:
                res.append(f)
            break

    print(f"\n\nОбработка {len(res)} писем")
    i = 1
    for file in res:
        print(f"Письмо №{i}")
        i += 1
        file_processing(file)


# Проход по всем письмам, которые были получены в течение недели
def check_mail_last_week(flag: str):
    try:
        # Подключаюсь к почте
        with emailHandler.MailBox(flag, SMTP_SERVER, SMTP_PORT, USER, PASSWORD) as mail:
            attachments = []  # Список вложений на одобрение

            print("\n\nПодключение к " + mail.USER)
            print("Считывание содержимого почтового ящика...\n\n")

            c = 0
            for msg_num in range(1, len(mail.emails) + 1):
                try:
                    # Считываю с письма вложения и удаляю с ненужным расширением
                    attachment = deleteNotValidFiles(mail.get_attachment(-msg_num))
                    c += 1
                    if len(attachment) == 0:  # Если вложений нет, пропускаю письмо
                        continue

                    # Считываю тему письма и дату получения
                    date, title = message_processing(mail.fetch_message(-msg_num))

                    # Добавляю вложение в список на одобрение
                    for i in attachment:
                        attachments.append([title, date, i])

                except NameError:  # Как только на обработку идут старые письма(старше недели), обработка завершается
                    break

            print(f"Всего {len(attachments)} вложения из {c-1 if c > 1 else 0} просмотренных писем")

        # Проходим по списку на одобрение и спрашиваем пользователя, какие файлы нужно проверить
        attachments_list_processing(attachments)

    except NameError as err:
        print(err.name)


# Главная функция
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
                DAYS_COUNT = int(input("Введите количество дней:\nN = "))
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
