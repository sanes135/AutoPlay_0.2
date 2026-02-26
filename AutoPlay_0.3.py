import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import keyword
import keyboard
import mouse
import os
import threading
import time
import traceback

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")
    return os.path.join(base_path, relative_path)


def get_registry_save_dir():
    """
    Получает путь к папке сохранения из реестра.
    Возвращает путь или None, если не найден.
    """
    if not HAS_WINREG:
        return None

    try:
        # Открываем ключ реестра (создаем, если не существует)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\AutoKM",
            0,
            winreg.KEY_READ
        )
        value, regtype = winreg.QueryValueEx(key, "SaveDir")
        winreg.CloseKey(key)

        # Проверяем, что это строковое значение и папка существует
        if isinstance(value, str) and os.path.isdir(value):
            return value
    except FileNotFoundError:
        # Ключ или значение не существует
        pass
    except Exception:
        # Любая другая ошибка доступа к реестру
        pass

    return None


def set_registry_save_dir(path):
    """
    Сохраняет путь к папке сохранения в реестр.
    """
    if not HAS_WINREG:
        return

    try:
        # Создаем или открываем ключ реестра
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\AutoKM")
        winreg.SetValueEx(key, "SaveDir", 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
    except Exception:
        # Игнорируем ошибки записи в реестр
        pass


class SaveFileDialog(QDialog):
    """
    Диалог для ввода имени файла при сохранении макроса.
    """

    def __init__(self, parent=None, initial_dir=""):
        super().__init__(parent)
        self.initial_dir = initial_dir
        self.setWindowTitle("Сохранить макрос")
        self.setModal(True)

        layout = QVBoxLayout(self)

        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("Введите имя файла")
        layout.addWidget(self.filename_edit)

        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("Ок")
        cancel_btn = QPushButton("Отмена")
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_filename(self):
        return self.filename_edit.text().strip()


class GlobalHotkeyManager(QObject):
    """
    Менеджер хоткеев
    """
    toggle_clicker_signal = pyqtSignal()
    toggle_macro_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.clicker_key = "F6"
        self.macro_key = "F8"
        self.clicker_handle = None
        self.macro_handle = None

    def init_hotkeys(self):
        self.clicker_handle = keyboard.add_hotkey(self.clicker_key, self.toggle_clicker_signal.emit, suppress=True)
        self.macro_handle = keyboard.add_hotkey(self.macro_key, self.toggle_macro_signal.emit, suppress=True)

    def change_clicker_hotkey(self, new_key):
        keyboard.clear_all_hotkeys()
        self.clicker_key = new_key
        self.init_hotkeys()

    def change_macro_hotkey(self, new_key):
        keyboard.clear_all_hotkeys()
        self.macro_key = new_key  # Исправлено: было self.macro_handle
        self.init_hotkeys()

    def clear_hotkeys(self):
        keyboard.clear_all_hotkeys()


class InstructionsTab(QWidget):
    """
    Вкладка с инструкцией по использованию макроса.
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setFont(QFont("Arial", 11))

        instruction_content = """
<h2>Инструкция по использованию макроса</h2>

<p><b>1. Редактор кода:</b></p>
<ul>
<li>В левой части находится редактор кода, где вы можете писать Python-скрипты для макроса.</li>
<li>В правой части находится консоль, она показывает выполнение вашего макроса.</li>
</ul>

<p><b>2. Выполнение макроса:</b></p>
<ul>
<li>Нажмите кнопку <i>"Запустить"</i> или нажмите на хоткей для начала выполнения макроса.</li>
<li>Чтобы остановить макрос во время выполнения, используйте кнопку <i>"Выключить"</i> или соответствующий хоткей.</li>
<li>Проверяйте статус выполнения в консоли справа.</li>
</ul>

<p><b>3. Горячие клавиши:</b></p>
<ul>
<li>Возле кнопок "Сохранить" и "Загрузить" вы можете выберать клавишу из списка для запуска/остановки макроса.</li>
<li>Горячие клавиши макроса и автокликера не работают одновременно.</li>
</ul>

<li><b>4. Функции работы с клавиатурой:</b>
    <ul>
        <li><code>self</code> - работа с самим кодом (лучше не использовать, можно сломать программу!!!).</li>
        <li><code>wait(seconds)</code> - пауза в секундах.</li>
        <li><code>should_stop()</code> - проверяет, нужно ли остановить макрос.</li>
        <li><code>print(...)</code> - выводит сообщение в консоль.</li>
        <li><code>keyboard</code> - это библиотека для управления клавиатуры.</li>
        <li><code>mouse</code> - это библиотека для управления мыши.</li>
    </ul>
</li>

<li><b>Функции работы с клавиатурой:</b>
    <ul>
        <li><code>key_press('key')</code> - нажимает и удерживает клавишу (например, key_press('shift')).</li>
        <li><code>key_release('key')</code> - отпускает клавишу (например, key_release('shift')).</li>
        <li><code>key_is_pressed('key')</code> - проверяет, нажата ли клавиша (возвращает True/False).</li>
        <li><code>write('text', delay)</code> - печатает текст с задержкой между символами (например, write('Hello World!', 0.1)).</li>
        <li><code>send('key_sequence')</code> - отправляет последовательность клавиш (например, send('ctrl+a')).</li>
        <li><code>set_key(replaced_key, key)</code> - заменяет одну клавишу другой, но учитывайте, если вы хотите заменить 
        нажатие кнопки "Я" на "П", то надо написать set_key("Z", "G"). И обязательно после завершения программы сделайте clean_keyboard()</li>
    </ul>
</li>
<li><b>Функции работы с мышью:</b>
    <ul>
        <li><code>press_mouse('button')</code> - зажимает кнопку мыши ('left', 'right', 'middle').</li>
        <li><code>release_mouse('button')</code> - отпускает кнопку мыши ('left', 'right', 'middle').</li>
        <li><code>mouse_move(x, y, absolute=True, duration=0)</code> - перемещает курсор мыши (absolute=True - абсолютные координаты, duration - время перемещения).</li>
        <li><code>mouse_drag(start_x, start_y, end_x, end_y, absolute=True, duration=0)</code> - перемещает курсор мыши с зажатой кнопкой (имитация перетаскивания).</li>
        <li><code>mouse_position()</code> - возвращает кортеж текущих координат курсора (x, y).</li>
        <li><code>mouse_is_pressed(button='left')</code> - проверяет, нажата ли кнопка мыши (возвращает True/False).</li>
    </ul>
</li>
</ul>

<p><b>5. Пример простого макроса:</b></p>
<pre># Пример кода макроса
print('Старт')
while not should_stop():
    key_press('A')
    click()
    wait(0.5)
print('Завершено')</pre>
        """

        instructions_text.setHtml(instruction_content)
        layout.addWidget(instructions_text)




class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Цвета
        keyword_color = QColor("#FF7F00")
        string_color = QColor("#00AA00")
        comment_color = QColor("#808080")
        builtin_color = QColor("#44AAFF")

        # Форматы
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(keyword_color)
        self.keyword_format.setFontWeight(QFont.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(string_color)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(comment_color)

        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(builtin_color)

        self.rules = []

        # Ключевые слова
        for kw in keyword.kwlist:
            pattern = r'\b' + kw + r'\b'
            self.rules.append((QRegExp(pattern), self.keyword_format))

        # Встроенные функции
        builtins = [
            'len', 'print', 'range', 'int', 'str', 'list', 'dict', 'tuple',
            'set', 'float', 'bool', 'input', 'type', 'isinstance', 'hasattr',
            'getattr', 'setattr', 'delattr', 'callable', 'globals', 'locals',
            'vars', 'dir', 'help', 'exit', 'quit', 'abs', 'all', 'any',
            'bin', 'chr', 'ord', 'hex', 'id', 'repr', 'round', 'sum',
            'max', 'min', 'pow', 'divmod', 'enumerate', 'filter', 'map',
            'sorted', 'zip', 'open', 'super', 'property', 'staticmethod',
            'classmethod', 'object', 'Exception', 'BaseException'
        ]
        for name in builtins:
            pattern = r'\b' + name + r'\b'
            self.rules.append((QRegExp(pattern), self.builtin_format))

        # Комментарии
        self.comment_start = QRegExp(r'#')
        self.comment_format = self.comment_format

        # Строки
        self.string_patterns = [
            QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'),
            QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'")
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            expr = QRegExp(pattern)
            index = expr.indexIn(text)
            while index >= 0:
                length = expr.matchedLength()
                self.setFormat(index, length, fmt)
                index = expr.indexIn(text, index + length)

        # Комментарии
        comment_idx = self.comment_start.indexIn(text)
        if comment_idx >= 0:
            self.setFormat(comment_idx, len(text) - comment_idx, self.comment_format)

        # Строки
        for expr in self.string_patterns:
            index = expr.indexIn(text)
            while index >= 0:
                length = expr.matchedLength()
                self.setFormat(index, length, self.string_format)
                index = expr.indexIn(text, index + length)

class CodeEditor(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptRichText(False)
        self.setFontFamily("Courier New")
        self.setFontPointSize(12)

        # Подсветка синтаксиса
        self.highlighter = PythonSyntaxHighlighter(self.document())

        # Словарь для автозавершения скобок
        self.brackets = {
            '(': ')',
            '[': ']',
            '{': '}',
            '"': '"',
            "'": "'"
        }

        # Настройка completer
        self.completer = None
        self.setup_completer()

    def setup_completer(self):
        import keyword
        # Список слов для автодополнения
        words = keyword.kwlist + [
            'len', 'print', 'range', 'int', 'str', 'list', 'dict', 'tuple',
            'set', 'float', 'bool', 'input', 'type', 'isinstance', 'hasattr',
            'getattr', 'setattr', 'delattr', 'callable', 'globals', 'locals',
            'vars', 'dir', 'help', 'exit', 'quit', 'abs', 'all', 'any',
            'bin', 'chr', 'ord', 'hex', 'id', 'repr', 'round', 'sum',
            'max', 'min', 'pow', 'divmod', 'enumerate', 'filter', 'map',
            'sorted', 'zip', 'open', 'super', 'property', 'staticmethod',
            'classmethod', 'object', 'Exception', 'BaseException'
        ]
        model = QStringListModel(words)
        self.completer = QCompleter(model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setWidget(self)
        self.completer.activated.connect(self.insert_completion)

    def insert_completion(self, completion):
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def text_under_cursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def focusInEvent(self, e):
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(e)

    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                self.completer.activated.emit(self.completer.currentCompletion())
                return

        key = event.key()
        text = event.text()

        # Активация completer по Ctrl+Space
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Space:
            self.open_completer_manually()
            return

        # Tab - вставка 4 пробелов
        if key == Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                # Если выделен текст, добавить отступ ко всем строкам
                start_pos = cursor.selectionStart()
                end_pos = cursor.selectionEnd()
                cursor.setPosition(start_pos)
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
                lines = cursor.selectedText().splitlines()
                indented_lines = ["    " + line for line in lines]
                cursor.insertText("\n".join(indented_lines))
            else:
                self.insertPlainText("    ")
            return

        # Автозавершение скобок/кавычек
        if text in self.brackets:
            cursor = self.textCursor()
            cursor.insertText(text)
            if self.brackets[text] != text:  # не кавычки
                cursor.insertText(self.brackets[text])
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)
            else:  # кавычки — проверим, что не внутри слова
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor, 1)
                next_char = cursor.selectedText()
                if not next_char or next_char.isspace():
                    cursor.setPosition(cursor.position())
                    cursor.insertText(self.brackets[text])
                    cursor.movePosition(QTextCursor.PreviousCharacter)
                    self.setTextCursor(cursor)
                else:
                    cursor.clearSelection()
                    cursor.insertText(text)
            return

        # Удаление парной скобки при Backspace
        if key == Qt.Key_Backspace:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor, 1)
            next_char = cursor.selectedText()
            current_pos = cursor.position()

            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
            line_text = self.document().findBlockByNumber(cursor.blockNumber()).text()
            cursor_pos_in_line = current_pos - cursor.position()

            if cursor_pos_in_line < len(line_text):
                current_char = line_text[cursor_pos_in_line - 1]
                if current_char in self.brackets and next_char == self.brackets[current_char]:
                    cursor.select(QTextCursor.WordUnderCursor)
                    cursor.insertText(current_char + next_char)
                    cursor.deletePreviousChar()
                    self.setTextCursor(cursor)
                    return

            super().keyPressEvent(event)
            return

        # Отступ при нажатии Enter
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            line_text = cursor.selectedText()
            indent = self.get_indent_level(line_text)

            super().keyPressEvent(event)

            new_cursor = self.textCursor()
            new_cursor.insertText('    ' * indent)
            self.setTextCursor(new_cursor)
            return

        # Запуск completer при вводе
        if len(text) > 0 and text.isalnum():
            self.update_completer()
        else:
            self.completer.popup().hide()

        super().keyPressEvent(event)

    def update_completer(self):
        prefix = self.text_under_cursor()
        if len(prefix) < 2:
            self.completer.popup().hide()
            return

        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() > 0:
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

    def open_completer_manually(self):
        prefix = self.text_under_cursor()
        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() > 0:
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)

    def get_indent_level(self, line_text):
        stripped = line_text.lstrip()
        base_indent = len(line_text) - len(stripped)
        indent_size = 4
        level = base_indent // indent_size

        if stripped.endswith(':'):
            level += 1
        return level


class CodeTab(QWidget):
    """
    Вкладка 'Код' для редактирования и выполнения макросов.
    """
    console_output = pyqtSignal(str)  # Сигнал для вывода в консоль

    def __init__(self, parent_macro_editor, save_dir_setting, global_hotkey_manager):
        super().__init__()
        parent_macro_editor.code_tab_instance = self  # Ссылка на экземпляр в родительское окно
        self.parent_macro_editor = parent_macro_editor
        self.save_dir_setting = save_dir_setting
        self.global_hotkey_manager = global_hotkey_manager  # Передаём менеджер сюда
        # Используем threading.Event для контроля остановки
        self.stop_event = threading.Event()
        # Хранение информации о потоке
        self.execution_thread = None
        # Словарь для хранения глобальных функций
        self.global_functions = {}
        self.init_ui()
        self.setup_global_functions()
        self.load_last_macro()

    def setup_global_functions(self):
        self.global_functions = {
            # system
            'print': lambda *args: self.print_to_console(' '.join(map(str, args))),
            'wait': self._thread_safe_wait,
            'should_stop': self._check_stop_flag,
            'self': self,
            'keyboard': keyboard,
            'mouse': mouse,
            # keyboard
            'key_press': lambda key: keyboard.press(key.lower()),
            'key_release': lambda button: keyboard.release(button.lower()),
            'key_is_pressed': lambda key: keyboard.is_pressed(key.lower()),
            'write': lambda text, delay: keyboard.write(text, delay),
            'send': lambda key: keyboard.send(key),
            'set_key': lambda replaced_key, key: keyboard.add_hotkey(replaced_key.lower(), lambda: keyboard.send(key.lower()), suppress=True),
            'clean_keyboard': lambda : keyboard.clear_all_hotkeys(),
            # mouse
            'click': lambda button='left': mouse.click(button),
            'press_mouse': lambda button='left': mouse.press(button),
            'release_mouse': lambda button='left': mouse.release(button),
            'mouse_move': lambda x, y, absolute=True, duration=0: mouse.move(x, y, absolute, duration),
            'mouse_drag': lambda start_x, start_y, end_x, end_y, absolute=True, duration=0: mouse.drag(start_x, start_y, end_x, end_y, absolute, duration),
            'mouse_position': lambda: mouse.get_position(),
            'mouse_is_pressed': lambda: mouse.is_pressed()
        }

    def init_ui(self):
        layout = QHBoxLayout(self)

        left_group = QGroupBox("Редактор кода")
        left_layout = QVBoxLayout(left_group)
        self.code_textarea = CodeEditor()
        self.code_textarea.setFont(QFont("Consolas", 12))
        self.code_textarea.setPlainText(
            "# Пример кода макроса\nprint('Start')\nwhile not should_stop():\n    key_press('A')\n    click()\n    wait(0.5)\nprint('End')")
        left_layout.addWidget(self.code_textarea)

        # Правая часть: Консоль и кнопки
        right_group = QGroupBox("Конsole и управление")
        right_layout = QVBoxLayout(right_group)

        # Консоль
        self.console_display = QTextEdit()
        self.console_display.setReadOnly(True)
        self.console_display.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.console_display)

        # Кнопки под консолью
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.run_btn = QPushButton("Запустить")
        self.kill_btn = QPushButton("Выключить")

        self.run_btn.clicked.connect(self.start_execution)
        self.kill_btn.clicked.connect(self.stop_execution)
        self.save_btn.clicked.connect(self.save_macro)

        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.run_btn)
        buttons_layout.addWidget(self.kill_btn)
        right_layout.addLayout(buttons_layout)

        # Комбобокс для хоткея над консолью
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Хоткей:"))
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems([
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
            "T", "U", "V", "W", "X", "Y", "Z",
            "ALT", "CTRL", "TAB", "SHIFT", "SPACE",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"
        ])
        self.hotkey_combo.setCurrentText("F8")
        hotkey_layout.addWidget(self.hotkey_combo)

        self.load_btn = QPushButton("Загрузить")
        hotkey_layout.addWidget(self.load_btn)
        self.load_btn.clicked.connect(self.load_macro_from_file)

        hotkey_layout.addStretch(1)
        right_layout.addLayout(hotkey_layout)

        # Сборка основного layout
        main_h_layout = QHBoxLayout()
        main_h_layout.addWidget(left_group, stretch=2)
        main_h_layout.addWidget(right_group, stretch=1)

        layout.addLayout(main_h_layout)

        self.console_output.connect(self.append_to_console)

    def load_last_macro(self):
        """Автоматически загружает последний сохраненный макрос при запуске."""
        macros_dir = self.save_dir_setting
        if not os.path.isdir(macros_dir):
            os.makedirs(macros_dir)

        # Ищем файлы с расширением .py в папке макросов
        macro_files = [f for f in os.listdir(macros_dir) if f.endswith('.txt')]
        if macro_files:
            # Берем последний по времени создания/изменения
            latest_file = max(macro_files, key=lambda x: os.path.getmtime(os.path.join(macros_dir, x)))
            file_path = os.path.join(macros_dir, latest_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                self.code_textarea.setPlainText(code)
                self.print_to_console(f"Загружен последний макрос: {latest_file}")
            except Exception as e:
                self.print_to_console(f"Ошибка загрузки макроса: {e}")

    def load_macro_from_file(self):
        """Загружает код макроса из выбранного файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл кода макроса",
            self.save_dir_setting
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                self.code_textarea.setPlainText(code)
                self.print_to_console(f"Загружен макрос из файла: {os.path.basename(file_path)}")
            except Exception as e:
                self.print_to_console(f"Ошибка загрузки файла: {e}")

    def append_to_console(self, text):
        self.console_display.moveCursor(QTextCursor.End)
        self.console_display.insertPlainText(text + "\n")
        self.console_display.moveCursor(QTextCursor.End)

    def print_to_console(self, text):
        self.console_output.emit(str(text))

    def save_macro(self):
        code = self.code_textarea.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "Предупреждение", "Код пустой.")
            return

        dialog = SaveFileDialog(self, initial_dir=self.save_dir_setting)
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.get_filename()
            if not filename:
                QMessageBox.warning(self, "Предупреждение", "Имя файла не может быть пустым.")
                return

            if not filename.endswith('.txt'):
                filename += '.txt'

            save_path = os.path.join(self.save_dir_setting, filename)
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.print_to_console(f"Макрос сохранен в {save_path}")
            except Exception as e:
                self.print_to_console(f"Ошибка сохранения: {e}")

    def start_execution(self):
        if self.execution_thread and self.execution_thread.is_alive():
            self.print_to_console("Макрос уже выполняется.")
            return

        code = self.code_textarea.toPlainText()
        if not code.strip():
            self.print_to_console("Код пустой.")
            return

        try:
            compiled_code = compile(code, '<macro>', 'exec')
        except SyntaxError as e:
            self.print_to_console(f"Синтаксическая ошибка: {e}")
            return
        except Exception as e:
            self.print_to_console(f"Ошибка компиляции: {e}")
            return

        # Сбрасываем событие остановки
        self.stop_event.clear()

        # Устанавливаем хоткей через глобальный менеджер
        self.global_hotkey_manager.change_macro_hotkey(self.hotkey_combo.currentText())

        globals_dict = self.global_functions.copy()
        locals_dict = {}

        def run_code_in_thread():
            thread_id = threading.get_ident()
            self.print_to_console(f"Поток макроса запущен (ID: {thread_id}).")
            try:
                exec(compiled_code, globals_dict, locals_dict)
            except SystemExit:
                self.print_to_console("Макрос завершен через exit().")
            except Exception as e:
                if not self.stop_event.is_set():
                    self.print_to_console(f"Ошибка выполнения: {e}")
                    self.print_to_console(f"Трейсбек: {traceback.format_exc()}")
                else:
                    self.print_to_console("Выполнение макроса прервано пользователем.")
            finally:
                # Сбрасываем указатель на поток после завершения
                self.execution_thread = None
                self.print_to_console(f"Поток макроса завершен (ID: {thread_id}).")

        self.execution_thread = threading.Thread(target=run_code_in_thread, daemon=False)
        self.execution_thread.start()
        self.print_to_console("Макрос запущен.")

    def _thread_safe_wait(self, seconds):
        """Безопасное ожидание с проверкой флага остановки."""
        start_time = time.time()
        remaining = seconds
        while remaining > 0:
            sleep_time = min(0.01, remaining)
            if self.stop_event.wait(timeout=sleep_time):
                self.print_to_console("Ожидание прервано по сигналу остановки.")
                return
            remaining = seconds - (time.time() - start_time)

    def _check_stop_flag(self):
        """Функция для проверки флага остановки в макросе."""
        return self.stop_event.is_set()

    def stop_execution(self):
        # Устанавливаем событие остановки
        self.stop_event.set()
        self.print_to_console("Отправлена команда остановки макроса...")

        # Ждем завершения потока
        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_thread.join(timeout=2.0)
            if self.execution_thread and self.execution_thread.is_alive():
                self.print_to_console("ПРЕДУПРЕЖДЕНИЕ: Поток макроса не завершился за 2 секунды.")
            else:
                self.print_to_console("Поток макроса успешно завершен.")
        else:
            self.print_to_console("Макрос не был активен или уже остановлен.")


