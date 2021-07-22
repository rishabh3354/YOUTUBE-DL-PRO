import datetime
import json
import os
import uuid
import requests
from cryptography.fernet import Fernet
from helper import check_internet_connection
from youtube_script import get_initial_document_dir

APP_NAME = "YOUTUBE_DL"

ENCRYPT_APP_NAME = {
    "PDF2GO": "wsa_pd",
    "SPEEDX": "wsa_sx",
    "Y2MATE": "wsa_ye",
    "HTOP": "wse_ht",
    "JPG2PDF": "wse_jf",
    "YOUTUBE_DL": "wse_yl"
}

HOME = get_initial_document_dir()
STANDARD_PATH = f'{HOME}/.app_conf'
LOCAL_EXPIRY_PATH = f'{HOME}/.linux_conf'

# API FOR LOCAL/SERVER
SERVER = "https://warlordsoftwares.in/"
LOCAL = "http://localhost/"
DOMAIN = SERVER


class ApplicationStartupTask:
    def __init__(self, app_name=APP_NAME):
        self.app_name = ENCRYPT_APP_NAME[app_name]
        self.today_date = datetime.datetime.now().date()
        self.expiry_folder = f'{LOCAL_EXPIRY_PATH}/{self.app_name}/local_conf'
        self.expiry_file = f'{LOCAL_EXPIRY_PATH}/{self.app_name}/local_conf/xpd.key'
        self.expiry_file_key = f'{LOCAL_EXPIRY_PATH}/{self.app_name}/local_conf/key.key'

    def create_free_trial_offline(self):
        expiry_date = self.check_for_expiry_date()

        if not expiry_date:
            context = dict()
            context["product"] = APP_NAME
            context["email"] = f"{generate_account_id()}@warlordsoft.in"
            context["plan"] = "Free Trial"
            context["is_active"] = True
            context["expiry_date"] = str(self.today_date + datetime.timedelta(days=7))
            context["created_on"] = str(self.today_date)

            try:
                os.makedirs(self.expiry_folder, exist_ok=True)
                key, cipher_text = encrypt_user_data_in_local(str(context["expiry_date"]).encode("utf-8"))
                with open(self.expiry_file, "wb+") as file:
                    file.write(cipher_text)
                with open(self.expiry_file_key, "wb+") as file:
                    file.write(key)
            except Exception as error:
                pass

            # update client cache
            save_user_data_in_client_side({"data": context})

    def check_for_expiry_date(self):
        expiry_date = None
        try:
            expiry_file = open(self.expiry_file, "rb+")
            key_file = open(self.expiry_file_key, "rb+")
            expiry = expiry_file.read()
            key = key_file.read()
            expiry_date = decrypt_user_data_in_local(expiry, key)
            if isinstance(expiry_date, bytes):
                expiry_date = expiry_date.decode('utf-8')
            else:
                expiry_date = expiry_date
        except Exception as tef:
            pass

        return expiry_date

    def update_local_expiry_and_client_data(self, new_data):
        new_expiry_date = new_data.get('expiry_date', 'N/A')
        if isinstance(new_expiry_date, bytes):
            new_expiry_date = new_expiry_date
        else:
            new_expiry_date = new_expiry_date.encode('utf-8')
        try:
            os.makedirs(self.expiry_folder, exist_ok=True)
            key, cipher_text = encrypt_user_data_in_local(new_expiry_date)
            with open(self.expiry_file, "wb+") as file:
                file.write(cipher_text)
            with open(self.expiry_file_key, "wb+") as file:
                file.write(key)
            # updating local client data
            save_user_data_in_client_side({"data": new_data})
        except Exception as error:
            pass


class SignInUpdatePlan:
    def __init__(self, product_name, token):
        self.plan_api = DOMAIN + 'accounts_api/plan_dashboard/'
        self.product_name = product_name
        if isinstance(token, bytes):
            self.token = token.decode('utf-8')
        else:
            self.token = token

    def get_user_paid_plan(self):
        context = dict()
        context["status"] = False
        context["message"] = ""
        context["data"] = None
        try:
            headers = {'Authorization': f'Token {self.token}'}
            response = requests.post(self.plan_api, data={'product': self.product_name}, headers=headers)
            if response.status_code in [200, 201]:
                message = json.loads(response.text)
                if message.get("status"):
                    context["status"] = True
                    context["message"] = message.get("message")
                    context["data"] = message.get("data")
                else:
                    context["status"] = False
                    context["message"] = message.get("message")
                    context["data"] = message.get("data")
            else:
                context["status"] = False
                context["message"] = "Internal Server Error"
        except Exception as e:
            context["status"] = False
            context["message"] = "Something went wrong"

        return context

    def update_local_expiry_and_client_data(self):
        status = {"status": False, "message": "Something went wrong!"}
        try:
            response_data = self.get_user_paid_plan()
            if response_data.get("status"):
                user_email = response_data.get("data", {}).get("data", {}).get("email")
                if response_data.get("data", {}).get("status"):
                    paid_plan_data = response_data.get("data")
                    ApplicationStartupTask().update_local_expiry_and_client_data(paid_plan_data.get("data"))
                update_email_on_client_data(user_email)
                status["status"] = True
                status["message"] = response_data.get("message")
            else:
                status["status"] = False
                status["message"] = response_data.get("message")
        except Exception as e:
            pass

        return status


