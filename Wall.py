import secret

import os
import re
import sys
import praw
# import dbus
import yaml
import random
import shutil
import ctypes
import pathlib
import requests
import argparse
import platform
import subprocess
import urllib.request
from bs4 import BeautifulSoup

from tqdm.auto import tqdm
# from progress.bar import FillingSquaresBar

# TODO сделать БД с хранением уже загруженных вариантов.

# TODO сделать возможность выбирать откуда загружать, больше двух вариантов.

# TODO сделать что-то вроде черного списка.

# TODO добавить какие ни будь индикаторы работы, а то просто пустая командная строка.

# TODO Придумать как  исключить картинки с F1.

# TODO Научить отличать nsfw картинки и по необходимости исключать их.

# TODO Сделать заглушку для случия если обои не найдены(скорее всего просто ставить предыдущии) и сообщение об этом
# ToDO декомпозировать все

class UpdateWall:
    # Возможно стоит удалить и переработать global. На данный момент толку от нее нет
    # Данная переменная нужна была при парсинге сайтов
    global html_links
    html_links = {
        'ze-robot': 'https://www.reddit.com/user/ze-robot/',
        'r-wallpaper': 'https://www.reddit.com/r/wallpaper/',
        'all': None,
    }

    # DE_SESSION = os.system('echo $DESKTOP_SESSION') 'echo $XDG_CURRENT_DESKTOP'  'ls /usr/bin/*session*'

    def __init__(self, args):
        self.href_list = []
        self.file_path = args.file / 'background.jpg'
        self.limit = args.limit
        self.recursion = False
        self.display_resolution = self._set_display_resolution(args.display_resolution)
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

    @staticmethod
    def _display_resolution_valid(resolution: str) -> bool:
        display_resolution_list = ['1920x1080', '1600x900', '1366x768', '1280x720',
                                   '1280x800', '1024x768', '1280x1024', '768x1024',
                                   '720x480', '352x240', '352x288', '352x480',
                                   '352x576', '480x480', '480x576', '528x480',
                                   '544x480', '544x576', '640x480', '704x480',
                                   '704x576', '720x576', '1280x1080', '3440x1440',
                                   '2560x1080', '3840x2160', '2560x1440', '2560x1600',
                                   '1920x1200', '1600x1200', '1080x1920', '720x1280',
                                   '720x1480', '1080x2220'
                                   ]

        if resolution in display_resolution_list:
            return True
        return False

    def _set_display_resolution(self, display_resolution):
        if self._display_resolution_valid(display_resolution):
            return display_resolution
        assert 'unvalid display resolution'
        config = read_config()
        return config['display']['resolution']

    def _os_system(self):
        """Проверка установленной операционной системы"""
        match platform.system():
            case 'Linux':
                self._linux_release()
            case 'Windows':
                ctypes.windll.user32.SystemParametersInfoW(20, 0, str(self.file_path), 3)

    # def __set_kde_wallpaper(self):
    #     plugin = 'org.kde.image'
    #     jscript = f"""
    #     var allDesktops = desktops();
    #     print (allDesktops);
    #     for (i=0;i<allDesktops.length;i++) {{
    #         d = allDesktops[i];
    #         d.wallpaperPlugin = "{plugin}";
    #         d.currentConfigGroup = Array("Wallpaper", "{plugin}", "General");
    #         d.writeConfig("Image", "file://{self.file_path}")
    #     }}
    #     """
    #     bus = dbus.SessionBus()
    #     plasma = dbus.Interface(bus.get_object(
    #         'org.kde.plasmashell', '/PlasmaShell'), dbus_interface='org.kde.PlasmaShell')
    #     plasma.evaluateScript(jscript)

    def _linux_release(self):
        """"Проверка рабочего окружения и выдача команды на изменение обоев"""
        match os.environ.get('XDG_CURRENT_DESKTOP'):
            case 'cinnamon' | 'X-Cinnamon':
                os.system(f"gsettings set org.cinnamon.desktop.background picture-uri 'file://{self.file_path}'")
            case 'GNOME' | 'ubuntu:GNOME' | 'GNOME-Classic:GNOME' | 'GNOME-Flashback:GNOME':
                os.system(f"gsettings set org.gnome.desktop.background picture-uri 'file://{self.file_path}'")
            case'LXQt':
                # Lubuntu
                # self.system_cmd = f"pcmanfm-qt --set-wallpaper='{self.ziro_file}'"
                # необходимо починить. меняет только первй рази и затем после перезагрузки системы
                os.system(f"pcmanfm-qt --set-wallpaper={str(self.file_path)}")
            case 'LXDE':
                os.system(f"pcmanfm --set-wallpaper={str(self.file_path)}")
            case 'MATE':
                os.system(f"gsettings set org.mate.background picture-filename {str(self.file_path)}")
            case 'xfce':
                desktop_wallpaper = subprocess.run(['xfconf-query', '-c', 'xfce4-desktop', '-m'],
                                                   stdout=subprocess.PIPE) \
                    .stdout.decode('utf-8')
                os.system(f"xfconf-query -c xfce4-desktop -p {desktop_wallpaper} -s {self.file_path}")
            case 'KDE':
                print('Currently not implemented')
                # Та же ситуация, что и с LXQt меняет только один раз и выполнении не меняет изображение при том же
                # названии файла
                # self.__set_kde_wallpaper()
            case _:
                assert 'Неизвестное графическое окружение'
                # TODO Вставить сюда предложение использовать команду без имени файла для изменения обоев
                # custom_cmd = input()
                exit()


    def _connection(self, url: str):
        """Подключение к сайту и подготовка супа"""
        connect = urllib.request.urlopen(url)
        html_code = connect.read().decode('utf-8')
        self.soup = BeautifulSoup(html_code, 'lxml')

    def get_link_from_web(self, teg: str, argument: str, argument_main: str, reg: str):
        """Парсинг сайта и получение ссылок изображений для загрузки"""
        # В разработке
        link_list = self.soup.find_all(teg, {argument: argument_main})
        for href in link_list:
            if re.search(reg, href['href']):
                self.href_list.append(href['href'])
        if not self.href_resource:
            self._connection(self.href_resource)
            self.get_link_from_web(teg, argument, argument_main, reg)
            assert f'Опять не прогрузилось попробуй снова'

    def get_link_list_reddit_redditor(self):
        # TODO оптимизировать и сделать более универсальным
        """"Получение ссылок изображений с постов пользователя"""
        users_comments = self.reddit.redditor('ze-robot').new(limit=self.limit)
        horizontal, vertical = self.display_resolution.split('x')
        reg = fr'https://resi\.ze-robot\.com/[\w/-]*-{horizontal}%C3%97{vertical}.jpg'
        with tqdm(total=self.limit) as pbar:
            pbar.set_description('get link image')

            for comment in users_comments:
                for link in re.findall(reg, comment.body_html):
                    self.href_list.append(link)
                pbar.update()
        print()

    def get_link_list_reddit_subreddit(self):
        # TODO так же сделать функцию более универсальной
        """Получение ссылок изображений с постов сабредита"""
        media_data = self.reddit.subreddit('wallpaper').new(limit=self.limit)
        aspect_ratio = 16 / 9
        with tqdm(total=self.limit) as pbar:
            pbar.set_description('get link image')
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
                        p = 0
                        for img in post.media_metadata.values():
                            p += 1
                            try:
                                img_s = img['s']
                            except KeyError:
                                continue
                            else:
                                if int(img_s['x']) / int(img_s['y']) == aspect_ratio:
                                    self.href_list.append(img_s['u'])
                    else:
                        assert 'Unknown attribute. The post is not recognized'
                        continue
                pbar.update()
            print()

    def _download_from_resource(self):
        """Рандомный выбор картинки и её загрузка"""
        if not self.href_list:
            assert ('No images matching your parameters were found.'
                    'Try different resolution settings for the image.')
            print('No images matching your parameters were found.'
                  'Try different resolution settings for the image.')
            exit()

        img_link = random.choice(self.href_list)
        with requests.get(img_link, stream=True) as resource:
            try:
                total_length = int(resource.headers.get('Content-Length'))

                with tqdm.wrapattr(resource.raw, 'read', total=total_length, desc="") as raw:
                    with open(self.file_path, 'wb') as out:
                        shutil.copyfileobj(raw, out)
                print()
            except TypeError as er:
                if not self.recursion:
                    self._download_from_resource()
                    self.resource = True
                else:
                    assert er
                    print(er)
                    exit('error')


        # resource = requests.get(img_link)
        # out = open(self.file_path, 'wb')
        # out.write(resource.content)
        # out.close()

    def install(self):
        """Загрузка с выбранного ресурса"""
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
        self._os_system()


