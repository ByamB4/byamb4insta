from time import sleep
from requests import Session
from os import getenv
from typing import Tuple, Union, Any
from json import load
from dotenv import load_dotenv

load_dotenv()

URL = 'https://api.mrinsta.com/api'

# CONFIGURE THIS
TARGET = 'byamb4'
PASSWORD = getenv('PASSWORD', 'Password!@#123')

class MrInsta:
    def __init__(self) -> None:
        print(f'[+] Target: {TARGET}')
        self.SESSION = Session()
        for account in load(open('accounts.json', 'r')):
            print(f"[*] Account: {account['email']}")
            success = self.login(account)
            if not success: continue

            is_free_followers_plan_active, is_free_post_like_active = self.active_subscription_setup()
            if not is_free_followers_plan_active:
                _, message = self.activate_follow_user()
                self.follow_user(message['user']['id'])
            else:
                print(f"\t[-] Follow plan not active")
            if not is_free_post_like_active:
                self.like_post()
            else:
                print(f"\t[-] Like post plan not active")

            total_coin = self.get_earned_coin_details()
            if total_coin > 0:
                self.redeem_earned_coin(total_coin)
            self.log_out()

            # idk sometimes previous session didn't cleary so just wait
            # we can write something like that `with Session() as session` but it makes code more ugly lol
            sleep(1)

    def validate_post_like(self) -> str:
        return self.SESSION.post(f'{URL}/validatePostLike').json()['message']

    def confirm_like_post(self, target_id: str) -> str:
        return self.SESSION.post(f'{URL}/confirmLikePosts', json={'post_id': target_id}).json()['message']

    def refresh_user_like(self) -> str:
        return self.SESSION.post(f'{URL}/refreshUserLike').json()['data']['id']

    def like_posts_info(self) -> str:
        return self.SESSION.get(f'{URL}/likePostsInfo').json()['data']['confirmed_posts']

    def active_subscription_setup(self) -> Tuple[bool, bool]:
        resp = self.SESSION.get(
            f'{URL}/activeSubscriptionSetupForAll').json()['data']
        return resp['is_free_followers_plan_active'], resp['is_free_post_like_active']

    def login(self, account: dict) -> bool:
        resp = self.SESSION.post(f'{URL}/login', json={
            'username': account['email'],
            # same password for all account
            'password': PASSWORD,
        }).json()
        if resp['success'] == False:
            print(f"\t[-] {resp['message']}")
            return False
        self.SESSION.headers.update({
            'Authorization': f"Bearer {resp['data']['access_token']}",
        })
        return True

    def log_out(self) -> None: self.SESSION.post(f'{URL}/logout')

    def get_earned_coin_details(self) -> int: return int(self.SESSION.get(
        f'{URL}/getEarnedCoinDetails').json()['data']['total_earn_coin'])

    def activate_follow_user(self) -> Tuple[bool, Union[str, Any]]:
        resp = self.SESSION.post(f'{URL}/activateFollowUser').json()
        message, data = resp['message'], resp['data']
        return (False, message) if "activated" in message else (True, data)

    def like_post(self) -> None:
        for _ in range(10):
            self.confirm_like_post(self.refresh_user_like())
            confirmed_posts = self.like_posts_info()
            if confirmed_posts > 10:
                break
            print(f'\t[+] Confirmed posts: {confirmed_posts}')
        self.validate_post_like()

    def follow_user(self, user_id: int) -> None:
        for _ in range(10):
            confirmed_followers = self.SESSION.get(
                f'{URL}/getTotalAndPendingFollow').json()['data']['confirmed_followers']
            if confirmed_followers + 1 > 10:
                break
            print(f'\t[+] Confirmed followers: {confirmed_followers + 1}')
            self.SESSION.post(f'{URL}/confirmFollow', json={
                'user_id': user_id,
                'premium_user': 1,
            })
            user_id = self.SESSION.post(
                f'{URL}/refreshUserFollow').json()['data']['user']['id']
        self.SESSION.post(f'{URL}/validateFollowUser')

    def redeem_earned_coin(self, total_coin: int) -> None:
        # coin, qnty should be more clear, fix needed
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

if __name__ == '__main__':
    MrInsta()
