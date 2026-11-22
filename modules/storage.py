# -- >> Imports << --
import os
import json
from datetime import datetime, timedelta
from modules.config import USERS, users, drafts, titles


# -- >> Classes << --
class Student:
    def __init__(
        self,
        uid,
        name='',
        group='',
        pro=False,
        used=0,
        reset=None,
        pro_until=None,
        history=None,
        invited=0,
        ref_by=None,
        ref_rewards=0,
        ref_rewarded=False,
        last_dice=0,
        name_tpl='{name}_{group}_{subject}',
        readme=True,
        is_student=True
    ):
        self.uid = uid
        self.name = name
        self.group = group
        self.pro = pro
        self.used = used
        self.reset = datetime.fromisoformat(reset) if reset else datetime.now() + timedelta(days=7)
        self.pro_until = datetime.fromisoformat(pro_until) if pro_until else None
        self.history = history if history is not None else []
        self.invited = invited
        self.ref_by = ref_by
        self.ref_rewards = ref_rewards
        self.ref_rewarded = ref_rewarded
        self.last_dice = last_dice
        self.name_tpl = name_tpl
        self.readme = readme
        self.is_student = is_student

    def registered(self):
        return bool(self.name and (self.group or not self.is_student))

    def refresh(self):
        changed = False
        if datetime.now() >= self.reset:
            self.used = 0
            self.reset = datetime.now() + timedelta(days=7)
            changed = True
        if self.pro and self.pro_until and datetime.now() >= self.pro_until:
            self.pro = False
            self.pro_until = None
            changed = True
        if changed:
            Storage.save()

    def allowed(self):
        self.refresh()
        return self.pro or self.used < 3

    def status(self):
        self.refresh()
        if self.pro:
            if self.pro_until:
                return f"Тариф Pro (до {self.pro_until.strftime('%d.%m.%Y')})"
            return 'Тариф Pro (безлимит)'
        date = self.reset.strftime('%d.%m.%Y %H.%M')
        return f'Тариф Базовый (осталось {max(0, 3 - self.used)} из 3, сброс {date})'

    def prefix(self):
        n = self.name.replace(' ', '_').replace('.', '')
        if not self.is_student or not self.group or self.group == '-':
            return n or str(self.uid)
        g = self.group.replace('/', '-')
        return f'{n}_{g}'

    def filename(self, subject):
        n = self.name.replace(' ', '_').replace('.', '')
        g = '' if (not self.is_student or self.group == '-') else self.group.replace('/', '-')
        s = subject.replace(' ', '_').replace(',', '')
        raw = self.name_tpl.format(name=n, group=g, subject=s)
        while '__' in raw:
            raw = raw.replace('__', '_')
        return raw.strip('_') or s

    def dump(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'group': self.group,
            'pro': self.pro,
            'used': self.used,
            'reset': self.reset.isoformat(),
            'pro_until': self.pro_until.isoformat() if self.pro_until else None,
            'history': self.history,
            'invited': self.invited,
            'ref_by': self.ref_by,
            'ref_rewards': self.ref_rewards,
            'ref_rewarded': self.ref_rewarded,
            'last_dice': self.last_dice,
            'name_tpl': self.name_tpl,
            'readme': self.readme,
            'is_student': self.is_student
        }


class Storage:
    path = USERS

    @classmethod
    def load(cls):
        if not os.path.exists(cls.path):
            return
        with open(cls.path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        for uid, data in raw.items():
            users[int(uid)] = Student(
                data['uid'],
                data.get('name', ''),
                data.get('group', ''),
                data.get('pro', False),
                data.get('used', 0),
                data.get('reset'),
                data.get('pro_until'),
                data.get('history', []),
                data.get('invited', 0),
                data.get('ref_by'),
                data.get('ref_rewards', 0),
                data.get('ref_rewarded', False),
                data.get('last_dice', 0),
                data.get('name_tpl', '{name}_{group}_{subject}'),
                data.get('readme', True),
                data.get('is_student', True)
            )

    @classmethod
    def save(cls):
        raw = {str(uid): u.dump() for uid, u in users.items()}
        with open(cls.path, 'w', encoding='utf-8') as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)


# -- >> Functions << --
def profile(uid):
    if uid not in users:
        users[uid] = Student(uid)
        Storage.save()
    return users[uid]


def cleanup(uid):
    for item in drafts.get(uid, []):
        if os.path.exists(item.path):
            os.remove(item.path)
    drafts[uid] = []
    titles.pop(uid, None)
