import os
import collections
import random
import re
import errno
from socket import error as socket_error
import discord
import asyncio
import logging.handlers
import wallet
import util


logging.basicConfig(filename='bot.log', level=logging.INFO)

logger = logging.getLogger("bot-main")

AT_BOT = "<@" + os.environ.get('494029842543804416') + ">"

BOT_VERSION = "1"

DEPOSIT_CHECK_JOB = 60.0  # seconds

CMD_HELP = "!help"
CMD_BALANCE = "!balance"
CMD_DEPOSIT = "!deposit"

logger.info("started.")
client = discord.Client()

BotFeature = collections.namedtuple('BotFeature', ['command', 'command_keywords', 'response_templates'])

general_responses = {
    "command_not_found":
        [
            "Type !help for list of commands",
            "Please use Proper Commands - You can find the commands by typing !help"
        ],
    "wallet_down":
        [
            "I can't find my wallet :sweat: :sweat:",
            "Wallet is down ! :astonished:"
        ],
    "new_deposit_unconfirmed":
        [
            "I received a new deposit (%.3f BCARD) :ok_hand: Waiting for 1 more confirmation" +
            " before you can start using the coins. I will let you know when your funds are confirmed.",
            "I got the %.3f BCARD you sent me :ok_hand: Just waiting for a confirmation. " +
            "I'll send you a message when that happens.",
            "Wow ! I got %.3f BCARD from you. Wait a moment so I receive one confirmation. " +
            "I'll tell you when your coins are confirmed."
        ],
    "new_deposit_confirmed":
        [
            "Your deposit (%.3f BCARD) has confirmed ! Coins are now available your wallet.",
            "Deposit (%.3f BCARD) has confirmed :card:"
        ],
    "deposit_confirmed":
        [
            "Your deposit (%.3f BCARD) is now confirmed ! :card:",
            "Confirmed ! %.3f BCARD was added to your account. :card:"
        ]
}


def setup_bot():
    help_feature = BotFeature(command="HELP",
                              command_keywords=["!help", "!man"],
                              response_templates=
                              {"success": [
                                  "BCARD-TipBot v%s - BCARD tip bot for Discord \n" +
                                  "Developed by <@109530829557903360> - feel free to give me feedback \n" +
                                  "\n" +
                                  ":card: You can tag me in a channel or send me a direct message"
                                  " to engage with me. \n\n"
                                  ":card: You can phrase your commands anyway you like, for example"
                                  " '!tip 2 BCARD to @user' and 'i command you to !tip @user an amount of 2' are"
                                  " equal. I'll let you know if I can't find what I'm looking for. \n\n"
                                  "Supported commands are:\n " +
                                  "\n" +
                                  ":card: !help !man \n" +
                                  "Show this message. \n"
                                  "\n" +
                                  ":card: !balance !wallet \n" +
                                  "Tells you how much coins you've got. There are two ways your balance increases: "
                                  "(1) receiving tips and (2) depositing coins. \n" +
                                  "\n" +
                                  ":card: !deposit \n" +
                                  "Gives you an address (with QR code) to transfer your coins, so you can start"
                                  " tipping others. You will receive a message when your transaction is received"
                                  " and confirmed. \n" +
                                  "\n" +
                                  ":card: !send !tip \n" +
                                  ":card: needs: @who, amount \n" +
                                  "Tip other users. You have to tag who you want to tip and tell me the amount. " +
                                  "If the operation is successful, the other users is informed of your action. \n" +
                                  "\n" +
                                  ":card: !withdraw \n" +
                                  ":card: needs: address \n" +
                                  "Withdraw all of your coins to your wallet. You have to supply an " +
                                  "address for this. \n" +
                                  "\n" +
                                  ":card: !top !rank !leaderboard \n" +
                                  "Show who has tipped the most. \n"
                              ]})

    balance_feature = BotFeature(command="BALANCE",
                                 command_keywords=["!balance", "!wallet"],
                                 response_templates=
                                 {"success": [
                                     "Balance: %.3f :card:",
                                     "You've got %.3f BCARD."
                                 ]})

    deposit_feature = BotFeature(command="DEPOSIT",
                                 command_keywords=["!deposit"],
                                 response_templates=
                                 {"success": [
                                     "Send your coins to %s please. I'll send you a message when I " +
                                     "receive your transaction. \n QR: %s",
                                     "Your deposit address is %s I will let you know when I receive your coins." +
                                     " \n QR: %s",
                                     "Great idea :smiley: ! Send your coins to %s and I'll let you know when they " +
                                     "arrive. \n QR: %s",
                                     "Wow :heart_eyes: ! Send your coins to %s and I'll let you know when they " +
                                     "arrive. \n QR: %s"
                                 ]})

    tip_feature = BotFeature(command="TIP",
                             command_keywords=["!send", "!tip"],
                             response_templates=
                             {"success": [
                                 "Tip successful ! Yay ! :blush: ",
                                 ":ok_hand: Tipped !",
                                 "Done."
                             ], "amount_not_found": [
                                 "I couldn't find the amount in your message :cry: ",
                                 "Don't know how much to tip."
                             ], "user_not_found": [
                                 "Don't know who you want to tip. :thinking: ",
                                 "I couldn't find who you want to tip in your message :cry: "
                             ], "insufficient_funds": [
                                 "You don't have enough coins to tip that much! ",
                                 "Insufficient funds! Consider depositing more coins."
                             ], "error": [
                                 "Something went wrong with the tip. Error logged. "
                             ], "tip_received": [
                                 "You were tipped %.3f by <@%s> ! Your account was funded. ",
                                 "%.3f BCARD was tipped to you by <@%s> ! You can tip other users or withdraw your coins."
                             ], "cant_tip_yourself": [
                                 "You can't tip yourself !"
                             ], "cant_tip_bot": [
                                 "You can't tip me !",
                                 "Thanks ... but I can't accept that! "
                             ]})

    withdraw_feature = BotFeature(command="WITHDRAW",
                                  command_keywords=["!withdraw"],
                                  response_templates=
                                  {"success": [
                                      "Transaction complete !",
                                      "Success !"
                                  ], "address_not_found": [
                                      "Please tell me where to send your coins. ",
                                      "What is the recipient address ? I couldn't find it in your message :bangbang: "
                                  ], "error": [
                                      "Something went wrong ! :exclamation: "
                                  ], "threshold": [
                                      "You do not have a minimum of 0.01 BCARD !",
                                      "Minimum withdraw amount is 0.01 BCARD !"
                                  ]})

    top_feature = BotFeature(command="TOP",
                             command_keywords=["!top", "!rank", "!leaderboard"],
                             response_templates=
                             {"header": [
                                 "Tip Leaderboard :point_down:",
                                 "Here is a list of users which gave out most tips:"
                             ], "empty": [
                                 "The leaderboard is empty ! :scream:",
                                 "No tips yet ! why not be the first to tip ? :thinking: "
                             ]})

    # todo
    ask_feature = BotFeature(command="ASK",
                             command_keywords=["!ask", "!demand", "!sendme", "!tipme", "!giveme"],
                             response_templates=
                             {"success": [
                                 "Hmmm"
                             ]})

    return [help_feature, balance_feature, deposit_feature, tip_feature, withdraw_feature, top_feature]


