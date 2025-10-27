from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters.state import StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from environs import Env
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog.widgets.kbd import Button, Row, Column, Url, Select, Group, Back, Next, Cancel, Start, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Calendar
from datetime import date
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User
from aiogram_dialog import Dialog, DialogManager, StartMode, Window, setup_dialogs

env = Env()
env.read_env()

BOT_TOKEN = env('BOT_TOKEN')
CHAT_ID = env('CHAT_ID')

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

router = Router()

order = {}


class StartSG(StatesGroup):
    start = State()
    no_click = State()
    category = State()

    restaurant = State()
    food = State()
    massage = State()
    present = State()
    walk = State()
    excursion = State()

    work = State()
    add_wish_work_repair = State()
    add_wish_work_buy = State()

    car = State()
    add_wish_car_repair = State()
    add_wish_car_buy = State()

    choice_date = State()
    choice_time = State()
    calendar = State()
    result = State()
    send_message = State()

    choice_change = State()
    add_wish = State()
    add_wish_detail = State()
    choice_date_add_wish = State()


# Выбор Категории
async def category_selection(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str):
    categories = await category_getter()
    selected_category = next((category for category in categories['categories'] if str(category[1]) == str(item_id)),
                             None)
    if selected_category:
        dialog_manager.dialog_data['category'] = selected_category[0]
        order.update(dialog_manager.dialog_data)
        print(order)
        category_state = {
            '🥂 Рестораны': StartSG.restaurant, '🍔 Еда': StartSG.food, '💆‍♀️ Массаж': StartSG.massage,
            '🎁 Подарки': StartSG.present, '👫 Прогулки': StartSG.walk, '🏯 Экскурсии': StartSG.excursion,
            '🏠 По дому': StartSG.work, '🚙 Машина': StartSG.car
        }
        await dialog_manager.switch_to(state=category_state[selected_category[0]])


# Выбор подкатегории (ресторана, еды, массажа и т.д.)
async def item_selection(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str, item_type: str):
    getters = {
        'restaurant': restaurant_getter, 'food': food_getter, 'massage': massage_getter,
        'present': present_getter, 'walk': walk_getter, 'excursion': excursion_getter,
        'work': working_getter, 'car': car_getter
    }
    items_data = await getters[item_type]()
    items_key = f"{item_type}s"
    selected_item = next((item for item in items_data[items_key] if item[1] == int(item_id)), None)
    if selected_item:
        dialog_manager.dialog_data['item'] = selected_item[0]
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.choice_date)


# Выбор подкатегории (ХОЗ. РАБОТЫ)
async def item_selection_work(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str,
                              item_type: str):
    getters = {
        'work': working_getter
    }
    items_data = await getters[item_type]()
    items_key = f"{item_type}s"
    selected_item = next((item for item in items_data[items_key] if item[1] == int(item_id)), None)
    if selected_item:
        dialog_manager.dialog_data['item'] = selected_item[0]
        order.update(dialog_manager.dialog_data)
        print(order)
        if selected_item[1] == 3:
            await dialog_manager.switch_to(state=StartSG.add_wish_work_repair)
        elif selected_item[1] == 4:
            await dialog_manager.switch_to(state=StartSG.add_wish_work_buy)
        else:
            await dialog_manager.switch_to(state=StartSG.choice_date)


# Выбор подкатегории (МАШИНА)
async def item_selection_car(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str,
                             item_type: str):
    getters = {
        'car': car_getter
    }
    items_data = await getters[item_type]()
    items_key = f"{item_type}s"
    selected_item = next((item for item in items_data[items_key] if item[1] == int(item_id)), None)
    if selected_item:
        dialog_manager.dialog_data['item'] = selected_item[0]
        order.update(dialog_manager.dialog_data)
        print(order)
        if selected_item[1] == 4:
            await dialog_manager.switch_to(state=StartSG.add_wish_car_repair)
        elif selected_item[1] == 5:
            await dialog_manager.switch_to(state=StartSG.add_wish_car_buy)
        else:
            await dialog_manager.switch_to(state=StartSG.choice_date)


