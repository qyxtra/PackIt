# -- >> Imports << --
import os
import time
import asyncio
import urllib.request
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, BotCommand, LabeledPrice, PreCheckoutQuery

from modules.config import (
    TOKEN, STARS, DICE_CD,
    IMG_MENU, IMG_PROFILE, IMG_TARIFFS, IMG_SETTINGS, IMG_HELP, IMG_PAY, IMG_REF, IMG_DICE,
    drafts
)
from modules.storage import Storage, profile
from modules.keyboards import Flow, Keyboard, NAME_PRESETS
from modules.texts import Text
from modules.helpers import msgs, render, upgrade
from modules.packing import router as packing_router


# -- >> Init << --
router = Router()
Storage.load()


# -- >> Helpers << --
async def grant_ref_reward(bot, u):
    if not u.ref_by or u.ref_rewarded:
        return
    u.ref_rewarded = True
    inviter = profile(u.ref_by)
    inviter.invited += 1
    inviter.ref_rewards += 1
    Storage.save()
    try:
        await bot.send_message(inviter.uid, Text.REF_NEW, reply_markup=Keyboard.ref_reward())
    except Exception:
        pass


# -- >> Handlers << --
@router.message(CommandStart())
async def start(msg, state, bot):
    await state.clear()
    uid = msg.from_user.id
    msgs.pop(uid, None)
    u = profile(uid)

    args = msg.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith('ref_'):
        ref = args[1][4:]
        if ref.isdigit() and int(ref) != uid and not u.ref_by and not u.registered():
            u.ref_by = int(ref)
            Storage.save()

    if not u.registered():
        await state.set_state(Flow.reg_name)
        await msg.answer(Text.REG_NAME, reply_markup=Keyboard.reg_name())
        return
    await render(msg, Text.dashboard(u), Keyboard.main(), photo=IMG_MENU)


@router.callback_query(Flow.reg_name, F.data == 'not_student')
async def not_student(cb, state, bot):
    u = profile(cb.from_user.id)
    u.is_student = False
    u.name = cb.from_user.first_name or 'Пользователь'
    u.group = '-'
    u.name_tpl = '{subject}'
    Storage.save()
    await state.clear()
    await cb.answer('✅ Выбран режим личного использования')
    await grant_ref_reward(bot, u)
    await render(cb, Text.dashboard(u), Keyboard.main(), photo=IMG_MENU)


@router.callback_query(Flow.reg_name, F.data == 'skip_name')
async def bypass(cb, state):
    u = profile(cb.from_user.id)
    u.is_student = True
    u.name = 'Студент'
    Storage.save()
    await state.set_state(Flow.reg_group)
    await render(cb, Text.REG_GROUP, Keyboard.skip('skip_group'))


@router.message(Flow.reg_name)
async def enroll(msg, state):
    u = profile(msg.from_user.id)
    u.is_student = True
    u.name = msg.text.strip()
    Storage.save()
    await state.set_state(Flow.reg_group)
    await msg.answer(Text.REG_GROUP, reply_markup=Keyboard.skip('skip_group'))


@router.callback_query(Flow.reg_group, F.data == 'skip_group')
async def omit(cb, state, bot):
    u = profile(cb.from_user.id)
    u.group = 'Группа'
    if u.name_tpl == '{subject}':
        u.name_tpl = '{name}_{group}_{subject}'
    Storage.save()
    await state.clear()
    await grant_ref_reward(bot, u)
    await render(cb, Text.dashboard(u), Keyboard.main(), photo=IMG_MENU)


@router.message(Flow.reg_group)
async def assign(msg, state, bot):
    u = profile(msg.from_user.id)
    u.group = msg.text.strip()
    if u.name_tpl == '{subject}':
        u.name_tpl = '{name}_{group}_{subject}'
    Storage.save()
    await state.clear()
    await grant_ref_reward(bot, u)
    await render(msg, Text.dashboard(u), Keyboard.main(), photo=IMG_MENU)


@router.callback_query(F.data == 'menu')
async def menu(cb, state):
    await state.clear()
    uid = cb.from_user.id
    msgs.pop(uid, None)
    u = profile(uid)
    await render(cb, Text.dashboard(u), Keyboard.main(), photo=IMG_MENU)


@router.callback_query(F.data == 'settings')
async def preferences(cb):
    u = profile(cb.from_user.id)
    await render(cb, Text.settings(u), Keyboard.settings(u), photo=IMG_SETTINGS)


@router.callback_query(F.data == 're_register')
async def re_register(cb):
    await render(cb, Text.REREG_CONFIRM, Keyboard.confirm_rereg())


@router.callback_query(F.data == 'confirm_rereg')
async def confirm_rereg(cb, state):
    await state.set_state(Flow.reg_name)
    await render(cb, Text.REG_NAME, Keyboard.reg_name())


