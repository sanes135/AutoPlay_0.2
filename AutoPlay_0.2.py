import sys
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence, QPalette, QColor
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QShortcut, QSpinBox, QLabel, QComboBox, QAction, QMainWindow, QShortcut
import keyboard
import mouse


class KeyBoardManager(QObject):
    Signal = pyqtSignal()

    def start(self):
        keyboard.add_hotkey("F6", self.Signal.emit, suppress=True)

    def change_key(self, key):
        keyboard.clear_all_hotkeys()
        keyboard.add_hotkey(key, self.Signal.emit, suppress=True)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        width = 420
        height = 400
        self.setWindowTitle("AutoPlay 0.1")
        self.setGeometry(300, 300, width, height)
        self.setFixedSize(width, height)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.list_keys = ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
                     "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
                     "ALT", "CTRL", "TAB", "SHIFT", "SPACE",
                     "1", "2", "3", "4", "5", "6", "7", "8", "9", "0")

        self.clicked_key = 'SPACE'

        self.time = 1000

        self.timer = QTimer()
        self.timer.setInterval(self.time)
        self.timer.timeout.connect(self.click)

        self.type_timer = QLabel(self)
        self.type_timer.setText("Off")
        self.type_timer.setGeometry(20, 280, 40, 20)

        self.manager = KeyBoardManager(self)
        self.manager.Signal.connect(self.toggle_timer)
        self.manager.start()

        self.hours = QSpinBox(self)
        self.hours.setGeometry(20, 20, 60, 30)
        self.hours.setStyleSheet("font-size: 12pt")
        self.hours.valueChanged.connect(self.set_cooldown)
        self.hours.setMaximum(24)

        self.hours_text = QLabel(self)
        self.hours_text.setText("hours")
        self.hours_text.setGeometry(30, 50, 80, 20)
        self.hours_text.setStyleSheet("font-size: 10pt")

        self.mins = QSpinBox(self)
        self.mins.setGeometry(120, 20, 60, 30)
        self.mins.setStyleSheet("font-size: 12pt")
        self.mins.valueChanged.connect(self.set_cooldown)
        self.mins.setMaximum(6000)

        self.mins_text = QLabel(self)
        self.mins_text.setText("mins")
        self.mins_text.setGeometry(132, 50, 80, 20)
        self.mins_text.setStyleSheet("font-size: 10pt")

        self.secs = QSpinBox(self)
        self.secs.setValue(1)
        self.secs.setGeometry(230, 20, 60, 30)
        self.secs.setStyleSheet("font-size: 12pt")
        self.secs.valueChanged.connect(self.set_cooldown)
        self.secs.setMaximum(100000)

        self.secs_text = QLabel(self)
        self.secs_text.setText("secs")
        self.secs_text.setGeometry(243, 50, 80, 20)
        self.secs_text.setStyleSheet("font-size: 10pt")

        self.mil_sec = QSpinBox(self)
        self.mil_sec.setGeometry(340, 20, 60, 30)
        self.mil_sec.setStyleSheet("font-size: 12pt")
        self.mil_sec.valueChanged.connect(self.set_cooldown)
        self.mil_sec.setMaximum(100000)

        self.mil_sec_text = QLabel(self)
        self.mil_sec_text.setText("mil-sec")
        self.mil_sec_text.setGeometry(345, 50, 80, 20)
        self.mil_sec_text.setStyleSheet("font-size: 10pt")

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_timer)
        self.start_button.setGeometry(20, 80, 190, 50)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_timer)
        self.stop_button.setGeometry(210, 80, 190, 50)
        self.stop_button.setEnabled(False)

        self.index_box = QComboBox(self)
        self.index_box.addItem("Mouse")
        self.index_box.addItem("Keyboard")
        self.index_box.currentIndexChanged.connect(self.index_changed)
        self.index_box.setGeometry(20, 140, 190, 30)
        self.mouse_keyboard = "Mouse"

        self.choosing_click_method_text = QLabel(self)
        self.choosing_click_method_text.setText("Set click method")
        self.choosing_click_method_text.setGeometry(50, 175, 165, 20)
        self.choosing_click_method_text.setStyleSheet("font-size: 10pt")

        self.type_mouse_clicked = QComboBox(self)
        self.type_mouse_clicked.addItem("Left")
        self.type_mouse_clicked.addItem("Right")
        self.type_mouse_clicked.addItem("Middle")
        self.type_mouse_clicked.currentIndexChanged.connect(self.mouse_changed)
        self.type_mouse_clicked.setGeometry(210, 140, 190, 30)
        self.type_mouse = "Left"

        self.type_mouse_clicked_text = QLabel(self)
        self.type_mouse_clicked_text.setText("Mouse click type")
        self.type_mouse_clicked_text.setGeometry(245, 175, 165, 20)
        self.type_mouse_clicked_text.setStyleSheet("font-size: 10pt")

        self.keys_box = QComboBox(self)
        self.keyboard_clicked_key = QComboBox(self)
        for i in self.list_keys:
            self.keyboard_clicked_key.addItem(i)
            self.keys_box.addItem(i)
        self.keys_box.setCurrentText("F6")
        self.keys_box.currentIndexChanged.connect(self.set_hotkey)
        self.keys_box.setGeometry(210, 200, 190, 30)

        self.keyboard_clicked_key.setCurrentText(self.clicked_key)
        self.keyboard_clicked_key.currentIndexChanged.connect(self.set_clicked_key)
        self.keyboard_clicked_key.setGeometry(20, 200, 190, 30)

        self.choosing_button_text = QLabel(self)
        self.choosing_button_text.setText("Keyboard click type")
        self.choosing_button_text.setGeometry(40, 230, 150, 20)
        self.choosing_button_text.setStyleSheet("font-size: 10pt")

        self.choosing_kotkey_text = QLabel(self)
        self.choosing_kotkey_text.setText("Set hotkey")
        self.choosing_kotkey_text.setGeometry(265, 230, 150, 20)
        self.choosing_kotkey_text.setStyleSheet("font-size: 10pt")

    def stop_timer(self):
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.timer.stop()
        self.type_timer.setText("Off")

    def start_timer(self):
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.timer.start()
        self.type_timer.setText("On")

    def click(self):
        if self.mouse_keyboard == "Mouse":
            mouse.click(self.type_mouse.lower())
        elif self.mouse_keyboard == "Keyboard":
            keyboard.press(self.clicked_key)
            keyboard.release(self.clicked_key)
        else:
            print('Index = Nothing')

    def toggle_timer(self):
        if self.timer.isActive():
            self.stop_timer()
        else:
            self.start_timer()

    def set_cooldown(self):
        self.time = (self.hours.value() * 3600000) + (self.mins.value() * 60000) + (self.secs.value() * 1000) + self.mil_sec.value()
        self.timer.setInterval(self.time)

    def set_hotkey(self):
        self.manager.change_key(self.keys_box.currentText())

    def set_clicked_key(self):
        self.clicked_key = self.keyboard_clicked_key.currentText()

    def index_changed(self):
        self.mouse_keyboard = self.index_box.currentText()

    def mouse_changed(self):
        self.type_mouse = self.type_mouse_clicked.currentText()




if __name__ == "__main__":
    print('There are two bugs in my program.\n'
          '1 - the text on different monitors is shifting.\n'
          '2 - sometimes, due to problems with PyQt5, the error "Process finished with exit code -1073740791 (0xC0000409)" is displayed.\n'
          'I will try to fix these bugs.')
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
