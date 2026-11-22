# -- >> Imports << --
import os
from aiogram import F, Router
from aiogram.types import FSInputFile, Message

from modules.config import TEMP, CODE_EXT, IMG_EXT, IMG_TARIFFS, drafts, titles
from modules.packer import Attachment, Code, Image, Packer
from modules.storage import profile, cleanup
from modules.keyboards import Flow, Keyboard
from modules.texts import Text
from modules.helpers import msgs, pending, locks, render, store, listing, sync


# -- >> Variables << --
router = Router()
counters = {}
seen_msgs = {}


# -- >> Public << --
@router.callback_query(F.data == 'pack')
async def collect(cb, state):
    uid = cb.from_user.id
    u = profile(uid)
    if not u.allowed():
        await render(cb, Text.LIMIT, Keyboard.tariffs(), photo=IMG_TARIFFS)
        return
    async with locks.setdefault(uid, __import__('asyncio').Lock()):
        pending[uid] = pending.get(uid, 0) + 1
        cleanup(uid)
        counters[uid] = 0
        seen_msgs[uid] = set()
        msgs.pop(uid, None)
    await state.set_state(Flow.files)
    sent = await render(cb, Text.FILES, Keyboard.collect())
    if isinstance(sent, Message):
        msgs[uid] = sent.message_id


@router.callback_query(F.data == 'clear')
async def reset(cb):
    uid = cb.from_user.id
    async with locks.setdefault(uid, __import__('asyncio').Lock()):
        pending[uid] = pending.get(uid, 0) + 1
        cleanup(uid)
        counters[uid] = 0
        msgs[uid] = cb.message.message_id
    await cb.answer('🗑 Очищено')
    try:
        await render(cb, Text.CLEARED, Keyboard.collect())
    except Exception:
        pass


@router.callback_query(Flow.files, F.data == 'remove_menu')
async def remove(cb):
    uid = cb.from_user.id
    items = drafts.get(uid, [])
    if not items:
        await cb.answer(Text.EMPTY, show_alert=True)
        return
    await render(cb, '🗑 *Удаление файла:*\nНажмите на файл, который нужно убрать из сборки.', Keyboard.remove(items))


@router.callback_query(Flow.files, F.data.startswith('del_file_'))
async def delete(cb):
    uid = cb.from_user.id
    items = drafts.get(uid, [])
    idx = int(cb.data[9:])
    if 0 <= idx < len(items):
        removed = items.pop(idx)
        if os.path.exists(removed.path):
            os.remove(removed.path)
        await cb.answer(f'❌ Удалён: {removed.title}')
    else:
        await cb.answer()

    if not items:
        msgs[uid] = cb.message.message_id
        await render(cb, Text.CLEARED, Keyboard.collect())
    else:
        await render(cb, '🗑 *Удаление файла:*\nНажмите на файл, который нужно убрать из сборки.', Keyboard.remove(items))


@router.callback_query(Flow.files, F.data == 'reorder')
async def reorder(cb):
    uid = cb.from_user.id
    items = drafts.get(uid, [])
    if len(items) < 2:
        await cb.answer('⚠️ Добавьте минимум 2 файла для сортировки.', show_alert=True)
        return
    await render(cb, '🔀 *Порядок файлов:*\nВыберите пресет или переместите файлы кнопками ⬆️ / ⬇️.', Keyboard.reorder(items))


@router.callback_query(Flow.files, F.data == 'back_collect')
async def back(cb):
    uid = cb.from_user.id
    items = drafts.get(uid, [])
    msgs[uid] = cb.message.message_id
    await render(cb, listing(uid), Keyboard.collect(has_items=bool(items)))


@router.callback_query(Flow.files, F.data == 'noop')
async def noop(cb):
    await cb.answer()


@router.callback_query(Flow.files, F.data.startswith('preset_'))
async def preset(cb):
    uid = cb.from_user.id
    items = drafts.get(uid, [])
    if not items:
        await cb.answer()
        return
    mode = cb.data[7:]
    if mode == 'code_first':
        items.sort(key=lambda x: 0 if isinstance(x, Code) else (1 if isinstance(x, Image) else 2))
    elif mode == 'img_first':
        items.sort(key=lambda x: 0 if isinstance(x, Image) else (1 if isinstance(x, Code) else 2))
    elif mode == 'alpha':
        items.sort(key=lambda x: x.title.lower())
    elif mode == 'reverse':
        items.reverse()
    await cb.answer('✅ Порядок применён')
    try:
        await render(cb, '🔀 *Порядок файлов обновлён:*\nВыберите пресет или переместите файлы кнопками ⬆️ / ⬇️.', Keyboard.reorder(items))
    except Exception:
        pass


@router.callback_query(Flow.files, F.data.startswith('move_up_'))
async def up(cb):
    uid = cb.from_user.id
    items = drafts.get(uid, [])
    idx = int(cb.data[8:])
    if 0 < idx < len(items):
        items[idx], items[idx - 1] = items[idx - 1], items[idx]
    await cb.answer()
    await render(cb, '🔀 *Порядок файлов:*\nВыберите пресет или переместите файлы кнопками ⬆️ / ⬇️.', Keyboard.reorder(items))


