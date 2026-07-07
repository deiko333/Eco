import csv
import random
import sqlite3
import sys
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from backend.engine import SimulationEngine, Plant, Herbivore, Fox, WaterSource


class FrontendDatabase:

    def __init__(self, db_name="ecobalance_frontend_history.db"):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                tick INTEGER NOT NULL,
                season TEXT NOT NULL,
                plants INTEGER NOT NULL,
                berry_bushes INTEGER NOT NULL,
                water_sources INTEGER NOT NULL,
                shelters INTEGER NOT NULL,
                herbivores INTEGER NOT NULL,
                foxes INTEGER NOT NULL,
                avg_herbivore_energy REAL,
                avg_herbivore_thirst REAL,
                avg_fox_energy REAL,
                avg_fox_hunger REAL,
                avg_fox_thirst REAL,
                danger_count INTEGER
            )
        """)
        connection.commit()
        connection.close()

    def save_snapshot(self, stats):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO simulation_snapshots (
                created_at, tick, season, plants, berry_bushes, water_sources,
                shelters, herbivores, foxes, avg_herbivore_energy,
                avg_herbivore_thirst, avg_fox_energy, avg_fox_hunger,
                avg_fox_thirst, danger_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            stats["tick"],
            stats["season"],
            stats["plants"],
            stats["berry_bushes"],
            stats["water_sources"],
            stats["shelters"],
            stats["herbivores"],
            stats["foxes"],
            stats["avg_herbivore_energy"],
            stats["avg_herbivore_thirst"],
            stats["avg_fox_energy"],
            stats["avg_fox_hunger"],
            stats["avg_fox_thirst"],
            stats["danger_count"],
        ))
        connection.commit()
        connection.close()


class PopulationGraph(FigureCanvas):

    def __init__(self):
        self.figure = Figure(figsize=(5, 3))
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        self.ticks = []
        self.plants = []
        self.herbivores = []
        self.foxes = []
        self.berries = []
        self.redraw()

    def add_point(self, stats):
        self.ticks.append(stats["tick"])
        self.plants.append(stats["plants"])
        self.herbivores.append(stats["herbivores"])
        self.foxes.append(stats["foxes"])
        self.berries.append(stats["berry_bushes"])
        if len(self.ticks) > 160:
            self.ticks = self.ticks[-160:]
            self.plants = self.plants[-160:]
            self.herbivores = self.herbivores[-160:]
            self.foxes = self.foxes[-160:]
            self.berries = self.berries[-160:]
        self.redraw()

    def reset_graph(self):
        self.ticks.clear()
        self.plants.clear()
        self.herbivores.clear()
        self.foxes.clear()
        self.berries.clear()
        self.redraw()

    def redraw(self):
        self.axes.clear()
        self.axes.plot(self.ticks, self.plants, label="Plants")
        self.axes.plot(self.ticks, self.herbivores, label="Herbivores")
        self.axes.plot(self.ticks, self.foxes, label="Foxes")
        self.axes.plot(self.ticks, self.berries, label="Berry Bushes")
        self.axes.set_title("Population Changes")
        self.axes.set_xlabel("Tick")
        self.axes.set_ylabel("Count")
        self.axes.grid(True, alpha=0.35)
        if self.ticks:
            self.axes.legend(loc="upper right")
        self.figure.tight_layout()
        self.draw()


class EcosystemCanvas(QWidget):

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.show_vision = True
        self.show_bars = True
        self.show_legend = True
        self.show_grid = False
        self.world_width = 1000
        self.world_height = 700
        self.setMinimumSize(820, 560)

    def season_colors(self, season):
        if season == "spring":
            return QColor("#DFF5D8"), QColor("#A5D6A7")
        if season == "summer":
            return QColor("#E8F5E9"), QColor("#81C784")
        if season == "autumn":
            return QColor("#FFF3E0"), QColor("#FFB74D")
        if season == "winter":
            return QColor("#E3F2FD"), QColor("#90CAF9")
        return QColor("#E8F5E9"), QColor("#81C784")

    def scale_x(self, x):
        return int((x / self.world_width) * self.width())

    def scale_y(self, y):
        return int((y / self.world_height) * self.height())

    def scale_radius(self, radius):
        return int((radius / self.world_width) * self.width())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
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
        entities = state.get("entities", [])
        for entity in entities:
            if entity["type"] in ("water", "shelter"):
                self.draw_entity(painter, entity)
        for entity in entities:
            if entity["type"] in ("plant", "berry_bush"):
                self.draw_entity(painter, entity)
        for entity in entities:
            if entity["type"] in ("herbivore", "fox"):
                self.draw_entity(painter, entity)
        self.draw_season_badge(painter, season, state.get("season_tick", 0))
        if self.show_legend:
            self.draw_legend(painter)
        self.draw_border(painter)

    def draw_grid(self, painter, color):
        painter.setPen(QPen(color, 1))
        for x in range(0, self.width(), 50):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 50):
            painter.drawLine(0, y, self.width(), y)

    def draw_border(self, painter):
        painter.setPen(QPen(QColor("#355C35"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect().adjusted(1, 1, -2, -2))

    def draw_winter_effect(self, painter):
        painter.setPen(QColor(255, 255, 255, 170))
        font = painter.font()
        font.setPointSize(15)
        painter.setFont(font)
        for i in range(55):
            x = (i * 73) % max(1, self.width())
            y = (i * 41) % max(1, self.height())
            painter.drawText(x, y, "•")

    def draw_autumn_effect(self, painter):
        painter.setPen(QColor("#A66A2C"))
        font = painter.font()
        font.setPointSize(13)
        painter.setFont(font)
        for i in range(26):
            x = (i * 83) % max(1, self.width())
            y = (i * 47) % max(1, self.height())
            painter.drawText(x, y, "🍂")

    def draw_entity(self, painter, entity):
        entity_type = entity["type"]
        x = self.scale_x(entity.get("x", 0))
        y = self.scale_y(entity.get("y", 0))
        if entity_type == "water":
            radius = self.scale_radius(entity.get("radius", 40))
            painter.setPen(QPen(QColor("#0D47A1"), 1))
            painter.setBrush(QBrush(QColor(66, 165, 245, 100)))
            painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
            self.draw_text(painter, x - 8, y + 6, "💧", 16)
        elif entity_type == "shelter":
            radius = self.scale_radius(entity.get("radius", 50))
            painter.setPen(QPen(QColor("#5D4037"), 1))
            painter.setBrush(QBrush(QColor(121, 85, 72, 120)))
            painter.drawRoundedRect(QRectF(x - radius, y - radius, radius * 2, radius * 2), 10, 10)
            self.draw_text(painter, x - 8, y + 6, "⛺", 16)
        elif entity_type == "plant":
            self.draw_text(painter, x, y, "🌿", 11 if entity.get("food_value", 10) > 25 else 9)
        elif entity_type == "berry_bush":
            self.draw_text(painter, x, y, "🫐", 13)
        elif entity_type == "herbivore":
            energy = entity.get("energy", 0)
            thirst = entity.get("thirst", 0)
            vision = int(entity.get("vision", 0))
            nearest_fox_dist = entity.get("nearest_fox_dist", 9999)
            if self.show_vision:
                scaled_vision = self.scale_radius(vision)
                painter.setPen(QPen(QColor(80, 80, 80, 28), 1))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(x - scaled_vision, y - scaled_vision, scaled_vision * 2, scaled_vision * 2))
            self.draw_text(painter, x, y, "🐰", 18)
            if self.show_bars:
                self.draw_bar(painter, x, y + 12, energy, 300, "energy")
                self.draw_bar(painter, x, y + 19, thirst, 300, "thirst")
                if nearest_fox_dist < 80:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor("#C62828"))
                    painter.drawRect(x, y + 26, 30, 4)
        elif entity_type == "fox":
            energy = entity.get("energy", 0)
            hunger = entity.get("hunger", 0)
            thirst = entity.get("thirst", 0)
            vision = int(entity.get("vision", 150))
            if self.show_vision:
                scaled_vision = self.scale_radius(vision)
                painter.setPen(QPen(QColor(230, 100, 20, 32), 1))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(x - scaled_vision, y - scaled_vision, scaled_vision * 2, scaled_vision * 2))
            self.draw_text(painter, x, y, "🦊", 19)
            if self.show_bars:
                self.draw_bar(painter, x, y + 12, energy, 300, "energy")
                self.draw_bar(painter, x, y + 19, hunger, 300, "hunger")
                self.draw_bar(painter, x, y + 26, thirst, 300, "thirst")

    def draw_text(self, painter, x, y, text, size):
        painter.setPen(QColor("#111111"))
        font = painter.font()
        font.setPointSize(size)
        painter.setFont(font)
        painter.drawText(x, y, text)

    def draw_bar(self, painter, x, y, value, max_value, bar_type):
        width = 30
        height = 5
        percent = value / max_value if max_value else 0
        percent = max(0, min(1, percent))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#D6D6D6"))
        painter.drawRect(x, y, width, height)
        if bar_type == "energy":
            color = QColor("#2E7D32") if percent > 0.6 else QColor("#FBC02D") if percent > 0.3 else QColor("#C62828")
        elif bar_type == "thirst":
            color = QColor("#B71C1C") if percent > 0.7 else QColor("#039BE5") if percent > 0.4 else QColor("#81D4FA")
        else:
            color = QColor("#B71C1C") if percent > 0.7 else QColor("#EF6C00") if percent > 0.4 else QColor("#43A047")
        painter.setBrush(color)
        painter.drawRect(x, y, int(width * percent), height)

    def draw_season_badge(self, painter, season, season_tick):
        color = {
            "spring": QColor(129, 199, 132, 220),
            "summer": QColor(255, 213, 79, 220),
            "autumn": QColor(255, 152, 0, 215),
            "winter": QColor(100, 181, 246, 220),
        }.get(season, QColor(129, 199, 132, 220))
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(self.width() - 210, 18, 188, 42, 12, 12)
        painter.setPen(QColor("#263238"))
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.width() - 194, 45, f"Season: {season} ({season_tick}/1000)")

    def draw_legend(self, painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 225))
        painter.drawRoundedRect(12, 12, 210, 270, 12, 12)
        painter.setPen(QColor("#263238"))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(25, 38, "Legend")
        font.setBold(False)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(25, 68, "💧  Water source")
        painter.drawText(25, 94, "⛺  Shelter")
        painter.drawText(25, 120, "🌿  Plant")
        painter.drawText(25, 146, "🫐  Berry bush")
        painter.drawText(25, 172, "🐰  Herbivore")
        painter.drawText(25, 198, "🦊  Fox")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2E7D32"))
        painter.drawRect(25, 218, 30, 5)
        painter.setPen(QColor("#263238"))
        painter.drawText(65, 224, "Energy")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#039BE5"))
        painter.drawRect(25, 241, 30, 5)
        painter.setPen(QColor("#263238"))
        painter.drawText(65, 247, "Thirst")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#EF6C00"))
        painter.drawRect(25, 264, 30, 5)
        painter.setPen(QColor("#263238"))
        painter.drawText(65, 270, "Hunger / danger")


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.engine = SimulationEngine()
        self.database = FrontendDatabase()
        self.max_plants = 0
        self.max_herbivores = 0
        self.min_herbivores = 0
        self.max_berry_bushes = 0
        self.max_foxes = 0
        self.last_fox_count = 0
        self.last_season = self.engine.season
        self.last_saved_tick = -1
        self.setWindowTitle("EcoBalance - Ecosystem Simulator")
        self.setGeometry(45, 35, 1540, 900)
        self.apply_style()
        self.create_widgets()
        self.build_layout()
        self.connect_signals()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(50)
        self.log_event("Simulation interface loaded.")
        self.update_labels()
        self.canvas.update()

    def apply_style(self):
        self.setStyleSheet("""
            QWidget { background-color: #F4F7F3; color: #263238; font-family: Arial; font-size: 13px; }
            QLabel { padding: 2px; }
            QPushButton { background-color: #2E7D32; color: white; border-radius: 8px; padding: 9px; font-weight: bold; }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:pressed { background-color: #1B5E20; }
            QPushButton#dangerButton { background-color: #B71C1C; }
            QPushButton#dangerButton:hover { background-color: #C62828; }
            QLineEdit { background-color: white; border: 1px solid #B0BEC5; border-radius: 6px; padding: 7px; }
            QTableWidget { background-color: white; border: 1px solid #CFD8DC; border-radius: 8px; gridline-color: #ECEFF1; }
            QTextBrowser { background-color: white; border: 1px solid #CFD8DC; border-radius: 8px; padding: 6px; }
            QGroupBox { background-color: #FFFFFF; border: 1px solid #CFD8DC; border-radius: 10px; margin-top: 12px; padding: 10px; font-weight: bold; color: #1B5E20; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
            QScrollArea { border: none; background-color: #F4F7F3; }
            QProgressBar { border: 1px solid #B0BEC5; border-radius: 6px; background-color: white; text-align: center; height: 16px; }
            QProgressBar::chunk { background-color: #66BB6A; border-radius: 6px; }
            QSlider::groove:horizontal { height: 6px; background: #CFD8DC; border-radius: 3px; }
            QSlider::handle:horizontal { background: #2E7D32; width: 16px; margin: -5px 0; border-radius: 8px; }
        """)

    def create_widgets(self):
        self.canvas = EcosystemCanvas(self.engine)
        self.graph = PopulationGraph()
        self.title_label = QLabel("🌍 EcoBalance")
        self.title_label.setStyleSheet("font-size: 25px; font-weight: bold; color: #1B5E20; padding: 8px;")
        self.subtitle_label = QLabel("Ecosystem Simulator")
        self.subtitle_label.setStyleSheet("font-size: 13px; color: #607D8B; padding-left: 8px;")
        self.status_label = QLabel("Status: Paused")
        self.status_label.setStyleSheet("background-color: #E3F2FD; color: #0D47A1; border-radius: 8px; padding: 9px; font-weight: bold;")
        self.tick_label = QLabel("Tick: 0")
        self.season_label = QLabel("Season: summer")
        self.season_progress = QProgressBar()
        self.season_progress.setMaximum(1000)
        self.plants_label = QLabel("Plants: 0")
        self.berry_label = QLabel("Berry Bushes: 0")
        self.water_label = QLabel("Water Sources: 0")
        self.shelter_label = QLabel("Shelters: 0")
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
        self.vision_checkbox = QCheckBox("Show vision ranges")
        self.vision_checkbox.setChecked(True)
        self.bars_checkbox = QCheckBox("Show energy / thirst / hunger bars")
        self.bars_checkbox.setChecked(True)
        self.legend_checkbox = QCheckBox("Show legend")
        self.legend_checkbox.setChecked(True)
        self.grid_checkbox = QCheckBox("Show grid")
        self.grid_checkbox.setChecked(False)
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.apply_button = QPushButton("Apply Settings")
        self.save_csv_button = QPushButton("Save CSV")
        self.save_db_button = QPushButton("Save Snapshot to DB")
        self.exit_button = QPushButton("Exit")
        self.exit_button.setObjectName("dangerButton")
        self.table = QTableWidget()
        self.table.setColumnCount(17)
        self.table.setHorizontalHeaderLabels(["Tick", "Season", "Plants", "Berry Bushes", "Water", "Shelters", "Herbivores", "Foxes", "Avg Herb Energy", "Avg Herb Thirst", "Avg Fox Energy", "Avg Fox Hunger", "Avg Fox Thirst", "Avg Speed", "Avg Vision", "Avg Plant Food", "Danger"])
        self.table.setMinimumHeight(210)
        self.log_browser = QTextBrowser()
        self.log_browser.setFixedHeight(150)

    def build_layout(self):
        main_splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(self.canvas, stretch=5)
        left_layout.addWidget(self.graph, stretch=2)
        right_panel = self.create_right_panel()
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([1060, 430])
        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)
        main_layout.addWidget(QLabel("Simulation History"))
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

    def create_right_panel(self):
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
        first_row = QHBoxLayout()
        first_row.addWidget(self.start_button)
        first_row.addWidget(self.pause_button)
        first_row.addWidget(self.reset_button)
        second_row = QHBoxLayout()
        second_row.addWidget(self.save_csv_button)
        second_row.addWidget(self.save_db_button)
        control_layout.addWidget(self.speed_label)
        control_layout.addWidget(self.speed_slider)
        control_layout.addLayout(first_row)
        control_layout.addLayout(second_row)
        control_layout.addWidget(self.exit_button)
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
        for label in [self.tick_label, self.plants_label, self.berry_label, self.water_label, self.shelter_label, self.herbivores_label, self.foxes_label]:
            population_layout.addWidget(label)
        population_box.setLayout(population_layout)
        stats_box = QGroupBox("Live Statistics")
        stats_layout = QVBoxLayout()
        for label in [self.energy_label, self.thirst_label, self.fox_energy_label, self.fox_hunger_label, self.fox_thirst_label, self.speed_info_label, self.vision_info_label, self.age_info_label, self.fox_age_label, self.food_label, self.danger_label]:
            stats_layout.addWidget(label)
        stats_box.setLayout(stats_layout)
        records_box = QGroupBox("Records")
        records_layout = QVBoxLayout()
        for label in [self.max_plants_label, self.max_berry_label, self.max_herbivores_label, self.max_foxes_label, self.min_herbivores_label]:
            records_layout.addWidget(label)
        records_box.setLayout(records_layout)
        log_box = QGroupBox("Event Log")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_browser)
        log_box.setLayout(log_layout)
        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
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
        scroll_area.setWidget(right_content)
        scroll_area.setMinimumWidth(430)
        scroll_area.setMaximumWidth(470)
        return scroll_area

    def connect_signals(self):
        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)
        self.apply_button.clicked.connect(self.apply_settings)
        self.save_csv_button.clicked.connect(self.save_table_to_csv)
        self.save_db_button.clicked.connect(self.save_snapshot_to_db)
        self.exit_button.clicked.connect(self.close)
        self.speed_slider.valueChanged.connect(self.change_speed)
        self.vision_checkbox.toggled.connect(self.change_visual_settings)
        self.bars_checkbox.toggled.connect(self.change_visual_settings)
        self.legend_checkbox.toggled.connect(self.change_visual_settings)
        self.grid_checkbox.toggled.connect(self.change_visual_settings)

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
        self.last_saved_tick = -1
        self.table.setRowCount(0)
        self.graph.reset_graph()
        self.log_browser.clear()
        self.status_label.setText("Status: Reset")
        self.log_event("Simulation reset.")
        self.update_labels()
        self.canvas.update()

    def apply_settings(self):
        try:
            plants_count = int(self.plants_input.text())
            herbivores_count = int(self.herbivores_input.text())
            foxes_count = int(self.foxes_input.text())
            water_count = int(self.water_input.text())
            self.validate_settings(plants_count, herbivores_count, foxes_count, water_count)
            self.engine = SimulationEngine()
            self.engine.pause()
            self.clear_world()
            self.spawn_custom_world(plants_count, herbivores_count, foxes_count, water_count)
            self.engine.current_tick = 0
            self.engine.season = "summer"
            self.engine.season_tick = 0
            self.canvas.engine = self.engine
            self.table.setRowCount(0)
            self.graph.reset_graph()
            self.max_plants = plants_count
            self.max_herbivores = herbivores_count
            self.min_herbivores = herbivores_count if herbivores_count > 0 else 0
            self.max_foxes = foxes_count
            self.max_berry_bushes = len(self.engine.world.berry_bushes)
            self.last_fox_count = foxes_count
            self.last_season = self.engine.season
            self.last_saved_tick = -1
            self.status_label.setText("Status: Settings Applied")
            self.log_event("New ecosystem settings applied.")
            self.update_labels()
            self.canvas.update()
        except ValueError as error:
            QMessageBox.warning(self, "Input Error", str(error))

    def validate_settings(self, plants, herbivores, foxes, water):
        if plants < 0 or herbivores < 0 or foxes < 0 or water < 0:
            raise ValueError("Counts must be positive numbers.")
        if plants > 1000:
            raise ValueError("Too many plants. Maximum allowed: 1000.")
        if herbivores > 250:
            raise ValueError("Too many herbivores. Maximum allowed: 250.")
        if foxes > 90:
            raise ValueError("Too many foxes. Maximum allowed: 90.")
        if water > 35:
            raise ValueError("Too many water sources. Maximum allowed: 35.")

    def clear_world(self):
        self.engine.world.plants = []
        self.engine.world.herbivores = []
        self.engine.world.berry_bushes = []
        self.engine.world.foxes = []
        self.engine.world.water_sources = []
        if hasattr(self.engine.world, "shelters"):
            self.engine.world.shelters = []

    def spawn_custom_world(self, plants_count, herbivores_count, foxes_count, water_count):
        width = self.engine.world.width
        height = self.engine.world.height
        for i in range(plants_count):
            self.engine.world.plants.append(Plant(i, random.randint(0, width), random.randint(0, height), 20))
        for i in range(herbivores_count):
            self.engine.world.herbivores.append(Herbivore(i, random.randint(0, width), random.randint(0, height), 100, 150, 0, 3, 150))
        for i in range(foxes_count):
            self.engine.world.foxes.append(Fox(i, random.randint(0, width), random.randint(0, height), 100, 0, 200, 0, 4, 200))
        for i in range(water_count):
            self.engine.world.water_sources.append(WaterSource(i, random.randint(100, width - 100), random.randint(100, height - 100), 40))
        if hasattr(self.engine.world, "spawn_berry_bushes"):
            self.engine.world.spawn_berry_bushes()
        if hasattr(self.engine.world, "spawn_shelters"):
            self.engine.world.spawn_shelters()

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
        stats = self.calculate_statistics()
        self.update_labels_from_stats(stats)
        self.canvas.update()
        if self.engine.running and stats["tick"] % 5 == 0 and stats["tick"] != 0:
            self.graph.add_point(stats)
        if self.engine.running and stats["tick"] % 10 == 0 and stats["tick"] != 0:
            self.add_table_row(stats)
        self.check_important_events(stats, old_fox_count)

    def calculate_statistics(self):
        state = self.engine.get_state()
        counts = state["counts"]
        herbivores = []
        foxes = []
        plants = []
        danger_count = 0
        for entity in state["entities"]:
            if entity["type"] == "herbivore":
                herbivores.append(entity)
                if entity.get("nearest_fox_dist", 9999) < 200:
                    danger_count += 1
            elif entity["type"] == "fox":
                foxes.append(entity)
            elif entity["type"] == "plant":
                plants.append(entity)
        return {
            "tick": state["tick"],
            "season": state.get("season", "summer"),
            "season_tick": state.get("season_tick", 0),
            "plants": counts.get("plants", 0),
            "berry_bushes": counts.get("berry_bushes", 0),
            "water_sources": counts.get("water_sources", 0),
            "shelters": counts.get("shelters", 0),
            "herbivores": counts.get("herbivores", 0),
            "foxes": counts.get("foxes", 0),
            "avg_herbivore_energy": self.average(herbivores, "energy"),
            "avg_herbivore_thirst": self.average(herbivores, "thirst"),
            "avg_fox_energy": self.average(foxes, "energy"),
            "avg_fox_hunger": self.average(foxes, "hunger"),
            "avg_fox_thirst": self.average(foxes, "thirst"),
            "avg_speed": self.average(herbivores, "speed"),
            "avg_vision": self.average(herbivores, "vision"),
            "avg_herbivore_age": self.average(herbivores, "age"),
            "avg_fox_age": self.average(foxes, "age"),
            "avg_plant_food": self.average(plants, "food_value"),
            "danger_count": danger_count,
        }

    def average(self, items, key):
        if not items:
            return 0
        return sum(item.get(key, 0) for item in items) / len(items)

    def update_labels(self):
        self.update_labels_from_stats(self.calculate_statistics())

    def update_labels_from_stats(self, stats):
        self.tick_label.setText(f"Tick: {stats['tick']}")
        self.season_label.setText(f"Season: {stats['season']}")
        self.season_progress.setValue(stats["season_tick"])
        self.plants_label.setText(f"Plants: {stats['plants']}")
        self.berry_label.setText(f"Berry Bushes: {stats['berry_bushes']}")
        self.water_label.setText(f"Water Sources: {stats['water_sources']}")
        self.shelter_label.setText(f"Shelters: {stats['shelters']}")
        self.herbivores_label.setText(f"Herbivores: {stats['herbivores']}")
        self.foxes_label.setText(f"Foxes: {stats['foxes']}")
        self.energy_label.setText(f"Average Herbivore Energy: {stats['avg_herbivore_energy']:.1f}")
        self.thirst_label.setText(f"Average Herbivore Thirst: {stats['avg_herbivore_thirst']:.1f}")
        self.fox_energy_label.setText(f"Average Fox Energy: {stats['avg_fox_energy']:.1f}")
        self.fox_hunger_label.setText(f"Average Fox Hunger: {stats['avg_fox_hunger']:.1f}")
        self.fox_thirst_label.setText(f"Average Fox Thirst: {stats['avg_fox_thirst']:.1f}")
        self.speed_info_label.setText(f"Average Speed: {stats['avg_speed']:.2f}")
        self.vision_info_label.setText(f"Average Vision: {stats['avg_vision']:.1f}")
        self.age_info_label.setText(f"Average Herbivore Age: {stats['avg_herbivore_age']:.1f}")
        self.fox_age_label.setText(f"Average Fox Age: {stats['avg_fox_age']:.1f}")
        self.food_label.setText(f"Average Plant Food: {stats['avg_plant_food']:.1f}")
        self.danger_label.setText(f"Herbivores in Danger: {stats['danger_count']}")
        self.update_records(stats)
        self.status_label.setText(self.get_ecosystem_status(stats))

    def update_records(self, stats):
        if self.min_herbivores == 0 and stats["herbivores"] > 0:
            self.min_herbivores = stats["herbivores"]
        self.max_plants = max(self.max_plants, stats["plants"])
        self.max_berry_bushes = max(self.max_berry_bushes, stats["berry_bushes"])
        self.max_herbivores = max(self.max_herbivores, stats["herbivores"])
        self.max_foxes = max(self.max_foxes, stats["foxes"])
        if stats["herbivores"] > 0:
            self.min_herbivores = min(self.min_herbivores, stats["herbivores"])
        self.max_plants_label.setText(f"Max Plants: {self.max_plants}")
        self.max_berry_label.setText(f"Max Berry Bushes: {self.max_berry_bushes}")
        self.max_herbivores_label.setText(f"Max Herbivores: {self.max_herbivores}")
        self.max_foxes_label.setText(f"Max Foxes: {self.max_foxes}")
        self.min_herbivores_label.setText(f"Min Herbivores: {self.min_herbivores}")

    def get_ecosystem_status(self, stats):
        if stats["herbivores"] == 0:
            return "Status: Herbivores extinct"
        if stats["avg_herbivore_thirst"] > 220 or stats["avg_fox_thirst"] > 260:
            return "Status: Water stress"
        if stats["foxes"] == 0 and stats["herbivores"] > 30:
            return "Status: Foxes migrated, reintroduction expected"
        if stats["foxes"] > stats["herbivores"]:
            return "Status: Too many predators"
        if stats["danger_count"] > stats["herbivores"] / 2:
            return "Status: Herbivores under pressure"
        if stats["plants"] < stats["herbivores"] * 2:
            return "Status: Food shortage"
        return "Status: Balanced"

    def check_important_events(self, stats, old_fox_count):
        if stats["season"] != self.last_season:
            self.log_event(f"Season changed: {self.last_season} → {stats['season']}")
            self.last_season = stats["season"]
        if old_fox_count == 0 and stats["foxes"] > 0 and self.engine.running:
            self.log_event(f"Foxes migrated back +{stats['foxes']}")
        self.last_fox_count = stats["foxes"]
        if self.engine.running and stats["herbivores"] == 0:
            self.engine.pause()
            self.status_label.setText("Status: Herbivores extinct")
            self.log_event("All herbivores died.")
            QMessageBox.information(self, "Simulation Ended", "All herbivores died. Foxes have no food left.")

    def add_table_row(self, stats):
        values = [stats["tick"], stats["season"], stats["plants"], stats["berry_bushes"], stats["water_sources"], stats["shelters"], stats["herbivores"], stats["foxes"], f"{stats['avg_herbivore_energy']:.1f}", f"{stats['avg_herbivore_thirst']:.1f}", f"{stats['avg_fox_energy']:.1f}", f"{stats['avg_fox_hunger']:.1f}", f"{stats['avg_fox_thirst']:.1f}", f"{stats['avg_speed']:.2f}", f"{stats['avg_vision']:.1f}", f"{stats['avg_plant_food']:.1f}", stats["danger_count"]]
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col, item)
        self.table.scrollToBottom()

    def save_table_to_csv(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "There is no simulation history to save.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save Simulation History", "simulation_history.csv", "CSV Files (*.csv)")
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                headers = [self.table.horizontalHeaderItem(col).text() for col in range(self.table.columnCount())]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_values = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_values.append(item.text() if item else "")
                    writer.writerow(row_values)
            QMessageBox.information(self, "Saved", "Simulation history saved successfully.")
            self.log_event("Simulation history exported to CSV.")
        except OSError as error:
            QMessageBox.warning(self, "Error", f"Could not save file: {error}")

    def save_snapshot_to_db(self):
        stats = self.calculate_statistics()
        if stats["tick"] == self.last_saved_tick:
            QMessageBox.information(self, "Already Saved", "This tick was already saved to database.")
            return
        try:
            self.database.save_snapshot(stats)
            self.last_saved_tick = stats["tick"]
            self.log_event("Current simulation snapshot saved to SQLite database.")
            QMessageBox.information(self, "Saved", "Current snapshot saved to SQLite database.")
        except sqlite3.Error as error:
            QMessageBox.warning(self, "Database Error", f"Could not save snapshot: {error}")

    def log_event(self, text):
        tick = self.engine.current_tick if hasattr(self, "engine") else 0
        self.log_browser.append(f"Tick {tick}: {text}")

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
