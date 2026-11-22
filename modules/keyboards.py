# -- >> Imports << --
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# -- >> Constants << --
NAME_PRESETS = [
    ('ngs', 'ФИО_Группа_Предмет', '{name}_{group}_{subject}'),
    ('gns', 'Группа_ФИО_Предмет', '{group}_{name}_{subject}'),
    ('sng', 'Предмет_ФИО_Группа', '{subject}_{name}_{group}'),
    ('ns', 'ФИО_Предмет', '{name}_{subject}'),
    ('s', 'Только Предмет', '{subject}')
]


# -- >> Classes << --
class Flow(StatesGroup):
    reg_name = State()
    reg_group = State()
    edit_name = State()
    edit_group = State()
    files = State()
    subject = State()


class Keyboard:
    @staticmethod
    def main():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📦 Собрать работу', callback_data='pack')],
            [
                InlineKeyboardButton(text='👤 Профиль', callback_data='profile'),
                InlineKeyboardButton(text='💳 Оплата', callback_data='pro')
            ],
            [
                InlineKeyboardButton(text='🤝 Пригласить друга', callback_data='invite'),
                InlineKeyboardButton(text='🎲 Попытать удачу', callback_data='dice')
            ],
            [
                InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings'),
                InlineKeyboardButton(text='💡 Инструкция', callback_data='help')
            ]
        ])

    @staticmethod
    def settings(u):
        rows = []
        presets = NAME_PRESETS if u.is_student else [
            ('ns', 'Имя_Название', '{name}_{subject}'),
            ('s', 'Только Название', '{subject}')
        ]
        for code, label, tpl in presets:
            mark = '✅ ' if tpl == u.name_tpl else ''
            rows.append([InlineKeyboardButton(text=f'{mark}{label}', callback_data=f'tpl_{code}')])
        readme_btn = '📄 README.txt в ZIP: Вкл ✅' if u.readme else '📄 README.txt в ZIP: Выкл ❌'
        rows.append([InlineKeyboardButton(text=readme_btn, callback_data='toggle_readme')])
        rows.append([InlineKeyboardButton(text='🔄 Пройти регистрацию заново', callback_data='re_register')])
        rows.append([InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def confirm_rereg():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='✅ Да, пройти заново', callback_data='confirm_rereg')],
            [InlineKeyboardButton(text='🔙 Назад в настройки', callback_data='settings')]
        ])

    @staticmethod
    def reg_name():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='💼 Я не студент', callback_data='not_student')],
            [InlineKeyboardButton(text='⏭ Пропустить', callback_data='skip_name')]
        ])

    @staticmethod
    def profile(is_student=True):
        edit_row = [InlineKeyboardButton(text='✏️ Изменить ФИО' if is_student else '✏️ Изменить имя', callback_data='set_name')]
        if is_student:
            edit_row.append(InlineKeyboardButton(text='🎓 Изменить группу', callback_data='set_group'))
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📜 История работ', callback_data='history')],
            edit_row,
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')]
        ])

    @staticmethod
    def history(items):
        rows = []
        for item in items[:5]:
            dt = f" ({item['date']})" if item.get('date') else ''
            rows.append([InlineKeyboardButton(text=f"📄 {item['title']}{dt}", callback_data=f"hist_{item['id']}")])
        rows.append([InlineKeyboardButton(text='🔙 В профиль', callback_data='profile')])
        rows.append([InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def collect(has_items=False):
        rows = [
            [InlineKeyboardButton(text='✅ Готово', callback_data='done')]
        ]
        if has_items:
            rows.append([
                InlineKeyboardButton(text='🔀 Порядок', callback_data='reorder'),
                InlineKeyboardButton(text='❌ Удалить файл', callback_data='remove_menu')
            ])
        rows.append([InlineKeyboardButton(text='🗑 Очистить список', callback_data='clear')])
        rows.append([InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def remove(items):
        rows = []
        for i, item in enumerate(items):
            name = item.title if len(item.title) <= 28 else item.title[:25] + '...'
            rows.append([InlineKeyboardButton(text=f'❌ {i + 1}. {name}', callback_data=f'del_file_{i}')])
        rows.append([InlineKeyboardButton(text='🔙 Назад к списку', callback_data='back_collect')])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def reorder(items):
        rows = [
            [
                InlineKeyboardButton(text='💻 Код -> 🖼 Скрины', callback_data='preset_code_first'),
                InlineKeyboardButton(text='🖼 Скрины -> 💻 Код', callback_data='preset_img_first')
            ],
            [
                InlineKeyboardButton(text='🔤 По алфавиту', callback_data='preset_alpha'),
                InlineKeyboardButton(text='🔄 Развернуть', callback_data='preset_reverse')
            ]
        ]
        for i, item in enumerate(items):
            name = item.title if len(item.title) <= 22 else item.title[:19] + '...'
            up = InlineKeyboardButton(text='⬆️' if i > 0 else '▪️', callback_data=f'move_up_{i}' if i > 0 else 'noop')
            down = InlineKeyboardButton(text='⬇️' if i < len(items) - 1 else '▪️', callback_data=f'move_dn_{i}' if i < len(items) - 1 else 'noop')
            rows.append([
                InlineKeyboardButton(text=f'{i + 1}. {name}', callback_data='noop'),
                up,
                down
            ])
        rows.append([InlineKeyboardButton(text='✅ Сохранить порядок', callback_data='back_collect')])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def format():
        strike = '\u0336'.join('Отчет Word .docx (Pro)') + '\u0336'
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📁 ZIP-архив (Бесплатно)', callback_data='make_zip')],
            [InlineKeyboardButton(text=f'📄 {strike}', callback_data='make_doc_soon')],
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')]
        ])

    @staticmethod
    def after_pack():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📦 Собрать ещё', callback_data='pack')],
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')]
        ])

    @staticmethod
    def tariffs(resume=False):
        rows = [
            [InlineKeyboardButton(text='⭐️ Тариф Pro', callback_data='select_pro')]
        ]
        if resume:
            rows.append([InlineKeyboardButton(text='🔙 Назад к выбору формата', callback_data='choose_format')])
        rows.append([InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def pay(resume=False):
        rows = [
            [InlineKeyboardButton(text='💳 Оформить за 99 ₽', callback_data='buy_rub')],
            [InlineKeyboardButton(text='⭐️ Оформить за 50 звёзд', callback_data='buy_stars')],
            [InlineKeyboardButton(text='🔙 К тарифам', callback_data='pro' if not resume else 'pro_resume')]
        ]
        rows.append([InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def dice():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🎲 Бросить кубик', callback_data='roll_dice')],
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')]
        ])

    @staticmethod
    def skip(target):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='⏭ Пропустить', callback_data=target)]
        ])

    @staticmethod
    def subject():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='⏭ Пропустить (по шаблону)', callback_data='skip_subject_tpl')],
            [InlineKeyboardButton(text="📄 Назвать просто 'Работа'", callback_data='skip_subject_raw')],
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')]
        ])

    @staticmethod
    def back():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='menu')]
        ])
