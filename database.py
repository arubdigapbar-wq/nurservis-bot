import os
import asyncpg
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Дерекқорға қосылу"""
        try:
            # Егер DATABASE_URL болса, соны қолдан
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                # Railway DATABASE_URL форматына бейімдеу
                if database_url.startswith('postgresql://'):
                    database_url = database_url.replace('postgresql://', 'postgres://')
                self.pool = await asyncpg.create_pool(database_url)
                print("✅ Дерекқорға DATABASE_URL арқылы қосылды!")
            else:
                # Әйтпесе жеке параметрлерді қолдан
                self.pool = await asyncpg.create_pool(**DB_CONFIG)
                print("✅ Дерекқорға жеке параметрлер арқылы қосылды!")
            
            await self.create_tables()
        except Exception as e:
            print(f"❌ Дерекқорға қосылу қатесі: {e}")
    
    # Қалған методтар өзгеріссіз қалады
    async def create_tables(self):
        """Кестелерді жасау"""
        async with self.pool.acquire() as conn:
            # Пайдаланушылар кестесі
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    full_name VARCHAR(255),
                    phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Жазылымдар кестесі
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    service_type VARCHAR(100),
                    car_make VARCHAR(100),
                    car_year INTEGER,
                    booking_date DATE,
                    booking_time TIME,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Админдер кестесі
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE
                )
            ''')
            print("✅ Кестелер дайын!")
    
    # Қалған методтар (add_user, add_booking, т.б.) өзгеріссіз қалады
    async def add_user(self, user_id, full_name, phone):
        """Жаңа пайдаланушы қосу"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, full_name, phone) 
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
            ''', user_id, full_name, phone)
    
    async def add_booking(self, user_id, service_type, car_make, car_year, booking_date, booking_time):
        """Жаңа жазылым қосу"""
        async with self.pool.acquire() as conn:
            booking_id = await conn.fetchval('''
                INSERT INTO bookings (user_id, service_type, car_make, car_year, booking_date, booking_time) 
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            ''', user_id, service_type, car_make, car_year, booking_date, booking_time)
            return booking_id
    
    async def get_today_bookings(self):
        """Бүгінгі жазылымдарды алу"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT b.*, u.full_name, u.phone 
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                WHERE b.booking_date = CURRENT_DATE
                ORDER BY b.booking_time
            ''')
            return rows
    
    async def get_all_bookings(self):
        """Барлық жазылымдарды алу"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT b.*, u.full_name, u.phone 
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                ORDER BY b.booking_date DESC, b.booking_time
            ''')
            return rows
    
    async def get_booking_stats(self):
        """Статистика алу"""
        async with self.pool.acquire() as conn:
            # Барлық жазылымдар саны
            total = await conn.fetchval('SELECT COUNT(*) FROM bookings')
            
            # Бүгінгі жазылымдар саны
            today = await conn.fetchval('SELECT COUNT(*) FROM bookings WHERE booking_date = CURRENT_DATE')
            
            # Осы аптадағы жазылымдар
            week = await conn.fetchval('''
                SELECT COUNT(*) FROM bookings 
                WHERE booking_date >= DATE_TRUNC('week', CURRENT_DATE)
            ''')
            
            # Осы айдағы жазылымдар
            month = await conn.fetchval('''
                SELECT COUNT(*) FROM bookings 
                WHERE booking_date >= DATE_TRUNC('month', CURRENT_DATE)
            ''')
            
            # Қызметтер бойынша бөлініс
            services = await conn.fetch('''
                SELECT service_type, COUNT(*) as count 
                FROM bookings 
                GROUP BY service_type
            ''')
            
            return {
                'total': total or 0,
                'today': today or 0,
                'week': week or 0,
                'month': month or 0,
                'services': services
            }