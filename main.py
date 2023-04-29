from requests import Session
from os import getenv, path
from json import load
from dotenv import load_dotenv
import typing

load_dotenv()

# =============== CONFIGURE THIS ===============
TARGET = 'byamb4'
PASSWORD = getenv('PASSWORD', 'Password!@#123')
# ==============================================

class MrInsta:
    def __init__(self) -> None:
        print(f'[+] Target: {TARGET}')
        self.URL = 'https://api.mrinsta.com/api'
        self.SESSION = Session()
        for account in load(open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'r')):
            print(f"[*] Account: {account['email']}")
            success = self.login(account)
            
            if not success:
                continue

            is_free_followers_plan_active, is_free_post_like_active = self.active_subscription_setup()
            _, message = self.activate_follow_user()
            if not is_free_followers_plan_active and not 'activated' in message:
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

    def validate_post_like(self) -> str:
        return self.SESSION.post(f'{self.URL}/validatePostLike').json()['message']

    def confirm_like_post(self, target_id: str) -> str:
        return self.SESSION.post(f'{self.URL}/confirmLikePosts', json={'post_id': target_id}).json()['message']

    def refresh_user_like(self) -> str:
        return self.SESSION.post(f'{self.URL}/refreshUserLike').json()['data']['id']

    def like_posts_info(self) -> str:
        return self.SESSION.get(f'{self.URL}/likePostsInfo').json()['data']['confirmed_posts']

    def active_subscription_setup(self) -> typing.Tuple[bool, bool]:
        resp = self.SESSION.get(
            f'{self.URL}/activeSubscriptionSetupForAll').json()['data']
        return resp['is_free_followers_plan_active'], resp['is_free_post_like_active']

    def login(self, account: dict) -> bool:
        resp = self.SESSION.post(f'{self.URL}/login', json={
            'username': account['email'],
            # same password for all account
            'password': PASSWORD,
        }).json()
        if resp['success'] == False:
            print(f"\t[-] {resp['message']}")
            return False
        try:
            self.SESSION.headers.update({
                'Authorization': f"Bearer {resp['data']['access_token']}",
            })
        except Exception as e:
            print('\t[-] Login failed')
            self.SESSION.close()
            self.SESSION = Session()
            return False
        return True

    def log_out(self) -> None: self.SESSION.post(f'{self.URL}/logout')

    def get_earned_coin_details(self) -> int: return int(self.SESSION.get(
        f'{self.URL}/getEarnedCoinDetails').json()['data']['total_earn_coin'])

    def activate_follow_user(self) -> typing.Tuple[bool, typing.Union[str, typing.Any]]:
        resp = self.SESSION.post(f'{self.URL}/activateFollowUser').json()
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
                f'{self.URL}/getTotalAndPendingFollow').json()['data']['confirmed_followers']
            if confirmed_followers + 1 > 10:
                break
            print(f'\t[+] Confirmed followers: {confirmed_followers + 1}')
            self.SESSION.post(f'{self.URL}/confirmFollow', json={
                'user_id': user_id,
                'premium_user': 1,
            })
            user_id = self.SESSION.post(
                f'{self.URL}/refreshUserFollow').json()['data']['user']['id']
        self.SESSION.post(f'{self.URL}/validateFollowUser')

    def redeem_earned_coin(self, total_coin: int) -> None:
        # coin, qnty should be more clear, fix needed
        coin, qnty = total_coin, total_coin // 10
        if total_coin > 1000:
            coin, qnty = 1000, 100
        resp = self.SESSION.post(f'{self.URL}/redeemEarnedCoinDetails', json={
            'service': 'followers',
            'comments': '',
            'link': f'https://www.instagram.com/{TARGET}/',
            'qnty': qnty,
            'coin': coin,
        }).json()
        print(f"\t[+] Message: {resp['message']}")


if __name__ == '__main__':
    MrInsta()