from typing import Any, Coroutine
from .abc import DownloadStrategy
import ffprobe3
import discord
import os

def get_platform_commands():
    # check windows or *nix
    if os.name == "nt":
        return [
            "ffmpeg -y -i {} -c:v libx264 -b:v {} -preset ultrafast -pass 1 -an -f null NUL",
            "ffmpeg -y -i {} -c:v libx264 -b:v {} -preset ultrafast -pass 2 -c:a aac -b:a 32k output.mp4"
        ]
    else:
        return [
            "ffmpeg -y -i {} -c:v libx264 -b:v {} -preset ultrafast -pass 1 -an -f null /dev/null",
            "ffmpeg -y -i {} -c:v libx264 -b:v {} -preset ultrafast -pass 2 -c:a aac -b:a 32k output.mp4"
        ]

class FFMpegCompressVideoStrategy(DownloadStrategy):
    def __init__(self, name) -> None:
        self.filename = name
        
    @staticmethod
    def can_download(_url):
        return False
    
    async def download(self, url, ctx) -> list[DownloadStrategy]:
        print("Compress")
        await ctx.send("Check compression")
        if os.path.getsize(self.filename) > 25e6:
            print("Shrinking video file to 25mb")
        
            probe = ffprobe3.probe(self.filename).format
            length = probe.duration_secs 

            
            target_filesize =  8388.608 * 23 #just to be safe 
            target_filesize -= 32 # remove audio bitrate and some more because ffmpeg lies to me about the file sizes

            target_filesize *= 0.8

            bitrate = str(int(target_filesize / int(length))) + "k"

            # run 2-pass encoding to calculate filesize
            
            ffname = "\"" + self.filename.replace("\"", "\\\"") + "\""
            cmd1 = get_platform_commands()[0].format(ffname, bitrate)
            print(cmd1)
            os.system(cmd1)
            
            cmd2 = get_platform_commands()[1].format(ffname, bitrate)
            print(cmd2)
            os.system(cmd2)
            print("Done2")
            if os.path.getsize("output.mp4") > 25e6:
                await ctx.send_followup("Could not compress. Sucks to suck")
                os.remove(self.filename)
                return []
            else:
                await ctx.send_followup("Uploading...")
                await ctx.send("Video:", file=discord.File("output.mp4"))
                os.remove(self.filename)
                return []
        else:
            print("Done11")
            probe = ffprobe3.probe(self.filename)
            v = probe.video[0]

            print("Codec:" + v.codec_name)
            if "hevc" in v.codec_name:
                return [FFMpegRencodeH264Strategy(self.filename)]
            await ctx.send_followup("Uploading...")
            await ctx.send("Video:", file=discord.File(self.filename))

            print("Done1")
            os.remove(self.filename)
            return []


class FFMpegRencodeH264Strategy(DownloadStrategy):
    def __init__(self, name) -> None:
        self.filename = name
        
    @staticmethod
    def can_download(_url):
        return False
    
    async def download(self, url, ctx) -> list[DownloadStrategy]:
        
        ffname = "\"" + self.filename.replace("\"", "\\\"") + "\""
        print("Re-encode required")
        os.system("ffmpeg -y -i " + ffname + " -c:v libx264 -preset ultrafast -c:a aac output.mp4")
        
        return [FFMpegCompressVideoStrategy(self.filename)]
        
