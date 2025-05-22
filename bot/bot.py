#!/usr/bin/env python3
import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# In-memory storage for pending media groups
media_groups: dict[str, dict] = {}


@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.reply(
        f"Hi {message.from_user.first_name}! I'll forward your messages to the channel."
    )


@dp.message(Command(commands=["help"]))
async def cmd_help(message: types.Message):
    await message.reply(
        "Send me any message, photo, video, document, or media group, and I'll forward it to the channel."
    )


@dp.message()
@dp.channel_post()
async def forward_handler(message: types.Message):
    mgid = message.media_group_id
    # If this is part of a media group, collect and schedule flush
    if mgid:
        group = media_groups.get(mgid)
        if not group:
            media_groups[mgid] = {
                "items": [],
                "chat_id": message.chat.id,
                "first_id": message.message_id,
            }

            async def flush(group_id: str):
                await asyncio.sleep(1)
                grp = media_groups.pop(group_id, None)
                if not grp:
                    return
                media = []
                for item in grp["items"]:
                    mtype = item["type"]
                    media_id = item["media"]
                    caption = item.get("caption")
                    entities = item.get("entities")
                    if mtype == "photo":
                        media.append(
                            types.InputMediaPhoto(
                                media=media_id,
                                caption=caption,
                                caption_entities=entities,
                            )
                        )
                    elif mtype == "video":
                        media.append(
                            types.InputMediaVideo(
                                media=media_id,
                                caption=caption,
                                caption_entities=entities,
                            )
                        )
                    elif mtype == "audio":
                        media.append(types.InputMediaAudio(media=media_id))
                    elif mtype == "document":
                        media.append(
                            types.InputMediaDocument(
                                media=media_id,
                                caption=caption,
                                caption_entities=entities,
                            )
                        )
                try:
                    await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
                except Exception as e:
                    logger.error(f"Error sending media group: {e}")
                # Notify the sender
                try:
                    await bot.send_message(
                        chat_id=grp["chat_id"],
                        reply_to_message_id=grp["first_id"],
                        text="Media group forwarded to the channel!",
                    )
                except Exception as e:
                    logger.error(f"Error notifying user: {e}")

            # Schedule the flush only once
            asyncio.create_task(flush(mgid))
        # Append this item
        group = media_groups[mgid]
        if message.photo:
            fid = message.photo[-1].file_id
            mtype = "photo"
        elif message.video:
            fid = message.video.file_id
            mtype = "video"
        elif message.audio:
            fid = message.audio.file_id
            mtype = "audio"
        elif message.document:
            fid = message.document.file_id
            mtype = "document"
        else:
            return
        item = {"type": mtype, "media": fid}
        if message.caption and not group["items"]:
            item["caption"] = message.caption
            item["entities"] = message.caption_entities
        group["items"].append(item)
        return

    # Single photo
    if message.photo:
        caption = message.caption or ""
        try:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=message.photo[-1].file_id,
                caption=caption or None,
                caption_entities=message.caption_entities,
            )
        except Exception as e:
            logger.error(f"Error forwarding photo: {e}")
        await message.reply("Photo forwarded to the channel!")
        return

    # Single video
    if message.video:
        caption = message.caption or ""
        try:
            await bot.send_video(
                chat_id=CHANNEL_ID,
                video=message.video.file_id,
                caption=caption or None,
                caption_entities=message.caption_entities,
            )
        except Exception as e:
            logger.error(f"Error forwarding video: {e}")
        await message.reply("Video forwarded to the channel!")
        return

    # Single document
    if message.document:
        caption = message.caption or ""
        try:
            await bot.send_document(
                chat_id=CHANNEL_ID,
                document=message.document.file_id,
                caption=caption or None,
                caption_entities=message.caption_entities,
            )
        except Exception as e:
            logger.error(f"Error forwarding document: {e}")
        await message.reply("Document forwarded to the channel!")
        return

    # Single audio
    if message.audio:
        caption = message.caption or ""
        try:
            await bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=message.audio.file_id,
                caption=caption or None,
                caption_entities=message.caption_entities,
            )
        except Exception as e:
            logger.error(f"Error forwarding audio: {e}")
        await message.reply("Audio forwarded to the channel!")
        return

    # Single voice
    if message.voice:
        caption = message.caption or ""
        try:
            await bot.send_voice(
                chat_id=CHANNEL_ID,
                voice=message.voice.file_id,
                caption=caption or None,
                caption_entities=message.caption_entities,
            )
        except Exception as e:
            logger.error(f"Error forwarding voice: {e}")
        await message.reply("Voice message forwarded to the channel!")
        return

    # Single sticker
    if message.sticker:
        try:
            await bot.send_sticker(
                chat_id=CHANNEL_ID,
                sticker=message.sticker.file_id,
            )
        except Exception as e:
            logger.error(f"Error forwarding sticker: {e}")
        await message.reply("Sticker forwarded to the channel!")
        return

    # Single video note
    if message.video_note:
        try:
            await bot.send_video_note(
                chat_id=CHANNEL_ID,
                video_note=message.video_note.file_id,
            )
        except Exception as e:
            logger.error(f"Error forwarding video note: {e}")
        await message.reply("Video note forwarded to the channel!")
        return

    # Fallback text
    if message.text:
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=message.text,
                entities=message.entities,
            )
        except Exception:
            await bot.send_message(chat_id=CHANNEL_ID, text=message.text)
        await message.reply("Message forwarded to the channel!")
        return


if __name__ == "__main__":
    dp.run_polling(bot)
