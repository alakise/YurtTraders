import asyncio
import json
import re
import threading
from os import read
from sqlite3 import OperationalError
from subprocess import check_output, CalledProcessError

import requests
import telethon.errors
from flask_socketio import emit
from telegram.constants import ParseMode
from telethon import TelegramClient, events
from telethon.errors import InviteHashExpiredError, FloodWaitError
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerChat
from urllib3.exceptions import NewConnectionError
from web3 import Web3

from bot_relations import BotRelations
from bsc_blockchain import BSCBlockchain
from operations import Operations
from user import User
import datetime, pytz
from telethon.tl.functions.messages import ImportChatInviteRequest
import os
from dotenv import load_dotenv

load_dotenv()
lock = threading.Lock()

def fire_and_forget(coro):
    """
    Run an asynchronous function in a new event loop on a separate thread.
    """
    _loop = asyncio.new_event_loop()
    threading.Thread(target=_loop.run_forever, daemon=True).start()
    _loop.call_soon_threadsafe(asyncio.create_task, coro)

class TelegramBot:
    """
    A class to handle interactions with Telegram using the Telethon library.
    """
    __api_id: int = int(os.getenv('TELEGRAM_API_ID'))
    __api_hash: str = os.getenv('TELEGRAM_API_HASH')
    me = None
    blockchain: BSCBlockchain
    client: TelegramClient

    not_important = [
        "announcement", "whitelist", "presale", 'vc is open', 'vc open', 'opening vc',
        'opening the vc', 'we will be having an ama', '0 spots', 'join vc', 'from the call',
        'from call', 'on the hunt', 'buyer position', 'VC time', 'recap', 'wl spot', 'wl spots',
        'shill me your gems', 'fucking sticker'
    ]

    def __init__(self, user: User, blockchain: BSCBlockchain, loop, connection):
        self.loop = loop
        self.user: User = user
        self.connection = connection
        self.blockchain: BSCBlockchain = blockchain
        self.known_contracts = []
        utc = pytz.UTC

        # Variables
        self.last_message = ""
        self.last_group = None
        self.last_params = None
        self.contract_cache = {}

    def get_telegram_user(self):
        """
        Retrieve the Telegram user details and emit the response.
        """
        me_array = {
            'username': self.me.username,
            'firstname': self.me.first_name,
        }
        emit('telegram_connect_response', {
            'success': True,
            'data': f'Telegram account connected: <b>@{me_array["username"]}</b>',
            'me': me_array
        })
        return True

    async def listen(self):
        """
        Listen for incoming Telegram messages and handle them.
        """
        # Save Session
        try:
            with open('sessions/' + self.user.config['phone_number'] + '.txt', 'r') as f:
                session = f.read()
        except FileNotFoundError:
            session = None

        client = TelegramClient(
            StringSession(session), self.__api_id, self.__api_hash,
            timeout=10, request_retries=20, connection_retries=60,
            retry_delay=10, loop=self.loop
        )
        self.client = client
        await client.start(phone=self.user.config['phone_number'])
        with open('sessions/' + self.user.config['phone_number'] + '.txt', 'w') as f:
            f.write(client.session.save())

        me = await client.get_me()
        self.me = me
        self.get_telegram_user()

        # Get user data
        user_data = self.user.config
        listen = user_data['telegram']['listen']
        whitelist = user_data['telegram']['whitelist']
        blacklist = user_data['telegram']['blacklist']
        operations = Operations(self.blockchain)

        groups = await self.__get_groups(self.client, listen)

        for callback, event in self.client.list_event_handlers():
            self.client.remove_event_handler(callback)

        group_list = list(groups.keys())
        bot_relations = BotRelations(client, self, operations, groups)

        @self.client.on(events.NewMessage(chats=group_list))
        @self.client.on(events.MessageEdited(chats=group_list))
        async def _(event):
            await self.on_message(event, bot_relations, groups, operations, whitelist, blacklist, client, me)

        try:
            await self.client.run_until_disconnected()
        except OperationalError:
            print("Database error, nothing important")

    async def on_message(self, event, bot_relations, groups, operations, whitelist, blacklist, client, me):
        """
        Handle incoming Telegram messages and take appropriate actions.
        """
        self.contract_cache = {}
        utc = pytz.UTC
        two_minutes = utc.localize(datetime.datetime.utcnow() - datetime.timedelta(seconds=25))
        message_new = two_minutes < event.message.date
        if not message_new:
            return False
        if self.last_message == event.message.message + str(event.message.id):
            return False
        self.last_message = event.message.message + str(event.message.id)
        emitter = ""
        important = False
        stop = False
        decision = False
        buy_made = False
        chat_id = getattr(event.peer_id, 'chat_id', None)
        if chat_id is None:
            chat_id = getattr(event.peer_id, 'channel_id', None)
        if chat_id is None:
            chat_id = getattr(event.peer_id, 'user_id', None)

        group = groups[chat_id]

        bot_names = {
            259643624: 'CalsiBot', 609517172: 'RoseBot', 771096498: 'Shieldy',
            210944655: 'Combot', 5135991425: 'Portal Keeper'
        }
        bot_list = [259643624, 609517172, 771096498, 210944655, 5135991425]
        bot_sender = False
        if event.message.from_id is not None and event.message.from_id.user_id in bot_list:
            bot_sender = True

        important_message = ""
        special_group = [1599711149, 1384778739, 759517080, 1729296266]
        event.message.message = self.__xor(event.message.message)
        event.message.message = operations.morse_alphabet(event.message.message)
        event.message.message = self.decrypt(event.message.message)

        if group[0]['alarm'] and not bot_sender:
            important_message += f"NEW MESSAGE FROM {group[0]['title']}\n"
            important_message += "🟢 Probably IMPORTANT\n"
            if not any(word in event.message.message.lower() for word in self.not_important):
                self.connection.response('important_alarm', {'data': 'wakeup'})
            important_message += f"MESSAGE:\n{event.message.message}\n"

        if self.__check_keyword(group, event.message.message, whitelist, blacklist) and not bot_sender:
            contract = operations.analyse_message(event.message.message)
            if not contract:
                contract = operations.analyse_message(event.message.message)
            if contract and not group[0]['portal']:
                decision = await self.buy_decision(contract, group, groups, chat_id)
                if decision['buy']:
                    buy_made = True
            else:
                if group[0]['portal']:
                    emitter += "Portal mode on, bot will only process portal containing messages in this group<br>"
                else:
                    emitter += "No contract found looking for channel links<br>"

                # Message date check variables
                utc = pytz.UTC
                yesterday = utc.localize(datetime.datetime.utcnow() - datetime.timedelta(days=1))

                tg_link = self.__search_tg_link(event.message.message)
                # Public Telegram link check
                if tg_link:
                    # From oldest to most-recent
                    message_counter = 0
                    last_ca = ""
                    contract_counter = 0
                    try:
                        async for message in client.iter_messages(tg_link, reverse=True, limit=200):
                            print(f'Message read https://t.me/c/{chat_id}/{message.id}')
                            message_counter += 1
                            message_new = yesterday < message.date
                            if not message_new:
                                print("Message is old")
                                pass
                            if message.message is not None and message_new and not group[0]['portal']:
                                contract = operations.analyse_message(message.message)
                                if contract:
                                    if last_ca == contract:
                                        contract_counter += 1
                                    else:
                                        contract_counter = 0
                                    last_ca = contract

                                    decision = await self.buy_decision(contract, group, groups, chat_id)
                                    if decision['buy']:
                                        buy_made = True
                                        break
                            # PreVerify - auto start
                            # ----------------------
                            if message.message is not None and message_counter < 15 and self.blockchain.network == 'BSC':
                                portal = await bot_relations.scanCaptcha(message, group)
                                if portal:
                                    self.last_params, self.last_group = portal

                            if not stop and message_counter < 15 and message.message is not None and message_new and not \
                                    group[0]['portal'] and self.blockchain.network == 'BSC':
                                telegram = re.findall(r't.me/\+([a-zA-Z0-9-_]+)', message.message)
                                if telegram:
                                    telegram = telegram[0]
                                    print("Telegram invite detected: ", telegram)
                                    try:
                                        updates = await client(ImportChatInviteRequest(telegram))
                                        stop = True
                                        messages_sub = await client.get_messages(updates.updates[1].channel_id, reverse=True, limit=50)
                                        for message_sub in messages_sub:
                                            print(message_sub.id, message_sub.text)
                                            message_new = yesterday < message_sub.date
                                            print("Is message new: ", message_new, yesterday, message_sub.date)
                                            if message_sub.message is not None and message_new:
                                                print(message_sub.message)
                                                contract = operations.analyse_message(message_sub.message)
                                                if contract:
                                                    decision = await self.buy_decision(contract, group, groups, chat_id)
                                                    if decision['buy']:
                                                        buy_made = True
                                                        break
                                    except InviteHashExpiredError:
                                        print("Telegram Hash Expired Invalid")
                                    except FloodWaitError:
                                        print("Telegram Flood Error")
                            elif stop:
                                break
                    except ValueError:
                        pass
                # Private Telegram link check
                telegram = re.findall(r't.me/\+([a-zA-Z0-9-_]+)', event.message.message)
                if telegram and not buy_made and not group[0]['portal']:
                    telegram = telegram[0]
                    print("Telegram invite detected: ", telegram)
                    try:
                        updates = await client(ImportChatInviteRequest(telegram))
                        stop = True
                        messages_sub = await client.get_messages(updates.updates[1].channel_id, reverse=True, limit=50)
                        for message_sub in messages_sub:
                            print(message_sub.id, message_sub.text)
                            message_new = yesterday < message_sub.date
                            print("Is message new: ", message_new, yesterday, message_sub.date)
                            if message_sub.message is not None and message_new:
                                print(message_sub.message)
                                contract = operations.analyse_message(message_sub.message)
                                if contract:
                                    decision = await self.buy_decision(contract, group, groups, chat_id)
                                    if decision['buy']:
                                        buy_made = True
                    except InviteHashExpiredError:
                        print("Telegram Hash Expired Invalid")
                    except FloodWaitError:
                        print("Telegram Flood Error")
                    except telethon.errors.AlreadyInConversationError:
                        print("Already in private group")

        else:
            emitter += "Keyword match failed."

        if self.__check_blacklist(group, event.message.message, blacklist) and event.message.media and not stop and not bot_sender:
            if event.message.file:
                size = event.message.file.size
                emitter += f' File found. Size: {size} bytes.<br>'
                if size < 500:
                    file_path = await client.download_media(event.message)
                    if file_path:
                        emitter += f' File saved to "{file_path}"'
                        with open(file_path, "r") as f:
                            file_content = f.read()
                        contract = operations.analyse_message(file_content)
                        if contract:
                            decision = await self.buy_decision(contract, group, groups, chat_id)
                    else:
                        emitter += ' Error while downloading media.'
                elif not event.photo:
                    event.message.message += " The guy probably sent a sticker"
            else:
                emitter += " Media is not a file (poll etc.)"
        elif not buy_made:
            emitter += "<br>No file found."

        if bot_sender:
            emitter = f"Message sender is a known bot: <b>{bot_names[event.message.from_id.user_id]}</b>"

        self.connection.response('message', {
            'data': emitter,
            'message_content': event.message.message,
            'title': group[0]['title'],
            'decision': decision
        }, True)

    @staticmethod
    def decrypt(decryption_input):
        """
        Decrypts a given string if it contains an online-toolz URL.
        """
        if 'online-toolz' in decryption_input:
            def find_longest_word(word_list):
                longest_word = max(word_list.replace('\n', ' ').replace('www.online-toolz.com', ' ').split(' '), key=len)
                return longest_word

            def has_numbers(input_string):
                return any(char.isdigit() for char in input_string)

            if has_numbers(find_longest_word(decryption_input)):
                url = 'https://www.online-toolz.com/functions/DECRYPT.php'
                myobj = {'input': find_longest_word(decryption_input)}
                x = requests.post(url, data=myobj)
                return decryption_input + " \nSymmetrical encryption result: " + x.text
            else:
                return decryption_input
        else:
            return decryption_input

    async def buy_decision(self, contract: str, group: dict, groups, chat_id) -> dict:
        """
        Makes a buy decision based on the contract, group, and market cap.
        
        Args:
            contract (str): The contract address.
            group (dict): The group data.
            groups (dict): All group data.
            chat_id (int): The chat ID.

        Returns:
            dict: A dictionary containing the decision to buy and additional info.
        """
        emitter = ""
        safe_to_buy = True
        if contract in self.contract_cache:
            return self.contract_cache[contract]
        if group[0]['single'] is True and (group[0]['buys'] > 0):
            safe_to_buy = False
            emitter += "Single contract buy ordered, not proceeding to buy.<br>"
            return {'buy': safe_to_buy, 'info': emitter, 'contract': contract}

        market_cap = self.blockchain.get_mcap(Web3.to_checksum_address(contract))
        if isinstance(market_cap, str):
            get_token_from_lp = self.blockchain.get_token_from_lp(Web3.to_checksum_address(contract))
            if get_token_from_lp:
                contract = get_token_from_lp
                market_cap = self.blockchain.get_mcap(Web3.to_checksum_address(contract))
        buy_strategy = False
        if isinstance(market_cap, str):
            safe_to_buy = False
            emitter += market_cap
        else:
            emitter += f'Pair size: {round(market_cap["LP_size"], 2)}.<br>Market cap calculated: {int(market_cap["market_cap"])}$<br>'
            for el in group:
                if el['mcap'] > int(market_cap["market_cap"]):
                    safe_to_buy = True
                    buy_strategy = el
                    emitter += f"Buy strategy market cap MATCHES: {el['mcap']}$<br>"
                    break
                else:
                    emitter += f"Buy strategy market cap exceeded: {el['mcap']}$<br>"
            else:
                safe_to_buy = False

            if safe_to_buy and group[0]['1p']:
                one_percent = float(market_cap['market_cap']) / self.blockchain.coin_price / 100
                emitter += f"1% buy = {one_percent}"
                if one_percent < float(buy_strategy['amount']):
                    group[0]['amount'] = one_percent
                    buy_strategy = group[0]
            if safe_to_buy and group[0]['quarterp']:
                one_percent = float(market_cap['market_cap']) / self.blockchain.coin_price / 400
                emitter += f"0.25% buy = {one_percent}"
                if one_percent < float(buy_strategy['amount']):
                    group[0]['amount'] = one_percent
                    buy_strategy = group[0]

        if group[0]['honeypot_check']:
            honeypot = self.honeypot_check(contract)
            if honeypot[0]:
                safe_to_buy = False
            emitter += f"{honeypot[1]}<br>"

        if safe_to_buy:
            groups[chat_id][0]['buys'] += 1
            await self.buy_order(contract, buy_strategy)
        self.contract_cache[contract] = {'buy': safe_to_buy, 'info': emitter, 'contract': contract}
        return {'buy': safe_to_buy, 'info': emitter, 'contract': contract}

    def moonarch_result(self, token):
        """
        Fetches and returns Moonarch results for a given token.
        
        Args:
            token (str): The token name.

        Returns:
            str: The Moonarch results for the token.
        """
        token = token.lower().replace('bsc', '').replace('portal', '').strip()
        token = ' '.join(token.split()[:2])
        url1 = f'https://api.moonarch.app/1.0/tokens/BSC/search/{token}'
        url2 = f'https://api.moonarch.app/1.0/tokens/BSC/search/{token.replace(" ", "")}' if ' ' in token else False

        def pretty_date(time=False):
            """
            Get a datetime object or an int() Epoch timestamp and return a pretty string like 'an hour ago', 'Yesterday', etc.
            """
            from datetime import datetime
            now = datetime.now()
            if isinstance(time, int):
                diff = now - datetime.fromtimestamp(time)
            elif isinstance(time, datetime):
                diff = now - time
            elif not time:
                diff = 0
            second_diff = diff.seconds
            day_diff = diff.days

            if day_diff < 0:
                return ''

            if day_diff == 0:
                if second_diff < 10:
                    return "just now"
                if second_diff < 60:
                    return f"{second_diff} seconds ago"
                if second_diff < 120:
                    return "a minute ago"
                if second_diff < 3600:
                    return f"{second_diff // 60} minutes ago"
                if second_diff < 7200:
                    return "an hour ago"
                if second_diff < 86400:
                    return f"{second_diff // 3600} hours ago"
            if day_diff == 1:
                return "Yesterday"
            if day_diff < 7:
                return f"{day_diff} days ago"
            if day_diff < 31:
                return f"{day_diff // 7} weeks ago"
            if day_diff < 365:
                return f"{day_diff // 30} months ago"
            return f"{day_diff // 365} years ago"

        try:
            resp = requests.get(url=url1)
            if url2:
                resp2 = requests.get(url=url2)
        except (NewConnectionError, ConnectionError):
            return False
        data = resp.json()
        if url2:
            data.extend(resp2.json())
        message_text = ""
        for token in data:
            message_text += f'{token["name"]} ${token["name"]}\nlaunched {pretty_date(token["creationDate"])}\nliquidity: {int(token["liq"]) / 10 ** 18}\nAddress: <code>{token["address"]}</code>\n----------------------'
        return message_text

    async def buy_order(self, contract: str, group: dict):
        """
        Executes a buy order for a specified contract and group.
        
        Args:
            contract (str): The contract address.
            group (dict): The group data.
        """
        loops = []
        loop_counter = 0
        wallet_counter = 0
        if group['multi']:
            for _ in range(group['repeat'] * len(self.blockchain.wallets)):
                loop = asyncio.new_event_loop()
                threading.Thread(target=loop.run_forever, daemon=True).start()
                loops.append(loop)
            for wallet in self.blockchain.wallets:
                i = wallet.nonce
                if group['wallets'] is not False and wallet_counter == group['wallets']:
                    break
                for _ in range(group['repeat']):
                    loops[loop_counter].call_soon_threadsafe(
                        asyncio.create_task, self.blockchain.buy(wallet, group['amount'], contract, i)
                    )
                    i += 1
                    loop_counter += 1
                wallet_counter += 1
        else:
            for _ in range(group['repeat']):
                loop = asyncio.new_event_loop()
                threading.Thread(target=loop.run_forever, daemon=True).start()
                loops.append(loop)
            i = self.blockchain.wallets[0].nonce
            for _ in range(group['repeat']):
                loops[loop_counter].call_soon_threadsafe(
                    asyncio.create_task, self.blockchain.buy(self.blockchain.wallets[0], group['amount'], contract, i)
                )
                loop_counter += 1
                i += 1
        self.connection.edi.token_interaction(contract)
        emit('nuke_response', {'data': "nuked"})

    @staticmethod
    def __search_tg_link(message: str):
        """
        Searches for a Telegram link in a given message.
        
        Args:
            message (str): The message to search.

        Returns:
            str: The Telegram link if found, else False.
        """
        x = re.search(r"@[A-Za-z0-9_]+|t\.me/[+\-A-Za-z0-9_]+", message)
        if x is None:
            return False
        else:
            print(x.group(0))
            return x.group(0)

    @staticmethod
    def __xor(data):
        """
        Performs XOR decryption on a given data string.
        
        Args:
            data (str): The data to decrypt.

        Returns:
            str: The decrypted data.
        """
        if "franklin.edu" in data:
            x = re.search(r"(?:[0-9]{1,3},){5,500}[0-9]{1,3}", data)
            if x is None:
                return ""
            encrypted = x.group(0)
            data.replace("http://cs.franklin.edu/~whittakt/ITEC136/examples/encrypter.html", '')
            encrypted = list(map(int, encrypted.split(',')))
            encrypted = bytearray(encrypted)

            keys = re.findall(r'[a-zA-Z0-9]+', data)
            for key in keys:
                key = bytes(key * 50, encoding='utf8')
                result = bytearray(a ^ b for a, b in zip(encrypted, key))
                if re.search(r"^(?:@[a-zA-Z0-9_+-]+)|(?:0x[a-fA-F0-9]{40})|(?:http)", str(result)):
                    return data + ' \nXOR result: ' + str(result)
            return data
        else:
            return data

    @staticmethod
    def __check_blacklist(group: dict, message: str, blacklist) -> bool:
        """
        Checks if a message contains any blacklisted words.
        
        Args:
            group (dict): The group data.
            message (str): The message to check.
            blacklist (str): The blacklist to check against.

        Returns:
            bool: True if the message does not contain blacklisted words, else False.
        """
        if group[0]['any']:
            return True
        blacklist = list(map(str.strip, blacklist.split(',')))
        if any(word in message.lower() for word in blacklist):
            return False
        return True

    @staticmethod
    def __check_keyword(group: dict, message: str, whitelist, blacklist) -> bool:
        """
        Checks if a message contains any whitelisted words and does not contain blacklisted words.
        
        Args:
            group (dict): The group data.
            message (str): The message to check.
            whitelist (str): The whitelist to check against.
            blacklist (str): The blacklist to check against.

        Returns:
            bool: True if the message contains whitelisted words and does not contain blacklisted words, else False.
        """
        if group[0]['any']:
            return True
        whitelist = list(map(str.strip, whitelist.split(',')))
        blacklist = list(map(str.strip, blacklist.split(',')))
        if any(word in message.lower() for word in blacklist):
            return False
        elif any(word in message.lower() for word in whitelist):
            return True
        return False

    async def get_dialogues(self):
        """
        Retrieves the list of dialogues (chats) from Telegram.
        
        Returns:
            dict: A dictionary of dialogues with their IDs and names.
        """
        print("Dialogue list received.")
        dialogues = {}
        dialogues_ui = []
        for dialog in await self.client.get_dialogs():
            dialogues[abs(dialog.id)] = dialog.name
            dialogues_ui.append({'id': dialog.id, 'name': dialog.name})
        emit("dialogues", {'dialogues': dialogues_ui})
        return dialogues

    @staticmethod
    def honeypot_check(address):
        """
        Checks if a given token address is a honeypot.
        
        Args:
            address (str): The token address.

        Returns:
            list: A list containing the honeypot status, interpretation, and status code.
        """
        honeypot_url = f'https://honeypot.api.rugdoc.io/api/honeypotStatus.js?address={address}&chain=bsc'
        interpretations = {
            "UNKNOWN": "The status of this token is unknown. This is usually a system error but could also be a bad sign for the token. Be careful.",
            "OK": " √ Honeypot tests passed. Our program was able to buy and sell it successfully. This however does not guarantee that it is not a honeypot.",
            "NO_PAIRS": "⚠ Could not find any trading pair for this token on the default router and could thus not test it.",
            "SEVERE_FEE": "⚠ A severely high trading fee (over 50%) was detected when selling or buying this token.",
            "HIGH_FEE": "⚠ A high trading fee (Between 20% and 50%) was detected when selling or buying this token. Our system was however able to sell the token again.",
            "MEDIUM_FEE": "⚠ A trading fee of over 10% but less than 20% was detected when selling or buying this token. Our system was however able to sell the token again.",
            "APPROVE_FAILED": "🚨 Failed to approve the token. This is very likely a honeypot.",
            "SWAP_FAILED": "🚨 Failed to sell the token. This is very likely a honeypot."
        }
        response = requests.get(honeypot_url)
        d = json.loads(response.content)
        honeypot_status = interpretations['UNKNOWN']
        for key, value in interpretations.items():
            if d["status"] in key:
                honeypot_status = value
        if d["status"] in ['SEVERE_FEE', 'NO_PAIRS', 'APPROVE_FAILED', 'SWAP_FAILED']:
            return [True, honeypot_status, d['status']]
        else:
            return [False, honeypot_status, d['status']]

    async def __get_groups(self, client: TelegramClient, listen: str) -> dict:
        """
        Retrieves the groups to listen to based on the user's configuration.
        
        Args:
            client (TelegramClient): The Telegram client.
            listen (str): The list of groups to listen to.

        Returns:
            dict: A dictionary of groups with their configurations.
        """
        listen = listen.strip().split(',')
        groups = {}
        dialogues = await self.get_dialogues()
        for listen_obj in listen:
            buy_repeat = 1
            buy_amount = 0

            sub_listen = listen_obj.split('*')
            sub_channel = sub_listen[0]
            sub_listen.pop(0)

            multi = any('multi' in s for s in sub_listen)
            alarm = any('alarm' in s for s in sub_listen)
            buy_any = any('any' in s for s in sub_listen)
            max_tx = any('max' in s for s in sub_listen)
            single = any('single' in s for s in sub_listen)
            honeypot_check = any('honeypot' in s for s in sub_listen)
            one_percent = any('1p' in s for s in sub_listen)
            quarter_percent = any('quarterp' in s for s in sub_listen)
            portal = any('portal' in s for s in sub_listen)

            mcap = 10 ** 12
            for s in sub_listen:
                if 'mcap' in s:
                    mcap = float(s.split('=')[1])

            wallets = False
            for s in sub_listen:
                if 'wallets' in s:
                    wallets = float(s.split('=')[1])

            if len(sub_listen) > 0:
                buy_plan = sub_listen[0].split('x')
                if len(buy_plan) > 1:
                    buy_repeat = buy_plan[0]
                    buy_amount = buy_plan[1]
                else:
                    buy_amount = buy_plan[0]

            if sub_channel:
                if re.match(r'^\+?-?[0-9]+$', sub_channel):
                    chat_id = abs(int(sub_channel))
                else:
                    entity = await client.get_input_entity(sub_channel)
                    chat_id = getattr(entity, 'chat_id', None)
                    if chat_id is None:
                        chat_id = getattr(entity, 'channel_id', None)
                    if chat_id is None:
                        chat_id = getattr(entity, 'user_id', None)
                title = dialogues.get(chat_id, 'Unknown Chat')
                if int('100' + str(chat_id)) in dialogues:
                    title = dialogues[int('100' + str(chat_id))]
                if chat_id in groups:
                    groups[chat_id].append({
                        'id': chat_id,
                        'title': title,
                        'amount': float(buy_amount),
                        'repeat': int(buy_repeat),
                        'multi': multi,
                        'any': buy_any,
                        'max_tx': max_tx,
                        'single': single,
                        'buys': 0,
                        'mcap': int(mcap),
                        'wallets': wallets,
                        'honeypot_check': honeypot_check,
                        'alarm': alarm,
                        '1p': one_percent,
                        'quarterp': quarter_percent,
                        'portal': portal
                    })
                    groups[chat_id] = sorted(groups[chat_id], key=lambda i: (i['mcap'], i['mcap']))
                else:
                    groups[chat_id] = [{
                        'id': chat_id,
                        'title': title,
                        'amount': float(buy_amount),
                        'repeat': int(buy_repeat),
                        'multi': multi,
                        'any': buy_any,
                        'max_tx': max_tx,
                        'single': single,
                        'buys': 0,
                        'mcap': int(mcap),
                        'wallets': wallets,
                        'honeypot_check': honeypot_check,
                        'alarm': alarm,
                        '1p': one_percent,
                        'quarterp': quarter_percent,
                        'portal': portal
                    }]
            else:
                pass

        return groups
