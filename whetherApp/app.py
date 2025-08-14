import sys
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QGridLayout, QGroupBox, QScrollArea, QRadioButton, QHBoxLayout
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer

import json
from datetime import date, datetime
import os
import qdarkstyle

# --- API Configuration ---
API_KEY = "a13985651d74ca9d9dac2ed8e66b5aa7"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
IP_API_URL = "http://ip-api.com/json"

# --- Main Application Class ---
class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Weather App")
        self.setGeometry(100, 100, 900, 650)
        self.units = "metric" # Default to Celsius

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        
        self.create_widgets()

    def create_widgets(self):
        title_label = QLabel("Advanced Weather App")
        title_label.setFont(QFont('Arial', 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title_label)

        controls_layout = QHBoxLayout()

        # --- Left Control Panel ---
        control_panel = QWidget()
        control_panel.setFixedWidth(350)
        control_panel_layout = QVBoxLayout(control_panel)

        # Unit Selection
        unit_group = QGroupBox("Units")
        unit_layout = QVBoxLayout()
        unit_group.setLayout(unit_layout)
        self.celsius_radio = QRadioButton("Celsius (°C)")
        self.celsius_radio.setChecked(True)
        self.fahrenheit_radio = QRadioButton("Fahrenheit (°F)")
        self.celsius_radio.toggled.connect(self.on_unit_change)
        unit_layout.addWidget(self.celsius_radio)
        unit_layout.addWidget(self.fahrenheit_radio)
        control_panel_layout.addWidget(unit_group)

        # Weather Lookup Group
        lookup_group = QGroupBox("Weather Lookup")
        lookup_layout = QGridLayout()
        lookup_group.setLayout(lookup_layout)
        
        city_label = QLabel("Enter City:")
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("e.g., New York, London")
        
        fetch_button = QPushButton("Get Weather")
        fetch_button.clicked.connect(self.get_weather)

        # --- New: Current Location Button ---
        location_button = QPushButton("Current Location")
        location_button.clicked.connect(self.get_initial_location)

        lookup_layout.addWidget(city_label, 0, 0)
        lookup_layout.addWidget(self.city_input, 0, 1)
        lookup_layout.addWidget(fetch_button, 1, 0, 1, 2)
        lookup_layout.addWidget(location_button, 2, 0, 1, 2)
        control_panel_layout.addWidget(lookup_group)

        # Current Weather Display
        self.current_weather_group = QGroupBox("Current Weather")
        self.current_weather_layout = QVBoxLayout(self.current_weather_group)
        self.current_weather_group.setLayout(self.current_weather_layout)
        self.current_weather_group.setMinimumHeight(200)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.current_weather_layout.addWidget(self.icon_label)

        self.info_label = QLabel("Enter a city or click 'Current Location' to begin.")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(QFont('Arial', 14))
        self.current_weather_layout.addWidget(self.info_label)
        
        control_panel_layout.addWidget(self.current_weather_group)
        
        controls_layout.addWidget(control_panel)

        # --- Right Forecast Panel ---
        self.forecast_group = QGroupBox("5-Day Forecast")
        self.forecast_layout = QHBoxLayout()
        self.forecast_group.setLayout(self.forecast_layout)
        
        self.forecast_scroll_area = QScrollArea()
        self.forecast_scroll_area.setWidgetResizable(True)
        self.forecast_scroll_area.setWidget(self.forecast_group)
        
        controls_layout.addWidget(self.forecast_scroll_area)
        self.main_layout.addLayout(controls_layout)

    def get_initial_location(self):
        try:
            self.info_label.setText("Detecting your location...")
            QApplication.processEvents()
            response = requests.get(IP_API_URL)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city')
                self.city_input.setText(city)
                self.get_weather()
            else:
                self.info_label.setText("Failed to detect location. Please enter a city.")
        except requests.exceptions.RequestException:
            self.info_label.setText("Failed to detect location. Please enter a city.")
            
    def on_unit_change(self):
        self.units = "metric" if self.celsius_radio.isChecked() else "imperial"
        self.get_weather()

    def get_weather(self):
        city = self.city_input.text().strip()
        if not city:
            QMessageBox.warning(self, "Input Error", "Please enter a city name.")
            return

        self.info_label.setText("Fetching weather...")
        self.icon_label.clear()
        
        QApplication.processEvents()
        
        weather_data = self.get_weather_data(city)
        forecast_data = self.get_forecast_data(city)
        
        if weather_data and forecast_data:
            self.display_weather(weather_data, city)
            self.display_forecast(forecast_data)
        else:
            self.info_label.setText("Error fetching weather data.")

    def get_weather_data(self, city):
        try:
            params = {"q": city, "appid": API_KEY, "units": self.units}
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Network Error", f"An error occurred: {e}")
            return None

    def get_forecast_data(self, city):
        try:
            params = {"q": city, "appid": API_KEY, "units": self.units}
            response = requests.get(FORECAST_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Network Error", f"An error occurred: {e}")
            return None

    def display_weather(self, data, city):
        weather_list = data.get("weather", [{}])[0]
        weather_desc = weather_list.get("description", "N/A")
        temperature = data.get("main", {}).get("temp", "N/A")
        
        icon_code = weather_list.get("icon", "N/A")
        if icon_code != "N/A":
            icon_path = f"icons/{icon_code}.png"
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            else:
                self.icon_label.setText("Icon not found")
        else:
            self.icon_label.clear()

        unit_symbol = "°C" if self.units == "metric" else "°F"
        info_text = (
            f"Current weather in {city.title()}:\n"
            f"Temperature: {temperature:.1f}{unit_symbol}\n"
            f"Condition: {weather_desc.title()}"
        )
        self.info_label.setText(info_text)

    def display_forecast(self, data):
        for i in reversed(range(self.forecast_layout.count())):
            self.forecast_layout.itemAt(i).widget().setParent(None)

        forecast_list = data.get("list", [])
        if not forecast_list:
            return

        unique_dates = []
        for forecast in forecast_list:
            forecast_date = datetime.fromtimestamp(forecast.get('dt')).date()
            if forecast_date not in unique_dates:
                unique_dates.append(forecast_date)

        for forecast_date in unique_dates:
            for forecast in forecast_list:
                if datetime.fromtimestamp(forecast.get('dt')).date() == forecast_date:
                    day_widget = QWidget()
                    day_layout = QVBoxLayout(day_widget)
                    
                    day_label = QLabel(forecast_date.strftime('%a'))
                    day_label.setAlignment(Qt.AlignCenter)
                    day_layout.addWidget(day_label)

                    icon_code = forecast.get("weather", [{}])[0].get("icon", "N/A")
                    if icon_code != "N/A":
                        icon_path = f"icons/{icon_code}.png"
                        pixmap = QPixmap(icon_path)
                        if not pixmap.isNull():
                            icon_label = QLabel()
                            icon_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))
                            icon_label.setAlignment(Qt.AlignCenter)
                            day_layout.addWidget(icon_label)
                        else:
                            icon_label = QLabel("No Icon")
                            icon_label.setAlignment(Qt.AlignCenter)
                            day_layout.addWidget(icon_label)
                    
                    unit_symbol = "°C" if self.units == "metric" else "°F"
                    temp_label = QLabel(f"Temp: {forecast['main']['temp']:.1f}{unit_symbol}")
                    temp_label.setAlignment(Qt.AlignCenter)
                    day_layout.addWidget(temp_label)
                    
                    self.forecast_layout.addWidget(day_widget)
                    break

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = WeatherApp()
    window.show()
    sys.exit(app.exec_())