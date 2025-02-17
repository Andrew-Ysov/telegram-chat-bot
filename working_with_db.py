# файл, созданный строго для работы с БД и для всех обращений к ней

import sqlite3


# создание таблицы пользователей (users)
def create_users_table():
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   login int, password text)''')
    conn.commit()
    cursor.close()
    conn.close()


# проверка того, используется ли данный логин,
# то есть находится ли такой логин уже в таблице users
def is_login_in_use(login):
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    result = cursor.execute(f'''SELECT (:login) FROM users ''', 
                            {'login':login})
    
    if result.fetchone() is None:
        conn.commit()
        cursor.close()
        conn.close()
        return False
    else:
        conn.commit()
        cursor.close()
        conn.close()
        return True


# получение правильного пароля из таблицы users
def get_correct_password(login):
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    cursor.execute(''' SELECT password FROM users WHERE login = (:phone_num) ''', 
                            {'phone_num':login})
    
    password = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return password
    

# регистрация пользователя, то есть добавление новых 
# номера телефона (login) и пароля в таблицу users
def register_user(login, password):
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    cursor.execute(''' INSERT INTO users (login, password) VALUES (:log, :pswrd) ''', 
                   {'log':login, 'pswrd':password})

    conn.commit()
    cursor.close()
    conn.close()


# создание собственной таблицы для каждого пользователя, 
# где именем таблицы выступает уникальный номер телефона (он же login из таблицы users)
def create_user_db(login):
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    login = [int(login)]

    cursor.execute(''' CREATE TABLE IF NOT EXISTS (:login) 
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
               home_name text,
               electricity text,
               water text,
               gas text,
               heating text)''',
               {'login':login})

    conn.commit()
    cursor.close()
    conn.close()


# добавление нового дома в таблицу пользователя
def add_new_home(login, name):
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    login = [int(login)]

    cursor.execute(''' INSERT INTO (:login) (home_name) VALUES (:home_name)''', 
                   {'home_name': name, 'login':login})

    conn.commit()
    cursor.close()
    conn.close()


# получение уникальных названий домов из таблицы пользователя
def get_home_names(login):
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    login = [int(login)]

    cursor.execute(''' SELECT DISTINCT home_name from (:login) ''',
                   {'login':login})
    home_names = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return home_names


# добавление данных в таблицу пользователя по соответствующей услуге и для соответствующего дома
def add_new_data(login, bill, home_name, data):
    login = [int(login)]
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    cursor.execute(''' SELECT id FROM (:login) 
                    WHERE home_name = (:name_of_home) and (:bill) is Null ''', 
                    {'name_of_home':home_name, 'login':login, 'bill':bill})
    
    first_occurance = cursor.fetchone()
    if first_occurance is not None:
        first_occurance = first_occurance[0]

        cursor.execute(''' UPDATE (:login) SET (:bill) = (:value) WHERE id = (:needed_id) ''', 
                       {'value':data, 'needed_id':first_occurance, 'login':login, 'bill':bill})
    else:
        cursor.execute(''' INSERT INTO (:login) (home_name, (:bill)) VALUES (:name_of_home, :value)''', 
                       {'name_of_home':home_name, 'value':data, 'login':login, 'bill':bill})
    
    conn.commit()
    cursor.close()
    conn.close()


# изменение последней записи в таблице пользователя по соответствующей услуге и для соответствующего дома
def change_last_data(login, bill, home_name, data):
    old_version_of_login = login
    login = [int(login)]
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    cursor.execute(''' SELECT id FROM (:login) 
                    WHERE home_name = (:name_of_home) and (:bill) is not Null ''', 
                    {'name_of_home':home_name, 'login':login, 'bill':bill})
    
    last_occurance = cursor.fetchall()
    if last_occurance != []:
        last_occurance = last_occurance[-1][0]

        cursor.execute(''' UPDATE (:login) SET (:bill) = (:value) WHERE id = (:needed_id) ''', 
                       {'value':data, 'needed_id':last_occurance, 'login':login, 'bill':bill},)
    else:
        add_new_data(old_version_of_login, bill, home_name, data)

    conn.commit()
    cursor.close()
    conn.close()


# получение данных из таблицы пользователя по конкретной услуге для соответствующего дома
def get_data(login, bill, home_name):
    login = [int(login)]
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    cursor.execute(''' SELECT (:bill) FROM (:login)  
                    WHERE home_name = (:name_of_home) and (:bill) is not Null ''', 
                    {'name_of_home':home_name, 'bill':bill, 'login':login})
    
    last_occurance = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()

    if last_occurance != []:
        last_occurance = last_occurance[-1][0]
        return last_occurance
    else:
        return None


# получение последних данных по всем услугам из таблицы пользователя, для соответствующего дома
def get_last_bills_data(login, home_name):
    bills = ['electricity', 'water', 'gas', 'heating']
    last = []

    for bill in bills:
        data = get_data(login, bill, home_name)
        last.append(data)

    return last


# получение двенадцати (включительно или меньше) последних записей по всем услугам
# из таблицы пользователя по соответствующему дому
def get_yearly_data(login, home_name, bill):
    login = [int(login)]
    conn = sqlite3.connect('data_for_bot.db')
    cursor = conn.cursor()

    cursor.execute(''' SELECT (:bill) FROM (:login) WHERE home_name = (:name_of_home) 
                   AND (:bill) is not Null ''', 
                   {'name_of_home':home_name, 'bill':bill, 'login':login})
    twelve = cursor.fetchmany(12)

    conn.commit()
    cursor.close()
    conn.close()

    result = []
    for data in twelve:
        result.append(data[0])
        
    return result