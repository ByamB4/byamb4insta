from requests import get, post
from os import getenv, path
from json import load, dump
from time import sleep
from dotenv import load_dotenv
from lxml import html
import typing
import signal

load_dotenv()

# =============== CONFIGURE THIS ===============
TARGET = 'byamb4'
PASSWORD = getenv('PASSWORD', 'Password!@#123')
# ==============================================

BASE_URL = 'https://api.mrinsta.com/api'

class MrInsta:
    def __init__(self) -> None:
        print(f'[+] Target: {TARGET}')
        for account in load(
            open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'r')):
                print(f'[+] Account: {account["email"]}')
                _, access_token, insta_session = self.login(account)
                if not _:
                    print(f"[-] Login failed")
                    return

                is_free_followers_plan_active, is_free_post_like_active = self.active_subscription_setup(
                    access_token, insta_session)
                _, message = self.activate_follow_user(access_token, insta_session)
                if not is_free_followers_plan_active and not 'activated' in message:
                    self.follow_user(message['user']['id'],
                                    access_token, insta_session)
                else:
                    print(f'\t[-] Follow plan not active')
                if not is_free_post_like_active:
                    self.like_post(access_token, insta_session)
                else:
                    print(f'\t[-] Like plan not active')

                total_coin = self.get_earned_coin_details(access_token, insta_session)
                if total_coin > 0:
                    self.redeem_earned_coin(
                        total_coin, access_token, insta_session)
                self.log_out(access_token, insta_session)

    def validate_post_like(self, access_token: str, insta_session: str) -> str:
        return post(f'{BASE_URL}/validatePostLike', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()['message']

    def confirm_like_post(self, target_id: str, access_token: str, insta_session: str) -> str:
        return post(f'{BASE_URL}/confirmLikePosts', json={'post_id': target_id}, headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()['message']

    def refresh_user_like(self, access_token: str, insta_session: str) -> str:
        return post(f'{BASE_URL}/refreshUserLike', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()['data']['id']

    def like_posts_info(self, access_token: str, insta_session: str) -> str:
        return get(f'{BASE_URL}/likePostsInfo', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()['data']['confirmed_posts']

    def active_subscription_setup(self, access_token: str, insta_session: str) -> typing.Tuple[bool, bool]:
        resp = get(
            f'{BASE_URL}/activeSubscriptionSetupForAll',
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            cookies={
                'mrinsta_session': insta_session
            }
        ).json()['data']
        return resp['is_free_followers_plan_active'], resp['is_free_post_like_active']

    def login(self, account: dict) -> typing.Tuple[bool, str, str]:
        resp = post(f'{BASE_URL}/login', json={
            'username': account['email'],
            'password': PASSWORD,
        })

        if 'access_token' in resp.json()['data']:
            return True, resp.json()['data']['access_token'], resp.cookies['mrinsta_session']
        # its related to mrinsta
        # print(f'[-] Login failed: {account}')
        # print(resp.json())
        return False, "", ""

    def log_out(self, access_token: str, insta_session: str) -> None: post(f'{BASE_URL}/logout', headers={
        "Authorization": f"Bearer {access_token}"
    }, cookies={
        "mrinsta_session": insta_session
    })

    def get_earned_coin_details(self, access_token: str, insta_session: str) -> int: return int(get(
        f'{BASE_URL}/getEarnedCoinDetails', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()['data']['total_earn_coin'])

    def activate_follow_user(self, access_token: str, insta_session: str) -> typing.Tuple[bool, typing.Union[str, typing.Any]]:
        resp = post(f'{BASE_URL}/activateFollowUser', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        message, data = resp['message'], resp['data']
        return (False, message) if "activated" in message else (True, data)

    def like_post(self, access_token: str, insta_session: str) -> None:
        for _ in range(10):
            self.confirm_like_post(
                self.refresh_user_like(access_token, insta_session), access_token, insta_session)
            confirmed_posts = self.like_posts_info(access_token, insta_session)
            if confirmed_posts > 10:
                break
        self.validate_post_like(access_token, insta_session)

    def follow_user(self, user_id: int, access_token: str, insta_session: str) -> None:
        for _ in range(10):
            confirmed_followers = get(
                f'{BASE_URL}/getTotalAndPendingFollow', headers={
                    "Authorization": f"Bearer {access_token}"
                }, cookies={
                    "mrinsta_session": insta_session
                }).json()['data']['confirmed_followers']
            if confirmed_followers + 1 > 10:
                break
            print(f'\t[*] Confirmed followers: {confirmed_followers + 1}')
            post(f'{BASE_URL}/confirmFollow', json={
                'user_id': user_id,
                'premium_user': 1,
            }, headers={
                "Authorization": f"Bearer {access_token}"
            }, cookies={
                "mrinsta_session": insta_session
            })
            user_id = post(
                f'{BASE_URL}/refreshUserFollow', headers={
                    "Authorization": f"Bearer {access_token}"
                }, cookies={
                    "mrinsta_session": insta_session
                }).json()['data']['user']['id']
        post(f'{BASE_URL}/validateFollowUser', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        })

    def redeem_earned_coin(self, total_coin: int, access_token: str, insta_session: str) -> None:
        # coin, qnty should be more clear, fix needed
        coin, qnty = total_coin, total_coin // 10
        if total_coin > 1000:
            coin, qnty = 1000, 100
        resp = post(f'{BASE_URL}/redeemEarnedCoinDetails', json={
            'service': 'followers',
            'comments': '',
            'link': f'https://www.instagram.com/{TARGET}/',
            'qnty': qnty,
            'coin': coin,
        }, headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        print(f"\t[*] Message: {resp['message']}")


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


if __name__ == '__main__':
    MrInsta()
    # CreateAccounts()
