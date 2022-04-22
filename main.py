import time
import datetime
import requests
from pprint import pprint
from tqdm import tqdm
import json


with open('token.txt', 'r') as file_object:
    token = file_object.read().strip()


class VK:

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }
        self.user_id = self.search_id()
        self.url = 'https://api.vk.com/method/'
        self.json, self.download_dict = self.json_upload_files()

    def search_id(self, screen_name=input('Введите ID пользователя:\n')):
        """Преобразование screen_name в id"""
        while True:
            try:
                url = 'https://api.vk.com/method/'
                params = {
                    'access_token': token,
                    'v': '5.131'
                }
                user_url = url + 'users.get'
                name_params = {'user_ids': screen_name}
                res = requests.get(user_url, params={**params, **name_params}).json()
                id = res['response'][0]['id']
            except:
                id = screen_name
            return id

    def search_photo(self):
        '''Получение фотографий из ВК'''
        photo_url = self.url + 'photos.get'
        photo_params = {
            'owner_id': self.user_id,
            'album_id': 'profile',
            'extended': 1,
             'photo_sizes': 1

        }
        res = requests.get(photo_url, params={**self.params, **photo_params}).json()
        return res['response']['count'], res['response']['items']

    def search_max_photo(self, search_dict):
        """Ссылка на максимальное разрешение фотографий"""
        max_res = 0
        need_photo = 0
        for q in range(len(search_dict)):
            photo_res = search_dict[q].get('width') * search_dict[q].get('height')
            if photo_res > max_res:
                max_res = photo_res
                need_photo = q
        return search_dict[need_photo].get('url'), search_dict[need_photo].get('type')

    def time_convert(self, timestamp):
        """Преобразование даты в привычный формат"""
        value = datetime.datetime.fromtimestamp(timestamp)
        date = value.strftime('%Y-%m-%d _ %H-%M-%S')
        return date

    def get_logs(self):
        '''Получение параметров фотографий'''
        photo_count, photo_items = self.search_photo()
        logs = {}
        for i in range(photo_count):
            likes_count = photo_items[i]['likes']['count']
            url_download, picture_size = self.search_max_photo(photo_items[i]['sizes'])
            date = self.time_convert(photo_items[i]['date'])
            inf = logs.get(likes_count, [])
            inf.append({'likes_count': likes_count,
                              'add_name': date,
                              'url_picture': url_download,
                              'size': picture_size})
            logs[likes_count] = inf
        return logs

    def json_upload_files(self):
        """Получение json файла и параметров для выгрузки фотографий"""
        json_list = []
        upload_dict = {}
        photo_dict = self.get_logs()
        for photo in photo_dict.keys():
            for value in photo_dict[photo]:
                if len(photo_dict[photo]) == 1:
                    file_name = f'{value["likes_count"]}.jpeg'
                else:
                    file_name = f'{value["likes_count"]}_{value["add_name"]}.jpeg'
                json_list.append({'file name': file_name, 'size': value["size"]})
                with open('./log.json', 'w') as file:
                    json.dump(json_list, file, indent=2)
                upload_dict[file_name] = photo_dict[photo][-1]['url_picture']
        return json_list, upload_dict


class Yandex:
    def __init__(self, Yatoken):
        self.Yatoken = Yatoken
        self.number = int(input('Введите необходимое количество фотографий для скачивания:\n'))
        self.folder_name = input('Введите название папки, где будут храниться файлы:\n')
        self.folder = self.create_folder(self.folder_name)

    def get_headers(self):
        '''Заголовок Яндекс запроса'''
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.Yatoken)
        }

    def create_folder(self,folder_name):
        '''Создание папки на Яндекс диске'''
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': folder_name}
        headers = self.get_headers()
        if requests.get(url, headers=headers, params=params).status_code != 200:
            requests.put(url, headers=headers, params=params)
            print(f'Папка {folder_name} успешно создана на Яндекс диске.\n')
        else:
            print(f'Папка {folder_name} уже существует.\n')
        return folder_name

    def upload_file_to_disk(self, dict_upload):
        """Выгрузка файлов на Яндекс диск"""
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params_log = {"path": f"{self.folder}/{'log.json'}",
                      "overwrite": "true"}
        response_log = requests.get(url, headers=headers, params=params_log)
        get_url_log = response_log.json()
        up_url_log = get_url_log['href']
        requests.put(up_url_log, data=open(f"{'log.json'}", 'rb'))
        copy_counter = 0
        print('Резервное копирование фотографий:')
        for key, i in zip(dict_upload.keys(), tqdm(range(self.number))):
            time.sleep(3)
            if copy_counter <= self.number:
                params = {'path': f'{self.folder}/{key}',
                            'url': dict_upload[key],
                            'overwrite': 'true'}
                requests.post(url, headers=headers, params=params)
                copy_counter += 1
            else:
                break

        print(f'\nРезервное копирование фотографий завершено!'
              f'\nНа Яндекс диске находятся указанное количество фотографий --> {len(dict_upload)}.')


if __name__ == '__main__':

    vk_user = VK(token, '5.131')

    Yatoken = ''
    yandex_user = Yandex(Yatoken)
    yandex_user.upload_file_to_disk(vk_user.download_dict)
