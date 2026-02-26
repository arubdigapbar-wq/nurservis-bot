import re
from datetime import datetime, time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import WORK_HOURS, WEEKEND_DAYS, PHONE

router = Router()

# FSM күйлері
class BookingStates(StatesGroup):
    service = State()
    full_name = State()
    phone = State()
    car_make = State()
    car_year = State()
    custom_make = State()
    custom_year = State()
    datetime = State()
    confirm = State()

# Қызметтер тізімі (callback_data үшін)
SERVICES = {
    "service_1": "🔧 Күрделі жөндеу",
    "service_2": "🛢 Май ауыстыру",
    "service_3": "💻 Компьютерлік диагностика",
    "service_4": "🔩 Шиномонтаж",
    "service_5": "⚙️ Отжиг дискілері",
    "service_6": "🔇 Босатқышты жөндеу",
    "service_7": "🎨 Бөлшектерді бояу"
}

# Маркалар
CAR_MAKES = ["Toyota", "Hyundai", "Kia", "Lada", "Nissan", "BMW"]
CAR_MAKES_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=make, callback_data=f"make_{make}") for make in CAR_MAKES[:3]],
        [InlineKeyboardButton(text=make, callback_data=f"make_{make}") for make in CAR_MAKES[3:6]],
        [InlineKeyboardButton(text="✏️ Басқа", callback_data="make_other")]
    ]
)

# Жылдар
YEARS = ["2024", "2023", "2022", "2021", "2020", "2019"]
YEARS_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=year, callback_data=f"year_{year}") for year in YEARS[:3]],
        [InlineKeyboardButton(text=year, callback_data=f"year_{year}") for year in YEARS[3:6]],
        [InlineKeyboardButton(text="✏️ Басқа", callback_data="year_other")]
    ]
)

# Қызмет таңдау батырмалары
services_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Күрделі жөндеу", callback_data="book_service_1")],
        [InlineKeyboardButton(text="🛢 Май ауыстыру", callback_data="book_service_2")],
        [InlineKeyboardButton(text="💻 Компьютерлік диагностика", callback_data="book_service_3")],
        [InlineKeyboardButton(text="🔩 Шиномонтаж", callback_data="book_service_4")],
        [InlineKeyboardButton(text="⚙️ Отжиг дискілері", callback_data="book_service_5")],
        [InlineKeyboardButton(text="🔇 Босатқышты жөндеу", callback_data="book_service_6")],
        [InlineKeyboardButton(text="🎨 Бөлшектерді бояу", callback_data="book_service_7")]
    ]
)

@router.message(F.text == "📝 Жазылу")
async def cmd_booking_start(message: Message, state: FSMContext):
    """Жазылуды бастау"""
    await message.answer(
        "📋 Қандай қызметке жазылғыңыз келеді?\n\nТөмендегілердің бірін таңдаңыз:",
        reply_markup=services_keyboard
    )
    await state.set_state(BookingStates.service)

@router.callback_query(lambda c: c.data.startswith('book_service_'))
async def process_service_selection(callback: CallbackQuery, state: FSMContext):
    """Қызмет таңдау"""
    service_key = callback.data
    service_name = SERVICES.get(service_key.replace('book_', ''), "Белгісіз")
    
    await state.update_data(service=service_name)
    await callback.message.answer("👤 Аты-жөніңізді толық жазыңыз:\n\nМысалы: Серіков Айбек")
    await state.set_state(BookingStates.full_name)
    await callback.answer()