def update_email_on_client_data(email):
    user_data = get_user_data_from_local()
    if user_data:
        user_data["email"] = email
    save_user_data_in_client_side({"data": user_data})


def encrypt_user_data_in_local(normal_data_str):
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(normal_data_str)

    return key, cipher_text


def decrypt_user_data_in_local(cipher_data_str, key):
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(cipher_data_str)

    return plain_text


def save_token_in_client_side(token):
    file_name = None
    token = token.encode('utf-8')

    try:
        app_name = ENCRYPT_APP_NAME[APP_NAME]
        os.makedirs(f'{STANDARD_PATH}/{app_name}/token', exist_ok=True)
        file_name = f'{STANDARD_PATH}/{app_name}/token/token.key'
        key_name = f'{STANDARD_PATH}/{app_name}/token/key.key'
        key, cipher_text = encrypt_user_data_in_local(token)
        with open(file_name, "wb+") as file:
            file.write(cipher_text)
        with open(key_name, "wb+") as file:
            file.write(key)
    except OSError as error:
        pass

    return file_name


def check_for_local_token():
    plain_text = None
    try:
        app_name = ENCRYPT_APP_NAME[APP_NAME]
        token_file = open(f'{STANDARD_PATH}/{app_name}/token/token.key', "rb+")
        token_key_file = open(f'{STANDARD_PATH}/{app_name}/token/key.key', "rb+")
        token = token_file.read()
        key = token_key_file.read()
        plain_text = decrypt_user_data_in_local(token, key)
        if isinstance(plain_text, bytes):
            plain_text = plain_text.decode('utf-8')
        else:
            plain_text = plain_text
    except OSError as error:
        pass
    except Exception as tef:
        pass

    return plain_text


def save_user_data_in_client_side(data_dict):
    try:
        app_name = ENCRYPT_APP_NAME[APP_NAME]
        os.makedirs(f'{STANDARD_PATH}/{app_name}/user_data', exist_ok=True)
        file_name = f'{STANDARD_PATH}/{app_name}/user_data/user_data.json'
        key_file = f'{STANDARD_PATH}/{app_name}/user_data/key.key'
        data = json.dumps(data_dict.get("data", {})).encode('utf-8')
        key, cipher_text = encrypt_user_data_in_local(data)
        with open(file_name, "wb+") as file:
            file.write(cipher_text)
        with open(key_file, "wb+") as file:
            file.write(key)
    except Exception as ee:
        pass


def get_user_data_from_local():
    plain_text = None
    try:
        app_name = ENCRYPT_APP_NAME[APP_NAME]
        user_data_file = open(f'{STANDARD_PATH}/{app_name}/user_data/user_data.json', "rb+")
        user_key_file = open(f'{STANDARD_PATH}/{app_name}/user_data/key.key', "rb+")
        data = user_data_file.read()
        key = user_key_file.read()
        plain_text = decrypt_user_data_in_local(data, key)
        plain_text = json.loads(plain_text)
    except Exception as error:
        pass
    return plain_text


def get_login_and_save_token(data):
    login_api = DOMAIN + "accounts_api/login_api/"
    context = dict()
    context["status"] = False
    context["token"] = ""
    context["token_path"] = ""
    context["message"] = ""
    try:
        if check_internet_connection():
            response = requests.post(login_api, data=data)
            if response.status_code in [200, 201]:
                message = json.loads(response.text)
                if message["status"]:
                    context["token"] = json.loads(message['message']).get("token", "")
                    context["token_path"] = save_token_in_client_side(context["token"])
                    context["status"] = True
                    context["message"] = "Login success"
                else:
                    context["status"] = False
                    context["message"] = message.get("message")

            else:
                context["status"] = False
                context["message"] = "Internal Server Error"
        else:
            context["message"] = "Please check your internet connection"
    except Exception as e:
        context["status"] = False
        context["message"] = "Login Failed"

    return context


def generate_account_id():
    return str(uuid.uuid4())[24:]


def days_left(date_str):
    days_left = "0 Day(s) Left"
    if date_str:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        todays_date = datetime.datetime.now().date()
        if todays_date <= date_obj:
            diff = (date_obj - todays_date).days
            if diff >= 1:
                days_left = f"{diff} Day(s) Left"
        else:
            days_left = "0 Day(s) Left"

    return days_left


def get_pytube_status():
    pytube_status_api = DOMAIN + 'accounts_api/pytube_status/'

    context = dict()
    context["status"] = False
    context["message"] = ""
    context["title"] = ""
    try:
        response = requests.post(pytube_status_api, data={'product': APP_NAME})
        if response.status_code in [200, 201]:
            message = json.loads(response.text)
            if message.get("status"):
                context["status"] = message.get("data", {}).get("status")
                context["title"] = message.get("data", {}).get("title")
                context["message"] = message.get("data", {}).get("message")
            else:
                context["status"] = False
                context["title"] = ""
                context["message"] = ""
        else:
            context["status"] = False
            context["title"] = ""
            context["message"] = ""
    except Exception as e:
        context["status"] = False
        context["message"] = ""

    return context["status"], context["title"], context["message"]
