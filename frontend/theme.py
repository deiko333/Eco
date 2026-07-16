FONT_FAMILY = '"Segoe UI", "Inter", "Noto Sans", Arial, sans-serif'


class Palette:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def light_palette():
    return Palette(
        forest_dark="#14281D",
        forest="#244D36",
        moss="#507A5A",
        sage="#8FAF91",
        sand="#E9E2D0",
        surface="#F7F7F2",
        surface_alt="#FFFFFF",
        lake="#4C8CA6",
        warning="#C9893D",
        danger="#B64B43",
        success="#3F7D53",
        text="#1D2720",
        muted="#6E7A72",
        border="#D8D9CE",
        shadow="rgba(20, 40, 29, 60)",
        panel="#FFFFFF",
        panel_alt="#F1F3EC",
        accent="#2E6B45",
        accent_hover="#357B50",
        accent_pressed="#204F34",
    )


def dark_palette():
    return Palette(
        forest_dark="#0D1912",
        forest="#1B3226",
        moss="#3E6650",
        sage="#6E8F72",
        sand="#C9BEA0",
        surface="#131C16",
        surface_alt="#1A2620",
        lake="#3E7A94",
        warning="#D19A54",
        danger="#C9645B",
        success="#4F9469",
        text="#EAF0E7",
        muted="#95A69B",
        border="#2B3A31",
        shadow="rgba(0, 0, 0, 110)",
        panel="#182420",
        panel_alt="#1F2D26",
        accent="#3E8A5C",
        accent_hover="#489C68",
        accent_pressed="#2E6B45",
    )

def apply_soft_shadow(widget, blur=20, y_offset=5, alpha=45):
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(20, 40, 29, alpha))

    widget.setGraphicsEffect(shadow)

class Theme:
    def __init__(self, mode="light"):
        self.mode = mode
        self.colors = light_palette() if mode == "light" else dark_palette()

    def toggle(self):
        self.mode = "dark" if self.mode == "light" else "light"
        self.colors = light_palette() if self.mode == "light" else dark_palette()
        return self.mode


    def app_stylesheet(self):
        c = self.colors
        return f"""
        QWidget {{
            background-color: {c.surface};
            color: {c.text};
            font-family: {FONT_FAMILY};
            font-size: 13px;
        }}
        QLabel {{ background: transparent; }}
        QToolTip {{
            background-color: {c.forest_dark};
            color: {c.sand};
            border: 1px solid {c.moss};
            padding: 6px 8px;
            border-radius: 6px;
        }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: transparent; width: 10px; margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {c.sage}; border-radius: 5px; min-height: 24px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

        QPushButton {{
            background-color: {c.accent};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {c.accent_hover}; }}
        QPushButton:pressed {{ background-color: {c.accent_pressed}; }}
        QPushButton:disabled {{ background-color: {c.border}; color: {c.muted}; }}
        QPushButton:focus {{ border: 2px solid {c.lake}; }}
        QPushButton#secondaryButton {{
            background-color: transparent;
            color: {c.forest};
            border: 1.5px solid {c.moss};
        }}
        QPushButton#secondaryButton:hover {{ background-color: {c.panel_alt}; }}
        QPushButton#dangerButton {{ background-color: {c.danger}; }}
        QPushButton#dangerButton:hover {{ background-color: #C9645B; }}
        QPushButton#iconButton {{
            background-color: {c.panel_alt};
            color: {c.forest};
            border-radius: 8px;
            padding: 8px;
        }}
        QPushButton#iconButton:hover {{ background-color: {c.sage}; color: white; }}
        QPushButton#iconButton:checked {{ background-color: {c.accent}; color: white; }}

        QLineEdit, QComboBox, QSpinBox {{
            background-color: {c.panel};
            border: 1.5px solid {c.border};
            border-radius: 8px;
            padding: 8px 10px;
            selection-background-color: {c.sage};
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1.5px solid {c.accent}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{
            background-color: {c.panel};
            border: 1px solid {c.border};
            selection-background-color: {c.sage};
            outline: none;
        }}

        QGroupBox {{
            background-color: {c.panel};
            border: 1px solid {c.border};
            border-radius: 12px;
            margin-top: 14px;
            padding: 12px;
            font-weight: 600;
            color: {c.forest_dark};
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; }}

        QTableWidget {{
            background-color: {c.panel};
            border: 1px solid {c.border};
            border-radius: 10px;
            gridline-color: {c.panel_alt};
            selection-background-color: {c.sage};
        }}
        QHeaderView::section {{
            background-color: {c.panel_alt};
            color: {c.forest_dark};
            padding: 6px;
            border: none;
            font-weight: 600;
        }}
        QTextBrowser {{
            background-color: {c.panel};
            border: 1px solid {c.border};
            border-radius: 10px;
            padding: 8px;
        }}
        QProgressBar {{
            border: none;
            border-radius: 6px;
            background-color: {c.panel_alt};
            text-align: center;
            height: 14px;
            color: {c.forest_dark};
        }}
        QProgressBar::chunk {{ background-color: {c.accent}; border-radius: 6px; }}
        QSlider::groove:horizontal {{ height: 6px; background: {c.panel_alt}; border-radius: 3px; }}
        QSlider::handle:horizontal {{ background: {c.accent}; width: 16px; margin: -6px 0; border-radius: 8px; }}
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1.5px solid {c.moss}; background: {c.panel}; }}
        QCheckBox::indicator:checked {{ background: {c.accent}; border: 1.5px solid {c.accent}; }}
        QSplitter::handle {{ background-color: {c.border}; }}
        """

    def card_style(self, accent=None):
        c = self.colors
        border_color = accent or c.border
        return f"""
            background-color: {c.panel};
            border: 1px solid {border_color};
            border-radius: 14px;
        """

    def title_font(self, size=26):
        f = QFontRef(size, True)
        return f


def QFontRef(size, bold):
    from PyQt5.QtGui import QFont
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(size)
    font.setBold(bold)
    return font


STATUS_COLORS = {
    "Balanced": "success",
    "Food Shortage": "warning",
    "Water Stress": "lake",
    "Predator Pressure": "warning",
    "Herbivore Extinction": "danger",
    "Predator Extinction": "warning",
    "Critical Ecosystem": "danger",
}