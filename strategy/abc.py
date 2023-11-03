from __future__ import annotations # allow self referential type annotations
from abc import ABC, abstractmethod
import discord


class DownloadStrategy(ABC): # Inherit from ABC(Abstract base class)
    @staticmethod
    @abstractmethod  # Decorator to define an abstract method
    def can_download(url):
        pass

    @abstractmethod
    async def download(self, url: str, ctx: discord.ApplicationContext) -> list[DownloadStrategy]:
        pass

