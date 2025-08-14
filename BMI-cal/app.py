import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QRadioButton, QGroupBox, QHBoxLayout
from PyQt5.QtGui import QFont, QDoubleValidator
from PyQt5.QtCore import Qt

import json
from datetime import date
import os
import qdarkstyle

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates

# --- Data Handling Functions ---
DATABASE_FILE = "bmi_data.json"

def load_data():
    """Loads user data from the JSON file."""
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_data(name, bmi):
    """Saves a new BMI entry for a user."""
    data = load_data()
    today = date.today().isoformat()
    
    if name not in data:
        data[name] = []
    
    data[name].append({"date": today, "bmi": bmi})
    
    with open(DATABASE_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# --- Main Application Class ---
class BMI_Calculator_App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced BMI Calculator")
        self.setGeometry(100, 100, 900, 600)

        self.data = load_data()
        self.units = "metric"

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        self.create_control_panel(main_layout)
        self.create_graph_panel(main_layout)
        
        self.style_widgets()

    def create_control_panel(self, main_layout):
        control_panel = QWidget()
        self.control_layout = QGridLayout()
        control_panel.setLayout(self.control_layout)

        # --- User Management (Text Field and Buttons) ---
        user_group = QGroupBox("User Profile")
        user_layout = QVBoxLayout()
        user_group.setLayout(user_layout)

        self.user_name_entry = QLineEdit()
        self.user_name_entry.setPlaceholderText("Enter or create a user name")
        
        load_profile_button = QPushButton("Load Profile")
        load_profile_button.clicked.connect(self.load_profile)
        
        delete_profile_button = QPushButton("Delete Profile")
        delete_profile_button.clicked.connect(self.delete_profile)
        
        user_layout.addWidget(self.user_name_entry)
        user_layout.addWidget(load_profile_button)
        user_layout.addWidget(delete_profile_button)

        # --- Unit Selection ---
        unit_group = QGroupBox("Units")
        unit_layout = QVBoxLayout()
        unit_group.setLayout(unit_layout)

        self.metric_radio = QRadioButton("Metric (kg, m)")
        self.metric_radio.setChecked(True)
        self.imperial_radio = QRadioButton("Imperial (lbs, in)")
        self.metric_radio.toggled.connect(self.on_unit_change)
        
        unit_layout.addWidget(self.metric_radio)
        unit_layout.addWidget(self.imperial_radio)

        # --- BMI Input and Calculation ---
        input_group = QGroupBox("BMI Calculator")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)

        validator = QDoubleValidator(0.0, 1000.0, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        
        self.weight_label = QLabel("Weight (kg):")
        self.weight_entry = QLineEdit()
        self.weight_entry.setValidator(validator)

        self.height_label = QLabel("Height (m):")
        self.height_entry = QLineEdit()
        self.height_entry.setValidator(validator)

        self.calculate_button = QPushButton("Calculate & Save BMI")
        self.calculate_button.clicked.connect(self.calculate_bmi)
        
        self.result_label = QLabel("Your BMI will appear here.")
        self.category_label = QLabel("Category: ")
        self.result_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.category_label.setFont(QFont('Arial', 12))

        input_layout.addWidget(self.weight_label, 0, 0)
        input_layout.addWidget(self.weight_entry, 0, 1)
        input_layout.addWidget(self.height_label, 1, 0)
        input_layout.addWidget(self.height_entry, 1, 1)
        input_layout.addWidget(self.calculate_button, 2, 0, 1, 2)
        input_layout.addWidget(self.result_label, 3, 0, 1, 2)
        input_layout.addWidget(self.category_label, 4, 0, 1, 2)

        self.control_layout.addWidget(user_group, 0, 0)
        self.control_layout.addWidget(unit_group, 1, 0)
        self.control_layout.addWidget(input_group, 2, 0)
        
        main_layout.addWidget(control_panel)

    def create_graph_panel(self, main_layout):
        graph_panel = QWidget()
        graph_layout = QVBoxLayout()
        graph_panel.setLayout(graph_layout)

        self.figure = plt.Figure(facecolor='#262626')
        self.canvas = FigureCanvas(self.figure)
        graph_layout.addWidget(self.canvas)
        main_layout.addWidget(graph_panel)
    
    def load_profile(self):
        name = self.user_name_entry.text().strip().title()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter a user name.")
            return

        if name not in self.data:
            QMessageBox.information(self, "New User", f"Profile for '{name}' does not exist. A new one will be created upon calculation.")
            self.show_history()
            return
        
        QMessageBox.information(self, "Success", f"Profile for '{name}' loaded.")
        self.show_history()

    def delete_profile(self):
        name = self.user_name_entry.text().strip().title()
        if not name or name not in self.data:
            QMessageBox.warning(self, "Error", "Please enter a valid user name to delete.")
            return

        if QMessageBox.question(self, "Delete Profile", f"Are you sure you want to delete profile for '{name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            del self.data[name]
            with open(DATABASE_FILE, 'w') as file:
                json.dump(self.data, file, indent=4)
            QMessageBox.information(self, "Success", f"Profile for '{name}' deleted.")
            self.show_history()
            
    def on_unit_change(self):
        if self.metric_radio.isChecked():
            self.units = "metric"
            self.weight_label.setText("Weight (kg):")
            self.height_label.setText("Height (m):")
            self.weight_entry.setPlaceholderText("Enter your weight in kilograms")
            self.height_entry.setPlaceholderText("Enter your height in meters (e.g., 1.75)")
        else:
            self.units = "imperial"
            self.weight_label.setText("Weight (lbs):")
            self.height_label.setText("Height (in):")
            self.weight_entry.setPlaceholderText("Enter your weight in pounds")
            self.height_entry.setPlaceholderText("Enter your height in inches (e.g., 68)")

    def calculate_bmi(self):
        current_user = self.user_name_entry.text().strip().title()
        if not current_user:
            QMessageBox.warning(self, "Input Error", "Please enter a user name first.")
            return

        try:
            if self.units == "metric":
                weight = float(self.weight_entry.text())
                height = float(self.height_entry.text())
                if height == 0:
                    QMessageBox.warning(self, "Input Error", "Height cannot be zero.")
                    return
                bmi = weight / (height ** 2)
            else:
                weight = float(self.weight_entry.text())
                height = float(self.height_entry.text())
                if height == 0:
                    QMessageBox.warning(self, "Input Error", "Height cannot be zero.")
                    return
                bmi = (weight / (height ** 2)) * 703
            
            self.result_label.setText(f"Hello {current_user}, your BMI is: {bmi:.2f}")

            if bmi < 18.5:
                category = "Underweight"
                self.category_label.setStyleSheet("color: #FFC107;")
            elif 18.5 <= bmi < 24.9:
                category = "Normal weight"
                self.category_label.setStyleSheet("color: #4CAF50;")
            elif 25 <= bmi < 29.9:
                category = "Overweight"
                self.category_label.setStyleSheet("color: #FF5722;")
            else:
                category = "Obesity"
                self.category_label.setStyleSheet("color: #F44336;")
            
            self.category_label.setText(f"Category: {category}")
            save_data(current_user, bmi)
            self.show_history()

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers.")

    def show_history(self):
        name = self.user_name_entry.text().strip().title()
        if not name:
            self.figure.clear()
            self.canvas.draw()
            return

        data = load_data()
        if name not in data or len(data[name]) < 1:
            self.figure.clear()
            ax = self.figure.add_subplot(111, facecolor='#262626')
            ax.text(0.5, 0.5, f"No history to plot for {name}. Enter data to begin.", ha='center', va='center', color='white', transform=ax.transAxes)
            self.canvas.draw()
            return

        dates = [date.fromisoformat(entry['date']) for entry in data[name]]
        bmis = [entry['bmi'] for entry in data[name]]

        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#262626')

        ax.axhspan(0, 18.5, facecolor='yellow', alpha=0.1, label='Underweight')
        ax.axhspan(18.5, 24.9, facecolor='green', alpha=0.1, label='Normal Weight')
        ax.axhspan(24.9, 29.9, facecolor='orange', alpha=0.1, label='Overweight')
        ax.axhspan(29.9, 100, facecolor='red', alpha=0.1, label='Obesity')

        ax.axhline(y=18.5, color='gray', linestyle='--', linewidth=1)
        ax.axhline(y=24.9, color='gray', linestyle='--', linewidth=1)
        ax.axhline(y=29.9, color='gray', linestyle='--', linewidth=1)
        
        ax.plot(dates, bmis, marker='o', color='white', linestyle='-', linewidth=2, label='Your BMI')
        
        ax.set_title(f"BMI History for {name}", color='white')
        ax.set_xlabel("Date", color='white')
        ax.set_ylabel("BMI", color='white')
        ax.tick_params(colors='white')
        ax.set_ylim(bottom=15, top=40)
        ax.legend()
        ax.grid(True, which='both', linestyle=':', linewidth=0.5)

        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.figure.autofmt_xdate(rotation=45, ha='right')
        
        self.canvas.draw()

    def style_widgets(self):
        self.result_label.setStyleSheet("color: #4CAF50;")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = BMI_Calculator_App()
    window.show()
    sys.exit(app.exec_())