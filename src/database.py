import sqlite3

from src.functions import tprint

con = sqlite3.connect('data/TelegramBot.db', check_same_thread=False)

table_list = list(con.execute("SELECT name FROM sqlite_master WHERE type='table';"))

if table_list:
    table_list = [el[0] for el in table_list]

with con:
    if 'user' not in table_list:
        con.execute("""
            CREATE TABLE user (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                telegram_id INT,
                telegram_nick TEXT,
                registration_date DATETIME,
                role_id INT DEFAULT 1,
                surname TEXT,
                name TEXT,
                patronymic TEXT,
                age INT,
                interests TEXT,
                city TEXT,
                photo BLOB,
                department TEXT,
                step TEXT
            );
        """)
        print('[INFO] таблица "user" успешно создана')

    if 'role' not in table_list:
        con.execute("""
            CREATE TABLE role (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT
            );
        """)
        print('[INFO] таблица "role" успешно создана')

    if 'feedback' not in table_list:
        con.execute("""
            CREATE TABLE feedback (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                from_user_id INT,
                to_user_id INT,
                message TEXT
            );
        """)
        print('[INFO] таблица "feedback" успешно создана')

    if 'department' not in table_list:
        con.execute("""
            CREATE TABLE department (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT
            );
        """)
        print('[INFO] таблица "department" успешно создана')

    if 'interest' not in table_list:
        con.execute("""
            CREATE TABLE interest (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                telegram_id INT
            );
            """)
        print('[INFO] таблица "interest" успешно создана')

to_sql = lambda el: str(el) if isinstance(el, int) else f"'{el}'"


def row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    data = {}
    for idx, col in enumerate(cursor.description):
        data[col[0]] = row[idx]
    return data


def get_table(table, conditions=None, current_query=None):
    req = f'SELECT * FROM {table} '
    if conditions:
        req += '\n\tWHERE '
        for condition in conditions.items():
            req += f"""{condition[0]}={to_sql(condition[1])} and """
        req = req[:-4]
    elif current_query:
        req += f'\n\tWHERE {current_query}'
    # tprint(req)
    with con:
        con.row_factory = row_to_dict
        response = con.execute(req)
        data = response.fetchall()
        return data


def insert_table(table, **kwargs):
    req = f"""INSERT INTO {table} ({', '.join(kwargs.keys())}) 
              values ({', '.join([to_sql(el) for el in kwargs.values()])})"""
    tprint(req)
    with con:
        con.execute(req)


def update_table(table, conditions, **kwargs):
    req = f"""UPDATE {table} SET """
    for kwarg in kwargs:
        req += f'{kwarg}={to_sql(kwargs[kwarg])}, '
    req = req[:-2] + ' \n\tWHERE '
    for condition in conditions.items():
        req += f"""{condition[0]}={to_sql(condition[1])}, """
    req = req[:-2]
    # tprint(req)
    with con:
        con.execute(req)

def delete_table(table, conditions=None, current_query=None):
    req = f"""DELETE FROM {table} """
    if conditions:
        req += '\n\tWHERE '
        for condition in conditions.items():
            req += f"""{condition[0]}={to_sql(condition[1])} and """
        req = req[:-4]
    elif current_query:
        req += f'\n\tWHERE {current_query}'
    # tprint(req)
    with con:
        con.row_factory = row_to_dict
        response = con.execute(req)
        data = response.fetchall()
        return data