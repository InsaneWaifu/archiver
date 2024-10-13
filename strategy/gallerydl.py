from typing import Any, Coroutine
from .abc import DownloadStrategy
from .pp import FFMpegCompressVideoStrategy
import urllib.parse
import os
from yt_dlp import YoutubeDL
from pprint import pprint
import yt_dlp
from gallery_dl import job, output
import asyncio
import io
import re
import discord
import httpx

class GalleryDLStrategy(DownloadStrategy):
    @staticmethod
    def can_download(url):
        return True
        
    async def download(self, url, ctx) -> list[DownloadStrategy]:
        j = job.DataJob(url)
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
                        async with httpx.AsyncClient(follow_redirects=True) as client:
                            async with client.stream('GET', url) as r:
                                fname = ""
                                if "filename" in page[2]:
                                    fname = page[2]["filename"] + "." + page[2]["extension"]
                                elif "Content-Disposition" in r.headers.keys():
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
        return []