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
APICORP_ADDRESS = "api.antiplagiat.ru:4959"
ExternalUserID = "test"
client = suds.client.Client(f"https://{APICORP_ADDRESS}/apiCorp/{COMPANY_NAME}?wsdl",
                            username=LOGIN,
                            password=PASSWORD)

# client = suds.client.Client("https://%s/apiCorp/%s?singleWsdl" % (APICORP_ADDRESS, COMPANY_NAME), username=LOGIN, password=PASSWORD)

def get_doc_data(filename):
    data = client.factory.create("DocData")
    data.Data = base64.b64encode(open(filename, "rb").read()).decode()
    data.FileName = os.path.splitext(filename)[0]
    data.FileType = os.path.splitext(filename)[1]
    data.ExternalUserID = ExternalUserID
    return data


# Проверить документ, получить ссылку на pdf-версию отчета "Antiplagiat"
def check_report(filename):
    # Описание загружаемого файла
    data = get_doc_data(filename)

    print(f"Загрузка файла " + data.FileName[data.FileName.rfind('\\') + 1:] + data.FileType + " на Антиплагиат.ру")

    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data)
        print(f"Файл загружен успешно!")
    except Exception:
        print(f"Ошибка загрузки файла")
        raise

    # Идентификатор документа.
    id = uploadResult.Uploaded[0].Id

    try:
        client.service.CheckDocument(id)
    except Exception:
        raise

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

    # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(max(status.EstimatedWaitTime, 10) * 0.1)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась неудачно.
    if status.Status == "Failed":
        print("При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))
        raise

    print(f"Файл прошел проверку!")
    print("Получение отчета в PDF")

    # Запросить формирование последнего полного отчета в формат PDF.
    exportReportInfo = client.service.ExportReportToPdf(id)

    while exportReportInfo.Status == "InProgress":
        time.sleep(max(exportReportInfo.EstimatedWaitTime, 10) * 0.1)
        exportReportInfo = client.service.ExportReportToPdf(id)

    # Формирование отчета закончилось неудачно.
    if exportReportInfo.Status == "Failed":
        print("При формировании PDF-отчета для документа %s произошла ошибка: %s" % (
            filename, exportReportInfo.FailDetails))
        raise

    # Получить ссылку на отчет на сайте "Антиплагиат"
    downloadLink = ANTIPLAGIAT_URI + exportReportInfo.DownloadLink
    # print("PDF full report (number = %s): %s" % (exportReportInfo.ReportNum, downloadLink))

    # Получить полный отчет
    options = client.factory.create("ReportViewOptions")
    options.FullReport = True
    options.NeedText = True
    options.NeedStats = True
    options.NeedAttributes = True
    fullreport = client.service.GetReportView(id, options)

    return [downloadLink, fullreport]


# Получение информации об аккаунте Антиплагиат.ру
def get_tariff_info():

    if COMPANY_NAME == "testapi":
        print("Используются данные для тестовых ")

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
