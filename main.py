import ftplib
import json
import threading
import sys
import os


class FTP:
    # Инициализируем сервер
    def __init__(self, ip, port, username, password):
        self.ip = ip
        self.port = port
        self.user = username
        self.password = password
        try:
            # Пытаемся подключиться к серверу и авторизироваться
            self.serv = ftplib.FTP(ip, port)
            self.serv.login(username, password)
        except Exception as e:
            sys.exit(e)


class Json:
    def __init__(self, filename):
        # Пытаемся открыть файл
        try:
            with open(filename, 'r') as f:
                self.file = json.load(f)
        except Exception as e:
            sys.exit(e)

    # Функция для получения настроек для подключения к серверу
    def get_value_for_setup(self, value):
        try:
            return self.file['ftp_configs'][value]
        except Exception as e:
            # Выходим, если в конфиге нет определенных значений
            sys.exit("В config.json нет {}".format(e))

    # Получаем количество файлов для копирования
    def files_amount(self,):
        return len(self.file['files'])


# Функция для копирования файла
def full_transfer(file, serv, dir):
    f_name = (file['f_name'])   #
    p_from = (file['p_from'])   # Получаем пути передачи
    p_to = (file['p_to'])       #
    full_path_from = p_from + '/' + f_name
    try:
        # Перемещаемся в нужную директорию; вставляем туда файл; перемещаемся обратно в корень FTP
        serv.cwd(p_to)
        serv.storbinary('STOR ' + f_name, open(full_path_from, 'rb'))
        serv.cwd(dir)
    except Exception as e:
        print(e)
        # raise SystemExit(1)
        # sys.exit(e)
        # Хотел выйти с exit кодом 1, но те 2 строчки выше почему-то не вызываются как в остальных эсепшнах ¯\_(ツ)_/¯

# Путь к конфиг файлу ↓
data = Json("config.json")

# Получаем значения для запуска сервера (actually, I think, there is some room for improvement)
ip = data.get_value_for_setup('ip')
port = data.get_value_for_setup('port')
user = data.get_value_for_setup('user')
password = data.get_value_for_setup('password')

if data.files_amount() < 1:
    sys.exit("Нет файлов для копирования!")

# Лист для потоков
thrs = []

try:
    # Для каждого файла из конфига подключамся к FTP и инициализируем потоки с функцией копирования файла
    # (если подключение вынести за цикл for, то ничего работать не будет, странно)
    for file in data.file['files']:
        ftp = FTP(ip, port, user, password).serv
        t = threading.Thread(target=full_transfer, args=(file, ftp, ftp.pwd()))
        thrs.append(t)
except Exception:
    sys.exit("Ошибка в инициализации потоков!")

# Запускаем потоки
try:
    for t in thrs:
        t.start()
except Exception:
    sys.exit("Ошибка в запуске потоков!")
