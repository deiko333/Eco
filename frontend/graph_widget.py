from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

HISTORY_LIMIT = 160


class GraphWidget(QWidget):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.mode = "population"
        self.ticks = []
        self.series = {
            "plants": [], "berry_bushes": [], "herbivores": [], "foxes": [],
            "avg_herbivore_energy": [], "avg_fox_energy": [],
            "avg_herbivore_thirst": [], "avg_fox_hunger": [], "avg_fox_thirst": [],
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Population", "Average Energy", "Thirst / Hunger"])
        self.mode_selector.currentIndexChanged.connect(self._on_mode_changed)
        layout.addWidget(self.mode_selector)

        c = theme.colors
        self.figure = Figure(figsize=(5, 2.6))
        self.figure.patch.set_alpha(0)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent;")
        layout.addWidget(self.canvas)
        self._style_axes(c)
        self.redraw()

    def _on_mode_changed(self, index):
        self.mode = ["population", "energy", "thirst"][index]
        self.redraw()

    def _style_axes(self, c):
        self.axes.set_facecolor("none")
        for spine in self.axes.spines.values():
            spine.set_color(c.border)
        self.axes.tick_params(colors=c.muted, labelsize=8)
        self.axes.xaxis.label.set_color(c.muted)
        self.axes.yaxis.label.set_color(c.muted)

    def add_point(self, stats):
        self.ticks.append(stats["tick"])
        self.series["plants"].append(stats["plants"])
        self.series["berry_bushes"].append(stats["berry_bushes"])
        self.series["herbivores"].append(stats["herbivores"])
        self.series["foxes"].append(stats["foxes"])
        self.series["avg_herbivore_energy"].append(stats["avg_herbivore_energy"])
        self.series["avg_fox_energy"].append(stats["avg_fox_energy"])
        self.series["avg_herbivore_thirst"].append(stats["avg_herbivore_thirst"])
        self.series["avg_fox_hunger"].append(stats["avg_fox_hunger"])
        self.series["avg_fox_thirst"].append(stats["avg_fox_thirst"])
        if len(self.ticks) > HISTORY_LIMIT:
            self.ticks = self.ticks[-HISTORY_LIMIT:]
            for k in self.series:
                self.series[k] = self.series[k][-HISTORY_LIMIT:]
        self.redraw()

    def reset(self):
        self.ticks = []
        for k in self.series:
            self.series[k] = []
        self.redraw()

    def redraw(self):
        c = self.theme.colors
        self.axes.clear()
        self._style_axes(c)
        if self.mode == "population":
            self.axes.plot(self.ticks, self.series["plants"], label="Plants", color=c.forest)
            self.axes.plot(self.ticks, self.series["berry_bushes"], label="Berry bushes", color="#8E5FA8")
            self.axes.plot(self.ticks, self.series["herbivores"], label="Herbivores", color=c.sand if self.theme.mode == "dark" else "#B08245")
            self.axes.plot(self.ticks, self.series["foxes"], label="Foxes", color=c.danger)
        elif self.mode == "energy":
            self.axes.plot(self.ticks, self.series["avg_herbivore_energy"], label="Herbivore energy", color=c.success)
            self.axes.plot(self.ticks, self.series["avg_fox_energy"], label="Fox energy", color=c.danger)
        else:
            self.axes.plot(self.ticks, self.series["avg_herbivore_thirst"], label="Herbivore thirst", color=c.lake)
            self.axes.plot(self.ticks, self.series["avg_fox_hunger"], label="Fox hunger", color=c.warning)
            self.axes.plot(self.ticks, self.series["avg_fox_thirst"], label="Fox thirst", color=c.danger)

        self.axes.grid(True, alpha=0.15, color=c.muted)
        if self.ticks:
            legend = self.axes.legend(loc="upper left", fontsize=7.5, frameon=False)
            for text in legend.get_texts():
                text.set_color(c.muted)
        self.figure.tight_layout()
        self.canvas.draw_idle()
