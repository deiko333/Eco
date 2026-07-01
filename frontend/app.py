import sys
import random

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QSlider, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QCheckBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QPen

from backend.engine import SimulationEngine, Plant, Herbivore, Fox


class EcosystemCanvas(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.show_vision = True
        self.show_bars = True
        self.setFixedSize(1000, 700)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#E8F5E9"))

        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)

        state = self.engine.get_state()

        for entity in state["entities"]:
            x = int(entity["x"])
            y = int(entity["y"])

            if entity["type"] == "plant":
                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🌿")

            elif entity["type"] == "berry_bush":
                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🫐")

            elif entity["type"] == "herbivore":
                energy = entity.get("energy", 0)
                vision = int(entity.get("vision", 0))
                nearest_fox_dist = entity.get("nearest_fox_dist", 9999)

                if self.show_vision:
                    painter.setPen(QPen(QColor(120, 120, 120, 35), 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(x - vision, y - vision, vision * 2, vision * 2)

                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🐰")

                if self.show_bars:
                    self.draw_energy_bar(painter, x, y + 8, energy, 300)

                    if nearest_fox_dist < 80:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(QColor("#C62828"))
                        painter.drawRect(x, y + 14, 24, 3)

            elif entity["type"] == "fox":
                energy = entity.get("energy", 0)
                hunger = entity.get("hunger", 0)
                vision = int(entity.get("vision", 150))

                if self.show_vision:
                    painter.setPen(QPen(QColor(255, 120, 0, 35), 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(x - vision, y - vision, vision * 2, vision * 2)

                painter.setPen(QColor("black"))
                painter.drawText(x, y, "🦊")

                if self.show_bars:
                    self.draw_energy_bar(painter, x, y + 8, energy, 300)

                    painter.setPen(Qt.NoPen)
                    if hunger > 250:
                        painter.setBrush(QColor("#B71C1C"))
                    elif hunger > 120:
                        painter.setBrush(QColor("#EF6C00"))
                    else:
                        painter.setBrush(QColor("#43A047"))

                    painter.drawRect(x, y + 14, 24, 3)

        self.draw_legend(painter)

    def draw_energy_bar(self, painter, x, y, value, max_value):
        width = 24
        height = 4

        percent = value / max_value
        if percent < 0:
            percent = 0
        if percent > 1:
            percent = 1

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#CCCCCC"))
        painter.drawRect(x, y, width, height)

        if percent > 0.6:
            painter.setBrush(QColor("#2E7D32"))
        elif percent > 0.3:
            painter.setBrush(QColor("#FBC02D"))
        else:
            painter.setBrush(QColor("#C62828"))

        painter.drawRect(x, y, int(width * percent), height)

    def draw_legend(self, painter):
        painter.setPen(QColor("black"))

        painter.drawText(20, 30, "🌿 Plant")
        painter.drawText(20, 55, "🫐 Berry bush")
        painter.drawText(20, 80, "🐰 Herbivore")
        painter.drawText(20, 105, "🦊 Fox")

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2E7D32"))
        painter.drawRect(20, 125, 24, 4)
        painter.setPen(QColor("black"))
        painter.drawText(55, 132, "Energy")

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#EF6C00"))
        painter.drawRect(20, 150, 24, 4)
        painter.setPen(QColor("black"))
        painter.drawText(55, 157, "Hunger / danger")

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawEllipse(20, 170, 18, 18)
        painter.setPen(QColor("black"))
        painter.drawText(55, 184, "Vision range")


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

        self.setWindowTitle("EcoBalance - Ecosystem Simulator")
        self.setGeometry(100, 100, 1450, 850)

        self.title_label = QLabel("EcoBalance Simulator")

        self.tick_label = QLabel("Tick: 0")
        self.plants_label = QLabel("Plants: 0")
        self.berry_label = QLabel("Berry Bushes: 0")
        self.herbivores_label = QLabel("Herbivores: 0")
        self.foxes_label = QLabel("Foxes: 0")

        self.energy_label = QLabel("Average Herbivore Energy: 0")
        self.fox_energy_label = QLabel("Average Fox Energy: 0")
        self.fox_hunger_label = QLabel("Average Fox Hunger: 0")

        self.speed_info_label = QLabel("Average Speed: 0")
        self.vision_info_label = QLabel("Average Vision: 0")
        self.age_info_label = QLabel("Average Herbivore Age: 0")
        self.fox_age_label = QLabel("Average Fox Age: 0")
        self.food_label = QLabel("Average Plant Food: 0")
        self.danger_label = QLabel("Herbivores in Danger: 0")
        self.status_label = QLabel("Status: Paused")

        self.max_plants_label = QLabel("Max Plants: 0")
        self.max_berry_label = QLabel("Max Berry Bushes: 0")
        self.max_herbivores_label = QLabel("Max Herbivores: 0")
        self.max_foxes_label = QLabel("Max Foxes: 0")
        self.min_herbivores_label = QLabel("Min Herbivores: 0")

        self.plants_input = QLineEdit()
        self.plants_input.setPlaceholderText("Plants count")
        self.plants_input.setText("150")

        self.herbivores_input = QLineEdit()
        self.herbivores_input.setPlaceholderText("Herbivores count")
        self.herbivores_input.setText("10")

        self.foxes_input = QLineEdit()
        self.foxes_input.setPlaceholderText("Foxes count")
        self.foxes_input.setText("4")

        self.speed_label = QLabel("Simulation Speed: 50 ms")

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(20)
        self.speed_slider.setMaximum(300)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.change_speed)

        self.vision_checkbox = QCheckBox("Show vision ranges")
        self.vision_checkbox.setChecked(True)
        self.vision_checkbox.toggled.connect(self.change_visual_settings)

        self.bars_checkbox = QCheckBox("Show energy/hunger bars")
        self.bars_checkbox.setChecked(True)
        self.bars_checkbox.toggled.connect(self.change_visual_settings)

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
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "Tick", "Plants", "Berry Bushes", "Herbivores", "Foxes",
            "Avg Herb Energy", "Avg Fox Energy", "Avg Fox Hunger",
            "Avg Speed", "Avg Vision", "Avg Herb Age", "Avg Plant Food",
            "Danger"
        ])
        self.table.setFixedHeight(250)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)

        side_layout = QVBoxLayout()
        side_layout.addWidget(self.title_label)

        side_layout.addWidget(QLabel("Initial Plants:"))
        side_layout.addWidget(self.plants_input)

        side_layout.addWidget(QLabel("Initial Herbivores:"))
        side_layout.addWidget(self.herbivores_input)

        side_layout.addWidget(QLabel("Initial Foxes:"))
        side_layout.addWidget(self.foxes_input)

        side_layout.addWidget(self.apply_button)

        side_layout.addWidget(self.speed_label)
        side_layout.addWidget(self.speed_slider)

        side_layout.addWidget(self.vision_checkbox)
        side_layout.addWidget(self.bars_checkbox)

        side_layout.addWidget(self.tick_label)
        side_layout.addWidget(self.plants_label)
        side_layout.addWidget(self.berry_label)
        side_layout.addWidget(self.herbivores_label)
        side_layout.addWidget(self.foxes_label)

        side_layout.addWidget(self.energy_label)
        side_layout.addWidget(self.fox_energy_label)
        side_layout.addWidget(self.fox_hunger_label)

        side_layout.addWidget(self.speed_info_label)
        side_layout.addWidget(self.vision_info_label)
        side_layout.addWidget(self.age_info_label)
        side_layout.addWidget(self.fox_age_label)
        side_layout.addWidget(self.food_label)
        side_layout.addWidget(self.danger_label)
        side_layout.addWidget(self.status_label)

        side_layout.addWidget(self.max_plants_label)
        side_layout.addWidget(self.max_berry_label)
        side_layout.addWidget(self.max_herbivores_label)
        side_layout.addWidget(self.max_foxes_label)
        side_layout.addWidget(self.min_herbivores_label)

        side_layout.addLayout(buttons_layout)
        side_layout.addWidget(self.save_button)

        side_layout.addWidget(QLabel("Simulation History:"))
        side_layout.addWidget(self.table)

        side_layout.addWidget(QLabel("Shortcuts: Space = Start/Pause, R = Reset, Esc = Close"))
        side_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.canvas)
        main_layout.addLayout(side_layout)

        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(50)

        self.update_labels()

    def start_simulation(self):
        self.engine.start()
        self.status_label.setText("Status: Running")

    def pause_simulation(self):
        self.engine.pause()
        self.status_label.setText("Status: Paused")

    def reset_simulation(self):
        self.engine = SimulationEngine()
        self.canvas.engine = self.engine

        self.max_plants = 0
        self.max_herbivores = 0
        self.min_herbivores = 0
        self.max_berry_bushes = 0
        self.max_foxes = 0
        self.last_fox_count = 0

        self.table.setRowCount(0)

        self.status_label.setText("Status: Reset")
        self.update_labels()
        self.canvas.update()

    def apply_settings(self):
        try:
            plants_count = int(self.plants_input.text())
            herbivores_count = int(self.herbivores_input.text())
            foxes_count = int(self.foxes_input.text())

            if plants_count < 0 or herbivores_count < 0 or foxes_count < 0:
                QMessageBox.warning(self, "Input Error", "Counts must be positive numbers.")
                return

            if plants_count > 1000 or herbivores_count > 200 or foxes_count > 80:
                QMessageBox.warning(self, "Input Error", "Too many organisms. Try smaller numbers.")
                return

            self.engine = SimulationEngine()
            self.engine.pause()

            self.engine.world.plants = []
            self.engine.world.herbivores = []
            self.engine.world.berry_bushes = []
            self.engine.world.foxes = []
            self.engine.current_tick = 0

            for i in range(plants_count):
                self.engine.world.plants.append(
                    Plant(
                        i,
                        random.randint(0, self.engine.world.width),
                        random.randint(0, self.engine.world.height),
                        20
                    )
                )

            for i in range(herbivores_count):
                self.engine.world.herbivores.append(
                    Herbivore(
                        i,
                        random.randint(0, self.engine.world.width),
                        random.randint(0, self.engine.world.height),
                        100,
                        150,
                        0,
                        3,
                        150
                    )
                )

            for i in range(foxes_count):
                self.engine.world.foxes.append(
                    Fox(
                        i,
                        random.randint(0, self.engine.world.width),
                        random.randint(0, self.engine.world.height),
                        100,
                        0,
                        200,
                        0,
                        4,
                        200
                    )
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
        self.canvas.update()

    def get_ecosystem_status(self, plants_count, herbivores_count, foxes_count, danger_count):
        if herbivores_count == 0:
            return "Status: Herbivores extinct"

        if foxes_count == 0 and herbivores_count > 30:
            return "Status: Foxes migrated, reintroduction expected"

        if foxes_count > herbivores_count:
            return "Status: Too many predators"

        if danger_count > herbivores_count / 2:
            return "Status: Herbivores under pressure"

        if plants_count < herbivores_count * 2:
            return "Status: Food shortage"

        return "Status: Balanced"

    def update_simulation(self):
        old_fox_count = self.last_fox_count

        self.engine.update()
        self.update_labels()
        self.canvas.update()

        state = self.engine.get_state()
        foxes_count = state["counts"].get("foxes", 0)

        if old_fox_count == 0 and foxes_count > 0 and self.engine.running:
            self.status_label.setText(f"Status: Foxes have migrated back +{foxes_count}")

        self.last_fox_count = foxes_count

        if self.engine.running and state["counts"]["herbivores"] == 0:
            self.engine.pause()
            self.status_label.setText("Status: Herbivores extinct")
            QMessageBox.information(
                self,
                "Simulation Ended",
                "All herbivores died. Foxes have no food left."
            )
            return

        if self.engine.current_tick % 10 == 0 and self.engine.current_tick != 0:
            self.add_table_row()

    def calculate_statistics(self):
        state = self.engine.get_state()

        plants_count = state["counts"]["plants"]
        herbivores_count = state["counts"]["herbivores"]
        berry_count = state["counts"].get("berry_bushes", 0)
        foxes_count = state["counts"].get("foxes", 0)

        total_energy = 0
        total_speed = 0
        total_vision = 0
        total_age = 0

        total_fox_energy = 0
        total_fox_hunger = 0
        total_fox_age = 0

        total_plant_food = 0
        plant_food_count = 0
        danger_count = 0

        for entity in state["entities"]:
            if entity["type"] == "herbivore":
                total_energy += entity.get("energy", 0)
                total_speed += entity.get("speed", 0)
                total_vision += entity.get("vision", 0)
                total_age += entity.get("age", 0)

                if entity.get("nearest_fox_dist", 9999) < 200:
                    danger_count += 1

            elif entity["type"] == "fox":
                total_fox_energy += entity.get("energy", 0)
                total_fox_hunger += entity.get("hunger", 0)
                total_fox_age += entity.get("age", 0)

            elif entity["type"] == "plant":
                total_plant_food += entity.get("food_value", 0)
                plant_food_count += 1

        if herbivores_count > 0:
            average_energy = total_energy / herbivores_count
            average_speed = total_speed / herbivores_count
            average_vision = total_vision / herbivores_count
            average_age = total_age / herbivores_count
        else:
            average_energy = 0
            average_speed = 0
            average_vision = 0
            average_age = 0

        if foxes_count > 0:
            average_fox_energy = total_fox_energy / foxes_count
            average_fox_hunger = total_fox_hunger / foxes_count
            average_fox_age = total_fox_age / foxes_count
        else:
            average_fox_energy = 0
            average_fox_hunger = 0
            average_fox_age = 0

        if plant_food_count > 0:
            average_food = total_plant_food / plant_food_count
        else:
            average_food = 0

        return (
            state, plants_count, berry_count, herbivores_count, foxes_count,
            average_energy, average_fox_energy, average_fox_hunger,
            average_speed, average_vision, average_age, average_fox_age,
            average_food, danger_count
        )

    def update_labels(self):
        (
            state, plants_count, berry_count, herbivores_count, foxes_count,
            avg_energy, avg_fox_energy, avg_fox_hunger,
            avg_speed, avg_vision, avg_age, avg_fox_age,
            avg_food, danger_count
        ) = self.calculate_statistics()

        if self.min_herbivores == 0 and herbivores_count > 0:
            self.min_herbivores = herbivores_count

        self.max_plants = max(self.max_plants, plants_count)
        self.max_berry_bushes = max(self.max_berry_bushes, berry_count)
        self.max_herbivores = max(self.max_herbivores, herbivores_count)
        self.max_foxes = max(self.max_foxes, foxes_count)

        if herbivores_count > 0:
            self.min_herbivores = min(self.min_herbivores, herbivores_count)

        self.tick_label.setText(f"Tick: {state['tick']}")
        self.plants_label.setText(f"Plants: {plants_count}")
        self.berry_label.setText(f"Berry Bushes: {berry_count}")
        self.herbivores_label.setText(f"Herbivores: {herbivores_count}")
        self.foxes_label.setText(f"Foxes: {foxes_count}")

        self.energy_label.setText(f"Average Herbivore Energy: {avg_energy:.1f}")
        self.fox_energy_label.setText(f"Average Fox Energy: {avg_fox_energy:.1f}")
        self.fox_hunger_label.setText(f"Average Fox Hunger: {avg_fox_hunger:.1f}")

        self.speed_info_label.setText(f"Average Speed: {avg_speed:.2f}")
        self.vision_info_label.setText(f"Average Vision: {avg_vision:.1f}")
        self.age_info_label.setText(f"Average Herbivore Age: {avg_age:.1f}")
        self.fox_age_label.setText(f"Average Fox Age: {avg_fox_age:.1f}")
        self.food_label.setText(f"Average Plant Food: {avg_food:.1f}")
        self.danger_label.setText(f"Herbivores in Danger: {danger_count}")

        ecosystem_status = self.get_ecosystem_status(
            plants_count,
            herbivores_count,
            foxes_count,
            danger_count
        )
        self.status_label.setText(ecosystem_status)

        self.max_plants_label.setText(f"Max Plants: {self.max_plants}")
        self.max_berry_label.setText(f"Max Berry Bushes: {self.max_berry_bushes}")
        self.max_herbivores_label.setText(f"Max Herbivores: {self.max_herbivores}")
        self.max_foxes_label.setText(f"Max Foxes: {self.max_foxes}")
        self.min_herbivores_label.setText(f"Min Herbivores: {self.min_herbivores}")

    def add_table_row(self):
        (
            state, plants_count, berry_count, herbivores_count, foxes_count,
            avg_energy, avg_fox_energy, avg_fox_hunger,
            avg_speed, avg_vision, avg_age, avg_fox_age,
            avg_food, danger_count
        ) = self.calculate_statistics()

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(str(state["tick"])))
        self.table.setItem(row, 1, QTableWidgetItem(str(plants_count)))
        self.table.setItem(row, 2, QTableWidgetItem(str(berry_count)))
        self.table.setItem(row, 3, QTableWidgetItem(str(herbivores_count)))
        self.table.setItem(row, 4, QTableWidgetItem(str(foxes_count)))
        self.table.setItem(row, 5, QTableWidgetItem(f"{avg_energy:.1f}"))
        self.table.setItem(row, 6, QTableWidgetItem(f"{avg_fox_energy:.1f}"))
        self.table.setItem(row, 7, QTableWidgetItem(f"{avg_fox_hunger:.1f}"))
        self.table.setItem(row, 8, QTableWidgetItem(f"{avg_speed:.2f}"))
        self.table.setItem(row, 9, QTableWidgetItem(f"{avg_vision:.1f}"))
        self.table.setItem(row, 10, QTableWidgetItem(f"{avg_age:.1f}"))
        self.table.setItem(row, 11, QTableWidgetItem(f"{avg_food:.1f}"))
        self.table.setItem(row, 12, QTableWidgetItem(str(danger_count)))

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
                    "Tick,Plants,Berry Bushes,Herbivores,Foxes,"
                    "Avg Herbivore Energy,Avg Fox Energy,Avg Fox Hunger,"
                    "Avg Speed,Avg Vision,Avg Herbivore Age,Avg Plant Food,Danger\n"
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
