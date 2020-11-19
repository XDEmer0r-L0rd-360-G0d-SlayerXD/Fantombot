# FantomBot.py

import discord
import requests
import asyncio
import time
import os
import sys
import subprocess
import shutil
import string

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
style.use("fivethirtyeight")

# I haven't added you because it would give you control of f!UPDATE and idk if you want that
# Has permission to use UPDATE and PULL commands
bot_owners = (532751332445257729,)
# Can do almost anything
bot_admins = (532751332445257729, 234168704181600258)

prefix = "f!"

# Fix dir
os.chdir(r"C:\Users\claym\AppData\Local\Programs\Python\Python37")

# Load token
with open('token', 'r') as f:
    token = str(f.read())

# ensure there is a data folder to store things
if not os.path.isdir('bot_data'):
    os.mkdir('bot_data')


def convert(fUSD: int = None, wFTM: int = None) -> float:
    """
    Gets its data via https://funi.exchange/#/swap/
    Convert only between fUSD and wFTM.
    """
    conversion_val = .000000000000000001
    wftm_token = "0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83"
    fusd_token = "0xad84341756bf337f5a0164515b1f6f993d194e1f"

    if fUSD:
        body = {"operationName": "GetUniswapAmountsOut", "variables": {"amountIn": str(hex(int(fUSD//conversion_val))), "tokens": [
            fusd_token, wftm_token]},
                "query": "query GetUniswapAmountsOut($amountIn: BigInt!, $tokens: [Address!]!) {\n  defiUniswapAmountsOut(amountIn: $amountIn, tokens: $tokens)\n}\n"}
    elif wFTM:
        body = {"operationName": "GetUniswapAmountsOut", "variables": {"amountIn": str(hex(int(wFTM//conversion_val))), "tokens": [
            wftm_token, fusd_token]},
                "query": "query GetUniswapAmountsOut($amountIn: BigInt!, $tokens: [Address!]!) {\n  defiUniswapAmountsOut(amountIn: $amountIn, tokens: $tokens)\n}\n"}
    else:
        raise ValueError('No conversion done.')
    url = 'https://xapi2.fantom.network/api'
    response = requests.post(url=url, json=body).json()
    val = response['data']['defiUniswapAmountsOut'][1]
    return int(val, 16) * conversion_val


def restart():
    print("Restarting.")
    subprocess.call(sys.executable + ' "' + os.path.realpath(__file__) + '"')
    # In theory the code never reaches this section but I felt like it should force close if it did
    quit()


def only_digits(test: str) -> bool:
    return not any([a not in string.digits for a in test])


async def dm(user_id: int, text: str):
    """
    A very simple dm wrapper for modularity
    """
    user = client.get_user(user_id)
    await user.send(text)


async def anondm(msg_args, base_channel, base_author):
    # log attempt
    with open('./bot_data/anon_dm_log.txt', 'a') as f:
        f.write(f'{base_author.id}({time.strftime("%Y%m%d-%H%M%S")}): {msg_args}')
    split = msg_args.split(' ')
    # makes sure it is long enough and then tests to ensure all id parts are digits
    if len(msg_args.split(' ')) < 2 or not only_digits(msg_args.split(' ')[0]):
        await base_channel.send("Poorly formatted. [command] [user id] [message]")
        return
    split[1] = " ".join(split[1:])
    await dm(int(split[0]), "Anon says:\n" + split[1].strip())
    return


client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    """
    Massive message parser to try to do things
    """
    # extra layer of variables to ensure I get to keep a pattern without accidentally breaking something
    msg_content = message.content
    msg_author = message.author
    msg_channel = message.channel

    # If bot message or has no prefix, ignore
    if message.author == client.user or len(msg_content) < len(prefix) or msg_content[:len(prefix)] != prefix:
        return

    # remove prefix, get command, and args(as a single string)
    # todo may need to remove this typing
    msg_command: str = msg_content[len(prefix):].split(' ')[0]
    temp = msg_content.split(' ')
    if len(temp) > 1:
        msg_args: str = ' '.join(temp[1:])
    else:
        # I may want to set this default to None or something else
        msg_args: str = ""

    if "" == msg_command:
        await msg_channel.send("No Command")

    elif "kill" == msg_command.lower() and msg_author.id in bot_admins:
        await client.close()

    elif 'ping' == msg_command.lower():
        await message.channel.send("Pong!")

    elif "anondm" in msg_command.lower():
        # this has been moved to a func for sandboxing of vars
        await anondm(msg_args, msg_channel, msg_author)

    elif "RESTART" == msg_command:
        # I felt that anyone should be allow to do this, but don't mind setting it to admin only
        await msg_channel.send("Restarting.")
        restart()

    elif "UPDATE" == msg_command and msg_author.id in bot_owners:
        # this timestamps the decommission of previous versions
        if "raw" not in msg_args:
            msg_channel.send("Url Issue (no url/missing raw).")
            return
        timestr = time.strftime("%Y%m%d-%H%M%S")
        # check for backup folder
        if not os.path.exists('./bot_data/past_versions'):
            os.mkdir("./bot_data/past_versions")
        # make folder for latest version
        os.mkdir(f"./bot_data/past_versions/{timestr}")
        # copy
        shutil.copy2('FantomBot.py', f"./bot_data/past_versions/{timestr}")
        # dl and overwrite from link
        with open('FantomBot.py', 'wb') as f:
            url = msg_args
            f.write(requests.get(url).content)
        await msg_channel.send("Updating.")
        restart()

    elif "PULL" == msg_command and msg_author.id in bot_owners:
        user = client.get_user(msg_author.id)
        file = discord.File('FantomBot.py', filename="FantomBot.py")
        await user.send("FantomBot.py", file=file)

    elif "wftm" == msg_command.lower():
        if msg_args == "":
            msg_args = "1"
        if only_digits(msg_args):
            price = convert(wFTM=max(0, int(msg_args)))
            await msg_channel.send(f"wFTM: {price}")
        else:
            await msg_channel.send("Bad value.")

    elif "graph" == msg_command.lower():
        # I think your want for time scales would be fixed you generated the graph
        # every time this calledand not by it self automatically.
        file = discord.File("price.png", filename="price.png")
        await msg_channel.send("price.png", file=file)

    else:
        await msg_channel.send("Command not found")


async def price_check_background_task():
    """
    Constantly pulls site data and updates the graph
    """
    await client.wait_until_ready()

    while not client.is_closed():
        price = None
        try:
            price = convert(wFTM=1)
            with open("price.csv", "a") as f:
                f.write(f"{int(time.time())},{price}\n")
            plt.clf()
            df = pd.read_csv("price.csv", names=['time', 'price'])
            # hour:  df = df[-60:]
            # day:   df = df[-1440:]
            # week:  df = df[-10080:]
            # month: df = df[-43200:]
            df['date'] = pd.to_datetime(df['time'], unit='s')
            df.drop("time", 1, inplace=True)
            df.set_index("date", inplace=True)
            df['price'].plot()
            plt.legend()
            plt.subplots_adjust(left=0.15)
            plt.savefig("price.png")
            
            await asyncio.sleep(60)
            
        except Exception as e:
            print(str(e))
            await dm(bot_admins[0], str(e), price,)
            await asyncio.sleep(60)


# regular bot stuff
client.loop.create_task(price_check_background_task())
client.run(token)
