

import asyncio
import base64
from datetime import datetime, timedelta
import os
import re
import aiohttp
import aiofiles
# import pyperclip
from bs4 import BeautifulSoup


baseURI = "https://www.xfxssr.me"
# https://www.xfxssr.me/nav/blog
# 从环境变量中获取 Telegram Bot Token 和 Chat ID
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
  raise ValueError("TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 环境变量未设置")

class SuLinkCloud:
  url = f"{baseURI}/nav/blog"
  sub_links = []

  @staticmethod
  def current_datetime() -> str:
    current_time = datetime.now()
    # 北京时间是 UTC+8，所以加上8小时
    beijing_time = current_time + timedelta(hours=8)
    current_datetime = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
    return current_datetime

  @staticmethod
  async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
          'chat_id': TELEGRAM_CHAT_ID,
          'text': message,
          'parse_mode': 'Markdown'  # 使 Telegram 解析 Markdown 格式
    }
    async with aiohttp.ClientSession() as session:
      async with session.post(url, json=payload) as response:
        if response.status == 200:
          print("Message sent successfully!")
        else:
          print(f"Failed to send message. Error: {response.status}, {await response.text()}")

  @classmethod
  async def get_net(cls, url: str, callback: callable):
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        if response.status < 300:
          content = await response.text()
          callback(content)
        else:
          print(f"状态码可能错误：{response.status}")

  @classmethod
  def parse_main_page(cls, text: str):
    html = BeautifulSoup(text, "html.parser")
    item = html.select_one('.cat_list .media-content')
    if item:
      cls.blog = item.attrs["href"].strip()
      print(cls.blog)
    else:
      print("没有捕获到符合的博客连接")

  @classmethod
  def parse_blog_page(cls, text: str):
    pattern = r'http://subssr\.xfxvpn\.me[^<\s"]*'
    matches = re.findall(pattern, text, flags=re.S)
    if matches:
      cls.sub_links = matches
      print("\n".join(matches))
    else:
      print("订阅链接未捕获：", matches)

  @classmethod
  async def main(cls):
    await cls.get_net(cls.url, cls.parse_main_page)
    await cls.get_net(cls.blog, cls.parse_blog_page)

    nodes = []
    def add_to_nodes(x):
      nonlocal nodes
      decoded_line = base64.b64decode(x).decode('utf-8', errors='ignore')
      nodes += decoded_line.split('\r\n')[4:]
      return nodes

    for link in cls.sub_links:
      await cls.get_net(link, add_to_nodes)
    nodes_base64 = base64.b64encode("\n".join(set(nodes)).encode('utf-8')).decode('utf-8')
    # pyperclip.copy(nodes_base64)
    # print(nodes_base64)
    if nodes_base64:
      async with aiofiles.open('site', 'w+', encoding="utf-8") as file:
        await file.write(nodes_base64)
        await cls.send_telegram_message(
          f"更新成功\n"
          f"Time: {cls.current_datetime()}\n"
          f"origin: `{baseURI}`\n"
          f"订阅地址: `https://raw.githubusercontent.com/mai19950/sulinkcloud/main/site`\n"
          f"```{'\n'.join(cls.sub_links)}```"
        )
        print("节点保存成功")
    else:
      print("没有节点")



if __name__ == '__main__':
  asyncio.run(SuLinkCloud().main())