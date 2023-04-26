from requests import Session
import os
from datetime import timedelta
import json
import zulu
import discord
from dotenv import load_dotenv

load_dotenv()
TARGET = 'jaki_oppa'
URL = 'https://api.mrinsta.com/api'

def main():
    resp = f'[+] Target: {TARGET}\n'
    for account in json.load(open('accounts.json', 'r')):
        session = Session()
        login(session, account)
        available, message = activate_follow_user(session)
        if not available:
            time_left = get_time_left(session)
            _ = f"[-] {without_email(account['email'])}: {time_left}"; print(_); resp += _ + '\n'
            continue
        _ = f"[+] Available: {without_email(account['email'])}"; print(_); resp += _ + '\n'
        logic(session, message['user']['id'])
        redeem_earned_coin(session)
    discord_log(resp)

def get_time_left(session: Session) -> timedelta:
    resp = session.get(f'{URL}/activeSubscriptionSetupForAll').json()
    end_time = zulu.parse(resp.get('data', {}).get('free_followers_end_datetime'))
    return str(max(end_time - zulu.now(), timedelta(0))).split('.')[0]

def without_email(email: str) -> str:
    return email.split('@')[0] if '@' in email else email


def login(session: Session, account: dict) -> None:
    resp = session.post(f'{URL}/login', json={
        'username': account['email'],
        'password': os.getenv('PASSWORD'),
    }).json()['data']
    session.headers.update({
        'Authorization': f"Bearer {resp['access_token']}",
    })

def activate_follow_user(session: Session) -> tuple:
    resp = session.post(f'{URL}/activateFollowUser').json()
    message, data = resp['message'], resp['data']
    return (False, message) if "activated" in message else (True, data)

def logic(session: Session, user_id: int) -> None:
    for _ in range(10):
        confirmed_followers = session.get(f'{URL}/getTotalAndPendingFollow').json()['data']['confirmed_followers']
        print(f'\t[+] Confirmed followers: {confirmed_followers+1}')
        session.post(f'{URL}/confirmFollow', json={
            'user_id': user_id,
            'premium_user': 1,
        })
        user_id = session.post(f'{URL}/refreshUserFollow').json()['data']['user']['id']
    session.post(f'{URL}/validateFollowUser')

def redeem_earned_coin(session: Session) -> None:
    resp = session.post(f'{URL}/api/redeemEarnedCoinDetails', json={
        'service': 'followers',
        'comments': '',
        'link': f'https://www.instagram.com/{TARGET}/',
        'qnty': '10',
        'coin': 100,
    }).json()
    print(f"\t[+] Message: {resp['message']}")


def discord_log(resp) -> None:
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready() -> None:
        await client.get_channel(int(os.getenv('DISCORD_CHANNEL'))).send(f'```{resp[:1500]}```')
        await client.close()

    client.run(os.getenv('DISCORD_TOKEN'))



if __name__ == '__main__':
    main()
