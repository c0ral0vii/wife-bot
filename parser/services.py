import aiohttp
from bs4 import BeautifulSoup
import asyncio
import aiofiles
import os
from typing import List, Dict
from src.database.models import AllRares
from src.database.orm.wifes import add_wife
from src.logger import setup_logger

class ParserModule:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.BASE_URL = "https://shikimori.one/characters/"
        self.logger = setup_logger(__name__)

    async def get_page(self, session: aiohttp.ClientSession, url: str) -> str:
        async with session.get(url, headers=self.headers) as response:
            response.raise_for_status()
            return await response.text()

    async def download_image(self, image_url: str, save_path: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, headers=self.headers) as response:
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    f.write(await response.read())

    async def parse_page(self):
        counter = 0
        async with aiohttp.ClientSession() as session:
            for entry in range(1, 180000):
                self.logger.info(f"Parsing page {counter}")
                try:
                    counter += 1
                    if counter % 10 == 0:
                        rarity = AllRares.LEGENDARY
                    elif counter % 5 == 0:
                        rarity = AllRares.EPIC
                    elif counter % 3 == 0:
                        rarity = AllRares.RARE
                    else:
                        rarity = AllRares.SIMPLE

                    page = await self.get_page(url=self.BASE_URL+str(entry), session=session)
                    soup = BeautifulSoup(page, 'lxml')

                    title = soup.find("header", class_="head").find("h1").text
                    img = soup.find("div", class_="c-poster").find("img")["src"]
                    anime_list = soup.find_all("div", class_="cc-roles")
                    titles = []

                    for anime in anime_list:
                        for i in anime.find_all("article"):
                            anime_title = i.find("span", class_="name-ru").text
                            titles.append(anime_title)

                    character_data = {
                        "title": title,
                        "img": img,
                        "rarity": rarity,
                        "anime_list": titles,
                    }
                    print(character_data)
                    new_wife = await add_wife(data=character_data)
                    await self._create_files(id=new_wife.id, image_url=img, session=session)
                except aiohttp.ClientError as e:
                    self.logger.error(f"Ошибка сети: {e}")
                    await asyncio.sleep(5)
                except Exception as e:
                    self.logger.warning(e)
                    continue


    async def _create_files(self, id: int, image_url: str, session: aiohttp.ClientSession):
        save_path = f"./media/wifes/{id}/profile.png"

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        await self.download_image(session, image_url, save_path)


    async def download_image(self, session: aiohttp.ClientSession, image_url: str, save_path: str):
        async with session.get(image_url) as response:
            response.raise_for_status()
            if "image" in response.headers.get("Content-Type", ""):
                async with aiofiles.open(save_path, "wb") as file:
                    while chunk := await response.content.read(8192):
                        await file.write(chunk)
                self.logger.info(f"Изображение успешно загружено и сохранено как {save_path}")
            else:
                self.logger.error("Ошибка: Ссылка не ведет на изображение.")

parse = ParserModule()