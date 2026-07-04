import sys
import random

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QSlider, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QCheckBox, QTextBrowser, QProgressBar, QScrollArea,
    QGroupBox, QGridLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QPen

from backend.engine import SimulationEngine, Plant, Herbivore, Fox, WaterSource


class EcosystemCanvas(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.show_vision = True
        self.show_bars = True
        self.show_legend = True
        self.show_grid = False
        self.setFixedSize(1000, 700)

    def season_colors(self, season):
        if season == "spring":
            return QColor("#DFF5D8"), QColor("#A5D6A7")
        elif season == "summer":
            return QColor("#E8F5E9"), QColor("#81C784")
        elif season == "autumn":
            return QColor("#FFF3E0"), QColor("#FFB74D")
        elif season == "winter":
            return QColor("#E3F2FD"), QColor("#90CAF9")
        return QColor("#E8F5E9"), QColor("#81C784")

    def paintEvent(self, event):
        painter = QPainter(self)

        state = self.engine.get_state()
        season = state.get("season", "summer")
        bg_color, grid_color = self.season_colors(season)

        painter.fillRect(self.rect(), bg_color)

        if self.show_grid:
            self.draw_grid(painter, grid_color)

        if season == "winter":
            self.draw_winter_effect(painter)
        elif season == "autumn":
            self.draw_autumn_effect(painter)

        font = painter.font()
        font.setPointSize(15)
        painter.setFont(font)

        for entity in state["entities"]:
            x = int(entity["x"])
            y = int(entity["y"])

            if entity["type"] == "water":
                radius = int(entity.get("radius", 40))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(66, 165, 245, 95))
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
                painter.setPen(QColor("#0D47A1"))
                painter.drawText(x - 9, y + 6, "💧")

            elif entity["type"] == "plant":
                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🌿")

            elif entity["type"] == "berry_bush":
                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🫐")

            elif entity["type"] == "herbivore":
                energy = entity.get("energy", 0)
                thirst = entity.get("thirst", 0)
                vision = int(entity.get("vision", 0))
                nearest_fox_dist = entity.get("nearest_fox_dist", 9999)

                if self.show_vision:
                    painter.setPen(QPen(QColor(90, 90, 90, 32), 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(x - vision, y - vision, vision * 2, vision * 2)

                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🐰")

                if self.show_bars:
                    self.draw_bar(painter, x, y + 9, energy, 300, "energy")
                    self.draw_bar(painter, x, y + 15, thirst, 300, "thirst")

                    if nearest_fox_dist < 80:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(QColor("#C62828"))
                        painter.drawRect(x, y + 21, 26, 3)

            elif entity["type"] == "fox":
                energy = entity.get("energy", 0)
                hunger = entity.get("hunger", 0)
                thirst = entity.get("thirst", 0)
                vision = int(entity.get("vision", 150))

                if self.show_vision:
                    painter.setPen(QPen(QColor(230, 100, 20, 34), 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(x - vision, y - vision, vision * 2, vision * 2)

                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🦊")

                if self.show_bars:
                    self.draw_bar(painter, x, y + 9, energy, 300, "energy")
                    self.draw_bar(painter, x, y + 15, hunger, 300, "hunger")
                    self.draw_bar(painter, x, y + 21, thirst, 300, "thirst")

        self.draw_season_badge(painter, season)

        if self.show_legend:
            self.draw_legend(painter)

    def draw_grid(self, painter, color):
        painter.setPen(QPen(color, 1))
        for x in range(0, self.width(), 50):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 50):
            painter.drawLine(0, y, self.width(), y)

    def draw_winter_effect(self, painter):
        painter.setPen(QColor(255, 255, 255, 170))
        for i in range(45):
            x = (i * 73) % self.width()
            y = (i * 41) % self.height()
            painter.drawText(x, y, "•")

    def draw_autumn_effect(self, painter):
        painter.setPen(QColor("#A66A2C"))
        for i in range(22):
            x = (i * 83) % self.width()
            y = (i * 47) % self.height()
            painter.drawText(x, y, "🍂")

    def draw_season_badge(self, painter, season):
        painter.setPen(Qt.NoPen)

        if season == "spring":
            painter.setBrush(QColor(129, 199, 132, 215))
        elif season == "summer":
            painter.setBrush(QColor(255, 213, 79, 220))
        elif season == "autumn":
            painter.setBrush(QColor(255, 152, 0, 210))
        else:
            painter.setBrush(QColor(100, 181, 246, 220))

        painter.drawRoundedRect(815, 18, 160, 36, 12, 12)
        painter.setPen(QColor("#263238"))
        painter.drawText(842, 42, f"Season: {season}")

    def draw_bar(self, painter, x, y, value, max_value, bar_type):
        width = 26
        height = 4

        percent = value / max_value
        if percent < 0:
            percent = 0
        if percent > 1:
            percent = 1

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#D6D6D6"))
        painter.drawRect(x, y, width, height)

        if bar_type == "energy":
            if percent > 0.6:
                painter.setBrush(QColor("#2E7D32"))
            elif percent > 0.3:
                painter.setBrush(QColor("#FBC02D"))
            else:
                painter.setBrush(QColor("#C62828"))

        elif bar_type == "thirst":
            if percent > 0.7:
                painter.setBrush(QColor("#B71C1C"))
            elif percent > 0.4:
                painter.setBrush(QColor("#039BE5"))
            else:
                painter.setBrush(QColor("#81D4FA"))

        else:
            if percent > 0.7:
                painter.setBrush(QColor("#B71C1C"))
            elif percent > 0.4:
                painter.setBrush(QColor("#EF6C00"))
            else:
                painter.setBrush(QColor("#43A047"))

        painter.drawRect(x, y, int(width * percent), height)

    def draw_legend(self, painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawRoundedRect(12, 12, 195, 250, 12, 12)

        painter.setPen(QColor("#263238"))
        painter.drawText(25, 35, "Legend")
        painter.drawText(25, 65, "💧 Water")
        painter.drawText(25, 90, "🌿 Plant")
        painter.drawText(25, 115, "🫐 Berry bush")
        painter.drawText(25, 140, "🐰 Herbivore")
        painter.drawText(25, 165, "🦊 Fox")

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2E7D32"))
        painter.drawRect(25, 185, 26, 4)
        painter.setPen(QColor("#263238"))
        painter.drawText(62, 192, "Energy")

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#039BE5"))
        painter.drawRect(25, 210, 26, 4)
        painter.setPen(QColor("#263238"))
        painter.drawText(62, 217, "Thirst")

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#EF6C00"))
        painter.drawRect(25, 235, 26, 4)
        painter.setPen(QColor("#263238"))
        painter.drawText(62, 242, "Hunger / danger")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = SimulationEngine()

        self.max_plants = 0
        self.max_herbivores = 0
        self.min_herbivores = 0
        self.max_berry_bushes = 0
        self.max_foxes = 0
        self.last_fox_count = 0
        self.last_season = self.engine.season

        self.setWindowTitle("EcoBalance - Ecosystem Simulator")
        self.setGeometry(60, 50, 1480, 880)

        self.setStyleSheet("""
            QWidget {
                background-color: #F4F7F3;
                color: #263238;
                font-family: Arial;
                font-size: 13px;
            }

            QLabel {
                padding: 2px;
            }

            QPushButton {
                background-color: #2E7D32;
                color: white;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #388E3C;
            }

            QPushButton:pressed {
                background-color: #1B5E20;
            }

            QLineEdit {
                background-color: white;
                border: 1px solid #B0BEC5;
                border-radius: 6px;
                padding: 6px;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
                gridline-color: #ECEFF1;
            }

            QTextBrowser {
                background-color: white;
                border: 1px solid #CFD8DC;
                border-radius: 8px;
                padding: 6px;
            }

            QCheckBox {
                padding: 3px;
            }

            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 10px;
                margin-top: 12px;
                padding: 10px;
                font-weight: bold;
                color: #1B5E20;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }

            QScrollArea {
                border: none;
                background-color: #F4F7F3;
            }

            QProgressBar {
                border: 1px solid #B0BEC5;
                border-radius: 6px;
                background-color: white;
                text-align: center;
                height: 15px;
            }

            QProgressBar::chunk {
                background-color: #66BB6A;
                border-radius: 6px;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background: #CFD8DC;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #2E7D32;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)

        self.title_label = QLabel("🌍 EcoBalance")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1B5E20; padding: 8px;")

        self.subtitle_label = QLabel("Ecosystem Simulator")
        self.subtitle_label.setStyleSheet("font-size: 14px; color: #607D8B; padding-left: 8px;")

        self.tick_label = QLabel("Tick: 0")
        self.season_label = QLabel("Season: summer")
        self.season_progress = QProgressBar()
        self.season_progress.setMaximum(1000)
        self.season_progress.setValue(0)

        self.plants_label = QLabel("Plants: 0")
        self.berry_label = QLabel("Berry Bushes: 0")
        self.water_label = QLabel("Water Sources: 0")
        self.herbivores_label = QLabel("Herbivores: 0")
        self.foxes_label = QLabel("Foxes: 0")

        self.energy_label = QLabel("Average Herbivore Energy: 0")
        self.thirst_label = QLabel("Average Herbivore Thirst: 0")
        self.fox_energy_label = QLabel("Average Fox Energy: 0")
        self.fox_hunger_label = QLabel("Average Fox Hunger: 0")
        self.fox_thirst_label = QLabel("Average Fox Thirst: 0")

        self.speed_info_label = QLabel("Average Speed: 0")
        self.vision_info_label = QLabel("Average Vision: 0")
        self.age_info_label = QLabel("Average Herbivore Age: 0")
        self.fox_age_label = QLabel("Average Fox Age: 0")
        self.food_label = QLabel("Average Plant Food: 0")
        self.danger_label = QLabel("Herbivores in Danger: 0")

        self.status_label = QLabel("Status: Paused")
        self.status_label.setStyleSheet("""
            background-color: #E3F2FD;
            color: #0D47A1;
            border-radius: 8px;
            padding: 8px;
            font-weight: bold;
        """)

        self.max_plants_label = QLabel("Max Plants: 0")
        self.max_berry_label = QLabel("Max Berry Bushes: 0")
        self.max_herbivores_label = QLabel("Max Herbivores: 0")
        self.max_foxes_label = QLabel("Max Foxes: 0")
        self.min_herbivores_label = QLabel("Min Herbivores: 0")

        self.plants_input = QLineEdit("150")
        self.herbivores_input = QLineEdit("10")
        self.foxes_input = QLineEdit("4")
        self.water_input = QLineEdit("5")

        self.speed_label = QLabel("Simulation Speed: 50 ms")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(20)
        self.speed_slider.setMaximum(300)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.change_speed)

        self.vision_checkbox = QCheckBox("Show vision ranges")
        self.vision_checkbox.setChecked(True)
        self.vision_checkbox.toggled.connect(self.change_visual_settings)

        self.bars_checkbox = QCheckBox("Show energy/thirst/hunger bars")
        self.bars_checkbox.setChecked(True)
        self.bars_checkbox.toggled.connect(self.change_visual_settings)

        self.legend_checkbox = QCheckBox("Show legend")
        self.legend_checkbox.setChecked(True)
        self.legend_checkbox.toggled.connect(self.change_visual_settings)

        self.grid_checkbox = QCheckBox("Show grid")
        self.grid_checkbox.setChecked(False)
        self.grid_checkbox.toggled.connect(self.change_visual_settings)

        self.canvas = EcosystemCanvas(self.engine)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.apply_button = QPushButton("Apply Settings")
        self.save_button = QPushButton("Save CSV")

        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)
        self.apply_button.clicked.connect(self.apply_settings)
        self.save_button.clicked.connect(self.save_table_to_csv)

        self.table = QTableWidget()
        self.table.setColumnCount(16)
        self.table.setHorizontalHeaderLabels([
            "Tick", "Season", "Plants", "Berry Bushes", "Water", "Herbivores", "Foxes",
            "Avg Herb Energy", "Avg Herb Thirst", "Avg Fox Energy", "Avg Fox Hunger",
            "Avg Fox Thirst", "Avg Speed", "Avg Vision", "Avg Plant Food", "Danger"
        ])
        self.table.setFixedHeight(210)

        self.log_browser = QTextBrowser()
        self.log_browser.setFixedHeight(145)

        self.build_layout()

        self.log_event("Simulation interface loaded.")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(50)

        self.update_labels()

    def build_layout(self):
        settings_box = QGroupBox("Simulation Settings")
        settings_layout = QGridLayout()

        settings_layout.addWidget(QLabel("Plants:"), 0, 0)
        settings_layout.addWidget(self.plants_input, 0, 1)
        settings_layout.addWidget(QLabel("Herbivores:"), 1, 0)
        settings_layout.addWidget(self.herbivores_input, 1, 1)
        settings_layout.addWidget(QLabel("Foxes:"), 2, 0)
        settings_layout.addWidget(self.foxes_input, 2, 1)
        settings_layout.addWidget(QLabel("Water:"), 3, 0)
        settings_layout.addWidget(self.water_input, 3, 1)
        settings_layout.addWidget(self.apply_button, 4, 0, 1, 2)

        settings_box.setLayout(settings_layout)

        control_box = QGroupBox("Controls")
        control_layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)

        control_layout.addWidget(self.speed_label)
        control_layout.addWidget(self.speed_slider)
        control_layout.addLayout(buttons_layout)
        control_layout.addWidget(self.save_button)

        control_box.setLayout(control_layout)

        display_box = QGroupBox("Display Options")
        display_layout = QVBoxLayout()
        display_layout.addWidget(self.vision_checkbox)
        display_layout.addWidget(self.bars_checkbox)
        display_layout.addWidget(self.legend_checkbox)
        display_layout.addWidget(self.grid_checkbox)
        display_box.setLayout(display_layout)

        season_box = QGroupBox("Season")
        season_layout = QVBoxLayout()
        season_layout.addWidget(self.season_label)
        season_layout.addWidget(self.season_progress)
        season_box.setLayout(season_layout)

        population_box = QGroupBox("Population")
        population_layout = QVBoxLayout()
        for label in [
            self.tick_label,
            self.plants_label,
            self.berry_label,
            self.water_label,
            self.herbivores_label,
            self.foxes_label
        ]:
            population_layout.addWidget(label)
        population_box.setLayout(population_layout)

        stats_box = QGroupBox("Live Statistics")
        stats_layout = QVBoxLayout()
        for label in [
            self.energy_label,
            self.thirst_label,
            self.fox_energy_label,
            self.fox_hunger_label,
            self.fox_thirst_label,
            self.speed_info_label,
            self.vision_info_label,
            self.age_info_label,
            self.fox_age_label,
            self.food_label,
            self.danger_label
        ]:
            stats_layout.addWidget(label)
        stats_box.setLayout(stats_layout)

        records_box = QGroupBox("Records")
        records_layout = QVBoxLayout()
        for label in [
            self.max_plants_label,
            self.max_berry_label,
            self.max_herbivores_label,
            self.max_foxes_label,
            self.min_herbivores_label
        ]:
            records_layout.addWidget(label)
        records_box.setLayout(records_layout)

        log_box = QGroupBox("Event Log")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_browser)
        log_box.setLayout(log_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(self.title_label)
        right_layout.addWidget(self.subtitle_label)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(settings_box)
        right_layout.addWidget(control_box)
        right_layout.addWidget(display_box)
        right_layout.addWidget(season_box)
        right_layout.addWidget(population_box)
        right_layout.addWidget(stats_box)
        right_layout.addWidget(records_box)
        right_layout.addWidget(log_box)
        right_layout.addWidget(QLabel("Shortcuts: Space = Start/Pause, R = Reset, Esc = Close"))
        right_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(right_panel)
        scroll_area.setFixedWidth(410)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.canvas)
        top_layout.addWidget(scroll_area)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(QLabel("Simulation History:"))
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def log_event(self, text):
        tick = self.engine.current_tick if hasattr(self, "engine") else 0
        self.log_browser.append(f"Tick {tick}: {text}")

    def start_simulation(self):
        self.engine.start()
        self.status_label.setText("Status: Running")
        self.log_event("Simulation started.")

    def pause_simulation(self):
        self.engine.pause()
        self.status_label.setText("Status: Paused")
        self.log_event("Simulation paused.")

    def reset_simulation(self):
        self.engine = SimulationEngine()
        self.canvas.engine = self.engine

        self.max_plants = 0
        self.max_herbivores = 0
        self.min_herbivores = 0
        self.max_berry_bushes = 0
        self.max_foxes = 0
        self.last_fox_count = 0
        self.last_season = self.engine.season

        self.table.setRowCount(0)
        self.log_browser.clear()
        self.log_event("Simulation reset.")

        self.status_label.setText("Status: Reset")
        self.update_labels()
        self.canvas.update()

    def apply_settings(self):
        try:
            plants_count = int(self.plants_input.text())
            herbivores_count = int(self.herbivores_input.text())
            foxes_count = int(self.foxes_input.text())
            water_count = int(self.water_input.text())

            if plants_count < 0 or herbivores_count < 0 or foxes_count < 0 or water_count < 0:
                QMessageBox.warning(self, "Input Error", "Counts must be positive numbers.")
                return

            if plants_count > 1000 or herbivores_count > 200 or foxes_count > 80 or water_count > 30:
                QMessageBox.warning(self, "Input Error", "Too many organisms. Try smaller numbers.")
                return

            self.engine = SimulationEngine()
            self.engine.pause()

            self.engine.world.plants = []
            self.engine.world.herbivores = []
            self.engine.world.berry_bushes = []
            self.engine.world.foxes = []
            self.engine.world.water_sources = []
            self.engine.current_tick = 0
            self.engine.season = "summer"
            self.engine.season_tick = 0

            for i in range(plants_count):
                self.engine.world.plants.append(
                    Plant(i, random.randint(0, self.engine.world.width), random.randint(0, self.engine.world.height), 20)
                )

            for i in range(herbivores_count):
                self.engine.world.herbivores.append(
                    Herbivore(i, random.randint(0, self.engine.world.width), random.randint(0, self.engine.world.height), 100, 150, 0, 3, 150)
                )

            for i in range(foxes_count):
                self.engine.world.foxes.append(
                    Fox(i, random.randint(0, self.engine.world.width), random.randint(0, self.engine.world.height), 100, 0, 200, 0, 4, 200)
                )

            for i in range(water_count):
                self.engine.world.water_sources.append(
                    WaterSource(i, random.randint(100, self.engine.world.width - 100), random.randint(100, self.engine.world.height - 100), 40)
                )

            self.engine.world.spawn_berry_bushes()

            self.canvas.engine = self.engine
            self.table.setRowCount(0)

            self.max_plants = plants_count
            self.max_herbivores = herbivores_count
            self.min_herbivores = herbivores_count
            self.max_foxes = foxes_count
            self.last_fox_count = foxes_count
            self.max_berry_bushes = len(self.engine.world.berry_bushes)
            self.last_season = self.engine.season

            self.log_event("New ecosystem settings applied.")

            self.status_label.setText("Status: Settings Applied")
            self.update_labels()
            self.canvas.update()

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid integer numbers.")

    def change_speed(self):
        value = self.speed_slider.value()
        self.timer.setInterval(value)
        self.speed_label.setText(f"Simulation Speed: {value} ms")

    def change_visual_settings(self):
        self.canvas.show_vision = self.vision_checkbox.isChecked()
        self.canvas.show_bars = self.bars_checkbox.isChecked()
        self.canvas.show_legend = self.legend_checkbox.isChecked()
        self.canvas.show_grid = self.grid_checkbox.isChecked()
        self.canvas.update()

    def update_simulation(self):
        old_fox_count = self.last_fox_count

        self.engine.update()
        self.update_labels()
        self.canvas.update()

        state = self.engine.get_state()
        foxes_count = state["counts"].get("foxes", 0)
        season = state.get("season", "summer")

        if season != self.last_season:
            self.log_event(f"Season changed: {self.last_season} → {season}")
            self.last_season = season

        if old_fox_count == 0 and foxes_count > 0 and self.engine.running:
            self.log_event(f"Foxes migrated back +{foxes_count}")

        self.last_fox_count = foxes_count

        if self.engine.running and state["counts"]["herbivores"] == 0:
            self.engine.pause()
            self.status_label.setText("Status: Herbivores extinct")
            self.log_event("All herbivores died.")
            QMessageBox.information(self, "Simulation Ended", "All herbivores died. Foxes have no food left.")
            return

        if self.engine.current_tick % 10 == 0 and self.engine.current_tick != 0:
            self.add_table_row()

    def calculate_statistics(self):
        state = self.engine.get_state()

        plants_count = state["counts"]["plants"]
        herbivores_count = state["counts"]["herbivores"]
        berry_count = state["counts"].get("berry_bushes", 0)
        foxes_count = state["counts"].get("foxes", 0)
        water_count = state["counts"].get("water_sources", 0)

        total_energy = 0
        total_thirst = 0
        total_speed = 0
        total_vision = 0
        total_age = 0

        total_fox_energy = 0
        total_fox_hunger = 0
        total_fox_thirst = 0
        total_fox_age = 0

        total_plant_food = 0
        plant_food_count = 0
        danger_count = 0

        for entity in state["entities"]:
            if entity["type"] == "herbivore":
                total_energy += entity.get("energy", 0)
                total_thirst += entity.get("thirst", 0)
                total_speed += entity.get("speed", 0)
                total_vision += entity.get("vision", 0)
                total_age += entity.get("age", 0)

                if entity.get("nearest_fox_dist", 9999) < 200:
                    danger_count += 1

            elif entity["type"] == "fox":
                total_fox_energy += entity.get("energy", 0)
                total_fox_hunger += entity.get("hunger", 0)
                total_fox_thirst += entity.get("thirst", 0)
                total_fox_age += entity.get("age", 0)

            elif entity["type"] == "plant":
                total_plant_food += entity.get("food_value", 0)
                plant_food_count += 1

        if herbivores_count > 0:
            average_energy = total_energy / herbivores_count
            average_thirst = total_thirst / herbivores_count
            average_speed = total_speed / herbivores_count
            average_vision = total_vision / herbivores_count
            average_age = total_age / herbivores_count
        else:
            average_energy = 0
            average_thirst = 0
            average_speed = 0
            average_vision = 0
            average_age = 0

        if foxes_count > 0:
            average_fox_energy = total_fox_energy / foxes_count
            average_fox_hunger = total_fox_hunger / foxes_count
            average_fox_thirst = total_fox_thirst / foxes_count
            average_fox_age = total_fox_age / foxes_count
        else:
            average_fox_energy = 0
            average_fox_hunger = 0
            average_fox_thirst = 0
            average_fox_age = 0

        if plant_food_count > 0:
            average_food = total_plant_food / plant_food_count
        else:
            average_food = 0

        return (
            state, plants_count, berry_count, water_count, herbivores_count, foxes_count,
            average_energy, average_thirst, average_fox_energy, average_fox_hunger,
            average_fox_thirst, average_speed, average_vision, average_age,
            average_fox_age, average_food, danger_count
        )

    def update_labels(self):
        (
            state, plants_count, berry_count, water_count, herbivores_count, foxes_count,
            avg_energy, avg_thirst, avg_fox_energy, avg_fox_hunger,
            avg_fox_thirst, avg_speed, avg_vision, avg_age,
            avg_fox_age, avg_food, danger_count
        ) = self.calculate_statistics()

        season = state.get("season", "summer")
        season_tick = state.get("season_tick", 0)

        self.tick_label.setText(f"Tick: {state['tick']}")
        self.season_label.setText(f"Season: {season}")
        self.season_progress.setValue(season_tick)

        self.plants_label.setText(f"Plants: {plants_count}")
        self.berry_label.setText(f"Berry Bushes: {berry_count}")
        self.water_label.setText(f"Water Sources: {water_count}")
        self.herbivores_label.setText(f"Herbivores: {herbivores_count}")
        self.foxes_label.setText(f"Foxes: {foxes_count}")

        self.energy_label.setText(f"Average Herbivore Energy: {avg_energy:.1f}")
        self.thirst_label.setText(f"Average Herbivore Thirst: {avg_thirst:.1f}")
        self.fox_energy_label.setText(f"Average Fox Energy: {avg_fox_energy:.1f}")
        self.fox_hunger_label.setText(f"Average Fox Hunger: {avg_fox_hunger:.1f}")
        self.fox_thirst_label.setText(f"Average Fox Thirst: {avg_fox_thirst:.1f}")

        self.speed_info_label.setText(f"Average Speed: {avg_speed:.2f}")
        self.vision_info_label.setText(f"Average Vision: {avg_vision:.1f}")
        self.age_info_label.setText(f"Average Herbivore Age: {avg_age:.1f}")
        self.fox_age_label.setText(f"Average Fox Age: {avg_fox_age:.1f}")
        self.food_label.setText(f"Average Plant Food: {avg_food:.1f}")
        self.danger_label.setText(f"Herbivores in Danger: {danger_count}")

        if self.min_herbivores == 0 and herbivores_count > 0:
            self.min_herbivores = herbivores_count

        self.max_plants = max(self.max_plants, plants_count)
        self.max_berry_bushes = max(self.max_berry_bushes, berry_count)
        self.max_herbivores = max(self.max_herbivores, herbivores_count)
        self.max_foxes = max(self.max_foxes, foxes_count)

        if herbivores_count > 0:
            self.min_herbivores = min(self.min_herbivores, herbivores_count)

        self.max_plants_label.setText(f"Max Plants: {self.max_plants}")
        self.max_berry_label.setText(f"Max Berry Bushes: {self.max_berry_bushes}")
        self.max_herbivores_label.setText(f"Max Herbivores: {self.max_herbivores}")
        self.max_foxes_label.setText(f"Max Foxes: {self.max_foxes}")
        self.min_herbivores_label.setText(f"Min Herbivores: {self.min_herbivores}")

        self.status_label.setText(
            self.get_ecosystem_status(plants_count, herbivores_count, foxes_count, danger_count, avg_thirst, avg_fox_thirst)
        )

    def get_ecosystem_status(self, plants_count, herbivores_count, foxes_count, danger_count, avg_thirst, avg_fox_thirst):
        if herbivores_count == 0:
            return "Status: Herbivores extinct"
        if avg_thirst > 220 or avg_fox_thirst > 260:
            return "Status: Water stress"
        if foxes_count == 0 and herbivores_count > 30:
            return "Status: Foxes migrated, reintroduction expected"
        if foxes_count > herbivores_count:
            return "Status: Too many predators"
        if danger_count > herbivores_count / 2:
            return "Status: Herbivores under pressure"
        if plants_count < herbivores_count * 2:
            return "Status: Food shortage"
        return "Status: Balanced"

    def add_table_row(self):
        (
            state, plants_count, berry_count, water_count, herbivores_count, foxes_count,
            avg_energy, avg_thirst, avg_fox_energy, avg_fox_hunger,
            avg_fox_thirst, avg_speed, avg_vision, avg_age,
            avg_fox_age, avg_food, danger_count
        ) = self.calculate_statistics()

        values = [
            state["tick"], state.get("season", "summer"), plants_count, berry_count,
            water_count, herbivores_count, foxes_count, f"{avg_energy:.1f}",
            f"{avg_thirst:.1f}", f"{avg_fox_energy:.1f}", f"{avg_fox_hunger:.1f}",
            f"{avg_fox_thirst:.1f}", f"{avg_speed:.2f}", f"{avg_vision:.1f}",
            f"{avg_food:.1f}", danger_count
        ]

        row = self.table.rowCount()
        self.table.insertRow(row)

        for col, value in enumerate(values):
            self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def save_table_to_csv(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "There is no simulation history to save.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Simulation History",
            "simulation_history.csv",
            "CSV Files (*.csv)"
        )

        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(
                    "Tick,Season,Plants,Berry Bushes,Water,Herbivores,Foxes,"
                    "Avg Herbivore Energy,Avg Herbivore Thirst,Avg Fox Energy,"
                    "Avg Fox Hunger,Avg Fox Thirst,Avg Speed,Avg Vision,"
                    "Avg Plant Food,Danger\n"
                )

                for row in range(self.table.rowCount()):
                    values = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        values.append(item.text() if item else "")
                    file.write(",".join(values) + "\n")

            QMessageBox.information(self, "Saved", "Simulation history saved successfully.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_R:
            self.reset_simulation()
        elif event.key() == Qt.Key_Space:
            if self.engine.running:
                self.pause_simulation()
            else:
                self.start_simulation()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
