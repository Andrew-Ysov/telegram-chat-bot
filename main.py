import telebot  
from telebot import types

from working_with_db import *
from helpers import *
from token import token


# в переменной bot указан уникальный для каждого бота токен, 
# его можно получить у @BotFather и использовать свой, тогда можно 
# создать и оформить другого бота 
bot = telebot.TeleBot(token)
login = ''
home_name = ''
service = ''


# реакция на команду /help
# вывод сообщения, объясняющего, что делает бот и как им пользоваться
@bot.message_handler(commands=['help'])
def help(message):
    about_me = ''' Бот создан для того, чтобы хранить данные по комунальным счетам.
Перед использованием бота в нём нужно зарегистрироваться или войти в аккаунт. \n
Касательно функционала: в боте можно хранить и вносить данные по счетам за воду, 
электричество, газ, отопление, также можно изменять уже введённые данные, если в них была ошибка. \n
Для безопасности пользователей при вводе пароля он сразу хэшируется. '''
    
    bot.send_message(message.chat.id, about_me)


# запуск бота, реакция на команду /start
# выводит две кнопки: вход и регистрация
@bot.message_handler(commands=['start'])
def start(message):

    create_users_table()

    markup = types.InlineKeyboardMarkup()

    check_in = types.InlineKeyboardButton('вход', callback_data='check_in')
    registration = types.InlineKeyboardButton('регистрация', callback_data='registration')

    markup.add(check_in, registration)

    bot.send_message(message.chat.id, 'Войдите в аккаунт или зарегистрируйтесь', reply_markup=markup)


# функция для обработки всех появляющихся кнопок,
# в зависимости от кнопки вызывется определённая функция
@bot.callback_query_handler(func=lambda callback: True)
def buttons(callback):
    global login
    global home_name
    global service
    
    # получение номера телефона от пользователя для регистрации
    if callback.data == 'registration':
        bot.send_message(callback.message.chat.id, 
                     'введите номер телефона, например:\n (79591234567 или 7 959 123 45 67)')
        bot.register_next_step_handler(callback.message, registration)
        
    # получение номера телефона от пользователя для входа в аккаунт 
    elif callback.data == 'check_in':
        bot.send_message(callback.message.chat.id, 
                     'введите номер телефона, например:\n (79591234567 или 7 959 123 45 67)')
        bot.register_next_step_handler(callback.message, check_in)
    
    # обработка кнопки выбора дома из списка существующих
    elif callback.data.split()[0] == 'choose':
        login = callback.data.split()[1]
        choose_home(callback.message, login)

    # обработка кнопки 'создание нового'
    elif callback.data.split()[0] == 'create':
        login = callback.data.split()[1]
        bot.send_message(callback.message.chat.id, 'дайте уникальное название новому жилью')
        bot.register_next_step_handler(callback.message, create_new_home, login)
    
    # после выбора дома пользователем, 
    # имя дома сохраняется в отдельной переменной для дальнейшего использования,
    # пользователь переходит в главное меню
    elif callback.data in get_list_of_homes(login):
        home_name = callback.data 
        main_menu(callback.message)
             
    # обработка кнопок выбора функция и действий пользователем
    elif callback.data == 'получить последние счета':
        get_all_bills(callback.message, login, home_name)  
    elif callback.data == 'получить счета за год':
        get_bills_for_year(callback.message, login, home_name)
    elif callback.data == 'получить счёт':
        service = callback.data
        choose_bill(callback.message)
    elif callback.data == 'добавить счёт':
        service = callback.data
        choose_bill(callback.message)
    elif callback.data == 'изменить счёт':
        service = callback.data
        choose_bill(callback.message)

    # обработка кнопок выбора услуг пользователем
    elif callback.data in ['electricity', 'water', 'gas', 'heating']:

        bill = callback.data
        if service == 'получить счёт':
            choosing_service(callback.message, service, bill, login, home_name)
        else:
            bot.send_message(callback.message.chat.id, f'введите показания счётчика')
            bot.register_next_step_handler(callback.message, choosing_service, 
                                           service, bill, login, home_name)


