import asyncio
import json
import urllib.request
import websockets
from config import misskey_host, token, ng_words

# thanks: https://qiita.com/CyberRex/items/e49828dba8e5867d8b26

ws_url = 'wss://%s/streaming?i=%s' % (misskey_host, token)


def check_if_ng_word_exists(text):
    detected = False
    for t in ng_words:
        if t in text:
            detected = True
            break
    return detected

def suspend_user(user_id):
    url = 'https://%s/api/admin/suspend-user' % misskey_host
    data = json.dumps({
        'i': token,
        'userId': user_id
    }).encode()
    header = { 'Content-Type': 'application/json', }
    req = urllib.request.Request(url, data, header)
    with urllib.request.urlopen(req) as res:
        body = res.read()
    return body

async def runner():
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({
            "type": "connect",
            "body": {
                "channel": "globalTimeline",
                "id": "test"
            }
        }))
        while True:
            data = json.loads(await ws.recv())
            if data['type'] == 'channel' and data['body']['type'] == 'note':
                note = data['body']['body']
                await on_note(note)


async def on_note(note):
    mentions = 0 if not "mentions" in note else len(note["mentions"])
    is_spam = False
    if note["replyId"] is None and 1 < mentions:
        account = "%s@%s" % (note["user"]["username"], note["user"]["host"])
        print("[%s] mention detected" % account)

        if check_if_ng_word_exists(note["text"]):
            print("[%s] NG word detected" % account)
            is_spam = True
        else:
            print("[%s] NG word does not found" % account)

        if is_spam:
            suspend_user(note["userId"])
            print("[%s] (%s) was suspended." % (account, note["userId"]))
        else:
            print("[%s] (%s) does not spam(maybe?)." % (account, note["userId"]))


asyncio.new_event_loop().run_until_complete(runner())