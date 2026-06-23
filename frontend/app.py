import sys
import random

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QSlider, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor

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
            x = entity["x"]
            y = entity["y"]

            if entity["type"] == "plant":
                painter.setBrush(QColor("green"))
                painter.drawEllipse(x, y, 8, 8)

            elif entity["type"] == "herbivore":
                energy = entity["energy"]

                if energy > 70:
                    painter.setBrush(QColor("gray"))
                elif energy > 30:
                    painter.setBrush(QColor("yellow"))
                else:
                    painter.setBrush(QColor("red"))

                painter.drawEllipse(x, y, 14, 14)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = SimulationEngine()

        self.setWindowTitle("EcoBalance - Ecosystem Simulator")
        self.setGeometry(100, 100, 1300, 850)

        self.title_label = QLabel("EcoBalance Simulator")

        self.tick_label = QLabel("Tick: 0")
        self.plants_label = QLabel("Plants: 0")
        self.herbivores_label = QLabel("Herbivores: 0")
        self.energy_label = QLabel("Average Energy: 0")
        self.status_label = QLabel("Status: Paused")

        self.plants_input = QLineEdit()
        self.plants_input.setPlaceholderText("Plants count")
        self.plants_input.setText("150")

        self.herbivores_input = QLineEdit()
        self.herbivores_input.setPlaceholderText("Herbivores count")
        self.herbivores_input.setText("10")

        self.speed_label = QLabel("Speed: 50 ms")

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

        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)
        self.apply_button.clicked.connect(self.apply_settings)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tick", "Plants", "Herbivores", "Avg Energy"])
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
        side_layout.addWidget(self.status_label)

        side_layout.addLayout(buttons_layout)

        side_layout.addWidget(QLabel("Simulation History:"))
        side_layout.addWidget(self.table)

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

        self.table.setRowCount(0)

        self.status_label.setText("Status: Reset")
        self.update_labels()
        self.canvas.update()

    def apply_settings(self):
        try:
            plants_count = int(self.plants_input.text())
            herbivores_count = int(self.herbivores_input.text())

            if plants_count < 0 or herbivores_count < 0:
                self.status_label.setText("Status: Count must be positive")
                return

            self.engine = SimulationEngine()
            self.engine.pause()

            self.engine.world.plants = []
            self.engine.world.herbivores = []

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

            self.status_label.setText("Status: Settings Applied")
            self.update_labels()
            self.canvas.update()

        except ValueError:
            self.status_label.setText("Status: Please enter valid numbers")

    def change_speed(self):
        value = self.speed_slider.value()
        self.timer.setInterval(value)
        self.speed_label.setText(f"Speed: {value} ms")

    def update_simulation(self):
        self.engine.update()
        self.update_labels()
        self.canvas.update()

        if self.engine.current_tick % 10 == 0 and self.engine.current_tick != 0:
            self.add_table_row()

    def update_labels(self):
        state = self.engine.get_state()

        plants_count = state["counts"]["plants"]
        herbivores_count = state["counts"]["herbivores"]

        total_energy = 0

        for entity in state["entities"]:
            if entity["type"] == "herbivore":
                total_energy += entity["energy"]

        if herbivores_count > 0:
            average_energy = total_energy / herbivores_count
        else:
            average_energy = 0

        self.tick_label.setText(f"Tick: {state['tick']}")
        self.plants_label.setText(f"Plants: {plants_count}")
        self.herbivores_label.setText(f"Herbivores: {herbivores_count}")
        self.energy_label.setText(f"Average Energy: {average_energy:.1f}")

    def add_table_row(self):
        state = self.engine.get_state()

        plants_count = state["counts"]["plants"]
        herbivores_count = state["counts"]["herbivores"]

        total_energy = 0

        for entity in state["entities"]:
            if entity["type"] == "herbivore":
                total_energy += entity["energy"]

        if herbivores_count > 0:
            average_energy = total_energy / herbivores_count
        else:
            average_energy = 0

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(str(state["tick"])))
        self.table.setItem(row, 1, QTableWidgetItem(str(plants_count)))
        self.table.setItem(row, 2, QTableWidgetItem(str(herbivores_count)))
        self.table.setItem(row, 3, QTableWidgetItem(f"{average_energy:.1f}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
