# -- >> Imports << --
import os


# -- >> Constants << --
TOKEN = '9277027034:AAFaanK9Tht2_e9gC26nIcR30lm33AXGb2E'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
