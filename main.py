from requests import Session
import os
from datetime import timedelta
import json
import zulu
import discord
from dotenv import load_dotenv

load_dotenv()
URL = 'https://api.mrinsta.com/api'

# CONFIGURE THIS
TARGET = 'jaki_oppa'
DISCORD_LOG = False

def main():
    message = f'[+] Target: {TARGET}'
    log = message + '\n'
    print(message)
    for account in json.load(open('accounts.json', 'r')):
        with Session() as session:
            login(session, account)
            available, message = activate_follow_user(session)
            if not available:
                time_left = get_time_left(session)
                _ = f"[-] {without_email(account['email'])}: {time_left}"; print(_); log += _ + '\n'
            else:
                _ = f"[+] Available: {without_email(account['email'])}"; print(_); log += _ + '\n'
                follow_user(session, message['user']['id'])
            total_coin = get_earned_coin_details(session)
            if total_coin > 0:
                redeem_earned_coin(session, total_coin)
            log_out(session)
    if DISCORD_LOG: discord_log(log)

def log_out(session: Session):
    print(f"\t[+] {session.post(f'{URL}/logout').json()['message']}")

def get_earned_coin_details(session: Session) -> int:
    total_coin = int(session.get(f'{URL}/getEarnedCoinDetails').json()['data']['total_earn_coin'])
    print(f'\t[+] Total coin: {total_coin}')
    return total_coin

def get_time_left(session: Session) -> timedelta:
    try:
        # thats weird issue, sometimes this endpoint returns empty data
        resp = session.get(f'{URL}/activeSubscriptionSetupForAll').json()
        seconds = (zulu.parse(
            resp['data']['free_followers_end_datetime']) - zulu.now()).seconds
        return timedelta(seconds=seconds)
    except:
        return timedelta(seconds=0)

def without_email(email: str) -> str: return email.split('@')[0] if '@' in email else email


def login(session: Session, account: dict) -> None:
    resp = session.post(f'{URL}/login', json={
        'username': account['email'],
        # same password for all account
        'password': os.getenv('PASSWORD'),
    }).json()['data']
    session.headers.update({
        'Authorization': f"Bearer {resp['access_token']}",
    })

def activate_follow_user(session: Session) -> tuple:
    resp = session.post(f'{URL}/activateFollowUser').json()
    message, data = resp['message'], resp['data']
    return (False, message) if "activated" in message else (True, data)

def follow_user(session: Session, user_id: int) -> None:
    for _ in range(10):
        confirmed_followers = session.get(f'{URL}/getTotalAndPendingFollow').json()['data']['confirmed_followers']
        print(f'\t[+] Confirmed followers: {confirmed_followers+1}')
        session.post(f'{URL}/confirmFollow', json={
            'user_id': user_id,
            'premium_user': 1,
        })
        user_id = session.post(f'{URL}/refreshUserFollow').json()['data']['user']['id']
    session.post(f'{URL}/validateFollowUser')

def redeem_earned_coin(session: Session, total_coin: int) -> None:
    coin = total_coin
    qnty = total_coin // 10
    if total_coin > 1000:
        coin = 1000
        qnty = 100
    resp = session.post(f'{URL}/redeemEarnedCoinDetails', json={
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
        await client.get_channel(int(os.getenv('DISCORD_CHANNEL'))).send(f'```{resp[:1500]}```')
        await client.close()

    client.run(os.getenv('DISCORD_TOKEN'))



if __name__ == '__main__':
    main()