bot_features = setup_bot()

@asyncio.coroutine
#async def handle_message(message):
def handle_message(message):
    features = [f for f in bot_features for c in f.command_keywords if c in message.content]
    if len(features) == 1:
        feat = features[0]

        if feat.command == "HELP":
            post_response(message, feat.response_templates["success"], BOT_VERSION)

        elif feat.command == "BALANCE":
            balance = wallet.get_balance(message.author.id)
            post_response(message, feat.response_templates["success"], balance)

        elif feat.command == "DEPOSIT":
            user_deposit_address = wallet.create_or_fetch_user(message.author.id, message.author.name).wallet_address
            post_response(message, feat.response_templates["success"], user_deposit_address,
                          get_qr_url(user_deposit_address))

        elif feat.command == "WITHDRAW":
            try:
                address = find_address(message.content)
                user = wallet.create_or_fetch_user(message.author.id, message.author.name)
                amount = user.balance
                if amount < 0.01:
                    post_response(message, feat.response_templates["threshold"])
                else:
                    wallet.make_transaction_to_address(user, amount, address)
                    post_response(message, feat.response_templates["success"])
            except util.TipBotException as e:
                if e.error_type == "address_not_found":
                    post_response(message, feat.response_templates["address_not_found"])
                if e.error_type == "error":
                    post_response(message, feat.response_templates["error"])

        elif feat.command == "TIP":
            try:
                amount = find_amount(message.content)
                target_user_id = find_user_id(message.content)
                if target_user_id == message.author.id:
                    post_response(message, feat.response_templates["cant_tip_yourself"])
                elif target_user_id == os.environ.get('BOT_ID'):
                    post_response(message, feat.response_templates["cant_tip_bot"])
                else:
                    #target_user = await client.get_user_info(target_user_id)
					target_user = yield from client.get_user_info(target_user_id)
                    wallet.make_transaction_to_user(message.author.id, amount, target_user.id, target_user.name)
                    try:
                        asyncio.get_event_loop().create_task(
                            post_dm(target_user_id, feat.response_templates["tip_received"], amount, message.author.id))
                    except Exception as e:
                        logger.error('could not send message')
                        logger.exception(e)
                    post_response(message, feat.response_templates["success"])
                    if 1 <= amount <= 5:
                        asyncio.get_event_loop().create_task(react_to_message(message, 1))
                    elif 5 < amount <= 10:
                        asyncio.get_event_loop().create_task(react_to_message(message, 2))
                    elif amount > 10:
                        asyncio.get_event_loop().create_task(react_to_message(message, 3))
                    asyncio.get_event_loop().create_task(react_to_message(message, 1))
            except util.TipBotException as e:
                if e.error_type == "amount_not_found":
                    post_response(message, feat.response_templates["amount_not_found"])
                if e.error_type == "user_not_found":
                    post_response(message, feat.response_templates["user_not_found"])
                if e.error_type == "insufficient_funds":
                    post_response(message, feat.response_templates["insufficient_funds"])
                if e.error_type == "error":
                    post_response(message, feat.response_templates["error"])

        elif feat.command == "TOP":
            top_users = wallet.get_top_users()
            if len(top_users) == 0:
                post_response(message, feat.response_templates["empty"])
            else:
                response = random.choice(feat.response_templates["header"]) + "\n"
                for top_user in top_users:
                    response += '\n %s %.3f XZC tipped by %s' % (util.get_numerical_emoji(top_user['index']),
                                                                 top_user['amount'], top_user['name'])
                    if top_user['index'] == 1:
                        response += ' :clap: :clap: '
                    elif top_user['index'] == 2:
                        response += ' :clap: '
                post_response(message, [response])

    else:
        post_response(message, general_responses["command_not_found"])


