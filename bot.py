import config
import keyboards
import utils

from config import API_TOKEN, State, Status
from database import Database
from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle.dispatch.rules.base import FromUserRule, PayloadRule
from vkbottle import GroupEventType
from math import ceil


bot = Bot(token=API_TOKEN)
database = Database("database.db")
utils.initDatabase(database)

CURRENT_MATERIAL_ID = None


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


@bot.on.message(
    command=("mat", 0)
)
async def materialSettingsHandler(message: Message):
    user_id = message.from_id
    utils.setUserState(database, user_id, State.MATERIAL_SETTINGS)
    await message.answer("Таблица материалов:", keyboard=keyboards.materialSettingsKeyboard(database))


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    PayloadRule({"cmd": "add_material"}),
)
async def addHandler(event: MessageEvent):
    user_id = event.object.user_id
    utils.setUserState(database, user_id, State.ADD_MATERIAL)
    await event.send_message("Введите название, цену за толщину и стоимость материала через запятую. Пример: \"Сталь, 20, 0.3\"")


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    PayloadRule({"cmd": "delete_material"}),
)
async def deleteHandler(event: MessageEvent):
    user_id = event.object.user_id
    utils.setUserState(database, user_id, State.DELETE_MATERIAL)
    await event.send_message("Выберите материал для удаления", keyboard=keyboards.removeMaterialKeyboard(database))


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.ADD_MATERIAL
)
async def addMaterialHandler(message: Message):
    user_id = message.from_id
    name, thickness_price, cost = message.text.split(",")

    database.commit("INSERT INTO materials(name, thickness_price, cost, status) VALUES(?, ?, ?, ?)", [name, thickness_price, cost, Status.EXISTS])
    utils.setUserState(database, user_id, State.MATERIAL_SETTINGS)

    await message.answer("Материал успешно добавлен!")
    await message.answer("Таблица материалов:", keyboard=keyboards.materialSettingsKeyboard(database))


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    func=lambda event: utils.getUserState(database, event.object.user_id) is State.DELETE_MATERIAL
)
async def deleteMaterialtHandler(event: MessageEvent):
    user_id = event.object.user_id
    material_id = event.object.payload.get("cmd").split("_")[1]

    database.commit("DELETE FROM materials WHERE id = ?", [material_id])

    utils.setUserState(database, user_id, State.MATERIAL_SETTINGS)

    await event.show_snackbar(f"Материал (ID: {material_id}) успешно удалён")
    await event.send_message("Таблица материалов:", keyboard=keyboards.materialSettingsKeyboard(database))


