import discord
from discord.ext import commands
from gallery_dl import job
from common import *
import logging
import httpx
import asyncio
import io
import re
import string
from gallery_dl import output
from discord import default_permissions
from yt_dlp import YoutubeDL
import os


opts = {'extract_flat': False,
 'final_ext': 'mp4',
 'fragment_retries': 10,
 'outtmpl': {'default': 'ooutput.mp4'},
 'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
 'retries': 10}
    
def dl(url):
    if os.path.isfile("ooutput.mp4"):
        os.remove("ooutput.mp4")
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    # redundant for most downloads as its already in an acceptable encoding. maybe check with ffprobe?
    os.system("ffmpeg -y -i ooutput.mp4 -c:v libx264 -c:a aac output.mp4")
    print("downloaded")
   
    
        
def addlogs():
    # stolen i think
    output.initialize_logging(logging.INFO)
    output.configure_logging(logging.INFO)
    output.setup_logging_handler("unsupportedfile", fmt="{message}")()

def truncate_str(input_string, max_length):
    if len(input_string) > max_length:
        return input_string[:max_length]
    else:
        return input_string


def format_tags(tags):
    def form(tag):
        new = ""
        for char in tag.lower():
            if char in string.ascii_lowercase + string.digits + "_":
                new += char
        return new
    return [form(tag) for tag in tags]

class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @slash()
    @default_permissions(manage_channels=True)
    async def nsfw(self, ctx):
        print(ctx.channel)
        chan = ctx.channel
        if chan.parent:
            chan = chan.parent
        await chan.edit(nsfw=True)
        await ctx.respond("Made nsfw")
    
    @slash()
    @default_permissions(manage_channels=True)
    async def createcategory(self,ctx,name: str, tags: str):
        tags = tags.split(",")
        print(tags)
        tags = format_tags(tags)
        print(tags)
        if len(tags)==0:
            await ctx.respond("Error blank tags, for a non private channel use public as the only tag")
            return
        perms = {}
        if tags[0] == "public":
            perms = {}
        else:
            po = discord.PermissionOverwrite()
            po.view_channel = False
            perms[ctx.guild.default_role] = po
            for tag in tags:
                role = discord.utils.get(ctx.guild.roles, name=tag)
                if role is None:
                    role = await ctx.guild.create_role(name=tag)
                perms[role] = discord.PermissionOverwrite()
                perms[role].view_channel = True
        await ctx.guild.create_forum_channel(name, overwrites=perms)
        await ctx.respond("Made")
        
    
    @slash()
    async def gallerydl(self,ctx,gallery: str):
        await ctx.defer()
        j = job.DataJob(gallery)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, j.run)
        await ctx.send_followup("Fetched")
        t = "Downloading urls...\nFetched: {}\n"
        msg = await ctx.send("Starting download")
        no = 0
        tasks = []
        for page in j.data:
            if page[0] == 3:
                no += 1
                await msg.edit(t.format(no))
                async def task(myno, url):
                    file = io.BytesIO()
                    try:
                        async with httpx.AsyncClient() as client:
                            async with client.stream('GET', url) as r:
                                fname = ""
                                if "Content-Disposition" in r.headers.keys():
                                    fname = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]
                                else:
                                    fname = url.split("/")[-1].split("?")[0]
                                async for chunk in r.aiter_bytes():
                                    file.write(chunk)
                        file.seek(0)
                        fname = str(hash(url))[0:6]+fname
                        await ctx.send(f"No. {myno}: `{url}`", file=discord.File(file, fname))
                    except Exception as e:
                        print(e)
                        await ctx.send(f"Failed number {myno}")
                tasks.append(asyncio.create_task(task(no, page[1])))
            else:
                ...
            
        await asyncio.gather(*tasks)
        print("done")
        await ctx.send("Done")
    
    @slash()
    async def ytdl(self, ctx, url: str):
        await ctx.defer()
        try:
            loop = asyncio.get_event_loop()
            print('dl')
            await loop.run_in_executor(None, lambda: dl(url))
            print("uploading")
            file = open("output.mp4", "rb")
            await ctx.send("File", file=discord.File(file, "ytdl.mp4"))
            file.close()
        finally:
            await ctx.send_followup("Done")
         
