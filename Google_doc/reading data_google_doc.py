import gspread
import os
import json
from dotenv import load_dotenv


def formating_google_tab_json(service_account_google, table_id):
    # Функция взаимодействует с таблицей и позволяет преобразовать ее в json
    client = gspread.service_account(filename=service_account_google)
    worksheet = client.open_by_key(table_id).sheet1
    list_of_dicts = worksheet.get_all_records()
    json_string = json.dumps(list_of_dicts, indent=4)
    # Откладочный принт
    print(json_string)

def main():
    load_dotenv()
    table_id =os.environ.get('TABLE_ID')
    service_account_google = os.environ.get('SERVICE_ACCOUNT_GOOGLE')
    formating_google_tab_json(service_account_google, table_id)


if __name__ == '__main__':
    main()