@bot.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    func=lambda event: utils.getUserState(database, event.object.user_id) is State.MATERIAL_SETTINGS
)
async def materialEditHandler(event: MessageEvent):
    user_id = event.object.user_id
    cmd = event.object.payload.get("cmd")

    if not cmd.startswith("material"):
        return

    material = utils.getMaterialById(database, cmd.split("_")[2])
    global CURRENT_MATERIAL_ID
    CURRENT_MATERIAL_ID = material.id

    if cmd.startswith("material_id"):
        await event.show_snackbar(f"Нельзя изменить ID материала ({material.name})")

    elif cmd.startswith("material_name"):
        utils.setUserState(database, user_id, State.EDIT_MATERIAL_NAME)
        await event.send_message(f"Введите новое название для материала (ID: {CURRENT_MATERIAL_ID} {material.name})")

    elif cmd.startswith("material_cost"):
        utils.setUserState(database, user_id, State.EDIT_MATERIAL_COST)
        await event.send_message(f"Введите новую базовую цену для материала (ID: {CURRENT_MATERIAL_ID} {material.name})")

    elif cmd.startswith("material_thickness"):
        utils.setUserState(database, user_id, State.EDIT_MATERIAL_THICKNESS)
        await event.send_message(f"Введите новую цену за толщину материала (ID: {CURRENT_MATERIAL_ID} {material.name})")

    elif cmd.startswith("material_status"):
        if material.status is Status.EXISTS:
            database.commit("UPDATE materials SET status = ? WHERE id = ?", [Status.STOPPED, CURRENT_MATERIAL_ID])
        else:
            database.commit("UPDATE materials SET status = ? WHERE id = ?", [Status.EXISTS, CURRENT_MATERIAL_ID])
        await event.show_snackbar(f"Статус материала (ID: {CURRENT_MATERIAL_ID} {material.name}) успешно изменён")
        await event.send_message("Таблица материалов:", keyboard=keyboards.materialSettingsKeyboard(database))


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.EDIT_MATERIAL_NAME
)
async def materialNameEditHandler(message: Message):
    user_id = message.from_id

    database.commit("UPDATE materials SET name = ? WHERE id = ?", [message.text, CURRENT_MATERIAL_ID])
    utils.setUserState(database, user_id, State.MATERIAL_SETTINGS)

    await message.answer("Название успешно изменено!")
    await message.answer("Таблица материалов:", keyboard=keyboards.materialSettingsKeyboard(database))


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.EDIT_MATERIAL_COST
)
async def materialCostEditHandler(message: Message):
    user_id = message.from_id

    database.commit("UPDATE materials SET cost = ? WHERE id = ?", [message.text, CURRENT_MATERIAL_ID])
    utils.setUserState(database, user_id, State.MATERIAL_SETTINGS)

    await message.answer("Цена за толщину материала успешно изменена!")
    await message.answer("Таблица материалов:", keyboard=keyboards.materialSettingsKeyboard(database))


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.EDIT_MATERIAL_THICKNESS
)
async def materialThicknessEditHandler(message: Message):
    user_id = message.from_id

    database.commit("UPDATE materials SET thickness_price = ? WHERE id = ?", [message.text, CURRENT_MATERIAL_ID])
    utils.setUserState(database, user_id, State.MATERIAL_SETTINGS)

    await message.answer("Базовая цена успешно изменена!")
    await message.answer("Таблица материалов:", keyboard=keyboards.materialSettingsKeyboard(database))



@bot.on.message(FromUserRule(), text="Начать")
@bot.on.message(FromUserRule(), text="◀️ На главную")
async def startHandler(message: Message):
    user_id = message.from_id

    result = database.getOne("SELECT user_id FROM users WHERE user_id = ?", [user_id])

    if result is None:
        database.commit("INSERT INTO users VALUES(?, ?)", [user_id, State.START])
        database.commit("INSERT INTO orders VALUES(?, NULL, NULL, NULL, NULL, ?, ?, ?)", [user_id, Status.STOPPED, Status.STOPPED, Status.STOPPED])

    utils.setUserState(database, user_id, State.START)
    users_info = await bot.api.users.get(message.from_id)

    await message.answer(
        message="Здравствуйте, {}, выберите действие".format(users_info[0].first_name),
        keyboard=keyboards.startKeyboard()
    )


@bot.on.message(FromUserRule(), text="Вызвать оператора")
async def startHandler(message: Message):
    user_id = message.from_id

    utils.setUserState(database, user_id, State.START)
    users_info = await bot.api.users.get(message.from_id)

    await message.answer(
        message="Мы вызвали оператора, с Вами скоро свяжутся",
        keyboard=keyboards.startKeyboard()
    )

    await bot.api.messages.send(
        user_id=config.ADMIN_ID,
        random_id=0,
        message=f"Новый ушлёпок:\n{users_info[0].first_name} {users_info[0].last_name}\n"
    )


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.START,
    text="Стоимость услуг"
)
async def mainMenuHandler(message: Message):
    user_id = message.from_id

    utils.setUserState(database, user_id, State.MATERIAL)
    materials = utils.getMaterials(database)

    if materials is None:
        return

    await message.answer(
        message="Выберите материал из списка:",
        keyboard=keyboards.materialKeyboard(database)
    )


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.MATERIAL
)
async def materialHandler(message: Message):
    user_id = message.from_id
    material = utils.getMaterialByName(database, message.text)

    if material is None:
        await message.answer(
            message="Такого материала нет в списке",
            keyboard=keyboards.materialKeyboard(database)
        )
        return

    if material.status is Status.STOPPED:
        await message.answer(
            message="К сожалению, данного материла нет в наличии, выберите доступный из списка",
            keyboard=keyboards.materialKeyboard(database)
        )
        return

    database.commit("UPDATE orders SET material_id = ? WHERE user_id = ?", [material.id, user_id])
    utils.setUserState(database, user_id, State.MATERIAL_SQUARE)
    await message.answer(
        "Укажите площадь материала (в квадратных сантиметрах)",
        keyboard=keyboards.operatorKeyboard()
    )


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.MATERIAL_SQUARE
)
async def materialSquareHandler(message: Message):
    user_id = message.from_id

    if not isfloat(message.text):
        await message.answer(
            "Неверный формат введённых данных, необходимо число (Например: 12 или 12.5)",
            keyboard=keyboards.operatorKeyboard())
        return

    database.commit("UPDATE orders SET material_square = ? WHERE user_id = ?", [ceil(float(message.text)), user_id])
    utils.setUserState(database, user_id, State.LENGTH)
    await message.answer(
        "Укажите длину реза (в метрах)",
        keyboard=keyboards.operatorKeyboard()
    )


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.LENGTH
)
async def lengthHandler(message: Message):
    user_id = message.from_id

    if not isfloat(message.text):
        await message.answer(
            "Неверный формат введённых данных, необходимо число (Например: 12 или 12.5)",
            keyboard=keyboards.operatorKeyboard()
        )
        return

    database.commit("UPDATE orders SET length = ? WHERE user_id = ?", [ceil(float(message.text)), user_id])
    utils.setUserState(database, user_id, State.GRAV_SQUARE)
    await message.answer(
        "Укажите площадь гравировки (в квадратных сантиметрах)",
        keyboard=keyboards.operatorKeyboard()
    )


