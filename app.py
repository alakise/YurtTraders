import asyncio
import sys
import threading
import webbrowser
import logging
from flask import Flask
from flask_socketio import SocketIO, emit
import requests.exceptions
from web3 import Web3
from bsc_blockchain import fire_and_forget
from connection import Connection

# Flask application setup
app = Flask(__name__, static_folder='static', static_url_path='/')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")
app.test_client()
connection = Connection(app)

# Configure logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.after_request
def after_request(response):
    """
    Set response headers to prevent caching and allow cross-origin requests.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/')
def index():
    """
    Serve the main page.
    """
    return app.send_static_file('index.html')

@socketio.event
def test_event(message):
    emit('test_response', {'data': message['data']})

@socketio.event
def login(message):
    connection.login(message)

@socketio.event
def check_login(message):
    print("YurtTraders Client checked login status...")
    connection.check_login()

@socketio.event
def log_out(message):
    connection.log_out()

@socketio.event
def set_mnemonic(message):
    connection.set_mnemonic(message)

@socketio.event
def refresh_wallet(message):
    try:
        connection.refresh_wallet()
    except requests.exceptions.ConnectionError:
        pass

@socketio.event
def distribute(message):
    print(message)
    fire_and_forget(connection.blockchain.distribute_balance(float(message['amount'])))

@socketio.event
def collect(message):
    print("Collecting to main wallet...")
    fire_and_forget(connection.blockchain.collect_to_main_wallet())

@socketio.event
def transfer(message):
    print("Transferring")
    fire_and_forget(
        connection.blockchain.transfer_bnb(
            connection.blockchain.wallets[0],
            message['receiver'],
            float(message['amount'])
        )
    )

@socketio.event
def single_buy(message):
    fire_and_forget(
        connection.blockchain.buy(
            connection.blockchain.wallets[0],
            message['amount'],
            message['contract']
        )
    )

@socketio.event
def approve(message):
    loops = []
    wallet_counter = 0
    print(message)
    if message['all']:
        for _ in range(len(connection.blockchain.wallets)):
            loop = asyncio.new_event_loop()
            threading.Thread(target=loop.run_forever, daemon=True).start()
            loops.append(loop)
        for wallet in connection.blockchain.wallets:
            loops[wallet_counter].call_soon_threadsafe(
                asyncio.create_task,
                connection.blockchain.approve(
                    wallet,
                    message['contract'],
                    message['check_balance']
                )
            )
            wallet_counter += 1
    else:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            connection.blockchain.approve(
                connection.blockchain.wallets[int(message['wallet'])],
                message['contract'],
                message['check_balance']
            )
        )

@socketio.event
def buy(message):
    print(message)
    loops = []
    loop_counter = 0
    wallet_counter = 0
    for _ in range(int(message['repeat']) * len(connection.blockchain.wallets)):
        loop = asyncio.new_event_loop()
        threading.Thread(target=loop.run_forever, daemon=True).start()
        loops.append(loop)
    for wallet in connection.blockchain.wallets:
        i = wallet.nonce
        if message['wallets'] is not False and wallet_counter == message['wallets']:
            break
        for _ in range(int(message['repeat'])):
            loops[loop_counter].call_soon_threadsafe(
                asyncio.create_task,
                connection.blockchain.buy(wallet, message['amount'], message['contract'], i)
            )
            i += 1
            loop_counter += 1
        wallet_counter += 1

# Telegram related socket events

@socketio.event
def telegram_connect():
    connection.telegram_connect()

@socketio.event
def telegram_disconnect():
    connection.disconnect_telegram()

@socketio.event
def telegram_dialogues():
    print("Telegram dialogue renewal request")
    fire_and_forget(connection.telegram.get_dialogues())

@socketio.event
def sell_gas(message):
    print("Sell gas calculated.")
    fire_and_forget(connection.blockchain.calculate_sell_gas(message['contract']))

@socketio.event
def sell(message):
    if connection.blockchain is not None:
        for wallet in range(message['count']):
            fire_and_forget(connection.blockchain.sell(connection.blockchain.wallets[wallet], message['contract']))
    else:
        emit('test_response', {
            'data': '<span style="color:red">Error: blockchain connection has not established. '
                    'Either you did not wait for the node response or did not set your mnemonic yet.</span>'
        })

@socketio.event
def save_settings(message):
    user_data: dict = connection.user.config
    print(user_data)

    update_wallet = False
    if int(user_data['buy']['wallets']) != int(message['buy']['wallets']) or user_data['active'] != message['active']:
        update_wallet = True

    update_telegram = False
    if (user_data['telegram']['whitelist'] != message['telegram']['whitelist'] or
        user_data['telegram']['blacklist'] != message['telegram']['blacklist'] or
        user_data['telegram']['listen'] != message['telegram']['listen']):
        update_telegram = True

    user_data.update(message)

    connection.user.config = user_data
    connection.user.save()

    if update_wallet:
        connection.blockchain = None
    connection.init_modules()
    if update_telegram and connection.telegram:
        connection.telegram_connect()

@app.before_request
def initialize():
    print("Application reloaded.")

if __name__ == '__main__':
    port = sys.argv[1] if len(sys.argv) > 1 else 3059

    print("\n##########################################################"
          "\n##################### YURTTRADERS V3 #####################"
          "\n################# http://localhost:" + str(port) + " ###################\n")
    print("Work location: ", __file__)
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
