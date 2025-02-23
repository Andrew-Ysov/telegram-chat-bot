import telebot  
from telebot import types

from working_with_db import *
from helpers import *
from token import token


"""variable bot is a unique token that you can from @BotFather."""
bot = telebot.TeleBot(token)
login = ''
home_name = ''
action = ''


@bot.message_handler(commands=['help'])
def help(message):
    """respond to help command, explains how bot works."""
    about_me = ''' Бот создан для того, чтобы хранить данные по комунальным счетам.
Перед использованием бота в нём нужно зарегистрироваться или войти в аккаунт. \n
Касательно функционала: в боте можно хранить и вносить данные по счетам за воду, 
электричество, газ, отопление, также можно изменять уже введённые данные, если в них была ошибка. \n
Для безопасности пользователей при вводе пароля он сразу хэшируется. '''
    
    bot.send_message(message.chat.id, about_me)


@bot.message_handler(commands=['start'])
def start(message):
    """starts the bot, displays bottons 'вход', 'регистрация', initializes database."""

    create_users_table()

    markup = types.InlineKeyboardMarkup()

    check_in = types.InlineKeyboardButton('вход', callback_data='check_in')
    registration = types.InlineKeyboardButton('регистрация', callback_data='registration')

    markup.add(check_in, registration)

    bot.send_message(message.chat.id, 'Войдите в аккаунт или зарегистрируйтесь', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def buttons(callback):
    """showing buttons and handling callback for them."""
    global login
    global home_name
    global action
    
    # get user's phone number to register him
    if callback.data == 'registration':
        bot.send_message(callback.message.chat.id, 
                     'введите номер телефона, например:\n (79591234567 или 7 959 123 45 67)')
        bot.register_next_step_handler(callback.message, registration)
        
    # get user's phone number to check in
    elif callback.data == 'check_in':
        bot.send_message(callback.message.chat.id, 
                     'введите номер телефона, например:\n (79591234567 или 7 959 123 45 67)')
        bot.register_next_step_handler(callback.message, check_in)
    
    # let user choose which home to work with
    elif callback.data.split()[0] == 'choose':
        login = callback.data.split()[1]
        choose_home(callback.message, login)

    # button to create a new home
    elif callback.data.split()[0] == 'create':
        login = callback.data.split()[1]
        bot.send_message(callback.message.chat.id, 'дайте уникальное название новому жилью')
        bot.register_next_step_handler(callback.message, create_new_home, login)
    
    # handling buttons after user chooses home name
    elif callback.data in get_list_of_homes(login):
        home_name = callback.data 
        main_menu(callback.message)
             
    # handling buttons for action choice
    elif callback.data == 'получить последние счета':
        get_last_bills(callback.message, login, home_name)  
    elif callback.data == 'получить счета за год':
        get_service_bills_for_year(callback.message, login, home_name)
    elif callback.data == 'получить счёт':
        action = callback.data
        choose_service(callback.message)
    elif callback.data == 'добавить счёт':
        action = callback.data
        choose_service(callback.message)
    elif callback.data == 'изменить счёт':
        action = callback.data
        choose_service(callback.message)

    # handling buttons for service choice
    elif callback.data in ['electricity', 'water', 'gas', 'heating']:

        service = callback.data
        if action == 'получить счёт':
            choosing_action(callback.message, action, service, login, home_name)
        else:
            bot.send_message(callback.message.chat.id, f'введите показания счётчика')
            bot.register_next_step_handler(callback.message, choosing_action, 
                                           action, service, login, home_name)


def registration(message):
    """test if user login is valid, if so: get user password, else print a message."""
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


def get_password(message, login):
    """make hash of password for future use."""
    hash_password = hashing(message.text.strip())
    
    register_user(login, hash_password)
    
    create_user_data_table(login)

    bot.send_message(message.chat.id, 'вы зарегистрированы')
    bot.send_message(message.chat.id, 'теперь нужно дать название жилью, о котором будут храниться данные')
    bot.register_next_step_handler(message, create_new_home, login)


def check_in(message):
    """userr's identification with phone number."""
    login = message.text.strip()
    login = ''.join(login.split())

    if not is_valid_login(login, False):
        bot.send_message(message.chat.id, ('такой номер телефона не используется, ' 
                                           'зарегистрируйтесь или введите правильный номер'))
        start(message)
    else:
        bot.send_message(message.chat.id, 'введите пароль')
        bot.register_next_step_handler(message, autentification, login)


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


def create_new_home(message, login):
    """create new home, check if it's already in use."""
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
    

def choose_home(message, login):
    homes = get_list_of_homes(login)

    markup = types.InlineKeyboardMarkup()

    for home in homes:
        button = types.InlineKeyboardButton(home, callback_data=home)
        markup.add(button, row_width=1)

    bot.send_message(message.chat.id, 'Выберите нужное жилье', reply_markup=markup)


def main_menu (message):
    """Show buttons for future actions."""
    markup = types.InlineKeyboardMarkup()

    get_last_bills_btn = types.InlineKeyboardButton('Просмотреть последние показания\n всех счётчиков', 
                                                   callback_data='получить последние счета')
    get_bill_btn = types.InlineKeyboardButton('Просмотреть последние\n показания счётчика', 
                                              callback_data='получить счёт')
    get_service_bills_for_year_btn = types.InlineKeyboardButton('Получить показания счётчиков, переданные за год', 
                                                        callback_data='получить счета за год')
    set_data_to_bill_btn = types.InlineKeyboardButton('Передать показания счётчика', 
                                                      callback_data='добавить счёт')
    change_last_bill_btn = types.InlineKeyboardButton('Изменить последние\n показания счётчика', 
                                                 callback_data='изменить счёт')

    markup.add(get_bill_btn, get_last_bills_btn, row_width=1)
    markup.add(set_data_to_bill_btn, change_last_bill_btn, row_width=1)
    markup.add(get_service_bills_for_year_btn, row_width=1)

    bot.send_message(message.chat.id, 'выберите, что хотите сделать дальше', reply_markup=markup)


def choose_service(message):
    services = ['electricity', 'water', 'gas', 'heating']
    rus_services = ['электричество', 'вода', 'газ', 'отопление']

    markup = types.InlineKeyboardMarkup()

    for service, rus_service in zip(services, rus_services):
        button = types.InlineKeyboardButton(rus_service, callback_data=service)
        markup.add(button)

    bot.send_message(message.chat.id, 'выберите услугу', reply_markup=markup)


def choosing_action(message, action, service, login, home_name):
    data = message.text.strip()

    if action == 'получить счёт':
        get_bill(message, login, service, home_name)
    elif action == 'добавить счёт':
        set_bill_data_to_service(message, login, service, home_name, data)
    elif action == 'изменить счёт':
        change_last_bill(message, login, service, home_name, data)


def get_bill(message, login, service, home_name):
    data = get_data(login, service, home_name)
    if data is None:
        data = 'отсутствует'
    bot.send_message(message.chat.id, f'последний показания по счётчику такие: {data}')
    main_menu(message)


def get_last_bills(message, login, home_name):
    bot.send_message(message.chat.id, 'вот ваши последние показания по всем счётчикам: ')
    bills_data = get_last_bills(login, home_name)
    rus_services = ['электричество', 'воду', 'газ', 'отопление']
    
    for service, data in zip(rus_services, bills_data):
        if data is None:
            data = 'отсутствует'
        bot.send_message(message.chat.id, f'счёт за {service}: {data}')
    main_menu(message)


def get_service_bills_for_year(message, login, home_name):
    yearly_bills = yearly_data(login, home_name)
    rus_services = ['электричество', 'воду', 'газ', 'отопление']

    for service, data in zip(rus_services, yearly_bills):
        if data == []:
            data = 'отсутствует'
        bot.send_message(message.chat.id, f'показания счётчика за {service}: {data}')
    main_menu(message)


def set_bill_data_to_service(message, login, service, home_name, data):
    add_new_data(login, service, home_name, data)
    bot.send_message(message.chat.id, 'показания счётчика были добавлены')
    main_menu(message)


def change_last_bill(message, login, service, home_name, data):
    change_last_data(login, service, home_name, data)
    bot.send_message(message.chat.id, 'показания счётчика были изменены')
    main_menu(message)


bot.polling(non_stop=True)