from requests import get, post
from os import getenv, path
from json import load, dump
from time import sleep
from dotenv import load_dotenv
from lxml import html
import typing

BASE_URL = 'https://api.mrinsta.com/api'

# =============== CONFIGURE THIS ===============
TARGET = 'byamb4'
DEBUG = False
PASSWORD = 'p4$$w0rD!'
# ==============================================


class RedeemCoin:
    def __init__(self) -> None:
        self.SPENT = 0
        self.QUANTITY = 1_000
        self.IS_DONE = False

        self.read_accounts()
        print(f'[+] Target: {TARGET}')
        self.process_accounts()

    def read_accounts(self):
        self.ACCOUNTS = load(
            open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'r'))

    def process_accounts(self):
        for account in self.ACCOUNTS:
            if self.IS_DONE: break
            _, access_token, insta_session = self.login(account)
            if not _:
                print(f"\t[-] Login failed: {account['email']}")
                return
            print(f'[+] Logged in: {account["email"]}')
            connected_accounts = self.get_connected_accounts(
                access_token, insta_session)
            usernames = [_['instagram_data']['username']
                        for _ in connected_accounts['connected_account']]
            usernames.append(
                connected_accounts['primary_account']['instagram_data']['username'])
            for username in usernames:
                if self.IS_DONE: break
                print(f'\t[*] Username: {username}')
                total_coin = self.get_earned_coin_details(
                    access_token, insta_session)
                if total_coin > 0:
                    self.IS_DONE = self.redeem_earned_coin(
                        total_coin, access_token, insta_session)
                    print(f'\t\t[+] Added: {self.SPENT}')
            self.log_out(access_token, insta_session)

    def get_connected_accounts(self, access_token: str, insta_session: str):
        resp = get(f'{BASE_URL}/listConnectedAccount', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        return resp['data']

    def login(self, account: dict) -> typing.Tuple[bool, str, str]:
        # it's related to mrinsta server
        for _ in range(50):
            sleep(2)
            resp = post(f'{BASE_URL}/login', json={
                'username': account['email'],
                'password': PASSWORD,
            })
            try:
                return True, resp.json()['data']['access_token'], resp.cookies['mrinsta_session']
            except Exception as e:
                pass
        return False, "", ""

    def log_out(self, access_token: str, insta_session: str) -> None: post(f'{BASE_URL}/logout', headers={
        "Authorization": f"Bearer {access_token}"
    }, cookies={
        "mrinsta_session": insta_session
    })

    def get_earned_coin_details(self, access_token: str, insta_session: str) -> int:
        try:
            resp = get(
            f'{BASE_URL}/getEarnedCoinDetails', headers={
                "Authorization": f"Bearer {access_token}"
            }, cookies={
                "mrinsta_session": insta_session
            }).json()
            return int(resp['data']['total_earn_coin'])
        except Exception as e:
            print(f'\t\t[-] Error@get_earned_coin_details: {e}')
            print(f'\t\t[-] {resp}')
            if DEBUG: input()
            return 0

    def redeem_earned_coin(self, total_coin: int, access_token: str, insta_session: str) -> bool:
        needed = self.QUANTITY - self.SPENT
        if needed <= 0:
            return True
        earn = min(total_coin // 10, needed)

        resp = post(f'{BASE_URL}/redeemEarnedCoinDetails', json={
            'service': 'followers',
            'comments': '',
            'link': f'https://www.instagram.com/{TARGET}/',
            'qnty': earn,
            'coin': earn * 10,
        }, headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        self.SPENT += earn
        return False


if __name__ == '__main__':
    RedeemCoin()
