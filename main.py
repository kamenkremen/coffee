import sys
import sqlite3

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from coffee import Ui_Form
from addEditCoffeeForm import Ui_Coffee_Form

WRONG_QUERY = 'ошибка'


class Example(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.resize(800, 600)
        self.setWindowTitle('Каталог')

        self.btn_add.clicked.connect(self.add_record)
        self.btn_upd.clicked.connect(self.update_record)
        self.btn_del.clicked.connect(self.delete_record)

        self.table.clicked.connect(self.clear_text)
        self.table.doubleClicked.connect(self.update_record)

        self.con = sqlite3.connect('data/coffee.sqlite')
        self.cur = self.con.cursor()
        self.results = self.cur.execute('SELECT * FROM Coffee').fetchall()
        self.titles = [description[0].capitalize() for description in self.cur.description]
        self.error = ''
        self.set_results()

    def upgrade(self):
        self.text.setText('Загрузка')
        self.repaint()
        self.results = sorted(self.cur.execute('SELECT * FROM Coffee').fetchall())
        self.set_results()
        self.text.setText('')
        self.update()

    def set_results(self):
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(len(self.titles))
        for i in range(len(self.titles)):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(self.titles[i]))
        for i, row in enumerate(self.results):
            self.table.setRowCount(self.table.rowCount() + 1)
            row = list(row)
            for j, item in enumerate(row):
                item = QTableWidgetItem(str(item))
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()

    def update_record(self):
        rows = set(i.row() for i in self.table.selectedItems())
        if len(rows) == 1:
            self.table.selectRow(*rows)
            row = [i.text() for i in self.table.selectedItems()]
            dialog = CoffeeDialog(self, *row)
            dialog.exec()
            if dialog.accepted:
                try:
                    items = dialog.get_items()

                    for n, i in enumerate(items):
                        if isinstance(i, str):
                            i = '"' + i.capitalize() + '"'
                        s = self.titles[n] + ' = ' + str(i)
                        que = f'''UPDATE Coffee SET {s} WHERE id = {items[0]}'''
                        self.cur.execute(que)
                        self.con.commit()
                        self.upgrade()
                except sqlite3.Error as error:
                    self.error = str(error) + ' ' + WRONG_QUERY
                    self.upgrade()
        else:
            self.text.setText('Выберите только одну клетку')

    def delete_record(self):
        rows = set(i.row() for i in self.table.selectedItems())
        if len(rows) == 1:
            self.table.selectRow(*rows)
            row = [i.text() for i in self.table.selectedItems()]

            subtitle = f'Вы действительно хотите \nудалить кофе "{row[1]}"?'
            dialog = QMessageBox(QMessageBox.Question, 'Подтверждение удаления', subtitle, QMessageBox.Yes |
                                 QMessageBox.No, self)
            ok = dialog.exec()

            if ok == QMessageBox.Yes:
                que = f'''DELETE FROM coffee WHERE id = {row[0]}'''
                self.cur.execute(que)
                self.con.commit()
                self.upgrade()
        else:
            self.text.setText('Выберите только одну клетку')

    def add_record(self):
        dialog = CoffeeDialog(self)
        dialog.exec()
        if dialog.accepted:
            try:
                items = dialog.get_items()
                items[0] = self.get_min_id()
                que = f'''INSERT INTO Coffee VALUES{tuple(items)}'''
                # que = f'''INSERT INTO Coffee({', '.join(self.titles)}) VALUES{tuple(items)}'''
                self.cur.execute(que)
                self.con.commit()
                self.upgrade()
            except sqlite3.Error:
                self.error = WRONG_QUERY
                self.upgrade()

    def get_min_id(self):
        ids = [0] + list(map(lambda x: x[0], self.results))
        for i in sorted(ids):
            if i + 1 not in ids:
                return int(i + 1)

    def clear_text(self):
        self.text.setText('')

    def closeEvent(self, event):
        self.con.close()


class CoffeeDialog(QDialog, Ui_Coffee_Form):
    def __init__(self, parent, id=-1, title='', level='', in_seeds='', cost='', volume=''):
        super().__init__(parent)
        self.setupUi(self)
        self.accepted = False
        self.id = id
        self.title.setText(title)
        self.level.setText(level)
        self.in_seeds.setText(in_seeds)
        self.cost.setText(cost)
        self.volume.setText(volume)

        self.buttonBox.accepted.connect(self.my_accept)
        self.buttonBox.rejected.connect(self.reject)
        self.resize(self.minimumSize())

    def clear_text(self):
        self.text.setText('')
        self.resize(self.minimumSize())

    def get_items(self):
        try:
            return [int(self.id), self.title.text(), self.level.text(),
                    self.in_seeds.text(), int(self.cost.text()), int(self.volume.text())]
        except Exception:
            return [0]

    def my_accept(self):
        try:
            get = self.get_items()
            id, title, level, in_seeds, cost, size = get
            if all(get) and len(get) == 6 and not title.isspace() and in_seeds.lower() in ('в зернах', 'молотый'):
                self.accepted = True
                self.accept()
            else:
                raise ValueError
        except Exception:
            self.text.setText('Данные введены неправильно')


class UserConfirmationDialog(QDialog):
    def __init__(self, parent, title, title_1):
        super().__init__(parent)
        self.accepted = False
        self.resized = False
        self.setWindowTitle(title)
        self.verticalLayout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setText(title_1)

        self.verticalLayout.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.No | QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.my_accept)
        self.buttonBox.rejected.connect(self.reject)

    def paintEvent(self, event):
        if not self.resized:
            self.setFixedSize(self.minimumSize().width() + 10, self.minimumSize().height() + 20)
            self.resized = True

    def my_accept(self):
        self.accepted = True
        self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