def save_config(config, arg):
    config['main']['limit'] = arg.limit
    config['main']['file_name'] = arg.file_name
    config['main']['file_path'] = str(arg.file)
    config['main']['resource'] = arg.resource

    config['display']['resolution'] = arg.display_resolution
    # config['display']['ratio'] = arg.ratio
    PATH = pathlib.Path(__file__).parent.absolute()
    with open(PATH / 'config.yaml', 'w') as f:
        yaml.dump(config, stream=f,
                  default_style=False, sort_keys=False)


def read_config():
    PATH = pathlib.Path(__file__).parent.absolute()
    with open(PATH / 'config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def args_error(error):
    """Вывод ошибки при некорректных аргументах"""
    print(f'Error: {error}')


def main(argv):
    """Создание аргументов и запуск программы"""
    config = read_config()

    limit = config['main']['limit']
    file_name = config['main']['file_name']
    file_path = pathlib.Path(config['main']['file_path'])
    if file_path == pathlib.Path('.'):
        file_path = pathlib.Path(__file__).parent.absolute()
    resource = config['main']['resource']

    resolution = config['display']['resolution']
    ratio = config['display']['ratio']

    # PATH = pathlib.Path(__file__).parent.absolute()

    parser = argparse.ArgumentParser(description='Load wallpaper from reddit', prog='Random_wallpaper')
    parser.error = args_error

    parser.add_argument('-r', '--resource',
                        help='selecting a resource to upload\n',
                        choices=['ze-robot', 'r-wallpaper', 'all'],
                        default=resource)
    parser.add_argument('-l', '--limit',
                        type=int, help='quantity limit for sampling',
                        default=limit)
    parser.add_argument('-f', '--file', type=pathlib.Path, help='path to save file ',
                        default=file_path,
                        metavar='path/to/folder')
    parser.add_argument('--file-name', help='file name',
                        default=file_name)
    parser.add_argument('-d', '--display-resolution', help='display resolution',
                        default=resolution,)
    parser.add_argument('-c', '--config-file', help='change config file',
                        action='store_true', default=False)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.1', help='program version\n')

    args = parser.parse_args()
    if args.config_file:
        save_config(config, args)
    wallpaper = UpdateWall(args)
    wallpaper.install()


if __name__ == '__main__':
    main(sys.argv)
