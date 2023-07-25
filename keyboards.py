import config
import utils

from database import Database
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback
from config import Status
from math import ceil


def startKeyboard():
    keyboard = Keyboard(one_time=True)
    keyboard.add(Text("Вызвать оператора"))
    keyboard.row()
    keyboard.add(Text("Стоимость услуг"), KeyboardButtonColor.POSITIVE)
    return keyboard.get_json()


def materialKeyboard(database: Database):
    keyboard = Keyboard(one_time=True)

    materials = utils.getMaterials(database)
    count = len(materials)
    c = 0

    for material in materials:
        if material.status is Status.STOPPED:
            keyboard.add(Text(material.name), color=KeyboardButtonColor.NEGATIVE)
        else:
            keyboard.add(Text(material.name))

        c += 1
        if c != count:
            keyboard.row()

    return keyboard.get_json()


def extraKeyboard(database: Database, user_id):
    keyboard = Keyboard(one_time=True)

    order = utils.getOrderByUserId(database, user_id)

    if order is None:
        return keyboard.get_json()

    price = ceil(order.material_square / 40) + 4
    button1_color = KeyboardButtonColor.PRIMARY if order.stain is Status.STOPPED else KeyboardButtonColor.POSITIVE
    button2_color = KeyboardButtonColor.PRIMARY if order.paint is Status.STOPPED else KeyboardButtonColor.POSITIVE
    button3_color = KeyboardButtonColor.PRIMARY if order.lacquer is Status.STOPPED else KeyboardButtonColor.POSITIVE

    keyboard.add(Text(f"Морилка +{price}₽"), color=button1_color)
    keyboard.add(Text(f"Краска +{price}₽"), color=button2_color)
    keyboard.row()
    keyboard.add(Text(f"Покрытие лаком +{price}₽"), color=button3_color)
    keyboard.row()
    keyboard.add(Text("Далее"))

    return keyboard.get_json()


def materialSettingsKeyboard(database: Database):
    keyboard = Keyboard(one_time=True, inline=False)

    materials = utils.getMaterials(database)

    for material in materials:
        keyboard.add(Callback(f"ID: {material.id}", payload={"cmd": f"material_id_{material.id}"}),
                     color=KeyboardButtonColor.NEGATIVE)
        keyboard.add(Callback(material.name, payload={"cmd": f"material_name_{material.id}"}))
        keyboard.add(Callback(material.cost, payload={"cmd": f"material_cost_{material.id}"}))
        keyboard.add(Callback(material.thickness_price, payload={"cmd": f"material_thickness_{material.id}"}))

        if material.status is Status.EXISTS:
            keyboard.add(Callback("В наличии", payload={"cmd": f"material_status_{material.id}"}),
                         color=KeyboardButtonColor.POSITIVE)
        else:
            keyboard.add(Callback("В стопе", payload={"cmd": f"material_status_{material.id}"}),
                         color=KeyboardButtonColor.NEGATIVE)
        keyboard.row()

    keyboard.add(Callback("Добавить ➕", payload={"cmd": "add_material"}))
    keyboard.add(Callback("Удалить ➖", payload={"cmd": "delete_material"}))
    keyboard.row()
    keyboard.add(Text("◀️ На главную"))
    return keyboard.get_json()


def removeMaterialKeyboard(database: Database):
    keyboard = Keyboard(one_time=True, inline=False)

    materials = utils.getMaterials(database)

    for material in materials:
        keyboard.add(Callback(f"ID: {material.id} {material.name}", payload={"cmd": f"delete_{material.id}"}))
        keyboard.row()

    keyboard.add(Text("◀️ На главную"))
    return keyboard.get_json()


def operatorKeyboard():
    keyboard = Keyboard(one_time=True)
    keyboard.add(Text("Вызвать оператора"))
    keyboard.row()
    keyboard.add(Text("◀️ На главную"))
    keyboard.get_json()