import os
import re
import random
import requests
import urllib.request
from bs4 import BeautifulSoup
# for test
from pprint import pprint


# TODO сделать БД с хранением уже загруженных вариантов.

# TODO сделать загрузку с  https://www.reddit.com/r/wallpaper/new/.
# TODO сделать возможность выбирать откуда загружать.
# TODO добавить какие ни будь индикаторы работы, а то просто пустая командная строка.

# TODO Придумать как  исключить картинки с F1.
# TODO Реализовать запуск на windows.
# TODO сделать что-то вроде черного списка.

class UpdateWall:
    global html_links
    html_links = {
        'ze-robot': 'https://www.reddit.com/user/ze-robot/',
        'r-wallpaper': 'https://www.reddit.com/r/wallpaper/'
    }
    word_exceptions = [

    ]
    def __init__(self, resource='ze-robot', file_path='background.jpg'):
        self.href_list = []
        self.file_path = file_path
        try:
            self.href_resource = html_links[resource]
            self.resource = resource
        except KeyError:
            self.resource = 'ze-robot'
            self.href_resource = html_links['ze-robot']
            print(f'Ваш ресурс еще не добавлен, в качестве ресурса по умолчанию'
                  f'Установлен ze-robot')
        self._connection(self.href_resource)

    def _connection(self, url: str):
        connect = urllib.request.urlopen(url)
        html_code = connect.read().decode('utf-8')
        self.soup = BeautifulSoup(html_code, 'lxml')

    def _download_from_resource(self, teg: str, argument: str, argument_main: str, reg: str):
        link_list = self.soup.find_all(teg, {argument: argument_main})
        for href in link_list:
            if re.search(reg, href['href']):
                self.href_list.append(href['href'])

        try:
            img_link = random.choice(self.href_list)
            resource = requests.get(img_link)
            out = open(self.file_path, 'wb')
            out.write(resource.content)
            out.close()
        except IndexError:
            self._connection(self.href_resource)
            self._download_from_resource(teg, argument, argument_main, reg)
            assert f'Опять не прогрузилось попробуй снова'

    def install(self):
        match self.resource:
            case 'ze-robot':
                self._download_from_resource('a', 'class', '_3t5uN8xUmg0TOwRCOGQEcU',
                                             r'https://resi\.ze-robot\.com/[\w/-]*-1920×1080.jpg')
            case 'r-wallpaper':
                ...
        # TODO самостоятельно подставлять путь до картинки.
        os.system("gsettings set org.cinnamon.desktop.background picture-uri 'file:///home/user/Walls/background.jpg'")


if __name__ == '__main__':
    test = UpdateWall()
    test.install()