# Назад к выбранной категории
async def back_to_category(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    category_state = {
        '🥂 Рестораны': StartSG.restaurant, '🍔 Еда': StartSG.food, '💆‍♀️ Массаж': StartSG.massage,
        '🎁 Подарки': StartSG.present, '👫 Прогулки': StartSG.walk, '🏯 Экскурсии': StartSG.excursion,
        '🏠 По дому': StartSG.work, '🚙 Машина': StartSG.car
    }
    current_category = order.get('category')
    if current_category in category_state:
        await dialog_manager.switch_to(state=category_state[current_category])


# Выбор даты
async def date_selection(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    dialog_manager.dialog_data['date'] = widget.text.text
    order.update(dialog_manager.dialog_data)
    print(order)


# Выбор времени
async def time_selection(callback: CallbackQuery, widget, dialog_manager: DialogManager, item_id: str):
    times = await time_getter()
    selected_time = next((time for time in times['times'] if time[1] == int(item_id)), None)
    if selected_time:
        dialog_manager.dialog_data['time'] = selected_time[0]
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.result)


# Календарь
async def calendar(callback: CallbackQuery, widget, dialog_manager: DialogManager, selected_date: date):
    dialog_manager.dialog_data['date'] = selected_date.strftime("%d.%m.%Y г.")
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.choice_time)


# Результат
async def result(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    await dialog_manager.switch_to(state=StartSG.result)


# Отправка сообщения
async def send_message(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    message = (f"🚨 <b><u>НОВЫЙ ЗАКАЗ</u></b> 🚨\n\n<b>{order['category']}:</b>   {order['item']}\n"
               f"<b>📆 Дата:</b>   {order['date']}\n<b>🕙 Время:</b>   {order['time']}")
    await bot.send_message(chat_id=CHAT_ID, text=message)


# Новое желание
async def add_wish(callback: CallbackQuery, widget, dialog_manager: DialogManager):
    dialog_manager.dialog_data['category'] = widget.text.text
    order.update(dialog_manager.dialog_data)
    print(order)


def add_wish_detail(text):
    if isinstance(text, str):
        return text
    raise ValueError


async def correct_text(callback: CallbackQuery, widget: TextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['item'] = text
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.choice_date_add_wish)


async def correct_text_work_repair(callback: CallbackQuery, widget: TextInput, dialog_manager: DialogManager,
                                   text: str):
    dialog_manager.dialog_data['item'] = 'Отремонтировать 🛠: ' + text
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.choice_date_add_wish)


async def correct_text_work_buy(callback: CallbackQuery, widget: TextInput, dialog_manager: DialogManager,
                                text: str):
    dialog_manager.dialog_data['item'] = 'Купить 💵: ' + text
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.choice_date_add_wish)


async def correct_text_car_repair(callback: CallbackQuery, widget: TextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['item'] = 'Отремонтировать 🛠: ' + text
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.choice_date_add_wish)


