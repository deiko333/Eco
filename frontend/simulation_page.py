from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSplitter,
    QGroupBox, QCheckBox, QSlider, QScrollArea, QTextBrowser, QSizePolicy,
    QGridLayout, QProgressBar, QComboBox
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
        self.sounds = None
        self.snapshot_callback = None
        self.graph_callback = None
        self.last_season = "summer"
        self.last_fox_count = 0
        self.effect_timer = QTimer()
        self.effect_timer.setInterval(80)
        self.effect_timer.timeout.connect(
            self._advance_effects
        )
        self.effect_timer.start()

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
        self.save_button.clicked.connect(self._save_clicked)
        self.back_button.clicked.connect(self._back_clicked)

        return bar

    def _icon_button(self, icon_name, tooltip):
        pixmap = self.assets.get_pixmap("icons", icon_name, size=20)
        return IconButton(pixmap, tooltip)

    def _save_clicked(self):
        if self.sounds:
            self.sounds.play_click()
        self.save_requested.emit()

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

        disaster_box = QGroupBox("Disasters")
        disaster_layout = QVBoxLayout(disaster_box)
        self.disaster_combo = QComboBox()
        self.disaster_combo.addItems(["Wildfire", "Drought", "Plague"])
        self.disaster_combo.currentTextChanged.connect(self._update_disaster_hint)
        self.disaster_hint_label = QLabel()
        self.disaster_hint_label.setWordWrap(True)
        self.disaster_hint_label.setStyleSheet(f"color: {self.theme.colors.muted}; font-size: 11px;")
        self.disaster_button = QPushButton("Trigger Disaster")
        self.disaster_button.setObjectName("dangerButton")
        self.disaster_button.clicked.connect(self._disaster_button_clicked)
        disaster_layout.addWidget(self.disaster_combo)
        disaster_layout.addWidget(self.disaster_hint_label)
        disaster_layout.addWidget(self.disaster_button)
        layout.addWidget(disaster_box)
        self._update_disaster_hint(self.disaster_combo.currentText())
        editor_box = QGroupBox("Map Editor")
        editor_layout = QVBoxLayout(editor_box)
        self.placement_combo = QComboBox()
        self.placement_combo.addItem("Plant","plant")
        self.placement_combo.addItem("Berry Bush", "berry_bush")
        self.placement_combo.addItem("Tree", "tree")
        self.placement_combo.addItem("Water Source", "water")
        self.placement_combo.addItem("Shelter", "shelter")
        self.placement_combo.addItem("Herbivore", "herbivore")
        self.placement_combo.addItem("Fox", "fox")

        self.placement_hint_label = QLabel("Select an entity, then click Place on Map.")
        self.placement_hint_label.setWordWrap(True)
        self.placement_hint_label.setStyleSheet(
            f"""
            color: {self.theme.colors.muted};
            font-size: 11px;
            """
        )

        self.placement_button = QPushButton("Place on Map")
        self.cancel_interaction_button = QPushButton("Cancel Map Tool")

        self.placement_button.clicked.connect(
            self._placement_button_clicked
        )
        self.cancel_interaction_button.clicked.connect(
            self._cancel_map_interaction
        )

        editor_layout.addWidget(
            self.placement_combo
        )
        editor_layout.addWidget(
            self.placement_hint_label
        )
        editor_layout.addWidget(
            self.placement_button
        )
        editor_layout.addWidget(
            self.cancel_interaction_button
        )

        layout.addWidget(editor_box)

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
        self.view.map_clicked_for_disaster.connect(self._map_clicked_for_disaster)
        self.view.map_clicked_for_placement.connect(self._map_clicked_for_placement)
        self.view.interaction_cancelled.connect(self._interaction_cancelled)
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
            ("plants", "Plants"), ("berry_bushes", "Berry Bushes"), ("trees", "Trees"),
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
        if self.sounds:
            self.sounds.play_click()
        if not self.engine:
            return
        self.engine.start()
        self.timer.start()
        self._log("Simulation started.")

    def pause(self, silent=False):
        if self.sounds and not silent:
            self.sounds.play_click()
        if not self.engine:
            return
        self.engine.pause()
        self.timer.stop()
        self._log("Simulation paused.")

    def is_dirty(self):
        return self.engine is not None and self.engine.current_tick > 0

    def _reset_clicked(self):
        if self.sounds:
            self.sounds.play_click()
        if confirm(self, self.theme, "Reset Simulation",
                   "Reset this simulation back to its starting configuration? Unsaved progress will be lost."):
            self.pause()
            self.reset_requested.emit()

    def _back_clicked(self):
        if self.sounds:
            self.sounds.play_click()
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

    def _update_disaster_hint(self, disaster_name):
        if disaster_name == "Drought":
            self.disaster_hint_label.setText("Shrinks every water source on the map. No click needed.")
        else:
            self.disaster_hint_label.setText(f"Click the map after triggering to strike a {disaster_name.lower()} there.")

    def _disaster_button_clicked(self):
        if not self.engine:
            return
        label = self.disaster_combo.currentText()
        disaster_type = label.lower()

        if disaster_type == "drought":
            if confirm(self, self.theme, "Trigger Drought",
                       "This will shrink every water source on the map. Continue?", danger=True):
                self.engine.trigger_disaster("drought", 0,0)
                self._log("A drought struck, shrinking every water source.")
                self.scene.add_disaster_effect(
                    "drought",
                    duration=100,
                )

                if self.sounds:
                    self.sounds.play_drought()

                self._refresh()
            return

        if confirm(self, self.theme, f"Trigger {label}",
                   f"Click anywhere on the map to strike a {disaster_type} there. Continue?", danger=True):
            self.view.disaster_mode = disaster_type
            self.view.setCursor(Qt.CrossCursor)
            self.disaster_hint_label.setText(f"Click the map now to strike a {disaster_type}...")

    def _map_clicked_for_disaster(self, x, y):
        if not self.engine or not self.view.disaster_mode:
            return
        disaster_type = self.view.disaster_mode
        self.engine.trigger_disaster(disaster_type, x, y)
        self._log(
            f"A {disaster_type} struck near "
            f"({int(x)}, {int(y)})."
        )
        self.scene.add_disaster_effect(
            disaster_type,
            x,
            y,
            duration=110,
        )
        if self.sounds:
            if disaster_type == "wildfire":
                self.sounds.play_fire()
            elif disaster_type == "plague":
                self.sounds.play_plague()
            else:
                self.sounds.play_alert()
        self.view.disaster_mode = None
        self.view.setCursor(Qt.ArrowCursor)
        self._update_disaster_hint(self.disaster_combo.currentText())
        self._refresh()

    def _placement_button_clicked(self):
        if not self.engine:
            return
        self.view.disaster_mode = None
        self.view.placement_mode = (
            self.placement_combo.currentData()
        )
        self.view.setCursor(Qt.CrossCursor)
        selected_label = (
            self.placement_combo.currentText()
        )
        self.placement_hint_label.setText(
            f"Placement active: click the map to add "
            f"{selected_label}. "
            f"Right-click or press Escape to cancel."
        )
        if self.sounds:
            self.sounds.play_click()
    def _map_clicked_for_placement(self, x, y):
        if (
            not self.engine
            or not self.view.placement_mode
        ):
            return

        x = max(
            0,
            min(
                float(x),
                self.engine.world.width,
            ),
        )
        y = max(
            0,
            min(
                float(y),
                self.engine.world.height,
            ),
        )

        placement_mode = self.view.placement_mode

        placement_methods = {
            "plant": self.engine.add_plant,
            "berry_bush": self.engine.add_berry_bush,
            "tree": self.engine.add_tree,
            "water": self.engine.add_water_source,
            "shelter": self.engine.add_shelter,
            "herbivore": self.engine.add_herbivore,
            "fox": self.engine.add_fox,
        }

        add_method = placement_methods.get(
            placement_mode
        )

        if add_method is None:
            self._cancel_map_interaction()
            return

        new_entity_id = add_method(x, y)

        readable_name = placement_mode.replace(
            "_",
            " ",
        )

        self._log(
            f"Added {readable_name} "
            f"#{new_entity_id} at "
            f"({int(x)}, {int(y)})."
        )

        if self.sounds:
            self.sounds.play_place()

        self._refresh()


    def _cancel_map_interaction(self):
        self.view.cancel_interaction()


    def _interaction_cancelled(self):
        self._update_disaster_hint(
            self.disaster_combo.currentText()
        )

        self.placement_hint_label.setText(
            "Select an entity, then click Place on Map."
        )


    def _advance_effects(self):
        if hasattr(self, "scene"):
            self.scene.advance_effects()

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
            "trees": counts.get("trees", 0),
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

        for key in ("plants", "berry_bushes", "trees", "herbivores", "foxes", "water_sources", "shelters"):
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
            if self.sounds:
                self.sounds.play_chime()
        if old_fox_count == 0 and stats["foxes"] > 0:
            self._log(f"Foxes returned to the ecosystem (+{stats['foxes']}).")
        self.last_fox_count = stats["foxes"]
        if self.engine.running and stats["herbivores"] == 0:
            self.pause(silent=True)
            self._log("All herbivores have died. Simulation paused.")
            if self.sounds:
                self.sounds.play_alert()
            show_info(self, self.theme, "Simulation Ended", "All herbivores died out. Foxes have no food source left.")

    def _log(self, text):
        tick = self.engine.current_tick if self.engine else 0
        self.log_browser.append(f"Tick {tick}: {text}")
