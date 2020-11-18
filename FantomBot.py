# FantomBot.py

import discord
import requests
import asyncio
import time
import os
import sys
import subprocess
import shutil

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
style.use("fivethirtyeight")

conversion_val = .000000000000000001
wftm_token = "0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83"
fusd_token = "0xad84341756bf337f5a0164515b1f6f993d194e1f"

with open('token', 'r') as f:
    token = str(f.read())


def convert(fUSD: int = None, wFTM: int = None) -> float:
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
    # print(response)
    val = response['data']['defiUniswapAmountsOut'][1]
    return int(val, 16) * conversion_val


def restart():
    print("Restarting.")
    subprocess.call(sys.executable + ' "' + os.path.realpath(__file__) + '"')
    quit()


client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    elif "f!kill" == message.content.lower():
        await client.close()
    elif "f!ping" == message.content.lower():
        await message.channel.send("Pong!")
    elif "f!RESTART" == message.content:
        message.channel.send("Restarting.")
        restart()
    elif "f!UPDATE" == message.content.split(' ')[0] and message.author.id == 532751332445257729:
        # this timestamps the decommission of previous versions
        timestr = time.strftime("%Y%m%d-%H%M%S")
        # check for backup folder
        if not os.path.exists('./past_versions'):
            os.mkdir("./past_versions")
        # make folder for latest version
        os.mkdir(f"./past_versions/{timestr}")
        # copy
        shutil.copy2('FantomBot.py', f"./past_versions/{timestr}")
        # dl and overwrite from link
        with open('FantomBot.py', 'wb') as f:
            url = "".join(message.content.split(' ')[1:])
            f.write(requests.get(url).content)
        await message.channel.send("Updated.")
        restart()

    elif "f!wftm" == message.content.lower():
        price = convert(wFTM=1)
        await message.channel.send(f"wFTM: {price}")
    elif "f!graph" == message.content.lower():        
        file = discord.File("price.png", filename="price.png")
        await message.channel.send("price.png", file=file)
    elif "f!" in message.content:
        await message.channel.send("Command not found.")
    # elif "f!graph 24" == message.content.lower():


async def price_check_background_task():
    await client.wait_until_ready()

    while not client.is_closed():
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
            df['date'] = pd.to_datetime(df['time'],unit='s')
            df.drop("time", 1, inplace=True)
            df.set_index("date", inplace=True)
            df['price'].plot()
            plt.legend
            plt.subplots_adjust(left=0.15)
            plt.savefig("price.png")
            
            await asyncio.sleep(60)
            
        except Exception as e:
            print(str(e))
            await asyncio.sleep(60)


client.loop.create_task(price_check_background_task())
client.run(token)
