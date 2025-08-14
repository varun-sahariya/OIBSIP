import sys
import random
import string
import pyperclip # <-- New import
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QVBoxLayout, QCheckBox, QGroupBox
)
from PyQt5.QtGui import QFont, QClipboard
from PyQt5.QtCore import Qt

import qdarkstyle

class PasswordGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Password Generator")
        self.setGeometry(100, 100, 450, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.create_widgets(main_layout)
        
    def create_widgets(self, main_layout):
        title_label = QLabel("Password Generator")
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        options_group = QGroupBox("Options")
        options_layout = QGridLayout()
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        length_label = QLabel("Password Length:")
        options_layout.addWidget(length_label, 0, 0)
        self.length_entry = QLineEdit("12")
        self.length_entry.setFixedWidth(50)
        options_layout.addWidget(self.length_entry, 0, 1)

        self.uppercase_check = QCheckBox("Include Uppercase Letters (A-Z)")
        self.uppercase_check.setChecked(True)
        options_layout.addWidget(self.uppercase_check, 1, 0, 1, 2)
        
        self.numbers_check = QCheckBox("Include Numbers (0-9)")
        self.numbers_check.setChecked(True)
        options_layout.addWidget(self.numbers_check, 2, 0, 1, 2)
        
        self.symbols_check = QCheckBox("Include Special Characters (!@#$%)")
        options_layout.addWidget(self.symbols_check, 3, 0, 1, 2)

        self.password_output = QLineEdit()
        self.password_output.setReadOnly(True)
        self.password_output.setFont(QFont('Courier New', 12))
        main_layout.addWidget(self.password_output)
        
        generate_button = QPushButton("Generate Password")
        generate_button.clicked.connect(self.generate_password)
        main_layout.addWidget(generate_button)
        
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_password_to_clipboard) # <-- New connection
        main_layout.addWidget(self.copy_button)

    def generate_password(self):
        try:
            length = int(self.length_entry.text())
            if length <= 0:
                QMessageBox.warning(self, "Error", "Password length must be a positive number.")
                return

            characters = ""
            if self.uppercase_check.isChecked():
                characters += string.ascii_uppercase
            if self.numbers_check.isChecked():
                characters += string.digits
            if self.symbols_check.isChecked():
                characters += string.punctuation
            
            characters += string.ascii_lowercase

            if not characters:
                QMessageBox.warning(self, "Error", "Please select at least one character type.")
                return
            
            password = ''.join(random.choice(characters) for _ in range(length))
            self.password_output.setText(password)

        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid number for password length.")

    def copy_password_to_clipboard(self):
        password = self.password_output.text()
        if password:
            pyperclip.copy(password)
            QMessageBox.information(self, "Success", "Password copied to clipboard!")
        else:
            QMessageBox.warning(self, "Error", "No password to copy.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = PasswordGeneratorApp()
    window.show()
    sys.exit(app.exec_())