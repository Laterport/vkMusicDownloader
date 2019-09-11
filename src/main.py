#!/usr/bin/python3
#-*- coding: utf-8 -*-

import os
import pickle
import requests
from time import time
import vk_api
from vk_api import audio

class vkMusicDownloader():

    __version__ = 'VK Music Downloader v1.0'

    CONFIG_DIR = "config"
    USERDATA_FILE = "{}/UserData.datab".format(CONFIG_DIR) #файл хранит логин, пароль и id
    vk_file = "{}/config.v2.json".format(CONFIG_DIR)
    REQUEST_STATUS_CODE = 200 
    path = 'music/'

    def auth_handler(self, remember_device=None):
        code = input("Введите код подтверждения\n> ")
        if (remember_device == None):
            remember_device = True
        return code, remember_device

    def saveUserData(self):
        SaveData = [self.login, self.password, self.my_id]

        with open(self.USERDATA_FILE, 'wb') as dataFile:
            pickle.dump(SaveData, dataFile)

    def auth(self, new=False):
        try:
            if (os.path.exists(self.USERDATA_FILE) and new == False):
                with open(self.USERDATA_FILE, 'rb') as DataFile:
                    LoadedData = pickle.load(DataFile)

                self.login = LoadedData[0]
                self.password = LoadedData[1]
                self.my_id = LoadedData[2]
            else:
                if (os.path.exists(self.USERDATA_FILE) and new == True):
                    os.remove(self.USERDATA_FILE)

                self.login = str(input("Введите логин\n> ")) 
                self.password = str(input("Введите пароль\n> ")) 
                self.my_id = str(input("Введите id профиля\n> "))
                self.saveUserData()

            SaveData = [self.login, self.password, self.my_id]
            with open(self.USERDATA_FILE, 'wb') as dataFile:
                pickle.dump(SaveData, dataFile)

            vk_session = vk_api.VkApi(login=self.login, password=self.password)
            try:
                vk_session.auth()
            except:
                vk_session = vk_api.VkApi(login=self.login, password=self.password, auth_handler=self.auth_handler)
                vk_session.auth()
            print('Вы успешно авторизовались.')
            vk = vk_session.get_api()
            global vk_audio 
            vk_audio = audio.VkAudio(vk_session)
        except KeyboardInterrupt:
            print('Вы завершили выполнение программы.')

    def main(self):
        try:
            if (not os.path.exists(self.CONFIG_DIR)):
                os.mkdir(self.CONFIG_DIR)
            if not os.path.exists(self.path):
                os.makedirs(self.path)

            auth_dialog = str(input("Авторизоваться заново? yes/no\n> "))
            if (auth_dialog == "yes"):
                self.auth(new=True)
            elif (auth_dialog == "no"):
                self.auth(new=False)
            else:
                print('Ошибка, неверный ответ.')
                self.main()
            print('Подготовка к скачиванию...')
            os.chdir(self.path) #меняем текущую директорию

            audio = vk_audio.get(owner_id=self.my_id)[0]
            print('Будет скачано: {} аудиозаписей.'.format(len(vk_audio.get(owner_id=self.my_id))))
            time_start = time() # сохраняем время начала скачивания
            print("Скачивание началось...\n")
            index = 1
            # собственно циклом загружаем нашу музыку 
            for i in vk_audio.get(owner_id=self.my_id):
                try:
                    fileM = "{} - {}.mp3".format(i["artist"], i["title"])
                    
                    if os.path.isfile(fileM) :
                        print("{} Уже скачен: {}.".format(index, fileM))
                    else :
                        print("{} Скачивается: {}.".format(index, fileM), end = "")
                        r = requests.get(audio["url"])
                        if r.status_code == self.REQUEST_STATUS_CODE:
                            print(' Скачивание завершено.')
                            with open(fileM, 'wb') as output_file:
                                output_file.write(r.content)
                except OSError:
                    print("{} Не удалось скачать аудиозапись: {}".format(index, fileM))
                    
                index += 1
            time_finish = time()
            print("" + str(len(vk_audio.get(owner_id=self.my_id))) + " аудиозаписей скачано за: " + str(time_finish - time_start) + " сек.")
        except KeyboardInterrupt:
            print('Вы завершили выполнение программы.')

if __name__ == '__main__':
    vkMD = vkMusicDownloader()
    vkMD.main()