async def correct_text_car_buy(callback: CallbackQuery, widget: TextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.dialog_data['item'] = 'Купить 💵: ' + text
    order.update(dialog_manager.dialog_data)
    print(order)
    await dialog_manager.switch_to(state=StartSG.choice_date_add_wish)


async def error_text(callback: CallbackQuery, widget: ManagedTextInput, dialog_manager: DialogManager,
                     error: ValueError):
    await dialog_manager.switch_to(state=StartSG.add_wish_detail)


# ГЕТТЕРЫ
# Приветствие
async def username_getter(event_from_user: User, **kwargs):
    return {'username': event_from_user.first_name}


# Рестораны
async def category_getter(**kwargs):
    categories = [
        ('🥂 Рестораны', 1), ('🍔 Еда', 2), ('💆‍♀️ Массаж', 3),
        ('🎁 Подарки', 4), ('👫 Прогулки', 5), ('🏯 Экскурсии', 6),
        ('🏠 По дому', 7), ('🚙 Машина', 8)
    ]
    return {'categories': categories}


# Рестораны
async def restaurant_getter(**kwargs):
    restaurants = [
        ('Мамука 🍛', 1), ('Gelateria Italiana 🍝', 2),
        ('The Бык 🥩', 3), ('Chiko 🍱', 4), ('Ханой 🍜', 5)
    ]
    return {'restaurants': restaurants}


# Еда
async def food_getter(**kwargs):
    foods = [
        ('Блинчики 🥞', 1), ('Пельмени 🥟', 2), ('Панкейки 🥞', 3), ('Рыбный суп 🐟', 4), ('Сырный суп 🧀', 5),
        ('Макароны 🍝', 6), ('Пицца 🍕', 7), ('Вкусно и Точка 🍟', 8), ('Оджах 🧇', 9)
    ]
    return {'foods': foods}


# Массаж
async def massage_getter(**kwargs):
    massages = [
        ('"Пяточки" 🦶', 1), ('Ножки 🦵', 2), ('Комплексный 🙌', 3), ('Массажер 🔫', 4)
    ]
    return {'massages': massages}


# Подарки
async def present_getter(**kwargs):
    presents = [
        ('Носки с котенком Гавом 🧦', 1), ('Мармелад 🍡', 2)
    ]
    return {'presents': presents}


# Прогулки
async def walk_getter(**kwargs):
    walks = [
        ('Волжская набережная 🌉', 1), ('Каток на Добрынина ⛸', 2),
        ('Сафари парк 🐇', 3), ('Арт-усадьба Веретьево 🦌', 4)
    ]
    return {'walks': walks}


# Экскурсии
async def excursion_getter(**kwargs):
    excursions = [
        ('Пушкинский музей 🏛', 1)
    ]
    return {'excursions': excursions}


# Хозяйственные работы
async def working_getter(**kwargs):
    works = [
        ('🧹 Помыть пол', 1), ('🛀 Помыть ванну', 2),
        ('🛠 Отремонтировать', 3), ('💵 Купить', 4)
    ]
    return {'works': works}


# Машина
async def car_getter(**kwargs):
    cars = [
        ('🧽 Экстерьер', 1), ('🪮 Интерьер', 2),
        ('🚿 Комплекс', 3), ('🛠 Ремонт', 4),
        ('💵 Купить', 5)
    ]
    return {'cars': cars}


# Время
async def time_getter(**kwargs):
    times = [
        ('10:00 ', 1), ('10:30', 2), ('11:00', 3), ('11:30', 4), ('12:00', 5), ('12:30', 6), ('13:00', 7),
        ('13:30', 8), ('14:00', 9), ('14:30', 10), ('15:00', 11), ('15:30', 12), ('16:00', 13), ('16:30', 14),
        ('17:00', 15), ('17:30', 16), ('18:00', 17), ('18:30', 18), ('19:00', 19), ('19:30', 20), ('20:00', 21),
        ('20:30', 22), ('21:00', 23), ('21:30', 24), ('22:00', 25), ('22:30', 26), ('23:00', 27), ('23:30', 28),
        ('Без времени 🤷‍♀️', 29)]
    return {'times': times}


# Результат
async def result_getter(**kwargs):
    return {'category': order['category'], 'item': order['item'],
            'date': order['date'], 'time': order['time']}


start_dialog = Dialog(
    # ПРИВЕТСТВИЕ
    Window(
        Const('😥 Жаль...\n\nЕсли чего-нибудь захотите - нажмите кнопку "✅ Давай!"'),
        SwitchTo(Const('✅ Давай!'), id='yes', state=StartSG.category),
        state=StartSG.no_click,
    ),
    Window(
        Format('<b>Привет, {username}! 👋☺️</b>\n\nЕсли у Вас есть какое-нибудь желание, '
               'я в этом помогу!\n\n<b>Начинаем?</b>\n\n\n'
               '<i><u>Для подробного ознакомления со всеми предложениями, '
               'а также для добавления нового желания перейдите на официальный сайт</u></i> ⬇️'),
        Url(Const('🌐 Перейти 🌐'), url=Const('https://julia-site.ru/'), id='b_site'),
        Row(
            Next(Const('✅ Давай!'), id='yes'),
            Back(Const('❎ Не хочу!'), id='no'),
        ),
        getter=username_getter,
        state=StartSG.start,
    ),

    # КАТЕГОРИИ
    Window(
        Const('<b>Отлично! Делайте свой выбор!</b>'),
        Group(
            Select(
                Format('{item[0]}'),
                id='category',
                item_id_getter=lambda x: x[1],
                items='categories',
                on_click=category_selection,
            ),
            width=2
        ),
        SwitchTo(Const('🆕 Добавить желание'), id='add_wish', state=StartSG.add_wish),
        Back(Const('◀️ Назад'), id='b_back'),
        state=StartSG.category,
        getter=category_getter,
    ),

    # РЕСТОРАНЫ
    Window(
        Const('Высокой кухней какого <b>ресторана</b> 🥂 желаете себя побаловать?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='restaurant',
                item_id_getter=lambda x: x[1],
                items='restaurants',
                on_click=lambda c, w, d, i: item_selection(c, w, d, i, 'restaurant'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.restaurant,
        getter=restaurant_getter
    ),

    # ЕДА
    Window(
        Const('Хм, и что же Вы хотите, чтобы я <b>приготовил</b> 🥘 или <b>заказал</b> 🍔?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='food',
                item_id_getter=lambda x: x[1],
                items='foods',
                on_click=lambda c, w, d, i: item_selection(c, w, d, i, 'food'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.food,
        getter=food_getter
    ),

    # МАССАЖ
    Window(
        Const('Какой вид <b>массажа</b> 💆‍♀️ хотите выбрать?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='massage',
                item_id_getter=lambda x: x[1],
                items='massages',
                on_click=lambda c, w, d, i: item_selection(c, w, d, i, 'massage'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.massage,
        getter=massage_getter
    ),

    # ПОДАРКИ
    Window(
        Const('Какой <b>подарок</b> 🎁 Вы ждёте от меня?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='present',
                item_id_getter=lambda x: x[1],
                items='presents',
                on_click=lambda c, w, d, i: item_selection(c, w, d, i, 'present'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.present,
        getter=present_getter
    ),

    # ПРОГУЛКИ
    Window(
        Const('И где бы нам с Вами <b>прогуляться</b> 👫?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='walk',
                item_id_getter=lambda x: x[1],
                items='walks',
                on_click=lambda c, w, d, i: item_selection(c, w, d, i, 'walk'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.walk,
        getter=walk_getter
    ),

    # ЭКУСКУРСИИ
    Window(
        Const('Экспозицию какого <b>музея</b> 🏯 желаете посетить?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='excursion',
                item_id_getter=lambda x: x[1],
                items='excursions',
                on_click=lambda c, w, d, i: item_selection(c, w, d, i, 'excursion'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.excursion,
        getter=excursion_getter
    ),

    # ХОЗЯЙСТВЕННЫЕ РАБОТЫ
    Window(
        Const('Какие работы по <b>дому</b> 🏠 необходимо сделать?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='work',
                item_id_getter=lambda x: x[1],
                items='works',
                on_click=lambda c, w, d, i: item_selection_work(c, w, d, i, 'work'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.work,
        getter=working_getter
    ),

    # ХОЗ. РАБОТЫ - ОТРЕМОНТИРОВАТЬ
    Window(
        Const('<b>Напишите что отремонтировать в квартире</b>'),
        TextInput(id='new_wish_work_repair', type_factory=add_wish_detail, on_success=correct_text_work_repair,
                  on_error=error_text),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.work),
        state=StartSG.add_wish_work_repair,
    ),

    # ХОЗ. РАБОТЫ - КУПИТЬ
    Window(
        Const('<b>Напишите что купить домой</b>'),
        TextInput(id='new_wish_work_buy', type_factory=add_wish_detail, on_success=correct_text_work_buy,
                  on_error=error_text),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.work),
        state=StartSG.add_wish_work_buy,
    ),

    # МАШИНА
    Window(
        Const('Какие работы по <b>машине</b> 🚙 необходимо сделать?'),
        Group(
            Select(
                Format('{item[0]}'),
                id='car',
                item_id_getter=lambda x: x[1],
                items='cars',
                on_click=lambda c, w, d, i: item_selection_car(c, w, d, i, 'car'),
            ),
            width=2
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.car,
        getter=car_getter
    ),

    # МАШИНА - ОТРЕМОНТИРОВАТЬ
    Window(
        Const('<b>Напишите что отремонтировать в машине</b>'),
        TextInput(id='new_wish_car_repair', type_factory=add_wish_detail, on_success=correct_text_car_repair,
                  on_error=error_text),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.car),
        state=StartSG.add_wish_car_repair,
    ),

    # МАШИНА - КУПИТЬ
    Window(
        Const('<b>Напишите что купить в машину</b>'),
        TextInput(id='new_wish_car_buy', type_factory=add_wish_detail, on_success=correct_text_car_buy,
                  on_error=error_text),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.car),
        state=StartSG.add_wish_car_buy,
    ),

    # ДАТА
    Window(
        Const('️❤️‍🔥 <b>Прекрасный выбор!</b> ❤️‍🔥\n\nУкажите дату 📆'),
        Group(
            Row(
                SwitchTo(Const('Сегодня 👌'), id='today', state=StartSG.choice_time, on_click=date_selection),
                SwitchTo(Const('Завтра 👉'), id='tomorrow', state=StartSG.choice_time, on_click=date_selection),
                SwitchTo(Const('Без даты 🤷‍♀️'), id='no_date', state=StartSG.choice_time, on_click=date_selection),
            ),
            width=2
        ),
        SwitchTo(Const('Выбрать дату'), id='choice_date', state=StartSG.calendar),
        Button(Const('◀️ Назад'), id='b_back', on_click=back_to_category),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.choice_date
    ),

    # КАЛЕНДАРЬ
    Window(
        Const('Укажите дату 📆'),
        Calendar(id='calendar', on_click=calendar),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.choice_date),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.calendar
    ),

    # ВРЕМЯ
    Window(
        Const('Укажите время 🕙'),
        Group(
            Select(
                Format('{item[0]}'),
                id='time',
                item_id_getter=lambda x: x[1],
                items='times',
                on_click=time_selection,
            ),
            width=4
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.choice_date),
        SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        state=StartSG.choice_time,
        getter=time_getter
    ),

    # РЕЗУЛЬТАТ
    Window(
        Format('<b>Подтвердите Ваш заказ!</b>\n\n'
               '<b>{category}:</b>   {item}\n'
               '<b>📆 Дата:</b>   {date}\n'
               '<b>🕙 Время:</b>   {time}'),
        SwitchTo(Const('✅ Верно!'), id='yes', state=StartSG.send_message, on_click=send_message),
        Row(
            SwitchTo(Const('🔄 Изменить!'), id='change', state=StartSG.choice_change),
            SwitchTo(Const('❎ Отменить заказ!'), id='cancel', state=StartSG.no_click),
        ),
        getter=result_getter,
        state=StartSG.result
    ),

    # ВЕРНО
    Window(
        Const('<b>Ваш заказ сформирован!</b>'),
        SwitchTo(Const('✅ Создать новый заказ'), id='new_order', state=StartSG.category),
        state=StartSG.send_message
    ),

    # ИЗМЕНИТЬ
    Window(
        Const('<b>Что Вы хотите изменить?</b>'),
        Group(
            Row(
                SwitchTo(Const('🔠 Категорию'), id='category', state=StartSG.category),
                SwitchTo(Const('🥂 Ресторан'), id='restaurant', state=StartSG.restaurant),
                SwitchTo(Const('🥘 Блюдо'), id='food', state=StartSG.food),
                SwitchTo(Const('💆‍♀️ Массаж'), id='massage', state=StartSG.massage),
                SwitchTo(Const('🎁 Подарки'), id='presents', state=StartSG.present),
                SwitchTo(Const('👫 Прогулки'), id='walks', state=StartSG.walk),
                SwitchTo(Const('🏯 Экскурсии'), id='excursions', state=StartSG.excursion),
                SwitchTo(Const('🏠 По дому'), id='works', state=StartSG.work),
                SwitchTo(Const('🚙 Машина'), id='cars', state=StartSG.car),
                SwitchTo(Const('📆 Дату'), id='date', state=StartSG.calendar, on_click=date_selection),
                SwitchTo(Const('🕙 Время'), id='time', state=StartSG.choice_time),
            ),
            width=3,
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.result),
        state=StartSG.choice_change
    ),

    # НОВОЕ ЖЕЛАНИЕ
    Window(
        Const('<b>Выберете категорию 🔠</b>'),
        Group(
            Row(
                SwitchTo(Const('🥂 Ресторан'), id='restaurant', state=StartSG.add_wish_detail, on_click=add_wish),
                SwitchTo(Const('🥘 Блюдо'), id='food', state=StartSG.add_wish_detail, on_click=add_wish),
                SwitchTo(Const('💆‍♀️ Массаж'), id='massage', state=StartSG.add_wish_detail, on_click=add_wish),
                SwitchTo(Const('🎁 Подарки'), id='presents', state=StartSG.add_wish_detail, on_click=add_wish),
                SwitchTo(Const('👫 Прогулки'), id='walks', state=StartSG.add_wish_detail, on_click=add_wish),
                SwitchTo(Const('🏯 Экскурсии'), id='excursions', state=StartSG.add_wish_detail, on_click=add_wish),
                SwitchTo(Const('🏠 По дому'), id='works', state=StartSG.add_wish_detail, on_click=add_wish),
                SwitchTo(Const('🚙 Машина'), id='cars', state=StartSG.add_wish_detail, on_click=add_wish),
            ),
            width=2,
        ),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.category),
        state=StartSG.add_wish,
    ),

    # ЗАПИСЬ ЖЕЛАНИЯ
    Window(
        Const('<b>Напишите Ваше желание</b>'),
        TextInput(id='new_wish', type_factory=add_wish_detail, on_success=correct_text, on_error=error_text),
        SwitchTo(Const('◀️ Назад'), id='b_back', state=StartSG.add_wish),
        state=StartSG.add_wish_detail,
    ),

    # ДАТА НОВОГО ЖЕЛАНИЯ
    Window(
        Const('️❤️‍🔥 <b>Прекрасный выбор!</b> ❤️‍🔥\n\nУкажите дату 📆'),
        Group(
            Row(
                SwitchTo(Const('Сегодня 👌'), id='today', state=StartSG.choice_time, on_click=date_selection),
                SwitchTo(Const('Завтра 👉'), id='tomorrow', state=StartSG.choice_time, on_click=date_selection),
                SwitchTo(Const('Без даты 🤷‍♀️'), id='no_date', state=StartSG.choice_time, on_click=date_selection),
            ),
            width=2
        ),
        SwitchTo(Const('Выбрать дату'), id='choice_date', state=StartSG.calendar),
        SwitchTo(Const('Назад'), id='b_back', state=StartSG.add_wish_detail),
        state=StartSG.choice_date_add_wish
    ),
)


# Это классический хэндлер, который будет срабатывать на команду /start
@router.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


dp.include_router(router)
dp.include_router(start_dialog)
setup_dialogs(dp)
dp.run_polling(bot)