@router.callback_query(F.data.startswith('tpl_'))
async def template(cb):
    code = cb.data[4:]
    u = profile(cb.from_user.id)
    preset = next((tpl for c, _, tpl in NAME_PRESETS if c == code), None)
    if not preset:
        await cb.answer()
        return
    if u.name_tpl == preset:
        await cb.answer('✅ Этот шаблон уже выбран')
        return
    u.name_tpl = preset
    Storage.save()
    await cb.answer('✅ Формат названия сохранён')
    await render(cb, Text.settings(u), Keyboard.settings(u), photo=IMG_SETTINGS)


@router.callback_query(F.data == 'toggle_readme')
async def toggle_readme(cb):
    u = profile(cb.from_user.id)
    u.readme = not u.readme
    Storage.save()
    state_text = 'включено' if u.readme else 'отключено'
    await cb.answer(f'✅ Добавление README.txt {state_text}')
    await render(cb, Text.settings(u), Keyboard.settings(u), photo=IMG_SETTINGS)


@router.callback_query(F.data == 'profile')
async def settings(cb):
    u = profile(cb.from_user.id)
    await render(cb, Text.profile(u), Keyboard.profile(u.is_student), photo=IMG_PROFILE)


@router.callback_query(F.data == 'history')
async def history(cb):
    u = profile(cb.from_user.id)
    if not u.history:
        await cb.answer('📭 История работ пока пуста.', show_alert=True)
        return
    await render(cb, f'📜 *Последние работы ({len(u.history[:5])})*\n👇 Выберите работу для скачивания.', Keyboard.history(u.history))


@router.callback_query(F.data.startswith('hist_'))
async def fetch(cb):
    wid = cb.data[5:]
    u = profile(cb.from_user.id)
    item = next((x for x in u.history if x['id'] == wid), None)
    if not item or not os.path.exists(item['path']):
        await cb.answer('⚠️ Файл не найден или был удален.', show_alert=True)
        return
    await cb.answer()
    dt = f" ({item['date']})" if item.get('date') else ''
    await cb.message.answer_document(FSInputFile(item['path']), caption=f"📄 *{item['title']}*{dt}")


@router.callback_query(F.data == 'set_name')
async def prompt(cb, state):
    await state.set_state(Flow.edit_name)
    await render(cb, Text.EDIT_NAME, Keyboard.back())


@router.message(Flow.edit_name)
async def rename(msg, state):
    u = profile(msg.from_user.id)
    u.name = msg.text.strip()
    Storage.save()
    await state.clear()
    label = 'ФИО' if u.is_student else 'Имя'
    await msg.answer(f'✅ {label} обновлено, *{u.name}*', reply_markup=Keyboard.profile(u.is_student))


@router.callback_query(F.data == 'set_group')
async def request(cb, state):
    await state.set_state(Flow.edit_group)
    await render(cb, Text.EDIT_GROUP, Keyboard.back())


@router.message(Flow.edit_group)
async def regroup(msg, state):
    u = profile(msg.from_user.id)
    u.group = msg.text.strip()
    Storage.save()
    await state.clear()
    await msg.answer(f'✅ Группа обновлена, *{u.group}*', reply_markup=Keyboard.profile(u.is_student))


@router.callback_query(F.data == 'invite')
async def invite(cb, bot):
    u = profile(cb.from_user.id)
    me = await bot.get_me()
    await render(
        cb,
        Text.invite(me.username, u.uid, u.invited, u.ref_rewards),
        Keyboard.invite(u.ref_rewards),
        photo=IMG_REF
    )


@router.callback_query(F.data == 'ref_rewards')
async def ref_rewards(cb):
    u = profile(cb.from_user.id)
    if u.ref_rewards <= 0:
        await cb.answer(Text.REF_EMPTY, show_alert=True)
        return
    await render(cb, Text.ref_rewards(u.ref_rewards), Keyboard.ref_reward(from_invite=True))


@router.callback_query(F.data == 'defer_ref_reward')
async def defer_ref_reward(cb):
    await cb.answer()
    await render(cb, Text.REF_DEFERRED, Keyboard.main())


@router.callback_query(F.data == 'claim_ref_packs')
async def claim_ref_packs(cb):
    u = profile(cb.from_user.id)
    if u.ref_rewards <= 0:
        await cb.answer(Text.REF_EMPTY, show_alert=True)
        return
    u.ref_rewards -= 1
    u.used = max(0, u.used - 2)
    Storage.save()
    await cb.answer('✅ Начислено +2 сборки!', show_alert=True)
    if u.ref_rewards > 0:
        await render(cb, Text.ref_rewards(u.ref_rewards), Keyboard.ref_reward(from_invite=True))
    else:
        await render(cb, Text.dashboard(u), Keyboard.main(), photo=IMG_MENU)


@router.callback_query(F.data == 'claim_ref_pro')
async def claim_ref_pro(cb):
    uid = cb.from_user.id
    u = profile(uid)
    if u.ref_rewards <= 0:
        await cb.answer(Text.REF_EMPTY, show_alert=True)
        return
    u.ref_rewards -= 1
    upgrade(uid, days=3)
    await cb.answer('⭐️ Начислено 3 дня подписки Pro!', show_alert=True)
    if u.ref_rewards > 0:
        await render(cb, Text.ref_rewards(u.ref_rewards), Keyboard.ref_reward(from_invite=True))
    else:
        await render(cb, Text.dashboard(u), Keyboard.main(), photo=IMG_MENU)


