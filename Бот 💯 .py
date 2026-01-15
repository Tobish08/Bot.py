import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from deep_translator import GoogleTranslator
from pypinyin import lazy_pinyin
import pykakasi
import urllib.parse

# --- Создаём экземпляр kakasi один раз при запуске ---
kks = pykakasi.kakasi()

# --- ВАЖНО: Замените на СВОЙ реальный Telegram ID ---
OWNER_ID = -5226545880

TOKEN = "7253188204:AAFFPO7Nsh8RDlFvMxOV5558Lw_Plv5yUZ8"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Словарь языков ---
LANGUAGES = {
    'ru': {'name': '🇷🇺 Русский', 'api_code': 'ru'},
    'en': {'name': '🇬🇧 English', 'api_code': 'en'},
    'es': {'name': '🇪🇸 Español', 'api_code': 'es'},
    'fr': {'name': '🇫🇷 Français', 'api_code': 'fr'},
    'de': {'name': '🇩🇪 Deutsch', 'api_code': 'de'},
    'it': {'name': '🇮🇹 Italiano', 'api_code': 'it'},
    'pt': {'name': '🇵🇹 Português', 'api_code': 'pt'},
    'zh': {'name': '🇨🇳 中文', 'api_code': 'zh-CN'},
    'ja': {'name': '🇯🇵 日本語', 'api_code': 'ja'},
    'tg': {'name': '🇹🇯 Тоҷикӣ (Tajik)', 'api_code': 'tg'}
}

# --- Состояния и данные ---
user_state = {}
user_data = {}

# --- КНОПКИ МЕНЮ ---
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Открыть переводчик")],
        [KeyboardButton(text="⭐ Поделиться впечатлениями")],
        [KeyboardButton(text="ℹ️ О боте")]
    ],
    resize_keyboard=True
)

# --- Кнопка "Назад" (теперь для сброса обоих языков) ---
back_to_all_langs_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Выбрать языки заново", callback_data="back_to_all_langs")]
    ]
)

