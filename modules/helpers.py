# -- >> Imports << --
import os
import time
import shutil
import asyncio
from datetime import datetime, timedelta
from aiogram.types import Message, FSInputFile, InputMediaPhoto

from modules.config import HISTORY, drafts
from modules.storage import Storage, profile
from modules.keyboards import Keyboard
from modules.texts import Text


# -- >> Variables << --
msgs = {}
cache = {}
locks = {}
pending = {}


# -- >> Functions << --
def media(path):
    return cache.get(path) or FSInputFile(path)


async def render(target, text, markup=None, photo=None):
    ok = bool(photo and os.path.exists(photo))

    if isinstance(target, Message):
        if ok:
            sent = await target.answer_photo(media(photo), caption=text, reply_markup=markup)
            if sent.photo:
                cache[photo] = sent.photo[-1].file_id
            return sent
        return await target.answer(text, reply_markup=markup)

    msg = target.message
    if msg.document:
        await msg.edit_reply_markup(reply_markup=None)
        if ok:
            sent = await msg.answer_photo(media(photo), caption=text, reply_markup=markup)
            if sent.photo:
                cache[photo] = sent.photo[-1].file_id
            return sent
        return await msg.answer(text, reply_markup=markup)

    if ok:
        content = InputMediaPhoto(media=media(photo), caption=text)
        if msg.photo:
            edited = await msg.edit_media(media=content, reply_markup=markup)
            if isinstance(edited, Message) and edited.photo:
                cache[photo] = edited.photo[-1].file_id
            return edited
        await msg.delete()
        sent = await msg.answer_photo(media(photo), caption=text, reply_markup=markup)
        if sent.photo:
            cache[photo] = sent.photo[-1].file_id
        return sent

    if msg.photo:
        await msg.delete()
        return await msg.answer(text, reply_markup=markup)
    if msg.text:
        return await msg.edit_text(text, reply_markup=markup)
    await msg.edit_reply_markup(reply_markup=None)
    return await msg.answer(text, reply_markup=markup)


def upgrade(uid, days=30):
    u = profile(uid)
    now = datetime.now()
    base = u.pro_until if (u.pro and u.pro_until and u.pro_until > now) else now
    u.pro = True
    u.pro_until = base + timedelta(days=days)
    Storage.save()
    return u


def store(u, title, src):
    wid = str(int(time.time() * 1000))
    date = datetime.now().strftime('%d.%m.%Y %H:%M')
    folder = os.path.join(HISTORY, u.prefix(), wid)
    os.makedirs(folder, exist_ok=True)
    dst = os.path.join(folder, os.path.basename(src))
    shutil.copy2(src, dst)

    u.history.insert(0, {'id': wid, 'title': title, 'date': date, 'path': dst})
    for old in u.history[5:]:
        target = os.path.dirname(old['path'])
        if os.path.exists(target):
            shutil.rmtree(target, ignore_errors=True)
    u.history = u.history[:5]
    Storage.save()


def listing(uid):
    items = drafts.get(uid, [])
    if not items:
        return Text.FILES
    names = '\n'.join(f'{i}. `{x.title}`' for i, x in enumerate(items, 1))
    return f"📥 *Получено файлов ({len(items)}):*\n\n{names}\n\n📎 Отправьте ещё или нажмите *'Готово'*:"


async def sync(msg, bot, uid):
    ver = pending.get(uid, 0) + 1
    pending[uid] = ver
    await asyncio.sleep(0.35)
    if pending.get(uid) != ver:
        return

    lock = locks.setdefault(uid, asyncio.Lock())
    async with lock:
        if pending.get(uid) != ver:
            return
        items = drafts.get(uid, [])
        text = listing(uid)
        markup = Keyboard.collect(has_items=bool(items))
        mid = msgs.get(uid)
        if mid:
            try:
                await bot.delete_message(chat_id=msg.chat.id, message_id=mid)
            except Exception:
                pass
        sent = await msg.answer(text, reply_markup=markup)
        msgs[uid] = sent.message_id
