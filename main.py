from requests import get, post
from os import getenv, path
from json import load, dump
from time import sleep
from dotenv import load_dotenv
from lxml import html
import typing
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

# =============== CONFIGURE THIS ===============
TARGET = 'tushig'
PASSWORD = getenv('PASSWORD', 'Password!@#123')
# ==============================================

BASE_URL = 'https://api.mrinsta.com/api'
DEBUG = False

def get_instagram_usernames() -> typing.List:
    ret = []
    with open('instagram_usernames.txt', 'r') as f:
        for _ in f.readlines():
            ret.append(_.strip())
    return ret[::-1]


class MrInsta:
    def __init__(self) -> None:
        self.WORKED_ACCOUNTS = []
        self.INSTAGRAM_USERNAMES = get_instagram_usernames()
        self.read_accounts()
        self.INDEX = 0

        print(f'[+] Target: {TARGET}')

        # for account in self.ACCOUNTS:
        #     self.process_account(account)
        self.process_accounts(max_workers=1)

    def read_accounts(self):
        self.ACCOUNTS = load(
            open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'r'))[::-1]

    def process_accounts(self, max_workers=10) -> None:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for account in self.ACCOUNTS:
                future = executor.submit(self.process_account, account)
                futures.append(future)
            for future in futures:
                future.result()

    def process_account(self, account):
        _, access_token, insta_session = self.login(account)
        if not _:
            print(f"\t[-] Login failed: {account['email']}")
            return
        print(f'[+] Logged in: {account["email"]}')
        self.connect_account(access_token, insta_session)


        connected_accounts = self.get_connected_accounts(
            access_token, insta_session)
        usernames = [_['instagram_data']['username']
                     for _ in connected_accounts['connected_account']]
        usernames.append(
            connected_accounts['primary_account']['instagram_data']['username'])
        for username in usernames:
            print(f'\t[*] Username: {username}')
            resp = post(f'{BASE_URL}/changeIGAccount', headers={
                "Authorization": f"Bearer {access_token}"
            }, cookies={
                "mrinsta_session": insta_session
            }, json={
                'username': username
            })
            insta_session, access_token = resp.cookies['mrinsta_session'], resp.json()[
                'data']['token']
            is_free_followers_plan_active, is_free_post_like_active = self.active_subscription_setup(
                access_token, insta_session)
            _, message = self.activate_follow_user(access_token, insta_session)
            if not is_free_followers_plan_active and not 'activated' in message:
                self.follow_user(message['user']['id'],
                                 access_token, insta_session)
            else:
                print(f'\t\t[-] Follow plan not active')
            if not is_free_post_like_active:
                self.like_post(access_token, insta_session)
            else:
                print(f'\t\t[-] Like plan not active')

            total_coin = self.get_earned_coin_details(
                access_token, insta_session)
            if total_coin > 0:
                self.redeem_earned_coin(
                    total_coin, access_token, insta_session)
        self.log_out(access_token, insta_session)

    def get_connected_accounts(self, access_token: str, insta_session: str):
        resp = get(f'{BASE_URL}/listConnectedAccount', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        return resp['data']

    def connect_account(self, access_token: str, insta_session: str):
        resp = get(f'{BASE_URL}/listConnectedAccount', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        print(f"\t[+] Connected accounts: {len(resp['data']['connected_account'])}")
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
                        print(f'\t[+] Works: {self.INSTAGRAM_USERNAMES[self.INDEX]}')
                        break
                    self.INDEX += 1
                except Exception as e:
                    print(f'[-] Error@connect_account: {e}')
                    print(resp)
                    input()

    def validate_post_like(self, access_token: str, insta_session: str) -> str:
        return post(f'{BASE_URL}/validatePostLike', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()['message']

    def confirm_like_post(self, target_id: str, access_token: str, insta_session: str) -> str:
        try:
            return post(f'{BASE_URL}/confirmLikePosts', json={'post_id': target_id}, headers={
                "Authorization": f"Bearer {access_token}"
            }, cookies={
                "mrinsta_session": insta_session
            }).json()['message']
        except Exception as e:
            print(f'[-] Error@confirm_like_post: {e}')
            input()

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
            print(f'\t\t[*] Confirmed posts: {confirmed_posts}')
            if confirmed_posts > 10:
                break
        self.validate_post_like(access_token, insta_session)

    def follow_user(self, user_id: int, access_token: str, insta_session: str) -> None:
        for _ in range(10):
            try:
                confirmed_followers = get(
                    f'{BASE_URL}/getTotalAndPendingFollow', headers={
                        "Authorization": f"Bearer {access_token}"
                    }, cookies={
                        "mrinsta_session": insta_session
                    }).json()['data']['confirmed_followers']
                if confirmed_followers + 1 > 10:
                    break
                print(f'\t\t[*] Confirmed followers: {confirmed_followers + 1}')
                post(f'{BASE_URL}/confirmFollow', json={
                    'user_id': user_id,
                    'premium_user': 1,
                }, headers={
                    "Authorization": f"Bearer {access_token}"
                }, cookies={
                    "mrinsta_session": insta_session
                })
                resp = post(
                    f'{BASE_URL}/refreshUserFollow', headers={
                        "Authorization": f"Bearer {access_token}"
                    }, cookies={
                        "mrinsta_session": insta_session
                    })
                user_id = resp.json()['data']['user']['id']
            except Exception as e:
                print(f'\t[-] Error@follow_user@{_}: {e}')
                print(resp.json())
                if DEBUG: input()
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
        print(f"\t\t[*] Message: {resp['message']}")


if __name__ == '__main__':
    MrInsta()
    # CreateAccounts()