def get_language_keyboard(lang_type: str):
    keyboard = []
    buttons = []
    counter = 0
    for code, info in LANGUAGES.items():
        buttons.append(InlineKeyboardButton(text=info['name'], callback_data=f"set_{lang_type}_{code}"))
        counter += 1
        if counter % 2 == 0:
            keyboard.append(buttons)
            buttons = []
    if buttons:
        keyboard.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_language_keyboard_back(lang_type: str):
    """Та же клавиатура, но с кнопкой 'Назад'"""
    keyboard = get_language_keyboard(lang_type).inline_keyboard
    keyboard.append([InlineKeyboardButton(text="🔄 Назад", callback_data="back_to_all_langs")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_language_keyboard_back_to_target():
    """Клавиатура для выбора целевого языка с кнопкой 'Назад' к выбору обоих"""
    keyboard = get_language_keyboard('target').inline_keyboard
    keyboard.append([InlineKeyboardButton(text="🔄 Назад", callback_data="back_to_all_langs")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_language_keyboard_back_to_source():
    """Клавиатура для выбора исходного языка с кнопкой 'Назад' к выбору обоих"""
    keyboard = get_language_keyboard('source').inline_keyboard
    keyboard.append([InlineKeyboardButton(text="🔄 Назад", callback_data="back_to_all_langs")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_pinyin(text: str) -> str:
    try:
        pinyin_list = lazy_pinyin(text)
        pinyin_str = ' '.join(pinyin_list)
        return pinyin_str
    except Exception as e:
        print(f"Ошибка при получении пиньиня: {e}")
        return ""

def get_romaji(text: str) -> str:
    try:
        result = kks.convert(text)
        romaji_parts = [item['hepburn'] for item in result]
        romaji_str = ''.join(romaji_parts)
        return romaji_str
    except Exception as e:
        print(f"Ошибка при получении ромадзи: {e}")
        return ""

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет!\n"
        "Я бот-переводчик.\n\n"
        "Выбери действие 👇",
        reply_markup=menu
    )

@dp.message()
async def handler(message: types.Message):
    text = message.text
    user_id = message.from_user.id

    if text == "📝 Открыть переводчик":
        user_state[user_id] = "choose_source"
        user_data[user_id] = {'source_lang': None, 'target_lang': None}
        msg = await message.answer("🔤 Выбери язык оригинала:", reply_markup=get_language_keyboard_back_to_source())
        user_data[user_id]['last_msg_id'] = msg.message_id

    elif text == "⭐ Поделиться впечатлениями":
        user_state[user_id] = "rate"
        user_data[user_id] = {}
        await message.answer("⭐ Оцени бота от 1 до 10")

    elif text == "ℹ️ О боте":
        instagram_link = "https://www.instagram.com/_tobish_08"
        creator_info = (
            "ℹ️ <b>Информация о боте:</b>\n\n"
            "🤖 Это бот-переводчик, который может переводить на 10 языках мира 🌐..\n\n"
            "<b>Создатель:</b> <a href='{link}'>_tobish_08</a>".format(link=instagram_link)
        )
        await message.answer(creator_info, parse_mode="HTML", disable_web_page_preview=True)

    elif user_state.get(user_id) == "rate":
        if not text.isdigit() or not (1 <= int(text) <= 10):
            await message.answer("❗ Введи число от 1 до 10")
            return

        user_data[user_id]['rating'] = text
        user_state[user_id] = "comment"
        await message.answer("💬 Напиши комментарий")

    elif user_state.get(user_id) == "comment":
        rating = user_data[user_id].get('rating')
        if not rating:
            await message.answer("❌ Произошла ошибка. Попробуйте заново.")
            user_state.pop(user_id, None)
            user_data.pop(user_id, None)
            return

        comment = text
        user = message.from_user

        feedback = (
            "📩 Новый отзыв\n\n"
            f"👤 Пользователь: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"⭐ Оценка: {rating}/10\n"
            f"💬 Комментарий:\n{comment}"
        )

        try:
            await bot.send_message(OWNER_ID, feedback)
            await message.answer("✅ Спасибо за отзыв! Он отправлен создателю 🙌", reply_markup=menu)
        except Exception as e:
            print(f"Ошибка отправки отзыва пользователю {OWNER_ID}: {e}")
            await message.answer("❌ Произошла ошибка при отправке отзыва. Попробуйте позже.")
            user_state.pop(user_id, None)
            user_data.pop(user_id, None)
            return

        user_state.pop(user_id, None)
        user_data.pop(user_id, None)

    elif user_state.get(user_id) == "translate":
        source_lang_code = user_data[user_id].get('source_lang')
        target_lang_code = user_data[user_id].get('target_lang')

        if not source_lang_code or not target_lang_code:
             await message.answer("❌ Произошла ошибка в настройках языка. Попробуй заново.")
             user_state.pop(user_id, None)
             user_data.pop(user_id, None)
             return

        source_api_code = LANGUAGES[source_lang_code]['api_code']
        target_api_code = LANGUAGES[target_lang_code]['api_code']

        if not text.strip():
            await message.answer("⚠️ Не могу переводить пустое сообщение.")
            return

        try:
            translated = GoogleTranslator(source=source_api_code, target=target_api_code).translate(text)
            if translated is None:
                raise Exception("Translation returned None")

            src_name = LANGUAGES[source_lang_code]['name']
            tgt_name = LANGUAGES[target_lang_code]['name']

            response_text = f"💬 Текст ({src_name}):\n{text}\n\n🌐 Перевод ({tgt_name}):\n{translated}\n"

            # --- ИСПРАВЛЕНО: Логика для пиньиня и ромадзи ---
            # Проверяем, являются ли языки китайским и японским
            is_source_zh = source_lang_code == 'zh'
            is_target_zh = target_lang_code == 'zh'
            is_source_ja = source_lang_code == 'ja'
            is_target_ja = target_lang_code == 'ja'

            # Если китайский -> японский
            if is_source_zh and is_target_ja:
                pinyin_original = get_pinyin(text)
                romaji_translated = get_romaji(translated)
                response_text += f"\n🔤 Пиньинь оригинала (中文):\n{pinyin_original}\n\n"
                response_text += f"🔤 Ромадзи перевода (日本語):\n{romaji_translated}"
            # Если японский -> китайский
            elif is_source_ja and is_target_zh:
                romaji_original = get_romaji(text)
                pinyin_translated = get_pinyin(translated)
                response_text += f"\n🔤 Ромадзи оригинала (日本語):\n{romaji_original}\n\n"
                response_text += f"🔤 Пиньинь перевода (中文):\n{pinyin_translated}"
            # Если только китайский участвует (исходный или целевой)
            elif is_source_zh:
                pinyin_original = get_pinyin(text)
                response_text += f"\n🔤 Пиньинь оригинала:\n{pinyin_original}"
            elif is_target_zh:
                pinyin_translated = get_pinyin(translated)
                response_text += f"\n🔤 Пиньинь перевода:\n{pinyin_translated}"
            # Если только японский участвует (исходный или целевой)
            elif is_source_ja:
                romaji_original = get_romaji(text)
                response_text += f"\n🔤 Ромадзи оригинала:\n{romaji_original}"
            elif is_target_ja:
                romaji_translated = get_romaji(translated)
                response_text += f"\n🔤 Ромадзи перевода:\n{romaji_translated}"

            msg_with_translation = await message.answer(response_text, reply_markup=back_to_all_langs_button)
            user_data[user_id]['last_translation_msg_id'] = msg_with_translation.message_id

        except Exception as e:
            print(f"Ошибка перевода для пользователя {user_id}: {e}")
            await message.answer("⚠️ Ошибка перевода. Попробуй ещё раз. Возможно, текст слишком сложный или язык определён неправильно.")

    else:
        await message.answer("❌ Неизвестная команда. Используй кнопки меню.")

@dp.callback_query()
async def handle_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "back_to_all_langs":
        if user_data.get(user_id, {}).get('last_translation_msg_id') == callback_query.message.message_id:
            user_data[user_id] = {'source_lang': None, 'target_lang': None}
            user_state[user_id] = "choose_source"
            
            last_translation_msg_id = user_data[user_id].get('last_translation_msg_id')
            if last_translation_msg_id:
                try:
                    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=last_translation_msg_id)
                except Exception as e:
                    print(f"Не удалось удалить сообщение с переводом: {e}")
            
            await callback_query.message.answer("🔤 Выбери язык оригинала:", reply_markup=get_language_keyboard_back_to_source())
            await callback_query.answer()
            return

    if data == "back_to_all_langs" and user_state.get(user_id) in ["choose_source", "choose_target"]:
        try:
            await callback_query.message.edit_text("🔄 Отмена... Подождите.")
        except Exception as e:
            print(f"Не удалось отредактировать сообщение перед удалением: {e}")
            try:
                await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
            except Exception as e_del:
                print(f"Не удалось удалить сообщение: {e_del}")
            await callback_query.answer()
            return

        await asyncio.sleep(0.5)

        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение с выбором языка при нажатии 'Назад': {e}")

        user_data[user_id] = {'source_lang': None, 'target_lang': None}
        user_state[user_id] = "choose_source"

        await callback_query.answer()
        return

    if data.startswith("set_source_"):
        lang_code = data.split('_')[2]
        user_data[user_id]['source_lang'] = lang_code
        user_state[user_id] = "choose_target"
        source_name = LANGUAGES[lang_code]['name']
        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")

        msg = await callback_query.message.answer(f"✅ Выбран язык оригинала: {source_name}\n\n🔤 Выбери язык перевода:", reply_markup=get_language_keyboard_back_to_target())
        user_data[user_id]['last_target_msg_id'] = msg.message_id
        await callback_query.answer()
        return

    elif data.startswith("set_target_"):
        lang_code = data.split('_')[2]
        user_data[user_id]['target_lang'] = lang_code
        user_state[user_id] = "translate"
        src_name = LANGUAGES[user_data[user_id]['source_lang']]['name']
        tgt_name = LANGUAGES[lang_code]['name']
        try:
            msg_id = user_data[user_id].get('last_target_msg_id')
            if msg_id:
                await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение выбора целевого языка: {e}")
        await callback_query.message.answer(f"✅ Язык оригинала: {src_name}\n✅ Язык перевода: {tgt_name}\n\nТеперь отправь текст для перевода.")
        await callback_query.answer()
        return

    await callback_query.answer()

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())