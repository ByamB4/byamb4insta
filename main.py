from requests import Session
from os import getenv
from datetime import timedelta
from json import load
import zulu
import discord
from dotenv import load_dotenv

load_dotenv()

URL = 'https://api.mrinsta.com/api'

# CONFIGURE THIS
TARGET = 'byamb4'
DISCORD_LOG = False
PASSWORD = getenv('PASSWORD', 'Password!@#123')

class MrInsta:
    def __init__(self) -> None:
        message = f'[+] Target: {TARGET}'
        log = message + '\n'
        print(message)
        self.SESSION = Session()
        for account in load(open('accounts.json', 'r')):
            self.login(account)
            available, message = self.activate_follow_user()
            if not available:
                time_left = self.get_time_left()
                _ = f"[-] {account['email']}: {time_left}"
                print(_)
                log += _ + '\n'
            else:
                _ = f"[+] Available: {account['email']}"
                print(_)
                log += _ + '\n'
                self.follow_user(message['user']['id'])
            total_coin = self.get_earned_coin_details()
            if total_coin > 0:
                self.redeem_earned_coin(total_coin)
            self.log_out()
        if DISCORD_LOG:
            discord_log(log)

    def login(self, account: dict) -> None:
        resp = self.SESSION.post(f'{URL}/login', json={
            'username': account['email'],
            # same password for all account
            'password': PASSWORD,
        }).json()['data']
        self.SESSION.headers.update({
            'Authorization': f"Bearer {resp['access_token']}",
        })

    def log_out(self) -> None: self.SESSION.post(f'{URL}/logout')

    def get_earned_coin_details(self) -> int:
        total_coin = int(self.SESSION.get(
            f'{URL}/getEarnedCoinDetails').json()['data']['total_earn_coin'])
        print(f'\t[+] Total coin: {total_coin}')
        return total_coin

    def get_time_left(self) -> timedelta:
        try:
            # thats weird issue, sometimes this endpoint returns empty data
            resp = self.SESSION.get(
                f'{URL}/activeSubscriptionSetupForAll').json()
            seconds = (zulu.parse(
                resp['data']['free_followers_end_datetime']) - zulu.now()).seconds
            return timedelta(seconds=seconds)
        except:
            return timedelta(seconds=0)

    def activate_follow_user(self) -> tuple:
        resp = self.SESSION.post(f'{URL}/activateFollowUser').json()
        message, data = resp['message'], resp['data']
        return (False, message) if "activated" in message else (True, data)

    def follow_user(self, user_id: int) -> None:
        for _ in range(10):
            confirmed_followers = self.SESSION.get(
                f'{URL}/getTotalAndPendingFollow').json()['data']['confirmed_followers']
            print(f'\t[+] Confirmed followers: {confirmed_followers+1}')
            self.SESSION.post(f'{URL}/confirmFollow', json={
                'user_id': user_id,
                'premium_user': 1,
            })
            user_id = self.SESSION.post(
                f'{URL}/refreshUserFollow').json()['data']['user']['id']
        self.SESSION.post(f'{URL}/validateFollowUser')

    def redeem_earned_coin(self, total_coin: int) -> None:
        coin, qnty = total_coin, total_coin // 10
        if total_coin > 1000:
            coin, qnty = 1000, 100
        resp = self.SESSION.post(f'{URL}/redeemEarnedCoinDetails', json={
            'service': 'followers',
            'comments': '',
            'link': f'https://www.instagram.com/{TARGET}/',
            'qnty': qnty,
            'coin': coin,
        }).json()
        print(f"\t[+] Message: {resp['message']}")


def discord_log(resp) -> None:
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready() -> None:
        await client.get_channel(int(getenv('DISCORD_CHANNEL'))).send(f'```{resp[:1500]}```')
        await client.close()

    client.run(getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    MrInsta()
