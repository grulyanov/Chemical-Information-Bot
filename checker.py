from config import LIST_SOURCES


class UserChecker:
    """
    Класс для взаимодействия с предпочтениями пользователя
    """

    def __init__(self):
        self.storage = {}

    def check_user(self, chat_id: str) -> bool:
        """
        Проверка есть ли пользователь в базе

        :param chat_id: Id чата
        :return:        True, если есть пользователь, иначе False
        """
        return True if chat_id in self.storage else False

    def _create_storage(self, chat_id):
        """
        Создает хранение для пользователя
        :param chat_id: Id чата
        """
        self.storage[chat_id] = {source: True for source in LIST_SOURCES}

    def change_settings(self, chat_id: str, source: str, type_: str) -> None:
        """
        Изменение использования источника

        :param chat_id: Id чата
        :param source:  Источник поиска
        :param type_:   Ищем по нему или нет
        """
        if not self.check_user(chat_id):
            self._create_storage(chat_id)
        self.storage[source] = type_

    def get_settings(self, chat_id: str) -> dict:
        """
        Получение настроек пользователя
        :param chat_id:
        :return:
        """
        if not self.check_user(chat_id):
            self._create_storage(chat_id)
        return self.storage[chat_id]
