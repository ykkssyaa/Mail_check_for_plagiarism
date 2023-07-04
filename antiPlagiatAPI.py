import suds
import base64
import os
import time
import suds.client

# TODO: Сделать через конфиг
ANTIPLAGIAT_URI = "https://testapi.antiplagiat.ru"

# Создать клиента сервиса(https)
LOGIN = "testapi@antiplagiat.ru"
PASSWORD = "testapi"
COMPANY_NAME = "testapi"
APICORP_ADDRESS = "api.antiplagiat.ru:44902"
client = suds.client.Client("https://api.antiplagiat.ru:4959/apiCorp/testapi?wsdl",
                            username=LOGIN,
                            password=PASSWORD)

import logging
logging.basicConfig(level=logging.INFO)


def get_doc_data(filename):
    data = client.factory.create("DocData")
    data.Data = base64.b64encode(open(filename, "rb").read()).decode()
    data.FileName = os.path.splitext(filename)[0]
    data.FileType = os.path.splitext(filename)[1]
    data.ExternalUserID = "test"
    return data


def simple_check(filename):
    print("SimpleCheck filename=" + filename)
    # Описание загружаемого файла
    data = get_doc_data(filename)

    docatr = client.factory.create("DocAttributes")
    personIds = client.factory.create("PersonIDs")
    personIds.CustomID = "original"

    arr = client.factory.create("ArrayOfAuthorName")

    author = client.factory.create("AuthorName")
    author.OtherNames = "Иван Иванович"
    author.Surname = "Иванов"
    author.PersonIDs = personIds

    arr.AuthorName.append(author)

    docatr.DocumentDescription.Authors = arr

    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data, docatr)
    except Exception:
        raise

    # Идентификатор документа. Если загружается не архив, то список загруженных документов будет состоять из одного элемента.
    id = uploadResult.Uploaded[0].Id

    try:
        # Отправить на проверку с использованием всех подключеных компании модулей поиска
        client.service.CheckDocument(id)
    # Отправить на проверку с использованием только собственного модуля поиска и модуля поиска "wikipedia". Для получения списка модулей поиска см. пример get_tariff_info()
    # client.service.CheckDocument(id, ["wikipedia", COMPANY_NAME])
    except suds.WebFault:
        raise

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

    # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(status.EstimatedWaitTime * 0.1)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась неудачно.
    if status.Status == "Failed":
        print(u"При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))

    # Получить краткий отчет
    report = client.service.GetReportView(id)

    print("Report Summary: %0.2f%%" % (report.Summary.Score,))
    for checkService in report.CheckServiceResults:
        # Информация по каждому поисковому модулю
        print("Check service: %s, Score.White=%0.2f%% Score.Black=%0.2f%%" %
              (checkService.CheckServiceName,
               checkService.ScoreByReport.Legal, checkService.ScoreByReport.Plagiarism))
        if not hasattr(checkService, "Sources"):
            continue
        for source in checkService.Sources:
            # Информация по каждому найденному источнику
            print('\t%s: Score=%0.2f%%(%0.2f%%), Name="%s" Author="%s" Url="%s"' %
                  (source.SrcHash, source.ScoreByReport, source.ScoreBySource,
                   source.Name, source.Author, source.Url))

    # Получить полный отчет
    options = client.factory.create("ReportViewOptions")
    options.FullReport = True
    options.NeedText = True
    options.NeedStats = True
    options.NeedAttributes = True
    fullreport = client.service.GetReportView(id, options)
    if fullreport.Details.CiteBlocks:
        # Найти самый большой блок заимствований и вывести его
        maxBlock = max(fullreport.Details.CiteBlocks, key=lambda x: x.Length)
        print(u"Max block length=%s Source=%s text:\n%s..." % (maxBlock.Length, maxBlock.SrcHash,
                                                               fullreport.Details.Text[
                                                               maxBlock.Offset:maxBlock.Offset + min(maxBlock.Length,
                                                                                                     200)]))

        print(u"Author Surname=%s OtherNames=%s CustomID=%s" % (
        fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].Surname,
        fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].OtherNames,
        fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].PersonIDs.CustomID))


