# -- >> Imports << --
import os


# -- >> Env << --
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE, '.env')

if os.path.exists(ENV_PATH):
    with open(ENV_PATH, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"\''))


# -- >> Constants << --
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError('BOT_TOKEN not found in .env file')

USERS = os.path.join(BASE, 'users.json')
TEMP = os.path.join(BASE, 'temp')
HISTORY = os.path.join(BASE, 'history')
ASSETS = os.path.join(BASE, 'assets')

IMG_MENU = os.path.join(ASSETS, 'главное_меню.png')
IMG_PROFILE = os.path.join(ASSETS, 'профиль.png')
IMG_TARIFFS = os.path.join(ASSETS, 'тарифы.png')
IMG_SETTINGS = os.path.join(ASSETS, 'настройки.png')
IMG_HELP = os.path.join(ASSETS, 'инструкция.png')
IMG_PAY = os.path.join(ASSETS, 'оплата.png')
IMG_REF = os.path.join(ASSETS, 'реферал.png')
IMG_DICE = os.path.join(ASSETS, 'удача.png')

RUB = 99
STARS = 50
DICE_CD = 86400

CODE_EXT = {'.py', '.cs', '.cpp', '.js', '.java', '.html', '.css', '.sql'}
IMG_EXT = {'.png', '.jpg', '.jpeg'}


# -- >> Variables << --
users = {}
drafts = {}
titles = {}


# -- >> Init << --
os.makedirs(TEMP, exist_ok=True)
os.makedirs(HISTORY, exist_ok=True)