@router.callback_query(F.data == 'dice')
async def dice(cb):
    u = profile(cb.from_user.id)
    now = time.time()
    if now - u.last_dice < DICE_CD:
        left = int(DICE_CD - (now - u.last_dice))
        hours, rem = divmod(left, 3600)
        mins = rem // 60
        await render(cb, f'⏳ *Попытать удачу*\n\nСледующий бросок будет доступен через *{hours} ч. {mins} мин.*', Keyboard.back(), photo=IMG_DICE)
        return
    text = (
        '🎲 *Попытать удачу*\n\n'
        'Бросьте кубик (раз в 24 часа)\n'
        '🎁 Выпадет *4 или 5*, бонусная сборка (+1 к лимиту)\n'
        '⭐️ Выпадет *6*, активация *подписки Pro* на 30 дней\n'
        '💨 Выпадет *от 1 до 3*, без приза'
    )
    await render(cb, text, Keyboard.dice(), photo=IMG_DICE)


@router.callback_query(F.data == 'roll_dice')
async def roll(cb):
    uid = cb.from_user.id
    u = profile(uid)
    now = time.time()
    if now - u.last_dice < DICE_CD:
        await cb.answer('⏳ Время еще не прошло!', show_alert=True)
        return

    u.last_dice = now
    await cb.message.delete()
    shot = await cb.message.answer_dice(emoji='🎲')
    val = shot.dice.value
    await asyncio.sleep(3.5)

    if val == 6:
        upgrade(uid, days=30)
        res = f'🎉 Выпало *{val}*! Поздравляем, вы выиграли *подписку Pro* на 30 дней! ⭐️'
    elif val in (4, 5):
        u.used = max(0, u.used - 1)
        Storage.save()
        res = f'🎁 Выпало *{val}*! Вы выиграли *+1 дополнительную сборку*.'
    else:
        Storage.save()
        res = f'🎲 Выпало *{val}*. В этот раз не повезло, попробуйте завтра.'

    await cb.message.answer(res, reply_markup=Keyboard.main())


@router.callback_query(F.data == 'pro')
async def pro(cb):
    u = profile(cb.from_user.id)
    u.refresh()
    if u.pro:
        await render(cb, Text.PRO, Keyboard.back(), photo=IMG_TARIFFS)
        return
    await render(cb, Text.TARIFFS, Keyboard.tariffs(), photo=IMG_TARIFFS)


@router.callback_query(F.data == 'pro_resume')
async def resume(cb):
    u = profile(cb.from_user.id)
    u.refresh()
    if u.pro:
        await render(cb, Text.PRO, Keyboard.back(), photo=IMG_TARIFFS)
        return
    await render(cb, Text.TARIFFS, Keyboard.tariffs(resume=True), photo=IMG_TARIFFS)


@router.callback_query(F.data == 'select_pro')
async def tariff(cb):
    draft = bool(drafts.get(cb.from_user.id))
    await render(cb, Text.PRO_INFO, Keyboard.pay(resume=draft), photo=IMG_PAY)


@router.callback_query(F.data == 'buy_rub')
async def rub(cb):
    uid = cb.from_user.id
    upgrade(uid)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer('🎉')
    if drafts.get(uid):
        await cb.message.answer(Text.PAID_DRAFT, reply_markup=Keyboard.format(True))
    else:
        await cb.message.answer(Text.PAID, reply_markup=Keyboard.main())


@router.callback_query(F.data == 'buy_stars')
async def stars(cb):
    await cb.answer()
    await cb.message.answer_invoice(
        title='⭐️ Подписка Pro (1 месяц)',
        description='⚡️ Безлимитные сборки работ, генерация отчетов в Word (.docx) будет добавлена позже.',
        payload='pro_monthly_stars',
        provider_token='',
        currency='XTR',
        prices=[LabeledPrice(label='⭐️ Подписка Pro (30 дней)', amount=STARS)]
    )


@router.pre_checkout_query()
async def checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def paid(msg: Message):
    uid = msg.from_user.id
    upgrade(uid)
    await msg.answer('🎉')
    if drafts.get(uid):
        await msg.answer(Text.PAID_DRAFT, reply_markup=Keyboard.format(True))
    else:
        await msg.answer(Text.PAID, reply_markup=Keyboard.main())


@router.callback_query(F.data == 'help')
async def instruction(cb):
    await render(cb, Text.HELP, Keyboard.back(), photo=IMG_HELP)


# -- >> Entry << --
async def run():
    proxies = urllib.request.getproxies()
    proxy = proxies.get('https') or proxies.get('http')

    session = AiohttpSession(proxy=proxy) if proxy else AiohttpSession()
    bot = Bot(
        token=TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode='Markdown')
    )

    try:
        await bot.set_my_commands([
            BotCommand(command='start', description='🚀 Главное меню')
        ])
        dp = Dispatcher()
        dp.include_routers(router, packing_router)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        print('\nBot stopped.')
