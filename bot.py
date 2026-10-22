
import os
import asyncio
import logging
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile
from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = os.getenv(
    "GEMINI_IMAGE_MODEL",
    "gemini-3.1-flash-lite-image",
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = genai.Client(api_key=GEMINI_API_KEY)


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎨 KODEX Art AI\n\n"
        "Преврати свою идею в изображение!\n\n"
        "✍️ Опиши картинку на русском или английском языке.\n"
        "Например: Белый робот в футуристическом городе "
        "с неоновым освещением.\n\n"
        "✨ Твоя фантазия — наше вдохновение!\n"
        "© KODEX MEDIA GROUP"
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "🖌 Как создать изображение?\n\n"
        "1. Опиши, что хочешь увидеть.\n"
        "2. Отправь сообщение.\n"
        "3. Подожди, пока бот создаст картинку.\n\n"
        "Чем точнее описание, тем лучше результат."
    )


@dp.message(F.text)
async def generate_image(message: Message):
    prompt = message.text.strip()

    if len(prompt) < 3:
        await message.answer("✍️ Опиши свою идею немного подробнее.")
        return

    status = await message.answer(
        "🎨 Создаю изображение…\nПожалуйста, подожди немного."
    )

    try:
        response = await client.aio.models.generate_content(
            model=IMAGE_MODEL,
            contents=(
                "Generate one high-quality image from the following prompt. "
                "Return an actual image, not only a text description.\n\n"
                + prompt
            ),
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        image_bytes = None

        for part in response.parts or []:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                break

        if not image_bytes:
            await status.edit_text(
                "😔 Модель не вернула изображение. "
                "Попробуй изменить описание."
            )
            return

        photo = BufferedInputFile(
            image_bytes,
            filename="kodex_art.png",
        )

        await message.answer_photo(
            photo=photo,
            caption="✨ Создано с помощью KODEX Art AI\n"
                    "© KODEX MEDIA GROUP",
        )

        await status.delete()

    except Exception:
        logging.exception("Image generation failed")
        await status.edit_text(
            "⚠️ Не удалось создать изображение.\n\n"
            "Возможно, модель недоступна или достигнут лимит API. "
            "Попробуй позже."
        )


@dp.message()
async def unsupported_message(message: Message):
    await message.answer(
        "💬 Пока я принимаю текстовые описания изображений. "
        "Напиши, какую картинку хочешь создать!"
    )


async def main():
    logging.info("Starting KODEX Art AI")
    try:
        await dp.start_polling(bot)
    finally:
        await client.aio.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
