from requests import get, post
from os import path
from json import load
import random
from time import sleep
import typing

# =============== CONFIGURE THIS ===============
TARGET = 'cristiano'
PASSWORD = 'Passw0rd!@#'
DEBUG = False
# ==============================================
BASE_URL = 'https://api.mrinsta.com/api'

class MrInsta:
    def __init__(self) -> None:
        accounts = load(
            open(f"{path.join(path.dirname(__file__), 'accounts.json')}", 'r'))
        random.shuffle(accounts)
        for account in accounts:
            _, access_token, insta_session = self.login(account)
            if not _:
                print(f"\t[-] Login failed: {account['email']}")
                continue
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
                _, message = self.activate_follow_user(
                    access_token, insta_session)
                if not is_free_followers_plan_active and not 'activated' in message:
                    self.follow_user(message['user']['id'], access_token, insta_session)
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
            if DEBUG:
                input()
            return 0

    def redeem_earned_coin(self, total_coin: int, access_token: str, insta_session: str) -> None:
        resp = post(f'{BASE_URL}/redeemEarnedCoinDetails', json={
            'service': 'followers',
            'comments': '',
            'link': TARGET,
            'qnty': total_coin // 10,
            'coin': total_coin,
        }, headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        print(f'\t\t[+] {resp["message"]}')

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

    def refresh_user_like(self, access_token: str, insta_session: str) -> int:
        resp = post(f'{BASE_URL}/refreshUserLike', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        try:
            return int(resp['data']['id'])
        except Exception as e:
            print(resp)
            return 0

    def like_posts_info(self, access_token: str, insta_session: str) -> int:
        resp = get(f'{BASE_URL}/likePostsInfo', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        }).json()
        try:
            return int(resp['data']['confirmed_posts'])
        except Exception as e:
            print(e)
            return 0

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
                if DEBUG:
                    print(f'\t[-] Error@follow_user@{_}: {e}')
                    input()
        post(f'{BASE_URL}/validateFollowUser', headers={
            "Authorization": f"Bearer {access_token}"
        }, cookies={
            "mrinsta_session": insta_session
        })


if __name__ == '__main__':
    MrInsta()
    # delete->MrInsta()