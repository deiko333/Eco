from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QComboBox, QGroupBox, QSlider
)

from services.save_manager import PRESETS, SAFE_LIMITS
from frontend.dialogs import show_error

MAP_THEMES = ["Temperate Forest", "Pine Forest", "Meadow", "Autumn Woodland"]


class SetupPage(QWidget):
    start_requested = pyqtSignal(dict)
    back_requested = pyqtSignal()

    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self._build()

    def _build(self):
        c = self.theme.colors
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 30, 60, 30)
        root.setSpacing(14)

        header = QLabel("New Simulation Setup")
        header.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {c.forest_dark};")
        root.addWidget(header)

        content = QHBoxLayout()
        root.addLayout(content, stretch=1)

        counts_box = QGroupBox("Ecosystem Composition")
        grid = QGridLayout(counts_box)
        self.spinboxes = {}
        labels = [
            ("plants", "Plants", 150), ("berry_bushes", "Berry Bushes", 15),
            ("herbivores", "Herbivores", 10), ("foxes", "Foxes", 4),
            ("water_sources", "Water Sources", 5), ("shelters", "Shelters", 4),
        ]
        for row, (key, label, default) in enumerate(labels):
            lo, hi = SAFE_LIMITS[key]
            grid.addWidget(QLabel(label), row, 0)
            spin = QSpinBox()
            spin.setRange(lo, hi)
            spin.setValue(default)
            grid.addWidget(spin, row, 1)
            self.spinboxes[key] = spin
        content.addWidget(counts_box, stretch=1)

        options_box = QGroupBox("Simulation Options")
        opt_layout = QGridLayout(options_box)
        opt_layout.addWidget(QLabel("Initial Season"), 0, 0)
        self.season_combo = QComboBox()
        self.season_combo.addItems(["spring", "summer", "autumn", "winter"])
        self.season_combo.setCurrentText("summer")
        opt_layout.addWidget(self.season_combo, 0, 1)

        opt_layout.addWidget(QLabel("Map Theme"), 1, 0)
        self.map_theme_combo = QComboBox()
        self.map_theme_combo.addItems(MAP_THEMES)
        opt_layout.addWidget(self.map_theme_combo, 1, 1)

        opt_layout.addWidget(QLabel("Simulation Speed"), 2, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(20, 300)
        self.speed_slider.setValue(50)
        opt_layout.addWidget(self.speed_slider, 2, 1)

        opt_layout.addWidget(QLabel("Save Name"), 3, 0)
        self.save_name_input = QLineEdit("My Ecosystem")
        opt_layout.addWidget(self.save_name_input, 3, 1)

        opt_layout.addWidget(QLabel("Load Preset"), 4, 0)
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Custom")
        self.preset_combo.addItems(list(PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        opt_layout.addWidget(self.preset_combo, 4, 1)

        content.addWidget(options_box, stretch=1)

        button_row = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("secondaryButton")
        self.start_button = QPushButton("Start Simulation")
        button_row.addWidget(self.back_button)
        button_row.addStretch()
        button_row.addWidget(self.start_button)
        root.addLayout(button_row)

        self.back_button.clicked.connect(self.back_requested.emit)
        self.start_button.clicked.connect(self._start_clicked)

    def _apply_preset(self, name):
        if name not in PRESETS:
            return
        for key, value in PRESETS[name].items():
            if key in self.spinboxes:
                self.spinboxes[key].setValue(value)

    def _start_clicked(self):
        counts = {key: spin.value() for key, spin in self.spinboxes.items()}
        save_name = self.save_name_input.text().strip() or "Untitled Simulation"
        config = dict(
            counts=counts,
            season=self.season_combo.currentText(),
            speed=self.speed_slider.value(),
            save_name=save_name,
            map_theme=self.map_theme_combo.currentText(),
        )
        self.start_requested.emit(config)
