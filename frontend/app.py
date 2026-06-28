import sys
import random

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QSlider, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QPen

from backend.engine import SimulationEngine, Plant, Herbivore


class EcosystemCanvas(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setFixedSize(1000, 700)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#E8F5E9"))

        state = self.engine.get_state()

        for entity in state["entities"]:
            x = int(entity["x"])
            y = int(entity["y"])

            if entity["type"] == "plant":
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("green"))
                painter.drawEllipse(x, y, 8, 8)

            elif entity["type"] == "herbivore":
                energy = entity["energy"]
                vision = int(entity.get("vision", 0))

                painter.setPen(QPen(QColor(120, 120, 120, 50), 1))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(x - vision, y - vision, vision * 2, vision * 2)

                painter.setPen(Qt.NoPen)

                if energy > 120:
                    painter.setBrush(QColor("gray"))
                elif energy > 50:
                    painter.setBrush(QColor("yellow"))
                else:
                    painter.setBrush(QColor("red"))

                painter.drawEllipse(x, y, 14, 14)

        self.draw_legend(painter)

    def draw_legend(self, painter):
        painter.setPen(QColor("black"))

        painter.setBrush(QColor("green"))
        painter.drawEllipse(20, 20, 10, 10)
        painter.drawText(40, 30, "Plant")

        painter.setBrush(QColor("gray"))
        painter.drawEllipse(20, 45, 12, 12)
        painter.drawText(40, 55, "Herbivore - high energy")

        painter.setBrush(QColor("yellow"))
        painter.drawEllipse(20, 70, 12, 12)
        painter.drawText(40, 80, "Herbivore - medium energy")

        painter.setBrush(QColor("red"))
        painter.drawEllipse(20, 95, 12, 12)
        painter.drawText(40, 105, "Herbivore - low energy")

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawEllipse(20, 120, 14, 14)
        painter.setPen(QColor("black"))
        painter.drawText(40, 132, "Vision range")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = SimulationEngine()

        self.max_plants = 0
        self.max_herbivores = 0
        self.min_herbivores = 0

        self.setWindowTitle("EcoBalance - Ecosystem Simulator")
        self.setGeometry(100, 100, 1350, 850)

        self.title_label = QLabel("EcoBalance Simulator")

        self.tick_label = QLabel("Tick: 0")
        self.plants_label = QLabel("Plants: 0")
        self.herbivores_label = QLabel("Herbivores: 0")
        self.energy_label = QLabel("Average Energy: 0")
        self.speed_info_label = QLabel("Average Speed: 0")
        self.vision_info_label = QLabel("Average Vision: 0")
        self.age_info_label = QLabel("Average Age: 0")
        self.status_label = QLabel("Status: Paused")

        self.max_plants_label = QLabel("Max Plants: 0")
        self.max_herbivores_label = QLabel("Max Herbivores: 0")
        self.min_herbivores_label = QLabel("Min Herbivores: 0")

        self.plants_input = QLineEdit()
        self.plants_input.setPlaceholderText("Plants count")
        self.plants_input.setText("150")

        self.herbivores_input = QLineEdit()
        self.herbivores_input.setPlaceholderText("Herbivores count")
        self.herbivores_input.setText("10")

        self.speed_label = QLabel("Simulation Speed: 50 ms")

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(20)
        self.speed_slider.setMaximum(300)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.change_speed)

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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tick", "Plants", "Herbivores", "Avg Energy",
            "Avg Speed", "Avg Vision", "Avg Age"
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

        side_layout.addWidget(self.apply_button)

        side_layout.addWidget(self.speed_label)
        side_layout.addWidget(self.speed_slider)

        side_layout.addWidget(self.tick_label)
        side_layout.addWidget(self.plants_label)
        side_layout.addWidget(self.herbivores_label)
        side_layout.addWidget(self.energy_label)
        side_layout.addWidget(self.speed_info_label)
        side_layout.addWidget(self.vision_info_label)
        side_layout.addWidget(self.age_info_label)
        side_layout.addWidget(self.status_label)

        side_layout.addWidget(self.max_plants_label)
        side_layout.addWidget(self.max_herbivores_label)
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

        self.table.setRowCount(0)

        self.status_label.setText("Status: Reset")
        self.update_labels()
        self.canvas.update()

    def apply_settings(self):
        try:
            plants_count = int(self.plants_input.text())
            herbivores_count = int(self.herbivores_input.text())

            if plants_count < 0 or herbivores_count < 0:
                QMessageBox.warning(self, "Input Error", "Counts must be positive numbers.")
                return

            if plants_count > 1000 or herbivores_count > 200:
                QMessageBox.warning(self, "Input Error", "Too many organisms. Try smaller numbers.")
                return

            self.engine = SimulationEngine()
            self.engine.pause()

            self.engine.world.plants = []
            self.engine.world.herbivores = []
            self.engine.current_tick = 0

            for i in range(plants_count):
                self.engine.world.plants.append(
                    Plant(
                        i,
                        random.randint(0, self.engine.world.width),
                        random.randint(0, self.engine.world.height),
                        10
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
                        100
                    )
                )

            self.canvas.engine = self.engine
            self.table.setRowCount(0)

            self.max_plants = plants_count
            self.max_herbivores = herbivores_count
            self.min_herbivores = herbivores_count

            self.status_label.setText("Status: Settings Applied")
            self.update_labels()
            self.canvas.update()

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid integer numbers.")

    def change_speed(self):
        value = self.speed_slider.value()
        self.timer.setInterval(value)
        self.speed_label.setText(f"Simulation Speed: {value} ms")

    def update_simulation(self):
        self.engine.update()
        self.update_labels()
        self.canvas.update()

        state = self.engine.get_state()

        if self.engine.running and state["counts"]["herbivores"] == 0:
            self.engine.pause()
            self.status_label.setText("Status: Simulation stopped - herbivores died")
            QMessageBox.information(self, "Simulation Ended", "All herbivores died.")
            return

        if self.engine.current_tick % 10 == 0 and self.engine.current_tick != 0:
            self.add_table_row()

    def calculate_statistics(self):
        state = self.engine.get_state()

        plants_count = state["counts"]["plants"]
        herbivores_count = state["counts"]["herbivores"]

        total_energy = 0
        total_speed = 0
        total_vision = 0
        total_age = 0

        for entity in state["entities"]:
            if entity["type"] == "herbivore":
                total_energy += entity.get("energy", 0)
                total_speed += entity.get("speed", 0)
                total_vision += entity.get("vision", 0)
                total_age += entity.get("age", 0)

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

        return state, plants_count, herbivores_count, average_energy, average_speed, average_vision, average_age

    def update_labels(self):
        state, plants_count, herbivores_count, avg_energy, avg_speed, avg_vision, avg_age = self.calculate_statistics()

        if self.min_herbivores == 0 and herbivores_count > 0:
            self.min_herbivores = herbivores_count

        self.max_plants = max(self.max_plants, plants_count)
        self.max_herbivores = max(self.max_herbivores, herbivores_count)

        if herbivores_count > 0:
            self.min_herbivores = min(self.min_herbivores, herbivores_count)

        self.tick_label.setText(f"Tick: {state['tick']}")
        self.plants_label.setText(f"Plants: {plants_count}")
        self.herbivores_label.setText(f"Herbivores: {herbivores_count}")
        self.energy_label.setText(f"Average Energy: {avg_energy:.1f}")
        self.speed_info_label.setText(f"Average Speed: {avg_speed:.2f}")
        self.vision_info_label.setText(f"Average Vision: {avg_vision:.1f}")
        self.age_info_label.setText(f"Average Age: {avg_age:.1f}")

        self.max_plants_label.setText(f"Max Plants: {self.max_plants}")
        self.max_herbivores_label.setText(f"Max Herbivores: {self.max_herbivores}")
        self.min_herbivores_label.setText(f"Min Herbivores: {self.min_herbivores}")

    def add_table_row(self):
        state, plants_count, herbivores_count, avg_energy, avg_speed, avg_vision, avg_age = self.calculate_statistics()

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(str(state["tick"])))
        self.table.setItem(row, 1, QTableWidgetItem(str(plants_count)))
        self.table.setItem(row, 2, QTableWidgetItem(str(herbivores_count)))
        self.table.setItem(row, 3, QTableWidgetItem(f"{avg_energy:.1f}"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{avg_speed:.2f}"))
        self.table.setItem(row, 5, QTableWidgetItem(f"{avg_vision:.1f}"))
        self.table.setItem(row, 6, QTableWidgetItem(f"{avg_age:.1f}"))

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
                file.write("Tick,Plants,Herbivores,Avg Energy,Avg Speed,Avg Vision,Avg Age\n")

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
