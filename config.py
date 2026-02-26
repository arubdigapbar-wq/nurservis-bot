import os
from dotenv import load_dotenv

# .env файлын жүктеу
load_dotenv()

# Бот токені
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Админ құпия сөзі
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Дерекқор параметрлері
DB_CONFIG = {
    'host': 'arubdigapbar.mysql.pythonanywhere-services.com',  # PythonAnywhere-тен көшіріңіз
    'port': 3306,
    'user': 'arubdigapbar',
    'password': 'сіздің_пароль',  # Databases бетінде қойған пароль
    'database': 'arubdigapbar$default'  # $ белгісімен
}

# Жұмыс уақыты
WORK_HOURS = {
    'start': 9,   # 09:00
    'end': 20     # 20:00
}

# Демалыс күндері (0=Дүйсенбі, 6=Жексенбі)
WEEKEND_DAYS = [6]  # Жексенбі

# Мекен-жай
ADDRESS = "Кенесары көшесі 45/2, Астана"
PHONE = "+7 707 222 80 80"
EMAIL = "nurservis@mail.ru"