import secret

import os
import re
import sys
import praw
import random
import pathlib
import requests
import argparse
import urllib.request
from bs4 import BeautifulSoup

# TODO сделать БД с хранением уже загруженных вариантов.

# TODO сделать возможность выбирать откуда загружать, больше двух вариантов.

# TODO сделать что-то вроде черного списка.

# TODO добавить какие ни будь индикаторы работы, а то просто пустая командная строка.

# TODO Придумать как  исключить картинки с F1.

# TODO Научить отличать nsfw картинки и по необходимости исключать их.

# TODO Сделать заглушку для случия если обои не найдены(скорее всего просто ставить предыдущии) и сообщение об этом

# TODO Реализовать запуск на windows.


class UpdateWall:
    global html_links
    html_links = {
        'ze-robot': 'https://www.reddit.com/user/ze-robot/',
        'r-wallpaper': 'https://www.reddit.com/r/wallpaper/',
        'all': None,
    }


    word_exceptions = [

    ]
    # DE_SESSION = os.system('echo $DESKTOP_SESSION') 'echo $XDG_CURRENT_DESKTOP'  'ls /usr/bin/*session*'

    def __init__(self, args):
        self.href_list = []
        self.file_path = args.file / 'background.jpg'
        self.limit = args.limit
        self.reddit = praw.Reddit(
            client_id=secret.client_id,
            client_secret=secret.client_secret,
            user_agent=secret.user_agent
        )
        try:
            self.href_resource = html_links[args.resource]
            self.resource = args.resource
        except KeyError:
            self.resource = 'ze-robot'
            self.href_resource = html_links['ze-robot']
            print(f'Ваш ресурс еще не добавлен, в качестве ресурса по умолчанию'
                  f'Установлен ze-robot')

    def _connection(self, url: str):
        connect = urllib.request.urlopen(url)
        html_code = connect.read().decode('utf-8')
        self.soup = BeautifulSoup(html_code, 'lxml')

    def get_link_from_web(self, teg: str, argument: str, argument_main: str, reg: str):
        # В разработке
        link_list = self.soup.find_all(teg, {argument: argument_main})
        for href in link_list:
            if re.search(reg, href['href']):
                self.href_list.append(href['href'])
        if not self.href_resource:
            self._connection(self.href_resource)
            self.get_link_from_web(teg, argument, argument_main, reg)
            assert f'Опять не прогрузилось попробуй снова'
        self._download_from_resource()

    def get_link_list_reddit_redditor(self):
        users_comments = self.reddit.redditor('ze-robot').new(limit=self.limit)
        reg = r'https://resi\.ze-robot\.com/[\w/-]*-1920%C3%971080.jpg'

        for comment in users_comments:
            for link in re.findall(reg, comment.body_html):
                self.href_list.append(link)

    def get_link_list_reddit_subreddit(self):
        media_data = self.reddit.subreddit('wallpaper').new(limit=self.limit)
        aspect_ratio = 16 / 9

        for post in media_data:
            if hasattr(post, 'crosspost_parent_list'):
                # do if post have repost image
                try:
                    # try to get image if in post it's one
                    images_list = post.crosspost_parent_list[0].get('preview').get('images')[0].get('source')
                    if int(images_list['width']) / int(images_list['height']) == aspect_ratio:
                        self.href_list.append(images_list['url'])
                except AttributeError:
                    # try to get image if in post they many
                    for img in post.crosspost_parent_list[0].get('media_metadata').values():
                        img_s = img['s']
                        if int(img_s['x']) / int(img_s['y']) == aspect_ratio:
                            self.href_list.append(img_s['u'])
            else:
                # just post
                if hasattr(post, 'preview'):
                    # try to get image if in post it's one
                    images_list = post.preview.get('images')[0].get('source')
                    if int(images_list['width']) / int(images_list['height']) == aspect_ratio:
                        self.href_list.append(images_list['url'])
                elif hasattr(post, 'media_metadata'):
                    # try to get image if in post they many
                    for img in post.media_metadata.values():
                        img_s = img['s']
                        if int(img_s['x']) / int(img_s['y']) == aspect_ratio:
                            self.href_list.append(img_s['u'])
                else:
                    assert 'Unknown attribute. The post is not recognized'
                    continue

    def _download_from_resource(self):
        img_link = random.choice(self.href_list)
        resource = requests.get(img_link)
        out = open(self.file_path, 'wb')
        out.write(resource.content)
        out.close()

    def install(self):
        match self.resource:
            case 'ze-robot':
                self.get_link_list_reddit_redditor()
                # self.get_link_from_web('a', 'class', '_3t5uN8xUmg0TOwRCOGQEcU',
                #                              r'https://resi\.ze-robot\.com/[\w/-]*-1920×1080.jpg')
            case 'r-wallpaper':
                self.get_link_list_reddit_subreddit()
            case 'all':
                self.get_link_list_reddit_redditor()
                self.get_link_list_reddit_subreddit()
            case 'web_':
                self._connection(self.href_resource)
        self._download_from_resource()
        os.system(f"gsettings set org.cinnamon.desktop.background picture-uri 'file://{self.file_path}'")



if __name__ == '__main__':
    test = UpdateWall()
    test.install()
