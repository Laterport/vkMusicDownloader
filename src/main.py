#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import vk_api
import getopt
from time import time
from vk_api import audio
import concurrent.futures
import subprocess

class vkMusicDownloader():
    CONFIG_DIR = "config"
    USERDATA_FILE = "{}/UserData.datab".format(CONFIG_DIR)
    REQUEST_STATUS_CODE = 200
    path = 'music/'

    def auth_handler(self, remember_device=None):
        # Обработчик двухфакторной аутентификации
        code = input("Введите код подтверждения 2FA\n> ")
        if remember_device is None:
            remember_device = True
        return code, remember_device

    def saveUserData(self):
        SaveData = [self.login, self.password, self.user_id]

        with open(self.USERDATA_FILE, 'w') as dataFile:
            dataFile.write(f"{self.login}\n")
            dataFile.write(f"{self.password}\n")
            dataFile.write(f"{self.user_id}\n")

    def loadUserData(self):
        if os.path.exists(self.USERDATA_FILE):
            with open(self.USERDATA_FILE, 'r') as dataFile:
                self.login = dataFile.readline().strip()
                self.password = dataFile.readline().strip()
                self.user_id = dataFile.readline().strip()
                return True
        return False

    def auth(self, new=False, user_id=None):
        if not new and self.loadUserData():
            user_id = user_id or self.user_id
        else:
            if os.path.exists(self.USERDATA_FILE):
                os.remove(self.USERDATA_FILE)

            self.login = input("Введите логин\n> ")
            self.password = input("Введите пароль\n> ")
            self.user_id = input("Введите id профиля\n> ")
            self.saveUserData()

        try:
            vk_session = vk_api.VkApi(login=self.login, password=self.password, app_id=2685278,
                                      auth_handler=self.auth_handler)
            vk_session.auth()
        except Exception as e:
            print('[error]:', e)
            return

        print('Вы успешно авторизовались.')
        self.vk = vk_session.get_api()
        self.vk_audio = audio.VkAudio(vk_session)

    def audio_get(self, audio, parallel=True):
        # собственно циклом загружаем нашу музыку

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for index, audio_info in enumerate(audio):
                executor.submit(self.audio_download, index, audio_info)

    def audio_download(self, index, audio):

        title = audio["title"]

        # Защита от длинного имени
        if len(title) > 100:
            title = title[:100]

        # Защита от недопустимых символов
        title = "".join([c for c in title if c.isalpha() or c.isdigit() or c == ' ']).rstrip()

        fileMP3 = f'{audio["artist"]} - {title}.mp3'
        fileMP3 = re.sub('/', '_', fileMP3)

        try:
            if os.path.isfile(fileMP3):
                print(f"{index} Уже скачен: {fileMP3}.")
            else:
                print(f"{index} Скачивается: {fileMP3}.")

                subprocess.run(
                    f'ffmpeg -http_persistent false -i {audio["url"]} -c copy -map a "{fileMP3}"',
                    shell=True,
                    check=True
                )
        except OSError:
            if not os.path.isfile(fileMP3):
                print(f"{index} Не удалось скачать аудиозапись: {fileMP3}")

    def main(self, auth_dialog='yes', user_id=None, parallel_flag=True):
        try:
            if (not os.path.exists(self.CONFIG_DIR)):
                os.mkdir(self.CONFIG_DIR)
            if not os.path.exists(self.path):
                os.makedirs(self.path)

            if (auth_dialog == 'yes'):
                auth_dialog = input("Авторизоваться заново? yes/no\n> ")
                if (auth_dialog == 'yes'):
                    self.auth(new=True, user_id=user_id)
                elif (auth_dialog == "no"):
                    self.auth(new=False, user_id=user_id)
                else:
                    print('Ошибка, неверный ответ.')
                    self.main()
            elif (auth_dialog == "no"):
                self.auth(new=False, user_id=user_id)

            print('Подготовка к скачиванию...')

            # В папке music создаем папку с именем пользователя, которого скачиваем.
            info = self.vk.users.get(user_id=self.user_id)
            music_path = f"{self.path}/{info[0]['first_name']} {info[0]['last_name']}"
            if not os.path.exists(music_path):
                os.makedirs(music_path)

            time_start = time()  # сохраняем время начала скачивания
            print("Скачивание началось...\n")

            os.chdir(music_path)  # меняем текущую директорию
            audio = self.vk_audio.get(owner_id=self.user_id)
            print(f'Будет скачано: {len(audio)} аудиозаписей с Вашей страницы.')

            # Получаем музыку.
            self.audio_get(audio, parallel_flag)
            count = 0 + len(audio)
            os.chdir("../..")
            albums = self.vk_audio.get_albums(owner_id=self.user_id)
            print(f'У Вас {len(albums)} альбома.')
            for i in albums:
                audio = self.vk_audio.get(owner_id=self.user_id, album_id=i['id'])
                count += len(audio)

                print(f"Будет скачано: {len(audio)} аудиозаписей из альбома {i['title']}.")

                album_path = f"{music_path}/{i['title']}"
                if not os.path.exists(album_path):
                    os.makedirs(album_path)

                os.chdir(album_path)  # меняем текущую директорию

                # Получаем музыку.
                self.audio_get(audio, parallel_flag)

                os.chdir("../../..")

                time_finish = time()
                print(f"{count} аудиозаписей скачано за: {str(time_finish - time_start)} сек.")
        except KeyboardInterrupt:
            print('Вы завершили выполнение программы.')


if __name__ == '__main__':
    vkMD = vkMusicDownloader()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hni:p")
    except getopt.GetoptError:
        print('./main.py [-n] [-h] [-i] [-p]')
        sys.exit(2)

    auth_dialog = 'yes'
    user_id = None
    parallel_flag = True

    if len(args) == 1:
        vkMD.main(auth_dialog=auth_dialog)
    else:
        for opt, arg in opts:
            if opt in ['-h']:
                print('./main.py [-n] [-h]')
                sys.exit()
            elif opt in ['-n']:
                auth_dialog = 'no'
            elif opt in ['-i']:
                user_id = int(arg)
            elif opt in ['-p']:
                parallel_flag = False

        try:
            vkMD.main(auth_dialog=auth_dialog, user_id=user_id, parallel_flag=parallel_flag)
        except vk_api.exceptions.AccessDenied as e:
            print('[error]:', e)
        except Exception as e:
            print('[error]:', e)

    sys.exit()
