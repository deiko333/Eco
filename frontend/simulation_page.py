from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSplitter,
    QGroupBox, QCheckBox, QSlider, QScrollArea, QTextBrowser, QSizePolicy,
    QGridLayout, QProgressBar
)
from frontend.ecosystem_scene import EcosystemScene, EcosystemView
from frontend.statistics_panel import StatCard, StatusBanner, SelectionDetailCard, ecosystem_status
from frontend.graph_widget import GraphWidget
from frontend.dialogs import confirm, show_info
from frontend.icon_button import IconButton

SEASON_ORDER = ["spring", "summer", "autumn", "winter"]


class SimulationPage(QWidget):
    back_to_menu_requested = pyqtSignal()
    save_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, theme, assets):
        super().__init__()
        self.theme = theme
        self.assets = assets
        self.engine = None
        self.save_name = "Untitled Simulation"
        self.snapshot_callback = None
        self.graph_callback = None 
        self.last_season = "summer"
        self.last_fox_count = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self._build_sidebar())
        main_splitter.addWidget(self._build_map())
        main_splitter.addWidget(self._build_insights())
        main_splitter.setSizes([260, 900, 340])
        root.addWidget(main_splitter, stretch=1)

        root.addWidget(self._build_bottom())

    def _build_topbar(self):
        c = self.theme.colors
        bar = QWidget()
        bar.setFixedHeight(58)
        bar.setStyleSheet(f"background-color: {c.forest_dark};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 6, 14, 6)

        logo = QLabel()
        logo.setPixmap(self.assets.get_pixmap("icons", "logo", size=36))
        layout.addWidget(logo)

        self.title_label = QLabel("EcoBalance")
        self.title_label.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        layout.addWidget(self.title_label)

        self.save_name_label = QLabel(self.save_name)
        self.save_name_label.setStyleSheet(f"color: {c.sand}; font-size: 12px; padding-left: 12px;")
        layout.addWidget(self.save_name_label)
        layout.addStretch()

        self.tick_label = QLabel("Tick: 0")
        self.season_label = QLabel("Season: summer")
        for lbl in (self.tick_label, self.season_label):
            lbl.setStyleSheet("color: white; font-size: 12.5px; font-weight: 600; padding: 0 10px;")
            layout.addWidget(lbl)

        self.start_button = self._icon_button("play", "Start")
        self.pause_button = self._icon_button("pause", "Pause")
        self.reset_button = self._icon_button("reset", "Reset")
        self.save_button = self._icon_button("save", "Save")
        self.back_button = self._icon_button("back", "Back to Menu")
        for b in (self.start_button, self.pause_button, self.reset_button, self.save_button, self.back_button):
            layout.addWidget(b)

        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.reset_button.clicked.connect(self._reset_clicked)
        self.save_button.clicked.connect(self.save_requested.emit)
        self.back_button.clicked.connect(self._back_clicked)

        return bar

    def _icon_button(self, icon_name, tooltip):
        pixmap = self.assets.get_pixmap("icons", icon_name, size=20)
        return IconButton(pixmap, tooltip)

    def _build_sidebar(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        status_box = QGroupBox("Season Progress")
        status_layout = QVBoxLayout(status_box)
        self.season_progress = QProgressBar()
        self.season_progress.setMaximum(1000)
        self.season_ticks_label = QLabel("1000 ticks remaining")
        status_layout.addWidget(self.season_progress)
        status_layout.addWidget(self.season_ticks_label)
        layout.addWidget(status_box)

        speed_box = QGroupBox("Speed")
        speed_layout = QVBoxLayout(speed_box)
        self.speed_label = QLabel("Tick every 50 ms")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(20, 300)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self._speed_changed)
        speed_layout.addWidget(self.speed_label)
        speed_layout.addWidget(self.speed_slider)
        layout.addWidget(speed_box)

        vis_box = QGroupBox("Visibility")
        vis_layout = QVBoxLayout(vis_box)
        self.vision_checkbox = QCheckBox("Show vision ranges")
        self.vision_checkbox.setChecked(True)
        self.status_ring_checkbox = QCheckBox("Show health status rings")
        self.status_ring_checkbox.setChecked(True)
        self.labels_checkbox = QCheckBox("Show entity labels")
        self.particles_checkbox = QCheckBox("Show weather particles")
        self.particles_checkbox.setChecked(True)
        for cb in (self.vision_checkbox, self.status_ring_checkbox, self.labels_checkbox, self.particles_checkbox):
            cb.toggled.connect(self._visibility_changed)
            vis_layout.addWidget(cb)
        layout.addWidget(vis_box)

        layout.addStretch()
        scroll.setWidget(content)
        scroll.setMinimumWidth(230)
        scroll.setMaximumWidth(300)
        return scroll

    def _build_map(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(4, 4, 4, 4)
        self.scene = EcosystemScene(self.assets)
        self.view = EcosystemView(self.scene)
        self.view.entity_selected.connect(self._entity_selected)
        layout.addWidget(self.view)
        return wrapper

    def _build_insights(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.status_banner = StatusBanner(self.theme)
        layout.addWidget(self.status_banner)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(8)
        self.cards = {}
        card_defs = [
            ("plants", "Plants"), ("berry_bushes", "Berry Bushes"),
            ("herbivores", "Herbivores"), ("foxes", "Foxes"),
            ("water_sources", "Water Sources"), ("shelters", "Shelters"),
            ("avg_herbivore_energy", "Avg Herb. Energy"), ("avg_herbivore_thirst", "Avg Herb. Thirst"),
            ("avg_fox_energy", "Avg Fox Energy"), ("avg_fox_hunger", "Avg Fox Hunger"),
            ("avg_fox_thirst", "Avg Fox Thirst"), ("danger_count", "Herbivores in Danger"),
        ]
        for i, (key, label) in enumerate(card_defs):
            card = StatCard(self.theme, label)
            self.cards[key] = card
            cards_grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(cards_grid)

        self.detail_card = SelectionDetailCard(self.theme)
        layout.addWidget(self.detail_card)

        layout.addStretch()
        scroll.setWidget(content)
        scroll.setMinimumWidth(300)
        scroll.setMaximumWidth(380)
        return scroll

    def _build_bottom(self):
        bottom = QSplitter(Qt.Horizontal)
        bottom.setFixedHeight(230)

        self.graph = GraphWidget(self.theme)
        bottom.addWidget(self.graph)

        log_box = QGroupBox("Event Log")
        log_layout = QVBoxLayout(log_box)
        self.log_browser = QTextBrowser()
        log_layout.addWidget(self.log_browser)
        bottom.addWidget(log_box)

        bottom.setSizes([700, 400])
        return bottom

    def attach_engine(self, engine, save_name, speed_ms=50):
        self.engine = engine
        self.save_name = save_name
        self.save_name_label.setText(save_name)
        self.scene.set_world_size(engine.world.width, engine.world.height)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.speed_slider.setValue(speed_ms)
        self.timer.setInterval(speed_ms)
        self.last_season = engine.season
        self.last_fox_count = len(engine.world.foxes)
        self.graph.reset()
        self.log_browser.clear()
        self._log(f"Simulation '{save_name}' loaded.")
        self._refresh()

    def start(self):
        if not self.engine:
            return
        self.engine.start()
        self.timer.start()
        self._log("Simulation started.")

    def pause(self):
        if not self.engine:
            return
        self.engine.pause()
        self.timer.stop()
        self._log("Simulation paused.")

    def is_dirty(self):
        return self.engine is not None and self.engine.current_tick > 0

    def _reset_clicked(self):
        if confirm(self, self.theme, "Reset Simulation",
                   "Reset this simulation back to its starting configuration? Unsaved progress will be lost."):
            self.pause()
            self.reset_requested.emit()

    def _back_clicked(self):
        self.pause()
        self.back_to_menu_requested.emit()

    def _speed_changed(self, value):
        self.timer.setInterval(value)
        self.speed_label.setText(f"Tick every {value} ms")

    def _visibility_changed(self):
        self.scene.show_vision = self.vision_checkbox.isChecked()
        self.scene.show_status_rings = self.status_ring_checkbox.isChecked()
        self.scene.show_labels = self.labels_checkbox.isChecked()
        self.scene.show_particles = self.particles_checkbox.isChecked()

    def _entity_selected(self, entity):
        self.detail_card.show_entity(entity)


    def _tick(self):
        if not self.engine:
            return
        old_fox_count = self.last_fox_count
        self.engine.update()
        state = self.engine.get_state()
        self.scene.sync(state)
        stats = self._compute_stats(state)
        self._update_ui(stats)

        if self.engine.running and stats["tick"] % 5 == 0 and stats["tick"] != 0 and self.graph_callback:
            self.graph_callback(stats)
            self.graph.add_point(stats)
        if self.engine.running and stats["tick"] % 10 == 0 and stats["tick"] != 0 and self.snapshot_callback:
            self.snapshot_callback(stats)

        self._check_events(stats, old_fox_count)

    def _refresh(self):
        if not self.engine:
            return
        state = self.engine.get_state()
        self.scene.sync(state)
        stats = self._compute_stats(state)
        self._update_ui(stats)

    def _compute_stats(self, state):
        counts = state["counts"]
        herbivores, foxes, plants = [], [], []
        danger = 0
        for e in state["entities"]:
            if e["type"] == "herbivore":
                herbivores.append(e)
                if e.get("nearest_fox_dist", 9999) < 200:
                    danger += 1
            elif e["type"] == "fox":
                foxes.append(e)
            elif e["type"] == "plant":
                plants.append(e)

        def avg(items, key):
            return sum(i.get(key, 0) for i in items) / len(items) if items else 0

        return {
            "tick": state["tick"], "season": state["season"], "season_tick": state["season_tick"],
            "plants": counts["plants"], "berry_bushes": counts["berry_bushes"],
            "water_sources": counts["water_sources"], "shelters": counts["shelters"],
            "herbivores": counts["herbivores"], "foxes": counts["foxes"],
            "avg_herbivore_energy": avg(herbivores, "energy"), "avg_herbivore_thirst": avg(herbivores, "thirst"),
            "avg_fox_energy": avg(foxes, "energy"), "avg_fox_hunger": avg(foxes, "hunger"),
            "avg_fox_thirst": avg(foxes, "thirst"), "avg_speed": avg(herbivores, "speed"),
            "avg_vision": avg(herbivores, "vision"), "avg_herbivore_age": avg(herbivores, "age"),
            "avg_fox_age": avg(foxes, "age"), "avg_plant_food": avg(plants, "food_value"),
            "danger_count": danger,
        }

    def _update_ui(self, stats):
        self.tick_label.setText(f"Tick: {stats['tick']}")
        self.season_label.setText(f"Season: {stats['season'].title()}")
        self.season_progress.setValue(stats["season_tick"])
        self.season_ticks_label.setText(f"{1000 - stats['season_tick']} ticks until next season")

        for key in ("plants", "berry_bushes", "herbivores", "foxes", "water_sources", "shelters"):
            self.cards[key].set_value(stats[key])
        c = self.theme.colors
        self.cards["avg_herbivore_energy"].set_value(f"{stats['avg_herbivore_energy']:.0f}")
        self.cards["avg_herbivore_thirst"].set_value(f"{stats['avg_herbivore_thirst']:.0f}")
        self.cards["avg_fox_energy"].set_value(f"{stats['avg_fox_energy']:.0f}")
        self.cards["avg_fox_hunger"].set_value(f"{stats['avg_fox_hunger']:.0f}")
        self.cards["avg_fox_thirst"].set_value(f"{stats['avg_fox_thirst']:.0f}")
        self.cards["danger_count"].set_value(stats["danger_count"], color=c.danger if stats["danger_count"] > 0 else None)

        status = ecosystem_status(stats)
        self.status_banner.set_status(status)

    def _check_events(self, stats, old_fox_count):
        if stats["season"] != self.last_season:
            self._log(f"Season changed: {self.last_season} to {stats['season']}.")
            self.last_season = stats["season"]
        if old_fox_count == 0 and stats["foxes"] > 0:
            self._log(f"Foxes returned to the ecosystem (+{stats['foxes']}).")
        self.last_fox_count = stats["foxes"]
        if self.engine.running and stats["herbivores"] == 0:
            self.pause()
            self._log("All herbivores have died. Simulation paused.")
            show_info(self, self.theme, "Simulation Ended", "All herbivores died out. Foxes have no food source left.")

    def _log(self, text):
        tick = self.engine.current_tick if self.engine else 0
        self.log_browser.append(f"Tick {tick}: {text}")
