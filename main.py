from requests import Session, get, post
from os import getenv, path
from json import load, dump
from time import sleep
from dotenv import load_dotenv
from lxml import html
import typing
import argparse

#load_dotenv()

# =============== CONFIGURE THIS ===============
PASSWORD: str = getenv('PASSWORD', 'Password!@#123')
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
        try:
            if resp['success'] == False:
                print(f"\t[-] {resp['message']}")
                return False
            self.SESSION.headers.update({
                'Authorization': f"Bearer {resp['data']['access_token']}",
            })
        except Exception as e:
            # this branch shouldn't happen
            # idk what causes this probably by mrinsta, still trying to figure this out
            # solution: try rerun (it works for me)
            print('\t[-] Login failed')
            print('\t[-] Try rerun')
            print(f'\t[DEBUG] {resp}')
            input()
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


class CreateAccounts:
    def __init__(self):
        _, email = self.generate_new_email()
        _, data = self.register(email)
        _, otp = self.get_otp(email)
        if not _:
            print('\t[-] No OTP found')
            exit()
        _, data = self.verify_email(email, otp)
        _ = self.connect_ig(email)

    def connect_ig(self, email: str):
        # Login again
        resp = post('https://api.mrinsta.com/api/login', json={
            "username": email,
            "password": PASSWORD
        }).json()
        user_id, access_token = resp['data']['user_id'], resp['data']['access_token']
        print(f"\t[+] {resp['message']}")

        # storeUpdateUserDetails
        resp = post('https://api.mrinsta.com/api/storeUpdateUserDetails', headers={
            "Authorization": f"Bearer {access_token}"
        }, json={
            "user_id": user_id,
            "location": "South America",
            "gender": "Prefer not to say",
            "age": "35-44"
        }).json()
        print(f"\t[+] {resp['message']}")

        # interests
        resp = post('https://api.mrinsta.com/api/storeUserWiseInterests', headers={
            "Authorization": f"Bearer {access_token}"
        }, json={
            "id": user_id,
            "interests": "22, 21, 20, 19",
        }).json()
        print(f"\t[+] {resp['message']}")

        accounts: dict = load(open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'r'))
        accounts.append({"email": email})
        print(accounts)
        with open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'w') as f:
            dump(accounts, f)

        # connect to instagram account
        # NOTE: need proper solution
        # resp = post('https://api.mrinsta.com/api/addConnectedIGAccount', headers={
        #     "Authorization": f"Bearer {access_token}"
        # }, json={
        #     "username": <INSTAGRAM_ACCOUNT_WITH_5_PUBLIC_POST>,
        # }).json()
        # print(resp)

    def get_otp(self, email: str):
        for _ in range(1, 20):
            try:
                sleep(2)
                print(f'\t[*] Trying: {_}')
                tree = html.fromstring(
                    get(f'https://email-fake.com/{email}').content)
                otp = tree.xpath(
                    "//table[@class='content']//h3")[0].text_content()
                if len(otp) == 6:
                    print(f'\t[+] OTP: {otp}')
                    return True, otp
            except:
                pass
        return False, ''

    def register(self, email: str):
        resp = post('https://api.mrinsta.com/api/register', json={
            "email": email,
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        }).json()
        if resp['success']:
            print('\t[+] Registered on mrinsta')
        return resp['success'], resp['data']

    def verify_email(self, email: str, otp: str):
        resp = get(f"https://api.mrinsta.com/api/verify/{otp}/{email}").json()
        if resp['success']:
            print("\t[+] Account activated")
            return resp['success'], resp['message']
        return False, resp

    def generate_new_email(self):
        tree = html.fromstring(get('https://email-fake.com/').content)
        mail = tree.xpath("//span[@id='email_ch_text']")[0].text_content()
        print(f'[+] Email: {mail}')
        if '@' in mail:
            return True, mail
        return False, ''

def setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--target", type=str, help="Target account id")
    parser.add_argument("-c", "--count", type=int, help="Fake account count: <int> or 0 for use old created accounts")

    return parser

def run(target: str, count: int) -> None:
    global TARGET
    TARGET = target
    if count:
        for _ in range(0, count):
            CreateAccounts()

    MrInsta() 
    
if __name__ == '__main__':
    parser = setup_argparse()
    args = parser.parse_args()

    run(args.target, args.count)