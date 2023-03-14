from user import User


class Users:
    def __init__(self, filename):
        """Инициализация"""
        self.filename = filename
        self.users = {}
        with open(self.filename, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                id, city, time = line.split(';')
                self.add_start(User(int(id), city, time=time))

    def add_start(self, user):
        """Бот запоминает все активные чаты"""
        if not self.is_exist(user.get_id()):
            self.users[user.get_id()] = user

    def add_new(self, user):
        """Добавляем новый чат"""
        if not self.is_exist(user.get_id()):
            self.users[user.get_id()] = user

            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(str(user.get_id()) + ';' + str(user.get_city()) + ';' + str(user.get_time()) + '\n')

    def set_city(self, user_id, city):
        """Меняем город"""
        if user_id in self.users.keys():
            self.users[user_id].set_city(city)

            with open(self.filename, 'w', encoding='utf-8') as f:
                for user in self.users.values():
                    f.write(str(user.get_id()) + ';' + str(user.get_city()) + ';' + str(user.get_time()) + '\n')

    def set_time(self, user_id, time):
        """Меняем время уведомлений"""
        if user_id in self.users.keys():
            self.users[user_id].set_time(time)

            with open(self.filename, 'w', encoding='utf-8') as f:
                for user in self.users.values():
                    f.write(str(user.get_id()) + ';' + str(user.get_city()) + ';' + str(user.get_time()) + '\n')

    def find(self, user_id):
        """Ищем чат по id"""
        if user_id in self.users.keys():
            return self.users[user_id]
        else:
            return None

    def is_exist(self, user_id):
        """Проверяем, есть ли чат среди активных"""
        if user_id in self.users.keys():
            return True
        else:
            return False

    def remove(self, user_id):
        """Удаляем чат из списка активных"""
        self.users.pop(user_id)

        with open(self.filename, 'w', encoding='utf-8') as f:
            for user in self.users.values():
                f.write(str(user.get_id()) + ';' + str(user.get_city()) + ';' + str(user.get_time()) + '\n')