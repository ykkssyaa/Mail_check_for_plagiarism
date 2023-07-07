import suds
import base64
import os
import time
import suds.client

# TODO: Сделать через конфиг
# TODO: Подключение к аккаунту
ANTIPLAGIAT_URI = "https://testapi.antiplagiat.ru"

# Создать клиента сервиса(https)
LOGIN = "testapi@antiplagiat.ru"
PASSWORD = "testapi"
COMPANY_NAME = "testapi"
APICORP_ADDRESS = "api.antiplagiat.ru:44902"
client = suds.client.Client("https://api.antiplagiat.ru:4959/apiCorp/testapi?wsdl",
                            username=LOGIN,
                            password=PASSWORD)


def get_doc_data(filename):
    data = client.factory.create("DocData")
    data.Data = base64.b64encode(open(filename, "rb").read()).decode()
    data.FileName = os.path.splitext(filename)[0]
    data.FileType = os.path.splitext(filename)[1]
    data.ExternalUserID = "test"
    return data


# TODO: Почистить код
# TODO: Добавить логирование того, что сейчас происходит

# Проверить документ, получить ссылку на pdf-версию отчета "Antiplagiat"
def check_report(filename):
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
    # client.service.CheckDocument(id, ["wikipedia", COMPANY_NAME])
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
        print("При формировании PDF-отчета для документа %s произошла ошибка: %s" % (
        filename, exportReportInfo.FailDetails))

    # Получить ссылку на отчет на сайте "Антиплагиат"
    # ВНИМАНИЕ! Не гарантируется что данная ссылка будет работать вечно, она может перестать работать в любой момент,
    # поэтому нельзя давать ее пользвателю. Нужно скачивать pdf себе и дальше уже управлять его временем жизни
    downloadLink = ANTIPLAGIAT_URI + exportReportInfo.DownloadLink
    print("PDF full report (number = %s): %s" % (exportReportInfo.ReportNum, downloadLink))

    # Получить полный отчет
    options = client.factory.create("ReportViewOptions")
    options.FullReport = True
    options.NeedText = True
    options.NeedStats = True
    options.NeedAttributes = True
    fullreport = client.service.GetReportView(id, options)

    # TODO: Удалить лишние выводы
    print(u"Author Surname=%s OtherNames=%s" % (
       fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].Surname,
       fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].OtherNames))

    return [downloadLink, fullreport]


# Получение информации об аккаунте Антиплагиат.ру
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

