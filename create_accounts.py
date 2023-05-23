
from requests import get, post
from os import getenv, path
from json import load, dump
from time import sleep
from dotenv import load_dotenv
from lxml import html
import typing
from concurrent.futures import ThreadPoolExecutor
import signal

# =============== CONFIGURE THIS ===============
TARGET = 'byamb4inst'
PASSWORD = getenv('PASSWORD', 'Password!@#123')
# ==============================================

BASE_URL = 'https://api.mrinsta.com/api'
DEBUG = True
class CreateAccounts:
    # create new accounts
    def __init__(self):
        self.EMAIL_URL = 'https://email-fake.com'
        self.WORKED_ACCOUNTS, self.ACCOUNTS, self.INDEX = [], [], 0
        signal.signal(signal.SIGINT, self.signal_handler)

        with open('followers.txt', 'r') as f:
            for _ in f.readlines():
                self.ACCOUNTS.append(_.strip())

        # working from behind, coz most of accounts taken by tulgaa
        self.ACCOUNTS = self.ACCOUNTS[::-1]

        while True:
            _, email = self.generate_new_email()
            _, user_id, access_token = self.register(email)
            _, otp = self.get_otp(access_token, email)
            if not _:
                print('\t[-] No OTP found')
                print(f'\t[-] Last account: {self.ACCOUNTS[self.INDEX]}')
                self.save_emails()
                self.WORKED_ACCOUNTS = []
                continue
            _, data = self.verify_email(email, otp)
            _ = self.connect_ig(email, user_id, access_token)
            if self.INDEX >= len(self.ACCOUNTS):
                print('[+] Well no account left')
                break

        with open('done', 'w') as f:
            f.write('\n'.join(self.WORKED_ACCOUNTS))

    def connect_ig(self, email: str, user_id: str, access_token: str):
        # storeUpdateUserDetails
        resp = post(f'{BASE_URL}/storeUpdateUserDetails', headers={
            "Authorization": f"Bearer {access_token}"
        }, json={
            "user_id": user_id,
            "location": "South America",
            "gender": "Prefer not to say",
            "age": "35-44"
        }).json()

        # interests
        resp = post(f'{BASE_URL}/storeUserWiseInterests', headers={
            "Authorization": f"Bearer {access_token}"
        }, json={
            "id": user_id,
            "interests": "22, 21, 20, 19",
        }).json()

        # connect to instagram account
        # NOTE: need proper solution
        while self.INDEX < len(self.ACCOUNTS):
            resp = post(f'{BASE_URL}/addConnectedIGAccount', headers={
                "Authorization": f"Bearer {access_token}"
            }, json={
                "username": self.ACCOUNTS[self.INDEX],
            }).json()
            # print(f'\t[*] Tried: {self.ACCOUNTS[self.INDEX]}: {resp}')
            if resp['success']:
                print(f'[+] Works: {self.ACCOUNTS[self.INDEX]}, {email}')
                self.WORKED_ACCOUNTS.append(email)
                return True
            self.INDEX += 1

    def get_otp(self, access_token: str, email: str):
        for _ in range(1, 50):
            # self.send_verify_email(access_token, email)
            sleep(2)
            try:
                tree = html.fromstring(
                    get(f'{self.EMAIL_URL}/{email}').content)
                otp = tree.xpath(
                    "//table[@class='content']//h3")[0].text_content()
                if len(otp) == 6:
                    # print(f'\t[+] OTP: {otp}')
                    return True, otp
            except Exception as e:
                # print(e)
                pass
        return False, ''

    def register(self, email: str) -> typing.Tuple[bool, str, str]:
        resp = post(f'{BASE_URL}/register', json={
            "email": email,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        }).json()
        try:
            return resp['success'], resp['data']['user_id'], resp['data']['token']['access_token']
        except Exception as e:
            return False, "", ""

    def verify_email(self, email: str, otp: str):
        resp = get(f"{BASE_URL}/verify/{otp}/{email}").json()
        if resp['success']:
            # print("\t[+] Account activated")
            return resp['success'], resp['message']
        return False, resp

    def generate_new_email(self):
        tree = html.fromstring(get(f'{self.EMAIL_URL}').content)
        mail = tree.xpath("//span[@id='email_ch_text']")[0].text_content()
        # print(f'[+] Email: {mail}')
        if '@' in mail:
            return True, mail
        return False, ''

    def save_emails(self):
        print(f'[+] New accounts: {len(self.WORKED_ACCOUNTS)}')
        print('[+] Exiting')
        if len(self.WORKED_ACCOUNTS) > 0:
            with open('accounts.json', 'r') as f:
                accounts = load(f)
            for _ in self.WORKED_ACCOUNTS:
                accounts.append({
                    'email': _
                })
            with open('accounts.json', 'w') as f:
                dump(accounts, f)

    def send_verify_email(self, access_token: str, email: str):
        resp = post(f"{BASE_URL}/sendVerifyEmail", headers={
            "Authorization": access_token
        }, json={
            "email": email
        }).json()
        return resp['success']

    def signal_handler(self, sig, frame) -> None:
        self.save_emails()
        exit(0)