@router.message(BookingStates.full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Аты-жөнін қабылдау"""
    full_name = message.text.strip()
    
    # Валидация
    if len(full_name) < 2 or not re.match(r'^[а-яА-ЯёЁa-zA-Z\s]+$', full_name):
        await message.answer("❌ Аты-жөніңіз дұрыс емес. Тек әріптер мен бос орын қолданыңыз.\nҚайтадан жазыңыз:")
        return
    
    await state.update_data(full_name=full_name)
    await message.answer("📞 Телефон нөміріңізді жазыңыз:\n\nФормат: +7 777 123 45 67 немесе 87771234567")
    await state.set_state(BookingStates.phone)

@router.message(BookingStates.phone)
async def process_phone(message: Message, state: FSMContext):
    """Телефон нөмірін қабылдау"""
    phone = message.text.strip()
    
    # Телефон валидациясы
    phone_pattern = r'^(\+7|8)[0-9]{10}$'
    cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    if not re.match(phone_pattern, cleaned_phone):
        await message.answer("❌ Қате формат! Телефонды дұрыс жазыңыз:\n+7 777 123 45 67 немесе 87771234567")
        return
    
    await state.update_data(phone=cleaned_phone)
    await message.answer(
        "🚘 Автокөлігіңіздің маркасын таңдаңыз:",
        reply_markup=CAR_MAKES_KEYBOARD
    )
    await state.set_state(BookingStates.car_make)
    

@router.callback_query(lambda c: c.data.startswith('make_'), BookingStates.car_make)
async def process_car_make(callback: CallbackQuery, state: FSMContext):
    """Автокөлік маркасын таңдау"""
    if callback.data == "make_other":
        await callback.message.answer("✏️ Автокөлік маркасын өзіңіз жазыңыз:")
        await state.set_state(BookingStates.custom_make)
    else:
        car_make = callback.data.replace('make_', '')
        await state.update_data(car_make=car_make)
        await callback.message.answer(
            "📅 Автокөлігіңіздің шыққан жылын таңдаңыз:",
            reply_markup=YEARS_KEYBOARD
        )
        await state.set_state(BookingStates.car_year)
    await callback.answer()

@router.message(BookingStates.custom_make)
async def process_custom_make(message: Message, state: FSMContext):
    """Басқа марканы қолмен енгізу"""
    car_make = message.text.strip()
    if len(car_make) < 2:
        await message.answer("❌ Марка аты тым қысқа. Қайтадан жазыңыз:")
        return
    
    await state.update_data(car_make=car_make)
    await message.answer(
        "📅 Автокөлігіңіздің шыққан жылын таңдаңыз:",
        reply_markup=YEARS_KEYBOARD
    )
    await state.set_state(BookingStates.car_year)

@router.callback_query(lambda c: c.data.startswith('year_'), BookingStates.car_year)
async def process_car_year(callback: CallbackQuery, state: FSMContext):
    """Автокөлік жылын таңдау"""
    current_year = datetime.now().year
    
    if callback.data == "year_other":
        await callback.message.answer("✏️ Автокөлік жылын өзіңіз жазыңыз (мысалы: 2015):")
        await state.set_state(BookingStates.custom_year)
    else:
        car_year = int(callback.data.replace('year_', ''))
        await state.update_data(car_year=car_year)
        await callback.message.answer(
            "📅 Қай күні және уақытта келе аласыз?\n\n"
            "Формат: Күн.Ай.Жыл, Сағат:Минут\n"
            "Мысалы: 25.05.2024, 14:00"
        )
        await state.set_state(BookingStates.datetime)
    await callback.answer()

@router.message(BookingStates.custom_year)
async def process_custom_year(message: Message, state: FSMContext):
    """Басқа жылды қолмен енгізу"""
    try:
        car_year = int(message.text.strip())
        current_year = datetime.now().year
        
        if car_year < 1980 or car_year > current_year + 1:
            await message.answer(f"❌ Жыл 1980-{current_year+1} аралығында болуы керек. Қайтадан жазыңыз:")
            return
        
        await state.update_data(car_year=car_year)
        await message.answer(
            "📅 Қай күні және уақытта келе аласыз?\n\n"
            "Формат: Күн.Ай.Жыл, Сағат:Минут\n"
            "Мысалы: 25.05.2024, 14:00"
        )
        await state.set_state(BookingStates.datetime)
    except ValueError:
        await message.answer("❌ Жыл сан болуы керек. Қайтадан жазыңыз:")

@router.message(BookingStates.datetime)
async def process_datetime(message: Message, state: FSMContext):
    """Күн мен уақытты қабылдау және тексеру"""
    datetime_str = message.text.strip()
    
    # Форматты тексеру: ДД.ММ.ЖЖЖЖ, СС:ММ
    pattern = r'^(\d{2})\.(\d{2})\.(\d{4}),\s*(\d{2}):(\d{2})$'
    match = re.match(pattern, datetime_str)
    
    if not match:
        await message.answer(
            "❌ Қате формат! Мысалдағыдай жазыңыз:\n"
            "25.05.2024, 14:00"
        )
        return
    
    day, month, year, hour, minute = map(int, match.groups())
    
    try:
        booking_date = datetime(year, month, day, hour, minute)
        now = datetime.now()
        
        # Күн тексеру (өткен күн болмауы керек)
        if booking_date.date() < now.date():
            await message.answer("❌ Өткен күнге жазылу мүмкін емес. Болашақ күнді таңдаңыз.")
            return
        
        # Егер бүгінгі күн болса, уақыт ағымдағы уақыттан кем болмауы керек
        if booking_date.date() == now.date() and booking_date.time() <= now.time():
            await message.answer("❌ Бүгінгі күн үшін уақыт ағымдағы уақыттан кеш болуы керек.")
            return
        
        # Жұмыс уақытын тексеру
        if hour < WORK_HOURS['start'] or hour >= WORK_HOURS['end']:
            await message.answer(f"❌ Жұмыс уақыты {WORK_HOURS['start']}:00 - {WORK_HOURS['end']}:00 аралығында. Басқа уақыт таңдаңыз.")
            return
        
        # Демалыс күнін тексеру (жексенбі)
        if booking_date.weekday() in WEEKEND_DAYS:  # 6 = Жексенбі
            await message.answer("❌ Жексенбі күні демалыс. Басқа күн таңдаңыз.")
            return
        
        # Барлық тексеруден өтсе, сақтаймыз
        data = await state.get_data()
        
        # Растау хабарламасы
        confirm_text = f"""
📝 Сіздің жазылым ақпаратыңыз:

Қызмет: {data.get('service')}
Аты-жөні: {data.get('full_name')}
Телефон: {data.get('phone')}
Автокөлік: {data.get('car_make')} {data.get('car_year')}
Уақыт: {datetime_str}

Барлығы дұрыс па?
        """
        
        # Инлайн батырмалар
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Иә, растаймын", callback_data="confirm_yes"),
                    InlineKeyboardButton(text="🔄 Қайта толтыру", callback_data="confirm_no")
                ]
            ]
        )
        
        await state.update_data(booking_date=booking_date.date(), booking_time=booking_date.time())
        await message.answer(confirm_text, reply_markup=confirm_keyboard)
        await state.set_state(BookingStates.confirm)
        
    except ValueError:
        await message.answer("❌ Қате күн! Мысалы: 25.05.2024, 14:00")

@router.callback_query(lambda c: c.data == "confirm_yes", BookingStates.confirm)
async def process_confirm_yes(callback: CallbackQuery, state: FSMContext):
    """Жазылымды растау"""
    data = await state.get_data()
    
    # Пайдаланушыны дерекқорға қосу (егер жоқ болса)
    await db.add_user(
        user_id=callback.from_user.id,
        full_name=data.get('full_name'),
        phone=data.get('phone')
    )
    
    # Жазылымды қосу
    booking_id = await db.add_booking(
        user_id=callback.from_user.id,
        service_type=data.get('service'),
        car_make=data.get('car_make'),
        car_year=data.get('car_year'),
        booking_date=data.get('booking_date'),
        booking_time=data.get('booking_time')
    )
    
    # Пайдаланушыға растау
    await callback.message.answer(f"""
✅ Сәтті жазылдыңыз!

Сіздің жазылым нөміріңіз: #{booking_id}
Күні: {data.get('booking_date').strftime('%d.%m.%Y')}, сағат {data.get('booking_time').strftime('%H:%M')}

📍 Мекен-жай: Кенесары көшесі 45/2, Астана
📞 Телефон: +7 707 222 80 80

Келуіңізді күтеміз!
    """)
    
    # Мұнда админге хабарлама жіберу керек (кейін қосамыз)
    
    await state.clear()
    await callback.answer()

@router.callback_query(lambda c: c.data == "confirm_no", BookingStates.confirm)
async def process_confirm_no(callback: CallbackQuery, state: FSMContext):
    """Қайта толтыру"""
    await state.clear()
    await callback.message.answer("🔄 Жазылым қайта басталды. /start басып, қайтадан көріңіз.")
    await callback.answer()