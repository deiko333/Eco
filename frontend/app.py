import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPainter, QColor

from backend.engine import SimulationEngine


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

            elif entity["type"] == "rabbit":
                painter.setBrush(QColor("gray"))
                painter.drawEllipse(x, y, 14, 14)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.engine = SimulationEngine()

        self.setWindowTitle("EcoBalance - Ecosystem Simulator")
        self.setGeometry(100, 100, 1200, 800)

        self.title_label = QLabel("EcoBalance Simulator")
        self.tick_label = QLabel("Tick: 0")
        self.plants_label = QLabel("Plants: 0")
        self.herbivores_label = QLabel("Herbivores: 0")

        self.canvas = EcosystemCanvas(self.engine)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")

        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)

        side_layout = QVBoxLayout()
        side_layout.addWidget(self.title_label)
        side_layout.addWidget(self.tick_label)
        side_layout.addWidget(self.plants_label)
        side_layout.addWidget(self.herbivores_label)
        side_layout.addLayout(buttons_layout)
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

    def pause_simulation(self):
        self.engine.pause()

    def reset_simulation(self):
        self.engine = SimulationEngine()
        self.canvas.engine = self.engine
        self.update_labels()
        self.canvas.update()

    def update_simulation(self):
        self.engine.update()
        self.update_labels()
        self.canvas.update()

    def update_labels(self):
        state = self.engine.get_state()

        plants_count = 0
        herbivores_count = 0

        for entity in state["entities"]:
            if entity["type"] == "plant":
                plants_count += 1
            elif entity["type"] == "herbivore":
                herbivores_count += 1

        self.tick_label.setText(f"Tick: {state['tick']}")
        self.plants_label.setText(f"Plants: {plants_count}")
        self.herbivores_label.setText(f"Herbivores: {herbivores_count}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())