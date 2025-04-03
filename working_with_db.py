"""Functions for working with database."""

import sqlite3
from contextlib import contextmanager

@contextmanager
def db_context():
    try:
        conn = sqlite3.connect('data_for_bot.db')
        cursor = conn.cursor()
        yield cursor
    finally:
        conn.commit()
        cursor.close()
        conn.close()

def create_users_table():
    with db_context() as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                       (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       login int, password text)''')


def is_login_in_use(login):
    with db_context() as cursor:
        result = cursor.execute(f'''SELECT (:login) FROM users ''', 
                                {'login':login})
    
        if result.fetchone() is None:
            return False
        else:
            return True


def get_correct_password(login):
    """get correct password from table users."""

    with db_context() as cursor:
        cursor.execute(''' SELECT password FROM users WHERE login = (:phone_num) ''', 
                                {'phone_num':login})
    
        password = cursor.fetchone()
        return password
    

def register_user(login, password):
    """save phone number (login) and password of a new user."""

    with db_context() as cursor:
        cursor.execute(''' INSERT INTO users (login, password) VALUES (:log, :pswrd) ''', 
                       {'log':login, 'pswrd':password})

def create_user_data_table(login):
    """create a seperate table for every user."""

    with db_context() as cursor:
        login = [int(login)]

        cursor.execute(''' CREATE TABLE IF NOT EXISTS (:login) 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   home_name text,
                   electricity text,
                   water text,
                   gas text,
                   heating text)''',
                   {'login':login})

def add_new_home(login, name):
    """save new address or home name for a user."""

    with db_context() as cursor:
        login = [int(login)]

        cursor.execute(''' INSERT INTO (:login) (home_name) VALUES (:home_name)''', 
                       {'home_name': name, 'login':login})

def get_home_names(login):
    """get user's addresses or home names."""

    with db_context() as cursor:
        login = [int(login)]

        cursor.execute(''' SELECT DISTINCT home_name from (:login) ''',
                    {'login':login})
        
        home_names = cursor.fetchall()
        return home_names


def add_new_data(login, service, home_name, data):
    """save bill's data for service, for a specific home_name."""
    
    with db_context() as cursor:
        login = [int(login)]

        cursor.execute(''' SELECT id FROM (:login) 
                        WHERE home_name = (:name_of_home) and (:service) is Null ''', 
                        {'name_of_home':home_name, 'login':login, 'service':service})
    
        first_occurance = cursor.fetchone()
        if first_occurance is not None:
            first_occurance = first_occurance[0]

            cursor.execute(''' UPDATE (:login) SET (:service) = (:value) WHERE id = (:needed_id) ''', 
                        {'value':data, 'needed_id':first_occurance, 'login':login, 'service':service})
        else:
            cursor.execute(''' INSERT INTO (:login) (home_name, (:service)) VALUES (:name_of_home, :value)''', 
                        {'name_of_home':home_name, 'value':data, 'login':login, 'service':service})

def change_last_data(login, service, home_name, data):
    
    with db_context() as cursor:
        old_version_of_login = login
        login = [int(login)]

        cursor.execute(''' SELECT id FROM (:login) 
                        WHERE home_name = (:name_of_home) and (:service) is not Null ''', 
                        {'name_of_home':home_name, 'login':login, 'service':service})
        
        last_occurance = cursor.fetchall()
        if last_occurance != []:
            last_occurance = last_occurance[-1][0]

            cursor.execute(''' UPDATE (:login) SET (:service) = (:value) WHERE id = (:needed_id) ''', 
                        {'value':data, 'needed_id':last_occurance, 'login':login, 'service':service},)
        else:
            add_new_data(old_version_of_login, service, home_name, data)

def get_data(login, service, home_name):
    """get all data for a service for a specific home."""

    with db_context() as cursor:
        login = [int(login)]


        cursor.execute(''' SELECT (:service) FROM (:login)  
                        WHERE home_name = (:name_of_home) and (:service) is not Null ''', 
                        {'name_of_home':home_name, 'service':service, 'login':login})
        
        last_occurance = cursor.fetchall()

        if last_occurance != []:
            last_occurance = last_occurance[-1][0]
            return last_occurance
        else:
            return None


def get_last_bills(login, home_name):
    services = ['electricity', 'water', 'gas', 'heating']
    last = []

    for service in services:
        data = get_data(login, service, home_name)
        last.append(data)

    return last


def get_yearly_data(login, home_name, service):
    """get last 12 row of data or get all data, if there's not enough rows."""
    
    with db_context() as cursor:
        login = [int(login)]

        cursor.execute(''' SELECT (:service) FROM (:login) WHERE home_name = (:name_of_home) 
                    AND (:service) is not Null ''', 
                    {'name_of_home':home_name, 'service':service, 'login':login})
        twelve = cursor.fetchmany(12)

        result = []
        for data in twelve:
            result.append(data[0])
            
        return result