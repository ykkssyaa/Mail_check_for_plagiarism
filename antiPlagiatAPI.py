import suds
import base64
import os
import suds.client

# TODO: Сделать через конфиг
ANTIPLAGIAT_URI = "https://testapi.antiplagiat.ru"

# Создать клиента сервиса(https)
LOGIN = "testapi@antiplagiat.ru"
PASSWORD = "testapi"
COMPANY_NAME = "testapi"
APICORP_ADDRESS = "api.antiplagiat.ru:44902"
client = suds.client.Client("https://%s/apiCorp/%s?singleWsdl" % (APICORP_ADDRESS, COMPANY_NAME),
                            username=LOGIN,
                            password=PASSWORD)

def get_doc_data(filename):
    data = client.factory.create("DocData")
    data.Data = base64.b64encode(open(filename, "rb").read()).decode()
    data.FileName = os.path.splitext(filename)[0]
    data.FileType = os.path.splitext(filename)[1]
    data.ExternalUserID = "ivanov"
    return data


if __name__ == '__main__':
    get_doc_data("main.py")