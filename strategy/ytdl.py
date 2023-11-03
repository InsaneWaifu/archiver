from typing import Any, Coroutine
from .abc import DownloadStrategy
from .pp import FFMpegCompressVideoStrategy
import urllib.parse
import os
from yt_dlp import YoutubeDL
from pprint import pprint
import yt_dlp

supported_sites = ["youtube.com", "tiktok.com", "youtu.be"]

opts = {'extract_flat': False,
 'fragment_retries': 10,
 'postprocessors': [],
 'retries': 10}
    

class FilenameCollectorPP(yt_dlp.postprocessor.common.PostProcessor):
    def __init__(self):
        super(FilenameCollectorPP, self).__init__(None)
        self.filenames = []

    def run(self, information):
        self.filenames.append(information['filepath'])
        return [], information

class YtdlStrategy(DownloadStrategy):
    @staticmethod
    def can_download(url):
        url_parsed = urllib.parse.urlparse(url)
        supported = False
        for site in supported_sites:
            if site in url_parsed.netloc:
                supported = True
                break
        
        return supported
        
    async def download(self, url, ctx) -> list[DownloadStrategy]:
        
        if os.path.isfile("ooutput.mp4"):
            os.remove("ooutput.mp4")

        opt2 = opts.copy()

        with YoutubeDL(opts) as ydl:
            meta = ydl.extract_info(
                url, download=False) 
            formats = meta.get('formats', [meta])
            # find acceptable formats
            # first preference: 1080p or below
            pref_format = None
            hasaudio = False
            worst_quality = 0
            for f in formats:
                try:
                    qual = int(f["format_note"][0:-1]) 
                    if qual <= 1080 and qual > worst_quality:
                        worst_quality = qual
                        pref_format = f["format_id"]
                        hasaudio = bool(f["audio_channels"])
                except ValueError:
                    # couldnt cast to int
                    pass
                except KeyError:
                    # no format_note
                    pass
            


            if pref_format and not hasaudio:
                pref_format += "+bestaudio"
            
            if pref_format:
                
                opt2["format"] = pref_format


            


        filename_collector = FilenameCollectorPP()
        with YoutubeDL(opt2) as ydl:
            ydl.add_post_processor(filename_collector)
            ydl.download([url])
        
        print("Downloaded")
        return [FFMpegCompressVideoStrategy(filename_collector.filenames[0])]
    
    