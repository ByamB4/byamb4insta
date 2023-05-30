import typing
from lxml import html
from requests import get, post
from json import load, dump
from time import sleep
import signal

# maybe not works in future coz some people may used instagram_accounts.txt
# then you have to find another valid usernames
BASE_URL = 'https://api.mrinsta.com/api'
PASSWORD = 'UPDATE ME'
DEBUG = 1

class CreateAccounts:
    # create new accounts
    def __init__(self):
        self.EMAIL_URL = 'https://email-fake.com'
        self.WORKED_ACCOUNTS, self.INSTAGRAM_USERNAMES, self.INDEX = [], [], 0
        signal.signal(signal.SIGINT, self.signal_handler)

        with open('instagram_usernames.txt', 'r') as f:
            for _ in f.readlines():
                self.INSTAGRAM_USERNAMES.append(_.strip())

        while True:
            _, email = self.generate_new_email()
            _, user_id, access_token, insta_session = self.register(email)
            _, otp = self.get_otp(access_token, email)
            if not _:
                # print('\t[-] No OTP found')
                # print(f'\t[-] Last account: {self.INSTAGRAM_USERNAMES[self.INDEX]}')
                self.WORKED_ACCOUNTS = []
                continue
            _, data = self.verify_email(email, otp)
            _ = self.connect_ig(email, user_id, access_token)
            if _:
                self.connect_account(access_token, insta_session)
            if self.INDEX >= len(self.INSTAGRAM_USERNAMES):
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
        # print(f'\t[*] Trying instagram usernames')
        while self.INDEX < len(self.INSTAGRAM_USERNAMES):
            try:
                resp = post(f'{BASE_URL}/addConnectedIGAccount', headers={
                    "Authorization": f"Bearer {access_token}"
                }, json={
                    "username": self.INSTAGRAM_USERNAMES[self.INDEX],
                }).json()
                if resp['success']:
                    print(f'[+] Works: {self.INSTAGRAM_USERNAMES[self.INDEX]}, {email}')
                    self.WORKED_ACCOUNTS.append(email)
                    return True
                self.INDEX += 1
            except Exception as e:
                if DEBUG:
                    print(f'[-] Error@connect_ig: {e}')
                    input()

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

    def register(self, email: str) -> typing.Union[bool, str, str, str]:
        resp = post(f'{BASE_URL}/register', json={
            "email": email,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        })
        try:
            return resp.json()['success'], resp.json()['data']['user_id'], resp.json()['data']['token']['access_token'], resp.cookies['mrinsta_session']
        except Exception as e:
            return False, "", "", ""

    def verify_email(self, email: str, otp: str):
        resp = get(f"{BASE_URL}/verify/{otp}/{email}").json()
        if resp['success']:
            # print("\t[+] Account activated")
            return resp['success'], resp['message']
        return False, resp

    def generate_new_email(self) -> typing.Union[bool, str]:
        tree = html.fromstring(get(f'{self.EMAIL_URL}').content)
        mail = tree.xpath("//span[@id='email_ch_text']")[0].text_content()
        # print(f'[+] Email: {mail}')
        if '@' in mail:
            return True, mail
        return False, ''

    def send_verify_email(self, access_token: str, email: str):
        resp = post(f"{BASE_URL}/sendVerifyEmail", headers={
            "Authorization": access_token
        }, json={
            "email": email
        }).json()
        return resp['success']

    def connect_account(self, access_token: str, insta_session: str):
        resp = get(f'{BASE_URL}/listConnectedAccount', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        print(
            f"\t[+] Connected accounts: {len(resp['data']['connected_account'])}")
        for _ in range(5 - len(resp['data']['connected_account'])):
            while self.INDEX < len(self.INSTAGRAM_USERNAMES):
                resp = post(f'{BASE_URL}/addConnectedIGAccount', headers={
                    "Authorization": f"Bearer {access_token}"
                }, json={
                    "username": self.INSTAGRAM_USERNAMES[self.INDEX],
                }, cookies={
                    "mrinsta_session": insta_session
                }).json()
                try:
                    if resp['success']:
                        print(
                            f'\t[+] Works: {self.INSTAGRAM_USERNAMES[self.INDEX]}')
                        break
                    self.INDEX += 1
                except Exception as e:
                    print(f'[-] Error@connect_account: {e}')
                    print(resp)
                    input()

    def save_emails(self):
        print(f'[+] New accounts: {len(self.WORKED_ACCOUNTS)}')
        print(f'[+] Last username: {self.INSTAGRAM_USERNAMES[self.INDEX]}')
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

    def signal_handler(self, sig, frame) -> None:
        self.save_emails()
        exit(0)


if __name__ == '__main__':
    CreateAccounts()