def get_tariff_info():
    print("GetTariffInfo")

    # Получить информацию о текущем тарифе
    tariffInfo = client.service.GetTariffInfo()

    print("Tariff name: %s" % (tariffInfo.Name))
    print("Tariff subscription date: %s" % (tariffInfo.SubscriptionDate))
    print("Tariff expiration date: %s" % (tariffInfo.ExpirationDate))
    print("Tariff total checks count: %s" % (tariffInfo.TotalChecksCount))
    print("Tariff remained checks count: %s" % (tariffInfo.RemainedChecksCount))

    print("\nAvailable check services:")

    for checkService in tariffInfo.CheckServices[0]:
        print("%s (%s)" % (checkService.Code, checkService.Description))


# Проверить документ, получить ссылку на pdf-версию отчета на сайте "Antiplagiat"
def export_report_to_pdf(filename):
    print("export_report_to_pdf")

    # Описание загружаемого файла
    data = get_doc_data(filename)

    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data)
    except Exception:
        raise

    # Идентификатор документа.  Если загружается не архив, то список
    # загруженных документов будет состоять из одного элемента.
    id = uploadResult.Uploaded[0].Id

    try:
        # Отправить на проверку с использованием всех подключеных компании модулей поиска
        client.service.CheckDocument(id)
		# Отправить на проверку с использованием только собственного модуля поиска и модуля поиска "wikipedia". Для получения списка модулей поиска см. пример get_tariff_info()
		#client.service.CheckDocument(id, ["wikipedia", COMPANY_NAME])
    except Exception:
        raise

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

     # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(max(status.EstimatedWaitTime, 10) * 0.1)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась не удачно.
    if status.Status == "Failed":
        print("При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))

    # Запросить формирование последнего полного отчета в формат PDF.
    exportReportInfo = client.service.ExportReportToPdf(id)

    while exportReportInfo.Status == "InProgress":
        time.sleep(max(exportReportInfo.EstimatedWaitTime, 10) * 0.1)
        exportReportInfo = client.service.ExportReportToPdf(id)

    # Формирование отчета закончилось неудачно.
    if exportReportInfo.Status == "Failed":
        print("При формировании PDF-отчета для документа %s произошла ошибка: %s" % (filename, exportReportInfo.FailDetails))

    # Получить ссылку на отчет на сайте "Антиплагиат"
    # ВНИМАНИЕ! Не гарантируется что данная ссылка будет работать вечно, она может перестать работать в любой момент,
    # поэтому нельзя давать ее пользвателю. Нужно скачивать pdf себе и дальше уже управлять его временем жизни
    downloadLink = ANTIPLAGIAT_URI + exportReportInfo.DownloadLink
    print("PDF full report (number = %s): %s" % (exportReportInfo.ReportNum, downloadLink))

    # Опции для формирования краткого отчета с номером 1 в формат PDF.
    options = client.factory.create("ExportReportOptions")
    options.ReportNum = 1
    options.ShortReport = True

    # Запросить формирование отчета в формат PDF с указанными опциями.
    exportReportInfo = client.service.ExportReportToPdf(id, options)

    # Цикл ожидания формирования отчета
    while exportReportInfo.Status == "InProgress":
        time.sleep(max(exportReportInfo.EstimatedWaitTime, 10) * 0.1)
        exportReportInfo = client.service.ExportReportToPdf(id, options)

    # Формирование отчета закончилось неудачно.
    if exportReportInfo.Status == "Failed":
        print("При формировании PDF-отчета для документа %s произошла ошибка" % (filename))

    # Получить ссылку на отчет на сайте "Антиплагиат"
    # ВНИМАНИЕ! Не гарантируется что данная ссылка будет работать вечно, она может перестать работать в любой момент,
    # поэтому нельзя давать ее пользвателю. Нужно скачивать pdf себе и дальше уже управлять его временем жизни
    downloadLink = ANTIPLAGIAT_URI + exportReportInfo.DownloadLink
    print("PDF short report (number = %s): %s" % (exportReportInfo.ReportNum, downloadLink))


if __name__ == '__main__':
    get_tariff_info()

    print(export_report_to_pdf("file.docx"))
