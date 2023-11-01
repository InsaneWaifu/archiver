from discord.ext import commands
import discord
COMMON_BOT = None
debug = False
if debug:
    ids = [1145090805065855098]
else:
    ids = None

def slash(*args, **kwargs):
    def h(func):       
        return discord.slash_command(guild_ids=ids, *args, **kwargs)(func)
    return h