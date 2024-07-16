import datetime
import re
import webbrowser

import pytz
from pytz import utc
from telethon import events
from telethon.errors import InviteHashExpiredError, FloodWaitError, UserAlreadyParticipantError
from telethon.tl.functions.messages import StartBotRequest, ImportChatInviteRequest


class BotRelations:

    def __init__(self, client, telegram_bot, operations, groups):
        self._client = client
        self._lastAutoEnter = utc.localize(datetime.datetime.utcnow() - datetime.timedelta(days=1))

        @client.on(events.NewMessage(chats=[259643624, 5541265268]))
        @client.on(events.MessageEdited(chats=[259643624, 5541265268]))
        async def _(event):
            await self.on_bot_message(event, client, telegram_bot, operations, groups)

        pass

    async def scanCaptcha(self, message, group):
        # CalsiBot
        if 'protected by' in message.message:

            print("PreVerify detected.")
            # print("Message buttons: ")

            for button_lists in message.buttons:
                for button in button_lists:
                    print(button.url, button.text)
                    if button.url and '' in button.url and self._lastAutoEnter < utc.localize(
                            datetime.datetime.utcnow()):
                        params = re.sub('.*start=', '', button.url)
                        request = StartBotRequest("CalsiBot", "CalsiBot",
                                                  params)
                        await self._client(request)
                        await self._client.send_message('CalsiBot', re.sub('is protected.*', '',
                                                                     message.raw_text))
                        self.lastPreVerify = utc.localize(
                            datetime.datetime.utcnow() + datetime.timedelta(seconds=15))
                        return [params, group]


        if 'MEVFree' in message.message:

            print("MEVFree Guardian")
            # print("Message buttons: ")
            for button_lists in message.buttons:
                for button in button_lists:
                    print(button.url, button.text)
                    if button.url and '' in button.url and self._lastAutoEnter < utc.localize(
                            datetime.datetime.utcnow()):
                        params = re.sub('.*start=', '', button.url)
                        request = StartBotRequest("MEVFreePortalBot", "MEVFreePortalBot",
                                                  params)
                        await self._client(request)
                        await self._client.send_message('MEVFreePortalBot', re.sub('is currently.*', '',
                                                                           message.message))
                        self.lastPreVerify = utc.localize(
                            datetime.datetime.utcnow() + datetime.timedelta(seconds=15))
                        return [params, group]
        return False

    async def on_bot_message(self, event, client, telegram_bot, operations, groups):
        # CalsiBot
        print("Portal Bot Message")
        telegram = False
        if 'Authentication' in event.message.text:
            print("MEVFree Guardian")
            # print("Message buttons: ")
            for button_lists in event.message.buttons:
                for button in button_lists:
                    if 'https://' in button.url:
                        webbrowser.open(button.url, new=0, autoraise=True)
        if 'Verification successful' in event.message.text:
            print("MEVFree Guardian")
            # print("Message buttons: ")
            for button_lists in event.message.buttons:
                for button in button_lists:
                    if 't.me' in button.url:
                        telegram = re.findall(r't.me/\+([a-zA-Z0-9-_]+)', button.url)


        if 't.me' in event.message.text:
            print("Captcha solved.")
            print("Link provided by: " + telegram_bot.last_group[0]['title'])
            telegram = re.findall(r't.me/\+([a-zA-Z0-9-_]+)', event.message.message)

        decision = False
        if telegram and telegram_bot.blockchain.network == 'BSC':
            telegram = telegram[0]
            print(telegram)
            try:
                updates = await client(ImportChatInviteRequest(telegram))
                utc = pytz.UTC
                yesterday = utc.localize(datetime.datetime.utcnow() - datetime.timedelta(days=1))
                telegram_bot.contract_cache = {}
                async for message_sub in client.iter_messages(updates.updates[1].channel_id,
                                                              reverse=True, limit=150):
                    message_new = yesterday < message_sub.date
                    if message_sub.message is not None and message_new:
                        print("Message read: ", message_sub.id, message_sub.text[0:20] + '...')

                        print("Is message new: ", message_new, yesterday, message_sub.date)
                        print(message_sub.message)
                        contract = operations.analyse_message(message_sub.message)
                        if contract:
                            decision = await telegram_bot.buy_decision(contract, telegram_bot.last_group,
                                                                       groups,
                                                                       telegram_bot.last_group[0]['id'])
                            if decision['buy']:
                                break
                telegram_bot.connection.response('message', {
                    'data': 'CalsiHack automatically entered a group from this active buy groups',
                    'message_content': 'This is an auto-generated pseudo message.',
                    'title': telegram_bot.last_group[0]['title'] + ' > ' + updates.chats[0].title,
                    'decision': decision}, True)

            except InviteHashExpiredError:
                print("Telegram Hash Expired Invalid")
            except FloodWaitError:
                print("Telegram Flood Error")
            except UserAlreadyParticipantError:
                print("User already participant")