class SettingsTab(QWidget):
    """
    Вкладка 'Настройки' для выбора директории сохранения макросов и настройки хоткеев.
    """

    def __init__(self, save_dir_setting, global_hotkey_manager):
        super().__init__()
        self.save_dir_setting = save_dir_setting
        self.global_hotkey_manager = global_hotkey_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Настройка папки
        folder_group = QGroupBox("Папка для сохранения макросов")
        folder_layout = QVBoxLayout(folder_group)

        label = QLabel("Выберите папку для сохранения макросов:")
        folder_layout.addWidget(label)

        self.path_label = QLabel(self.save_dir_setting)
        self.path_label.setWordWrap(True)
        folder_layout.addWidget(self.path_label)

        browse_btn = QPushButton("Выбрать папку...")
        browse_btn.clicked.connect(self.browse_directory)
        folder_layout.addWidget(browse_btn)

        layout.addWidget(folder_group)
        layout.addStretch(1)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выбрать папку", self.save_dir_setting)
        if directory:
            self.save_dir_setting = directory
            self.path_label.setText(directory)
            # Сохраняем путь в реестр
            set_registry_save_dir(directory)


class MacroEditorWindow(QMainWindow):
    """
    Окно редактора макросов. Заменяет главное окно при вызове.
    """

    def __init__(self, auto_clicker_window, global_hotkey_manager):
        super().__init__()
        self.active = None
        self.auto_clicker_window = auto_clicker_window
        self.global_hotkey_manager = global_hotkey_manager  # Передаём менеджер
        username = os.getlogin()
        print(username)

        # Получаем путь из реестра, если он есть, иначе используем стандартный
        saved_path = get_registry_save_dir()
        if saved_path and os.path.isdir(saved_path):
            self.save_dir_setting = saved_path
        else:
            self.save_dir_setting = fr"C:\Users\{username}\.AutoKM"
            if not os.path.exists(self.save_dir_setting):
                os.makedirs(self.save_dir_setting)
            # Сохраняем стандартный путь в реестр
            set_registry_save_dir(self.save_dir_setting)

        # Атрибут для хранения экземпляра CodeTab
        self.code_tab_instance = None
        self.init_ui()

        # Подключаем сигнал переключения макроса
        self.global_hotkey_manager.toggle_macro_signal.connect(self.toggle_macro_from_hotkey)

    def init_ui(self):
        window_width = 900
        window_height = 650
        self.setWindowTitle("Редактор макросов")
        self.setGeometry(300, 300, window_width, window_height)
        self.setFixedSize(window_width, window_height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создание вкладок
        self.tabs = QTabWidget()
        # Передаём global_hotkey_manager в CodeTab
        self.code_tab = CodeTab(self, self.save_dir_setting, self.global_hotkey_manager)
        self.instructions_tab = InstructionsTab()
        self.settings_tab = SettingsTab(self.save_dir_setting, self.global_hotkey_manager)

        self.tabs.addTab(self.code_tab, "Код")
        self.tabs.addTab(self.instructions_tab, "Инструкция")
        self.tabs.addTab(self.settings_tab, "Настройки")

        layout.addWidget(self.tabs)

    def toggle_macro_from_hotkey(self):
        """Переключает состояние макроса по хоткею."""
        if self.active:
            if self.code_tab.execution_thread and self.code_tab.execution_thread.is_alive():
                # Останавливаем макрос
                self.code_tab.stop_execution()
            else:
                # Запускаем макрос
                self.code_tab.start_execution()

    def closeEvent(self, event):
        # Обязательно останавливаем макрос и удаляем хоткеи при закрытии
        if self.code_tab.execution_thread and self.code_tab.execution_thread.is_alive():
            self.code_tab.stop_execution()
            # Даем время на остановку
            if self.code_tab.execution_thread and self.code_tab.execution_thread.is_alive():
                reply = QMessageBox.question(self, 'Поток активен',
                                             "Поток макроса все еще активен. Закрыть окно?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    event.ignore()
                    return

        self.active = False
        self.auto_clicker_window.show()
        self.auto_clicker_window.active = True
        event.accept()


# --- Изменения в существующем классе ---

class AutoClickerWindow(QMainWindow):
    """
    Основное окно приложения автокликера.
    Позволяет настраивать таймер, методы кликов (мышь/клавиатура), горячие клавиши.
    """

    def __init__(self, global_hotkey_manager):
        super().__init__()
        self.global_hotkey_manager = global_hotkey_manager  # Передаём менеджер
        self.macro_window = None  # Не создаем окно сразу
        self.active = None
        self.init_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        window_width = 420
        window_height = 430

        self.setWindowTitle("AutoKM 0.3")
        self.setGeometry(300, 300, window_width, window_height)
        self.setFixedSize(window_width, window_height)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(5)

        self.time_input_layout = QHBoxLayout()
        self.time_labels_layout = QHBoxLayout()
        self.control_buttons_layout = QHBoxLayout()
        self.control_buttons_layout.setContentsMargins(0, 10, 0, 10)
        self.mouse_settings_layout = QHBoxLayout()
        self.keyboard_settings_layout = QHBoxLayout()
        self.hotkey_settings_layout = QHBoxLayout()
        self.input_method_layout = QHBoxLayout()

        self.available_keys = (
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
            "T", "U", "V", "W", "X", "Y", "Z",
            "ALT", "CTRL", "TAB", "SHIFT", "SPACE",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"
        )

        self.current_click_key = 'SPACE'
        self.current_mouse_button = "Left"
        self.current_hotkey = "F6"
        self.current_timer_interval_ms = 1000

        self.timer = QTimer()
        self.timer.setInterval(self.current_timer_interval_ms)
        self.timer.timeout.connect(self.perform_click)

        # Подключаем сигнал из глобального менеджера
        self.global_hotkey_manager.toggle_clicker_signal.connect(self.toggle_timer_state)

        # Инициализируем главный хоткей через менеджер
        self.global_hotkey_manager.init_hotkeys()

        self.timer_status_label = QLabel(self)
        self.timer_status_label.setText("Off")
        # --- Создание и настройка элементов интерфейса ---

        self.hours_spinbox = QSpinBox()
        self.hours_spinbox.setStyleSheet("font-size: 12pt; min-height: 30px;")
        self.hours_spinbox.valueChanged.connect(self.update_timer_interval)
        self.hours_spinbox.setMaximum(24)
        self.hours_label = QLabel("hours")
        self.hours_label.setStyleSheet("font-size: 10pt")

        self.minutes_spinbox = QSpinBox()
        self.minutes_spinbox.setStyleSheet("font-size: 12pt; min-height: 30px;")
        self.minutes_spinbox.valueChanged.connect(self.update_timer_interval)
        self.minutes_spinbox.setMaximum(1000)
        self.minutes_label = QLabel("mins")
        self.minutes_label.setStyleSheet("font-size: 10pt")

        self.seconds_spinbox = QSpinBox()
        self.seconds_spinbox.setValue(1)
        self.seconds_spinbox.setStyleSheet("font-size: 12pt; min-height: 30px;")
        self.seconds_spinbox.valueChanged.connect(self.update_timer_interval)
        self.seconds_spinbox.setMaximum(1000)
        self.seconds_label = QLabel("secs")
        self.seconds_label.setStyleSheet("font-size: 10pt")

        self.milliseconds_spinbox = QSpinBox()
        self.milliseconds_spinbox.setStyleSheet("font-size: 12pt; min-height: 30px;")
        self.milliseconds_spinbox.valueChanged.connect(self.update_timer_interval)
        self.milliseconds_spinbox.setMaximum(1000)
        self.milliseconds_label = QLabel("mil-sec")
        self.milliseconds_label.setStyleSheet("font-size: 10pt")

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        self.start_button.setStyleSheet("min-height: 60px; font-size: 12pt; min-width: 150px;")

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_timer)
        self.stop_button.setStyleSheet("min-height: 60px; font-size: 12pt; min-width: 150px;")
        self.stop_button.setEnabled(False)

        self.use_mouse_checkbox = QCheckBox('Mouse')
        self.use_mouse_checkbox.setStyleSheet('font-size: 10pt; min-height: 30px;')
        self.use_mouse_checkbox.click()

        self.use_keyboard_checkbox = QCheckBox('Keyboard')
        self.use_keyboard_checkbox.setStyleSheet('font-size: 10pt; min-height: 30px;')

        self.input_method_layout.addWidget(self.use_mouse_checkbox)
        self.input_method_layout.addWidget(self.use_keyboard_checkbox)

        self.mouse_button_type_combobox = QComboBox()
        self.mouse_button_type_combobox.setStyleSheet("min-height: 25px;")
        self.mouse_button_type_combobox.addItems(["Left", "Right", "Middle"])
        self.mouse_button_type_combobox.currentTextChanged.connect(self.on_mouse_button_changed)
        self.mouse_button_type_label = QLabel("Mouse click type")
        self.mouse_button_type_label.setStyleSheet("font-size: 10pt")

        self.keyboard_key_combobox = QComboBox()
        self.keyboard_key_combobox.setStyleSheet("min-height: 25px;")
        self.keyboard_key_combobox.addItems(self.available_keys)
        self.keyboard_key_combobox.setCurrentText(self.current_click_key)
        self.keyboard_key_combobox.currentTextChanged.connect(self.on_keyboard_key_changed)
        self.keyboard_key_label = QLabel("Keyboard click type")
        self.keyboard_key_label.setStyleSheet("font-size: 10pt")

        self.hotkey_combobox = QComboBox()
        self.hotkey_combobox.setStyleSheet("min-height: 25px;")
        self.hotkey_combobox.addItems(self.available_keys)
        self.hotkey_combobox.setCurrentText(self.current_hotkey)
        self.hotkey_combobox.currentTextChanged.connect(self.on_hotkey_changed)
        self.hotkey_label = QLabel("Set hotkey")
        self.hotkey_label.setStyleSheet("font-size: 10pt")

        # Добавление элементов в соответствующие layouts
        self.time_input_layout.addWidget(self.hours_spinbox)
        self.time_input_layout.addWidget(self.minutes_spinbox)
        self.time_input_layout.addWidget(self.seconds_spinbox)
        self.time_input_layout.addWidget(self.milliseconds_spinbox)

        self.time_labels_layout.addWidget(self.hours_label)
        self.time_labels_layout.addWidget(self.minutes_label)
        self.time_labels_layout.addWidget(self.seconds_label)
        self.time_labels_layout.addWidget(self.milliseconds_label)

        self.control_buttons_layout.addWidget(self.start_button)
        self.control_buttons_layout.addWidget(self.stop_button)

        settings_vertical_layout = QVBoxLayout()
        settings_vertical_layout.setSpacing(2)
        settings_vertical_layout.setContentsMargins(0, 0, 0, 0)
        settings_vertical_layout.addWidget(self.mouse_button_type_label)
        settings_vertical_layout.addWidget(self.mouse_button_type_combobox)
        settings_vertical_layout.addWidget(self.keyboard_key_label)
        settings_vertical_layout.addWidget(self.keyboard_key_combobox)
        settings_vertical_layout.addWidget(self.hotkey_label)
        settings_vertical_layout.addWidget(self.hotkey_combobox)

        self.main_layout.addLayout(self.time_input_layout)
        self.main_layout.addLayout(self.time_labels_layout)
        self.main_layout.addLayout(self.control_buttons_layout)
        self.main_layout.addLayout(settings_vertical_layout)
        self.main_layout.addLayout(self.input_method_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.timer_status_label)

        self.macro_button = QPushButton("Написать макрос")
        self.macro_button.setStyleSheet("min-height: 30px; font-size: 10pt;")
        self.macro_button.clicked.connect(self.open_macro_editor)
        self.main_layout.addWidget(self.macro_button)

    def stop_timer(self):
        if self.active and self.current_timer_interval_ms > 0:
            self.stop_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.timer.stop()
            self.timer_status_label.setText("Off")

    def start_timer(self):
        if self.active and self.current_timer_interval_ms > 0:
            self.stop_button.setEnabled(True)
            self.start_button.setEnabled(False)
            self.timer.start()
            self.timer_status_label.setText("On")

    def perform_click(self):
        if self.active and self.current_timer_interval_ms > 0:
            if self.use_mouse_checkbox.isChecked():
                mouse.click(self.current_mouse_button.lower())
            if self.use_keyboard_checkbox.isChecked():
                keyboard.press(self.current_click_key)
                keyboard.release(self.current_click_key)

    def toggle_timer_state(self):
        if self.active and self.current_timer_interval_ms > 0:
            if self.timer.isActive():
                self.stop_timer()
            else:
                self.start_timer()
        else:
            self.stop_timer()

    def update_timer_interval(self):
        self.current_timer_interval_ms = (
                self.hours_spinbox.value() * 3600000 +
                self.minutes_spinbox.value() * 60000 +
                self.seconds_spinbox.value() * 1000 +
                self.milliseconds_spinbox.value()
        )

        if self.current_timer_interval_ms > 0:
            self.timer.setInterval(self.current_timer_interval_ms)

    def on_hotkey_changed(self, new_key):
        self.current_hotkey = new_key
        # Изменяем хоткей через глобальный менеджер
        self.global_hotkey_manager.change_clicker_hotkey(new_key)

    def on_keyboard_key_changed(self, new_key):
        self.current_click_key = new_key

    def on_mouse_button_changed(self, new_button):
        self.current_mouse_button = new_button

    def open_macro_editor(self):
        # Создаем окно макросов только при первом открытии
        if self.macro_window is None:
            self.macro_window = MacroEditorWindow(self, self.global_hotkey_manager)
        self.hide()
        self.active = False
        self.macro_window.show()
        self.macro_window.active = True

    def closeEvent(self, event):
        # При закрытии основного окна, очищаем все глобальные хоткеи через менеджер
        self.global_hotkey_manager.clear_hotkeys()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('../tea.ico')))
    global_hotkey_manager = GlobalHotkeyManager()
    window = AutoClickerWindow(global_hotkey_manager)
    window.show()
    window.active = True
    sys.exit(app.exec_())