@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.GRAV_SQUARE
)
async def gravSquareHandler(message: Message):
    user_id = message.from_id

    if not isfloat(message.text):
        await message.answer(
            "Неверный формат введённых данных, необходимо число (Например: 12 или 12.5)",
            keyboard=keyboards.operatorKeyboard()
        )
        return

    database.commit("UPDATE orders SET grav_square = ? WHERE user_id = ?", [ceil(float(message.text)), user_id])
    utils.setUserState(database, user_id, State.EXTRA_SERVICES)
    await message.answer("Выберите дополнительные услуги", keyboard=keyboards.extraKeyboard(database, user_id))

@bot.on.message(
    FromUserRule(),
    func=lambda message: utils.getUserState(database, message.from_id) is State.EXTRA_SERVICES
)
async def extraHandler(message: Message):
    user_id = message.from_id

    order = utils.getOrderByUserId(database, user_id)

    if order is None:
        return

    if message.text.startswith("Морилка"):
        order.stain = Status.EXISTS if order.stain is Status.STOPPED else Status.STOPPED
        database.commit("UPDATE orders SET stain = ? WHERE user_id = ?", [order.stain, user_id])

        if order.paint is Status.EXISTS:
            database.commit("UPDATE orders SET paint = ? WHERE user_id = ?", [Status.STOPPED, user_id])
    elif message.text.startswith("Краска"):
        order.paint = Status.EXISTS if order.paint is Status.STOPPED else Status.STOPPED
        database.commit("UPDATE orders SET paint = ? WHERE user_id = ?", [order.paint, user_id])

        if order.stain is Status.EXISTS:
            database.commit("UPDATE orders SET stain = ? WHERE user_id = ?", [Status.STOPPED, user_id])
    elif message.text.startswith("Покрытие лаком"):
        order.lacquer = Status.EXISTS if order.lacquer is Status.STOPPED else Status.STOPPED
        database.commit("UPDATE orders SET lacquer = ? WHERE user_id = ?", [order.lacquer, user_id])
    elif message.text == "Далее":
        utils.setUserState(database, user_id, State.START)
        order = utils.getOrderByUserId(database, user_id)

        if order.material is None:
            return

        work = ceil(order.material_square / 40)
        if work < 5:
            work = 5

        price = (order.material_square * order.material.cost) + \
        (order.length * order.material.thickness_price) + \
        (order.grav_square * 3) + \
        (order.stain * work) + \
        (order.paint * work) + \
        (order.lacquer * work) + \
        work

        if price < 50:
            price = 50

        await message.answer(
            f"Стоимость работы: {ceil(price)}₽",
            keyboard=keyboards.operatorKeyboard()
        )

        return

    await message.answer("Выберите дополнительные услуги", keyboard=keyboards.extraKeyboard(database, user_id))


if __name__ == '__main__':
    bot.run_forever()
