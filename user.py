import random


class User:
    def __init__(self, user_id, city=None, time=None):
        """Инициализация"""
        self.id = user_id
        self.city = city
        self.img_num = random.randint(0, 2)
        if city is not None:
            self.city = city.title()
        self.time = "непишимне"
        if time is not None:
            self.time = time.rstrip()

    def get_id(self):
        """Возвращаем id чата"""
        return self.id

    def set_city(self, city):
        """Задаем город"""
        self.city = city

    def get_city(self):
        """Возвращаем город пользователя"""
        return self.city

    def get_img_num(self):
        """Возвращаем id чата"""
        self.img_num += 1
        if self.img_num > 3:
            self.img_num = 1
        return self.img_num

    def set_time(self, time):
        """Задаем время уведомлений"""
        self.time = time

    def get_time(self):
        """Возвращаем время уведомлений"""
        return self.time