from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QCheckBox, QGroupBox, QGridLayout, QSpinBox
)

DEFAULT_SETTINGS = {
    "theme": "light",
    "map_quality": "high",
    "show_vision_ranges": True,
    "show_status_bars": True,
    "show_entity_labels": False,
    "show_weather_particles": True,
    "graph_update_frequency": 5,
    "autosave_interval_ticks": 200,
    "sound_enabled": True,
    "fullscreen": False,
}


class SettingsPage(QWidget):
    back_requested = pyqtSignal()
    settings_changed = pyqtSignal(dict)

    def __init__(self, theme, database):
        super().__init__()
        self.theme = theme
        self.db = database
        self.current_user = None
        self.settings = dict(DEFAULT_SETTINGS)
        self._build()

    def _build(self):
        c = self.theme.colors
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 30, 60, 30)
        root.setSpacing(14)

        header = QLabel("Settings")
        header.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {c.forest_dark};")
        root.addWidget(header)

        box = QGroupBox("Application Settings")
        grid = QGridLayout(box)
        row = 0

        grid.addWidget(QLabel("Theme"), row, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        grid.addWidget(self.theme_combo, row, 1)
        row += 1

        grid.addWidget(QLabel("Map Visual Quality"), row, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["low", "medium", "high"])
        grid.addWidget(self.quality_combo, row, 1)
        row += 1

        self.vision_checkbox = QCheckBox("Show vision ranges by default")
        grid.addWidget(self.vision_checkbox, row, 0, 1, 2)
        row += 1
        self.bars_checkbox = QCheckBox("Show status bars by default")
        grid.addWidget(self.bars_checkbox, row, 0, 1, 2)
        row += 1
        self.labels_checkbox = QCheckBox("Show entity labels by default")
        grid.addWidget(self.labels_checkbox, row, 0, 1, 2)
        row += 1
        self.particles_checkbox = QCheckBox("Show weather particles by default")
        grid.addWidget(self.particles_checkbox, row, 0, 1, 2)
        row += 1

        grid.addWidget(QLabel("Graph Update Frequency (ticks)"), row, 0)
        self.graph_freq_spin = QSpinBox()
        self.graph_freq_spin.setRange(1, 50)
        grid.addWidget(self.graph_freq_spin, row, 1)
        row += 1

        grid.addWidget(QLabel("Auto-Save Interval (ticks)"), row, 0)
        self.autosave_spin = QSpinBox()
        self.autosave_spin.setRange(0, 2000)
        self.autosave_spin.setSpecialValueText("Disabled")
        grid.addWidget(self.autosave_spin, row, 1)
        row += 1

        self.sound_checkbox = QCheckBox("Sound effects (soft clicks & chimes)")
        grid.addWidget(self.sound_checkbox, row, 0, 1, 2)
        row += 1

        self.fullscreen_checkbox = QCheckBox("Launch in fullscreen")
        grid.addWidget(self.fullscreen_checkbox, row, 0, 1, 2)
        row += 1

        root.addWidget(box)
        root.addStretch()

        button_row = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("secondaryButton")
        self.save_button = QPushButton("Save Settings")
        button_row.addWidget(self.back_button)
        button_row.addStretch()
        button_row.addWidget(self.save_button)
        root.addLayout(button_row)

        self.back_button.clicked.connect(self.back_requested.emit)
        self.save_button.clicked.connect(self._save_clicked)

    def set_user(self, user):
        self.current_user = user
        stored = self.db.load_settings(user["id"]) if user else {}
        self.settings = {**DEFAULT_SETTINGS, **stored}
        self._apply_to_widgets()

    def _apply_to_widgets(self):
        s = self.settings
        self.theme_combo.setCurrentText(s["theme"])
        self.quality_combo.setCurrentText(s["map_quality"])
        self.vision_checkbox.setChecked(s["show_vision_ranges"])
        self.bars_checkbox.setChecked(s["show_status_bars"])
        self.labels_checkbox.setChecked(s["show_entity_labels"])
        self.particles_checkbox.setChecked(s["show_weather_particles"])
        self.graph_freq_spin.setValue(s["graph_update_frequency"])
        self.autosave_spin.setValue(s["autosave_interval_ticks"])
        self.sound_checkbox.setChecked(s["sound_enabled"])
        self.fullscreen_checkbox.setChecked(s["fullscreen"])

    def _save_clicked(self):
        self.settings = dict(
            theme=self.theme_combo.currentText(),
            map_quality=self.quality_combo.currentText(),
            show_vision_ranges=self.vision_checkbox.isChecked(),
            show_status_bars=self.bars_checkbox.isChecked(),
            show_entity_labels=self.labels_checkbox.isChecked(),
            show_weather_particles=self.particles_checkbox.isChecked(),
            graph_update_frequency=self.graph_freq_spin.value(),
            autosave_interval_ticks=self.autosave_spin.value(),
            sound_enabled=self.sound_checkbox.isChecked(),
            fullscreen=self.fullscreen_checkbox.isChecked(),
        )
        if self.current_user:
            self.db.save_settings(self.current_user["id"], self.settings)
        self.settings_changed.emit(self.settings)
