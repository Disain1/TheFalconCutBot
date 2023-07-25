import sqlite3


class Database:
    def __init__(self, path: str):
        self.path = path
        self.__conn = sqlite3.connect(path)
        self.__c = self.__conn.cursor()

    def getOne(self, query: str, params: list = []):
        result = self.__c.execute(query, params).fetchone()
        self.__conn.execute
        return result

    def getAll(self, query: str, params: list = []):
        result = self.__c.execute(query, params).fetchall()
        self.__conn.execute
        return result

    def commit(self, query: str, params: list = []):
        self.__c.execute(query, params)
        self.__conn.commit()

    def close(self):
        self.__conn.close()