from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QLinearGradient, QPalette, QBrush, QColor


class StartPage(QWidget):
    new_simulation_requested = pyqtSignal()
    continue_requested = pyqtSignal()
    history_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, theme, assets):
        super().__init__()
        self.theme = theme
        self.assets = assets
        self._build()

    def _build(self):
        c = self.theme.colors
        self.setAutoFillBackground(True)
        self._paint_background()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch(2)

        logo_label = QLabel()
        logo_label.setPixmap(self.assets.get_pixmap("icons", "logo", size=110))
        logo_label.setAlignment(Qt.AlignCenter)
        root.addWidget(logo_label)

        title = QLabel("EcoBalance")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 42px; font-weight: 800; color: {c.forest_dark}; letter-spacing: 1px;")
        root.addWidget(title)

        subtitle = QLabel("E C O S Y S T E M   S I M U L A T O R")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 13px; color: {c.muted}; font-weight: 600;")
        root.addWidget(subtitle)

        root.addSpacing(30)

        button_col = QVBoxLayout()
        button_col.setSpacing(12)
        button_col.setAlignment(Qt.AlignCenter)

        self.new_button = QPushButton("New Simulation")
        self.continue_button = QPushButton("Continue Simulation")
        self.history_button = QPushButton("Simulation History")
        self.history_button.setObjectName("secondaryButton")
        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("secondaryButton")
        self.exit_button = QPushButton("Exit")
        self.exit_button.setObjectName("dangerButton")

        for b in (self.new_button, self.continue_button, self.history_button, self.settings_button, self.exit_button):
            b.setFixedWidth(280)
            b.setFixedHeight(46)
            button_col.addWidget(b, alignment=Qt.AlignCenter)

        wrapper = QWidget()
        wrapper.setLayout(button_col)
        root.addWidget(wrapper)

        root.addStretch(3)

        footer = QFrame()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 10, 24, 14)
        version_label = QLabel("EcoBalance v1.0")
        authors_label = QLabel("Developed as a university final project")
        authors_label.setAlignment(Qt.AlignCenter)
        project_label = QLabel("University Final Project")
        project_label.setAlignment(Qt.AlignRight)
        for lbl in (version_label, authors_label, project_label):
            lbl.setStyleSheet(f"color: {c.muted}; font-size: 11px;")
        footer_layout.addWidget(version_label)
        footer_layout.addWidget(authors_label, stretch=1)
        footer_layout.addWidget(project_label)
        root.addWidget(footer)

        self.new_button.clicked.connect(self.new_simulation_requested.emit)
        self.continue_button.clicked.connect(self.continue_requested.emit)
        self.history_button.clicked.connect(self.history_requested.emit)
        self.settings_button.clicked.connect(self.settings_requested.emit)
        self.exit_button.clicked.connect(self.exit_requested.emit)

    def _paint_background(self):
        c = self.theme.colors
        palette = self.palette()
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, QColor(c.sand))
        gradient.setColorAt(0.55, QColor(c.sage))
        gradient.setColorAt(1.0, QColor(c.forest))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

    def set_continue_enabled(self, enabled):
        self.continue_button.setEnabled(enabled)
        self.continue_button.setToolTip("" if enabled else "No saved simulation found for this profile yet.")

    def refresh_theme(self):
        self._paint_background()