# регистрация, после получения номера телефона, проверка правильности номера
# получение пароля или отработка неправильного (уже занятого) номера телефона
def registration(message):
    global login
    login = message.text.strip()
    login = ''.join(login.split())
    
    if is_valid_login(login, True):

        bot.send_message(message.chat.id, 'введите пароль')
        bot.register_next_step_handler(message, get_password, login)
    else:
        if is_login_in_use(login):
            bot.send_message(message.chat.id, 'такой номер уже используется')
        else:
            bot.send_message(message.chat.id, 'неправильный номер телефона, введите 11 цифр вашего номера')
        bot.register_next_step_handler(message, registration)


# получение пароля, его хэширование
def get_password(message, login):
    hash_password = hashing(message.text.strip())
    
    register_user(login, hash_password)
    
    create_user_db(login)

    bot.send_message(message.chat.id, 'вы зарегистрированы')
    bot.send_message(message.chat.id, 'теперь нужно дать название жилью, о котором будут храниться данные')
    bot.register_next_step_handler(message, create_new_home, login)


# вход в аккаунт, идентификация пользователя, проверка правильности номера телефона
def check_in(message):
    login = message.text.strip()
    login = ''.join(login.split())

    if not is_valid_login(login, False):
        bot.send_message(message.chat.id, ('такой номер телефона не используется, ' 
                                           'зарегистрируйтесь или введите правильный номер'))
        start(message)
    else:
        bot.send_message(message.chat.id, 'введите пароль')
        bot.register_next_step_handler(message, autentification, login)


# аутентификация (проверка правильности хэшированого пароля)
def autentification(message, login):
    hash_password = hashing(message.text.strip())

    if is_password_correct(login, hash_password):
        bot.send_message(message.chat.id, 'пароль правильный, вы вошли в аккаунт')

        markup = types.InlineKeyboardMarkup()

        choose_home_btn = types.InlineKeyboardButton('выбрать дом', callback_data=f'choose {login}')
        create_home_btn = types.InlineKeyboardButton('создать ещё один дом', callback_data=f'create {login}')

        markup.row(choose_home_btn, create_home_btn)
        bot.send_message(message.chat.id, 'что вы будете делать дальше?', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'пароль не верный, проверьте пароль и введите правильный')
        bot.register_next_step_handler(message, autentification, login)


# создание в базе данных нового, уникального дома (жилья), о котором можно хранить данные
# обработка случая, когда название уже используется пользователем
def create_new_home(message, login):
    home_name = message.text.strip()

    if home_name in get_list_of_homes(login):
        bot.send_message(message.chat.id, 'вы уже использовали такое название для жилья, введите уникальное')
        bot.register_next_step_handler(message, create_new_home, login)

    else:
        add_new_home(login, home_name)

        bot.send_message(message.chat.id, 'новый дом добавлен')

        markup = types.InlineKeyboardMarkup()

        choose_home_btn = types.InlineKeyboardButton('выбрать дом', callback_data=f'choose {login}')
        create_home_btn = types.InlineKeyboardButton('создать ещё один дом', callback_data=f'create {login}')

        markup.row(choose_home_btn, create_home_btn)
        bot.send_message(message.chat.id, 'что вы будете делать дальше?', reply_markup=markup)
    

# выбор дома из списка доступных в базе данных
def choose_home(message, login):
    homes = get_list_of_homes(login)

    markup = types.InlineKeyboardMarkup()

    for home in homes:
        button = types.InlineKeyboardButton(home, callback_data=home)
        markup.add(button, row_width=1)

    bot.send_message(message.chat.id, 'Выберите нужное жилье', reply_markup=markup)


