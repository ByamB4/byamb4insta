from requests import get, post
from os import getenv, path
from json import load, dump
from time import sleep
from lxml import html
import typing
from concurrent.futures import ThreadPoolExecutor

PASSWORD = 'p4$$w0rD!'
BASE_URL = 'https://api.mrinsta.com/api'
DEBUG = False

class CollectPoint:
    def __init__(self) -> None:
        self.WORKED_ACCOUNTS = []
        self.read_accounts()
        self.INDEX = 0
        self.process_accounts()

    def read_accounts(self):
        self.ACCOUNTS = load(
            open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'r'))[::-1]

    def process_accounts(self):
        for account in self.ACCOUNTS:
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

            self.log_out(access_token, insta_session)

    def get_connected_accounts(self, access_token: str, insta_session: str):
        resp = get(f'{BASE_URL}/listConnectedAccount', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        return resp['data']

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
                print(
                    f'\t\t[*] Confirmed followers: {confirmed_followers + 1}')
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
                if DEBUG:
                    input()
        post(f'{BASE_URL}/validateFollowUser', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        })


if __name__ == '__main__':
    CollectPoint()