@router.callback_query(Flow.files, F.data.startswith('move_dn_'))
async def down(cb):
    uid = cb.from_user.id
    items = drafts.get(uid, [])
    idx = int(cb.data[8:])
    if 0 <= idx < len(items) - 1:
        items[idx], items[idx + 1] = items[idx + 1], items[idx]
    await cb.answer()
    await render(cb, '🔀 *Порядок файлов:*\nВыберите пресет или переместите файлы кнопками ⬆️ / ⬇️.', Keyboard.reorder(items))


@router.message(Flow.files, F.document)
async def document(msg, bot):
    uid = msg.from_user.id
    seen = seen_msgs.setdefault(uid, set())
    if msg.message_id in seen:
        return
    seen.add(msg.message_id)

    doc = msg.document
    ext = os.path.splitext(doc.file_name)[1].lower()
    if ext in CODE_EXT:
        item = Code('', doc.file_name)
    elif ext in IMG_EXT:
        item = Image('', doc.file_name)
    else:
        item = Attachment('', doc.file_name)

    idx = counters.get(uid, 0) + 1
    counters[uid] = idx
    path = f'{TEMP}/{uid}_{idx}_{doc.file_name}'
    item.path = path
    drafts.setdefault(uid, []).append(item)

    await bot.download(doc, destination=path)
    await sync(msg, bot, uid)


@router.message(Flow.files, F.photo)
async def photo(msg, bot):
    uid = msg.from_user.id
    seen = seen_msgs.setdefault(uid, set())
    if msg.message_id in seen:
        return
    seen.add(msg.message_id)

    pic = msg.photo[-1]
    idx = counters.get(uid, 0) + 1
    counters[uid] = idx
    title = f'screen_{idx}.jpg'
    path = f'{TEMP}/{uid}_{idx}_{title}'

    item = Image(path, title)
    drafts.setdefault(uid, []).append(item)

    await bot.download(pic, destination=path)
    await sync(msg, bot, uid)


@router.callback_query(Flow.files, F.data == 'done')
async def subject(cb, state):
    uid = cb.from_user.id
    if not drafts.get(uid):
        await cb.answer(Text.EMPTY, show_alert=True)
        return
    pending[uid] = pending.get(uid, 0) + 1
    msgs.pop(uid, None)
    await state.set_state(Flow.subject)
    await render(cb, Text.SUBJECT, Keyboard.subject())


@router.callback_query(Flow.subject, F.data == 'skip_subject_tpl')
async def tpl(cb, state):
    uid = cb.from_user.id
    u = profile(uid)
    u.refresh()
    titles[uid] = ('Работа', True)
    await state.clear()
    await render(cb, Text.FORMAT, Keyboard.format(u.pro))


@router.callback_query(Flow.subject, F.data == 'skip_subject_raw')
async def raw(cb, state):
    uid = cb.from_user.id
    u = profile(uid)
    u.refresh()
    titles[uid] = ('Работа', False)
    await state.clear()
    await render(cb, Text.FORMAT, Keyboard.format(u.pro))


@router.message(Flow.subject)
async def choose(msg, state):
    uid = msg.from_user.id
    u = profile(uid)
    u.refresh()
    titles[uid] = (msg.text.strip(), True)
    await state.clear()
    await msg.answer(Text.FORMAT, reply_markup=Keyboard.format(u.pro))


@router.callback_query(F.data == 'choose_format')
async def select(cb):
    u = profile(cb.from_user.id)
    u.refresh()
    await render(cb, Text.FORMAT, Keyboard.format(u.pro))


@router.callback_query(F.data == 'make_zip')
async def archive(cb):
    uid = cb.from_user.id
    u = profile(uid)
    if not u.allowed():
        await render(cb, Text.LIMIT_SHORT, Keyboard.tariffs(), photo=IMG_TARIFFS)
        return
    items = drafts.get(uid, [])
    if not items:
        await cb.answer(Text.RESTART, show_alert=True)
        return
    await cb.answer()
    title, use_tpl = titles.get(uid, ('Работа', True))
    packer = Packer(u, title, use_tpl=use_tpl)
    for item in items:
        packer.add(item)
    out = packer.zip()
    u.used += 1
    store(u, title, out)
    caption = '📦 *Готово!*' if u.pro else f'📦 *Готово!* {u.status()}'
    await cb.message.delete()
    await cb.message.answer_document(FSInputFile(out), caption=caption, reply_markup=Keyboard.after())
    if os.path.exists(out):
        os.remove(out)
    cleanup(uid)


@router.callback_query(F.data == 'make_doc_soon')
async def soon(cb):
    await cb.answer(Text.WORD_SOON, show_alert=True)


@router.callback_query(F.data == 'make_doc')
async def report(cb):
    uid = cb.from_user.id
    u = profile(uid)
    u.refresh()
    items = drafts.get(uid, [])
    if not items:
        await cb.answer(Text.RESTART, show_alert=True)
        return
    if not u.pro:
        await render(cb, Text.NO_PRO, Keyboard.tariffs(resume=True), photo=IMG_TARIFFS)
        return
    if not any(isinstance(item, Code) for item in items):
        await cb.answer(Text.NO_CODE, show_alert=True)
        return
    await cb.answer()
    title, use_tpl = titles.get(uid, ('Работа', True))
    packer = Packer(u, title, use_tpl=use_tpl)
    for item in items:
        packer.add(item)
    out = packer.word()
    store(u, title, out)
    await cb.message.delete()
    await cb.message.answer_document(FSInputFile(out), caption=Text.DONE, reply_markup=Keyboard.after())
    if os.path.exists(out):
        os.remove(out)
    cleanup(uid)