# главное меню
# выбор пользователем доступных функций и действий, которые можно выполнить, касательно этого дома
def main_menu (message):
    markup = types.InlineKeyboardMarkup()

    get_all_bills_btn = types.InlineKeyboardButton('Просмотреть последние показания\n всех счётчиков', 
                                                   callback_data='получить последние счета')
    get_bill_btn = types.InlineKeyboardButton('Просмотреть последние\n показания счётчика', 
                                              callback_data='получить счёт')
    get_bills_for_year_btn = types.InlineKeyboardButton('Получить показания счётчиков, переданные за год', 
                                                        callback_data='получить счета за год')
    set_data_to_bill_btn = types.InlineKeyboardButton('Передать показания счётчика', 
                                                      callback_data='добавить счёт')
    change_bill_btn = types.InlineKeyboardButton('Изменить последние\n показания счётчика', 
                                                 callback_data='изменить счёт')

    markup.add(get_bill_btn, get_all_bills_btn, row_width=1)
    markup.add(set_data_to_bill_btn, change_bill_btn, row_width=1)
    markup.add(get_bills_for_year_btn, row_width=1)

    bot.send_message(message.chat.id, 'выберите, что хотите сделать дальше', reply_markup=markup)


# выбор того, какую услугу пользователь хочет выбрать, 
# поскольку услуга выбирается в нескольких функциях, то разные функции обращаются к этой функции, 
# а также эта функция ведёт к нескольким другим 
def choose_bill(message):
    bills = ['electricity', 'water', 'gas', 'heating']
    rus_bills = ['электричество', 'вода', 'газ', 'отопление']

    markup = types.InlineKeyboardMarkup()

    for bill, rus_bill in zip(bills, rus_bills):
        button = types.InlineKeyboardButton(rus_bill, callback_data=bill)
        markup.add(button)

    bot.send_message(message.chat.id, 'выберите услугу', reply_markup=markup)


# после выбора услуги вызывется соответствующая функция
def choosing_service(message, service, bill, login, home_name):
    data = message.text.strip()

    if service == 'получить счёт':
        get_bill(message, login, bill, home_name)
    elif service == 'добавить счёт':
        set_data_to_bill(message, login, bill, home_name, data)
    elif service == 'изменить счёт':
        change_bill(message, login, bill, home_name, data)


# получение счёта по конкретной услуге
def get_bill(message, login, bill, home_name):
    data = get_data(login, bill, home_name)
    if data == None:
        data = 'отсутствует'
    bot.send_message(message.chat.id, f'последний показания по счётчику такие: {data}')
    main_menu(message)


# получение последних счетов по всем услугам
def get_all_bills(message, login, home_name):
    bot.send_message(message.chat.id, 'вот ваши последние показания по всем счётчикам: ')
    bills_data = get_last_bills_data(login, home_name)
    rus_bills = ['электричество', 'воду', 'газ', 'отопление']
    
    for bill, data in zip(rus_bills, bills_data):
        if data == None:
            data = 'отсутствует'
        bot.send_message(message.chat.id, f'счёт за {bill}: {data}')
    main_menu(message)


# получение всех имеющихся счетов (только двенадцать счетов включительно) по всем услугам 
def get_bills_for_year(message, login, home_name):
    yearly_bills = yearly_data(login, home_name)
    rus_bills = ['электричество', 'воду', 'газ', 'отопление']

    for bill, data in zip(rus_bills, yearly_bills):
        if data == []:
            data = 'отсутствует'
        bot.send_message(message.chat.id, f'показания счётчика за {bill}: {data}')
    main_menu(message)


# добавление данных по конкретному счёту
def set_data_to_bill(message, login, bill, home_name, data):
    add_new_data(login, bill, home_name, data)
    bot.send_message(message.chat.id, 'показания счётчика были добавлены')
    main_menu(message)


# внесение изменений в последний счёт по конкретной услуге в случае ошибки пользователя
def change_bill(message, login, bill, home_name, data):
    change_last_data(login, bill, home_name, data)
    bot.send_message(message.chat.id, 'показания счётчика были изменены')
    main_menu(message)


bot.polling(non_stop=True)