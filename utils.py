from database import Database
from config import Status


def initDatabase(db: Database):
    # СОЗДАНИЕ ТАБЛИЦ
    db.commit("CREATE TABLE IF NOT EXISTS users(user_id INTEGER, state INTEGER)")

    db.commit("""CREATE TABLE IF NOT EXISTS orders(
    user_id INTEGER,
    material_id INTEGER,
    material_square FLOAT,
    length FLOAT,
    grav_square FLOAT,
    stain INTEGER,
    paint INTEGER,
    lacquer INTEGER
    )""")

    db.commit("CREATE TABLE IF NOT EXISTS materials(id INTEGER PRIMARY KEY, name STRING, cost FLOAT, thickness_price INTEGER, status INTEGER)")

    # ДОБАВЛЕНИЕ БАЗОВЫХ МАТЕРИАЛОВ
    c = db.getOne("SELECT count(*) FROM materials")[0]  # если таблица с материалами пустая
    if c == 0:
        db.commit("INSERT INTO materials(name, cost, thickness_price, status) VALUES(?, ?, ?, ?)", ["Фанера 3мм", 0.04, 15, Status.EXISTS])
        db.commit("INSERT INTO materials(name, cost, thickness_price, status) VALUES(?, ?, ?, ?)", ["Фанера 4мм", 0.05, 17, Status.EXISTS])
        db.commit("INSERT INTO materials(name, cost, thickness_price, status) VALUES(?, ?, ?, ?)", ["Фанера 6мм", 0.08, 25, Status.EXISTS])
        db.commit("INSERT INTO materials(name, cost, thickness_price, status) VALUES(?, ?, ?, ?)", ["Свой материал", 0, 0, Status.EXISTS])


def getUserState(db: Database, user_id: int):
    result = db.getOne("SELECT state FROM users WHERE user_id = ?", [user_id])

    if result is not None:
        return result[0]

    return None


def setUserState(db: Database, user_id: int, state: int):
    db.commit("UPDATE users SET state = ? WHERE user_id = ?", [state, user_id])


class Material:
    def __init__(self, id, name, cost, thickness_price, status):
        self.id = id
        self.name = name
        self.cost = cost
        self.thickness_price = thickness_price
        self.status = status

    def __str__(self) -> str:
        return super().__str__()


class Order:
    def __init__(self, user_id, material: Material, material_square, length, grav_square, stain, paint, lacquer):
        self.user_id = user_id
        self.material = material
        self.material_square = material_square
        self.length = length
        self.grav_square = grav_square
        self.stain = stain
        self.paint = paint
        self.lacquer = lacquer

    def __str__(self) -> str:
        return super().__str__()


def getMaterialByName(db: Database, name):
    result = db.getOne("SELECT * FROM materials WHERE name = ?", [name])

    if result is None:
        return None

    return Material(result[0], result[1], result[2], result[3], result[4])


def getMaterialById(db: Database, id):
    result = db.getOne("SELECT * FROM materials WHERE id = ?", [id])

    if result is None:
        return None

    return Material(result[0], result[1], result[2], result[3], result[4])


def getMaterials(db: Database):
    result = db.getAll("SELECT * FROM materials")

    if result is None:
        return None

    return [Material(row[0], row[1], row[2], row[3], row[4]) for row in result]


def getOrderByUserId(db: Database, user_id):
    result = db.getOne("SELECT * FROM orders LEFT JOIN materials ON orders.material_id = materials.id WHERE user_id = ? ", [user_id])

    if result is None:
        return None

    return Order(
        user_id,
        Material(result[8], result[9], result[10], result[11], result[12]),
        result[2],
        result[3],
        result[4],
        result[5],
        result[6],
        result[7]
    )

