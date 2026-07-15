from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame


def ecosystem_status(stats):
    if stats["herbivores"] == 0:
        return "Herbivore Extinction"
    if stats["foxes"] == 0 and stats["herbivores"] > 30:
        return "Predator Extinction"
    if stats["avg_herbivore_thirst"] > 220 or stats["avg_fox_thirst"] > 260:
        return "Water Stress"
    if stats["foxes"] > 0 and stats["herbivores"] > 0 and stats["foxes"] > stats["herbivores"] / 2:
        return "Predator Pressure"
    if stats["plants"] < stats["herbivores"] * 2:
        return "Food Shortage"
    if stats["herbivores"] == 0 and stats["foxes"] == 0:
        return "Critical Ecosystem"
    return "Balanced"


STATUS_MESSAGES = {
    "Balanced": "The ecosystem is stable.",
    "Food Shortage": "Vegetation is struggling to keep up with herbivores.",
    "Water Stress": "Average thirst levels are dangerously high.",
    "Predator Pressure": "Foxes are outnumbering the herbivore population's ability to sustain them.",
    "Herbivore Extinction": "All herbivores have died out.",
    "Predator Extinction": "Foxes have vanished while herbivores thrive.",
    "Critical Ecosystem": "Multiple species are near collapse.",
}


class StatCard(QFrame):
    def __init__(self, theme, title, icon_pixmap=None):
        super().__init__()
        self.theme = theme
        self.setStyleSheet(theme.card_style())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        if icon_pixmap is not None:
            icon_label = QLabel()
            icon_label.setPixmap(icon_pixmap)
            icon_label.setFixedSize(icon_pixmap.size())
            layout.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {theme.colors.muted}; font-size: 11px; font-weight: 600;")
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"color: {theme.colors.text}; font-size: 19px; font-weight: 700;")
        text_col.addWidget(self.title_label)
        text_col.addWidget(self.value_label)
        layout.addLayout(text_col, stretch=1)

    def set_value(self, value, color=None):
        self.value_label.setText(str(value))
        if color:
            self.value_label.setStyleSheet(f"color: {color}; font-size: 19px; font-weight: 700;")


class StatusBanner(QFrame):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.status_label = QLabel("Balanced")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: 700; color: white;")
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("font-size: 11.5px; color: rgba(255,255,255,0.85);")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addWidget(self.detail_label)
        self.set_status("Balanced")

    def set_status(self, status):
        c = self.theme.colors
        color = {
            "Balanced": c.success,
            "Food Shortage": c.warning,
            "Water Stress": c.lake,
            "Predator Pressure": c.warning,
            "Herbivore Extinction": c.danger,
            "Predator Extinction": c.warning,
            "Critical Ecosystem": c.danger,
        }.get(status, c.forest)
        self.setStyleSheet(f"background-color: {color}; border-radius: 12px;")
        self.status_label.setText(status)
        self.detail_label.setText(STATUS_MESSAGES.get(status, ""))


class SelectionDetailCard(QFrame):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setStyleSheet(theme.card_style())
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.title_label = QLabel("No selection")
        self.title_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {theme.colors.forest_dark};")
        self.layout.addWidget(self.title_label)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(14)
        self.layout.addLayout(self.grid)
        self._rows = []

    def clear(self):
        self.title_label.setText("No selection")
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._rows = []

    def show_entity(self, entity):
        self.clear()
        etype = entity.get("type", "entity")
        self.title_label.setText(f"{etype.replace('_', ' ').title()}  #{entity.get('id', '')}")

        fields = self._fields_for(entity)
        for row, (label, value) in enumerate(fields):
            l1 = QLabel(label)
            l1.setStyleSheet(f"color: {self.theme.colors.muted}; font-size: 11.5px;")
            l2 = QLabel(str(value))
            l2.setStyleSheet(f"color: {self.theme.colors.text}; font-size: 12.5px; font-weight: 600;")
            self.grid.addWidget(l1, row, 0)
            self.grid.addWidget(l2, row, 1)

    def _fields_for(self, e):
        t = e["type"]
        if t == "herbivore":
            return [
                ("Age", f"{e.get('age', 0)} / {e.get('max_age', '?')}"),
                ("Energy", f"{e.get('energy', 0):.0f}"),
                ("Thirst", f"{e.get('thirst', 0):.0f}"),
                ("Speed", f"{e.get('speed', 0):.2f}"),
                ("Vision", f"{e.get('vision', 0):.0f}"),
                ("Nearest fox", f"{e.get('nearest_fox_dist', 'n/a')}"),
                ("Drinking", "Yes" if e.get("is_drinking") else "No"),
            ]
        if t == "fox":
            return [
                ("Age", f"{e.get('age', 0)} / {e.get('max_age', '?')}"),
                ("Energy", f"{e.get('energy', 0):.0f}"),
                ("Hunger", f"{e.get('hunger', 0):.0f}"),
                ("Thirst", f"{e.get('thirst', 0):.0f}"),
                ("Vision", f"{e.get('vision', 0):.0f}"),
                ("Hunting", "Yes" if e.get("is_hunting") else "No"),
            ]
        if t == "plant":
            return [("Age", e.get("age", 0)), ("Food value", e.get("food_value", 0))]
        if t == "berry_bush":
            return [("Food value", e.get("food_value", 0))]
        if t == "water":
            return [("Radius", e.get("radius", 0))]
        if t == "shelter":
            return [("Radius", e.get("radius", 0))]
        return []
