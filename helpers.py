"""Additional functions."""

import hashlib

from working_with_db import is_login_in_use, get_home_names, get_correct_password, get_yearly_data


def is_valid_login(login, registration):
    if len(login) != 11:
        return False
    
    try: 
        int(login)
    except: 
        return False
    
    if not registration:
        if is_login_in_use(login):
            return True
        else:
            return False
    
    if is_login_in_use(login):
        return False
    else:
        return True


def hashing(password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed


def is_password_correct(login, attempted_password):
    """compare correct password with attempted one."""
    correct_password = get_correct_password(login)[0]

    if correct_password == attempted_password:
        return True
    else:
        return False


def get_list_of_homes(login):
    homes = get_home_names(login)
    names = []

    for home in homes:
        names.append(home[0])
    
    return names


def yearly_data(login, home_name): 
    """get yearly data for every service."""
    data = []
    services = ['electricity', 'water', 'gas', 'heating']

    for service in services:
        yearly_bill_data = get_yearly_data(login, home_name, service)
        data.append(yearly_bill_data)
    
    return data