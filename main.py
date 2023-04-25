from requests import Session
import os
from datetime import timedelta
import json
import zulu
import discord
from dotenv import load_dotenv

PROJECT_NAME = os.path.dirname(os.path.abspath(__file__)).split('/')[-1]

class MrInsta:
    BASE_URL = 'https://api.mrinsta.com'
    TARGET = 'byamb4'
    RESPONSE: str = ''
    ACCOUNTS: list = []

    def __init__(self):
        load_dotenv()
        message = f'[*] Target: {self.TARGET}'
        print(message)
        self.RESPONSE += f'{message}\n'
        self.SESSION = Session()
        self.read_accounts()
        for account in self.ACCOUNTS:
            self.login(account)
            available, _message = self.activate_follow_user()
            if not available:
                time_left = self.get_time_left()
                message = f"[-] {self.without_email(account['email'])}: {time_left}"
                print(message)
                self.RESPONSE += f"{message}\n"
                continue
            message = f"[+] Available: {self.without_email(account['email'])}"
            print(message)
            self.RESPONSE += f"{message}\n"
            self.logic(_message['user']['id'])
            self.validate_follow_user()
            self.redeem_earned_coin()

    def get_time_left(self) -> None:
        try:
            resp = self.SESSION.get(
                f'{self.BASE_URL}/api/activeSubscriptionSetupForAll').json()
            seconds = (zulu.parse(
                resp['data']['free_followers_end_datetime']) - zulu.now()).seconds
            return timedelta(seconds=seconds)
        except Exception as e:
            return timedelta(seconds=0)

    def without_email(self, _) -> str:
        return _.split('@')[0] if '@' in _ else _

    def read_accounts(self) -> None:
        self.ACCOUNTS = json.load(open(f'{get_project_root()}/accounts.json', 'r'))

    def login(self, creds) -> None:
        try:
            resp = self.SESSION.post(f'{self.BASE_URL}/api/login', json={
                'username': creds['email'],
                'password': os.getenv('PASSWORD'),
            })
            data = resp.json()['data']
            self.SESSION.headers.update({
                'Authorization': f"Bearer {data['access_token']}",
            })
        except Exception as e:
            self.RESPONSE += f'[-] ERROR (login): {str(e)}'

    def activate_follow_user(self) -> tuple:
        try:
            resp = self.SESSION.post(
                f'{self.BASE_URL}/api/activateFollowUser').json()
            _message, _data = resp['message'], resp['data']
            return (False, _message) if "activated" in _message else (True, _data)
        except Exception as e:
            self.RESPONSE += f'[-] ERROR (active_follow_user): {e}'

    def logic(self, user_id) -> None:
        for _ in range(10):
            confirmed_followers = self.get_confirmed_followers()
            print(f'\t[+] Confirmed followers: {confirmed_followers+1}')
            self.confirm_follow({'user_id': user_id, 'premium_user': 1})
            user_id = self.refresh_user_follow()

    def refresh_user_follow(self) -> None:
        try:
            resp = self.SESSION.post(
                f'{self.BASE_URL}/api/refreshUserFollow').json()['data']
            return resp['user']['id']
        except Exception as e:
            self.RESPONSE += f'[-] ERROR (refresh_user_follow): {str(e)}'

    def get_confirmed_followers(self) -> int:
        try:
            resp = self.SESSION.get(
                f'{self.BASE_URL}/api/getTotalAndPendingFollow').json()['data']
            return resp['confirmed_followers']
        except Exception as e:
            self.RESPONSE += f'[-] ERROR (get_confirmed_followers): {str(e)}'

    def confirm_follow(self, data) -> str:
        self.SESSION.post(f'{self.BASE_URL}/api/confirmFollow', json={
            'user_id': data['user_id'],
            'premium_user': data['premium_user'],
        })

    def validate_follow_user(self) -> None:
        message = self.SESSION.post(
            f'{self.BASE_URL}/api/validateFollowUser').json()['message']
        print(f'\t[+] Message: {message}')

    def redeem_earned_coin(self) -> None:
        resp = self.SESSION.post(f'{self.BASE_URL}/api/redeemEarnedCoinDetails', json={
            'service': 'followers',
            'comments': '',
            'link': f'https://www.instagram.com/{self.TARGET}/',
            'qnty': '10',
            'coin': 100
        }).json()
        message = f"\t[+] Message: {resp['message']}"
        print(message)


def discord_log(resp) -> None:
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready() -> None:
        await client.get_channel(os.getenv('DISCORD_CHANNEL')).send(f'```{resp[:1500]}```')
        await client.close()

    client.run(os.getenv('DISCORD_TOKEN'))


def get_project_root():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return cwd[:cwd.find(PROJECT_NAME) + len(PROJECT_NAME)]


if __name__ == '__main__':
    try:
        mrinsta = MrInsta()
    except Exception as e:
        print(e)
        discord_log(str(e))
        exit()

    discord_log(mrinsta.RESPONSE)
