import ftplib
import json
import threading
import sys
from multiprocessing import cpu_count

# Введите путь для файла config.json
config_path = "config.json"

# Введите ограничение на количество потоков, заменив None (иначе используется количество доступных потоков в системе)
cpus = None


class FTP:
    # Инициализируем сервер с информацией, получаемой из файла
    def __init__(self, file):
        self.ip = file.get_value_for_setup('ip')
        self.port = file.get_value_for_setup('port')
        self.user = file.get_value_for_setup('user')
        self.password = file.get_value_for_setup('password')
        try:
            # Пытаемся подключиться к серверу и авторизироваться
            self.serv = ftplib.FTP(self.ip, self.port)
            if self.user == "anonymous":
                self.serv.login(self.user)
            else:
                self.serv.login(self.user, self.password)  # Добавил отдельную конфигурацию для анонимных серверов,
        except Exception as e:                             # но оно авторизировалось бы и без этого, если оставить поле пароля пустым
            sys.exit(e)


class Json:
    def __init__(self, filename):
        # Пытаемся открыть файл
        try:
            f = open(filename, 'r')
            self.file = json.load(f)
            f.close()
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


# Конфигурационный файл
data = Json(config_path)


if data.files_amount() < 1:
    sys.exit("Нет файлов для копирования!")

# Лист для потоков
thrs = []

try:
    # Для каждого файла из конфига подключамся к FTP и инициализируем потоки с функцией копирования файла
    # (если подключение вынести за цикл for, то ничего работать не будет, странно)

    for file in data.file['files']:
        ftp = FTP(data).serv
        t = threading.Thread(target=full_transfer, args=(file, ftp, ftp.pwd()))
        thrs.append(t)
except Exception:
    sys.exit("Ошибка в инициализации потоков!")

# Запускаем потоки (если файлов меньше кол-ва потоков на устройстве, то запускаем кол-во потоков, равное
# кол-ву файлов; иначе - каждый раз запускаем по макс кол-ву тредов, а в конце - оставшееся
# Если введено ограничение на потоки - используем его; если нет - берем количество потоков в системе

if cpus is None:
    cpus = cpu_count()
used_cpus = cpus
upper = 0
try:
    while upper < len(thrs):
        lower = upper
        if len(thrs) < used_cpus:
            upper = len(thrs)
        else:
            upper += cpus
            used_cpus += cpus
        for i in range(lower, upper):
            thrs[i].start()
        for i in range(lower, upper):
            thrs[i].join()

except Exception as e:
    sys.exit(e)