def get_qr_url(text):
    return 'https://chart.googleapis.com/chart?cht=qr&chl=%s&chs=180x180&choe=UTF-8&chld=L|2' % text


def find_address(input_text):
    regex = r'\w{25,34}'
    matches = re.findall(regex, input_text, re.IGNORECASE)
    if len(matches) == 1:
        return matches[0].strip()
    else:
        raise util.TipBotException("address_not_found")


def find_amount(input_text):
    regex = r'(?:^|\s)(\d*\.?\d+)(?=$|\s)'
    matches = re.findall(regex, input_text, re.IGNORECASE)
    if len(matches) == 1:
        return float(matches[0].strip())
    else:
        raise util.TipBotException("amount_not_found")


def find_user_id(input_text):
    regex = r'(?:^|\s)<@!?(\w*)>(?=$|\s)'
    matches = re.findall(regex, input_text, re.IGNORECASE)
    if len(matches) == 1:
        return matches[0].strip()
    else:
        raise util.TipBotException("user_not_found")


def post_response(message, response_list, *args):
    response = random.choice(response_list) % tuple(args)
    if not message.channel.is_private:
        response = "<@" + message.author.id + "> " + response
    logger.info("sending response: '%s' to message: %s", response, message.content)
    asyncio.get_event_loop().create_task(client.send_message(message.channel, response))


async def react_to_message(message, level):
    if level == 1:
        #await client.add_reaction(message, '\U0001F44D')   # thumbs up
		yield from client.add_reaction(message, '\U0001F44D')   # thumbs up
    elif level == 2:
        #await client.add_reaction(message, '\U0001F44F')   # clap
		yield from client.add_reaction(message, '\U0001F44F')   # clap
    elif level == 3:
        #await client.add_reaction(message, '\U0001F633')   # flushed
		yield from client.add_reaction(message, '\U0001F633')   # flushed


async def post_dm(user_id, text_list, *args):
    text = random.choice(text_list) % tuple(args)
    logger.info("sending dm: '%s' to user: %s", text, user_id)
    #await client.send_message(await client.get_user_info(user_id), text)
	yield from client.send_message(yield from client.get_user_info(user_id), text)


async def check_for_deposit():
    try:
        #await asyncio.sleep(DEPOSIT_CHECK_JOB)
		yield from asyncio.sleep(DEPOSIT_CHECK_JOB)
        results = wallet.parse_incoming_transactions()
        for result in results:
            #await post_dm(result[0], general_responses[result[1]], result[2])
			yield from post_dm(result[0], general_responses[result[1]], result[2])
        asyncio.get_event_loop().create_task(check_for_deposit())
    except Exception as ex:
        logger.exception(ex)
        asyncio.get_event_loop().create_task(check_for_deposit())


@client.event
async def on_ready():
    logger.info('connected as %s and id %s', client.user.name, client.user.id)
    asyncio.get_event_loop().create_task(check_for_deposit())


@client.event
async def on_message(message):
    if AT_BOT in message.content or (message.channel.is_private and message.author.id != client.user.id):
        try:
            if not message.channel.is_private:
                message.content = message.content.replace(AT_BOT, '', 1)
            #await client.send_typing(message.channel)
			yield from client.send_typing(message.channel)
            #await handle_message(message)
			yield from handle_message(message)
        except socket_error as serr:
            if serr.errno != errno.ECONNREFUSED:
                raise serr
            logger.exception("wallet down !")
            post_response(message, general_responses["wallet_down"])


client.run(os.environ.get("NDk0MDI5ODQyNTQzODA0NDE2.DotlTQ.fS4kaB7cSjBYR_PrwJMh0aZkZRU"))
