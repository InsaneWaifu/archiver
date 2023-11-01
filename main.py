from dotenv import load_dotenv
import os
load_dotenv()

import discord
from discord.ext import commands
import common 
it = discord.Intents.all()
bot = commands.Bot(intents=it)
common.COMMON_BOT = bot
@bot.event
async def on_ready():
    print("ready")
import util
bot.add_cog(util.Util(bot))
bot.run(os.environ["TOKEN"])
