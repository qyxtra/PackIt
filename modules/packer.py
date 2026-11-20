# -- >> Imports << --
import os
import zipfile
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt


# -- >> Classes << --
class Attachment:
    def __init__(self, path, title):
        self.path = path
        self.title = title

    def info(self):
        return f'Файл, {self.title}'


class Code(Attachment):
    def text(self):
        with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def lines(self):
        return len(self.text().splitlines())

    def info(self):
        return f'Код, {self.title} ({self.lines()} строк)'


class Image(Attachment):
    def info(self):
        kb = round(os.path.getsize(self.path) / 1024, 1)
        return f'Скриншот, {self.title} ({kb} КБ)'


class Packer:
    def __init__(self, student, subject, use_tpl=True):
        self.student = student
        self.subject = subject.replace(' ', '_').replace(',', '')
        self.use_tpl = use_tpl
        self.items = []

    def add(self, item):
        self.items.append(item)

    def _base_name(self):
        return self.student.filename(self.subject) if self.use_tpl else self.subject

    def zip(self):
        name = f'{self._base_name()}.zip'
        if self.student.is_student:
            lines = [
                f'Студент, {self.student.name}',
                f'Группа, {self.student.group}',
                f'Работа, {self.subject}',
                f"Дата, {datetime.now().strftime('%d.%m.%Y %H.%M')}",
                '-' * 30
            ]
        else:
            lines = [
                f'Автор, {self.student.name}',
                f'Работа, {self.subject}',
                f"Дата, {datetime.now().strftime('%d.%m.%Y %H.%M')}",
                '-' * 30
            ]
        with zipfile.ZipFile(name, 'w') as z:
            for i, item in enumerate(self.items, 1):
                z.write(item.path, arcname=f'{i:02d}_{item.title}')
                lines.append(f'{i}. {item.info()}')
            if self.student.readme:
                z.writestr('README.txt', '\n'.join(lines))
        return name

    def word(self):
        name = f'{self._base_name()}.docx'
        doc = Document()
        doc.add_heading('ОТЧЕТ ПО РАБОТЕ' if not self.student.is_student else 'ОТЧЕТ ПО ПРАКТИЧЕСКОЙ РАБОТЕ', 0)
        p = doc.add_paragraph()
        if self.student.is_student:
            p.add_run(f'Студент, {self.student.name}\n').bold = True
            p.add_run(f'Группа, {self.student.group}\n').bold = True
            p.add_run(f'Дисциплина и тема, {self.subject}\n').bold = True
        else:
            p.add_run(f'Автор, {self.student.name}\n').bold = True
            p.add_run(f'Тема, {self.subject}\n').bold = True
        p.add_run(f"Дата выполнения, {datetime.now().strftime('%d.%m.%Y')}\n")
        doc.add_page_break()

        for item in self.items:
            doc.add_heading(item.title, level=2)
            if isinstance(item, Code):
                code = doc.add_paragraph()
                run = code.add_run(item.text())
                run.font.name = 'Consolas'
                run.font.size = Pt(9)
            elif isinstance(item, Image):
                doc.add_picture(item.path, width=Inches(5.5))
        doc.save(name)
        return name
