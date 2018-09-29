# BCARD-TIP

BCARD-Tip is a Discord tip bot for BCARD.

## Usage

To run the bot you need python 3.4.2+. Dependencies can be installed with `pip`.

```
pip3 install -r requirements.txt
```

Before running the bot set these environment variables:

```
RPC_USER: BCARD wallet's rpc user
RPC_PASSWORD: BCARD wallet's rpc password
BOT_ID: Discord Bot ID
TOKEN: Discord Bot Token
```

Run the bot:

```
python3 bot.py
```

## Requirements

- Python 3.4.2+
- BCARD wallet with RPC enabled
- `discord` library
- `peewee` library
- `python-bitcoinrpc` library
