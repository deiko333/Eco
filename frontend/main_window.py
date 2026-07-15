from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox

from frontend.theme import Theme
from frontend.asset_manager import AssetManager
from frontend.start_page import StartPage
from frontend.profile_page import ProfilePage
from frontend.setup_page import SetupPage
from frontend.simulation_page import SimulationPage
from frontend.history_page import HistoryPage
from frontend.settings_page import SettingsPage
from frontend.dialogs import confirm, confirm_discard, show_error, show_info, ask_text

from services.database import DatabaseManager
from services.save_manager import SaveManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EcoBalance - Ecosystem Simulator")
        self.setGeometry(40, 30, 1560, 940)

        self.db = DatabaseManager()
        self.save_manager = SaveManager(self.db)
        self.theme = Theme("light")
        self.assets = AssetManager(self.theme)

        self.current_user = None
        self.active_save_id = None
        self.last_setup_config = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._build_pages()
        self._apply_theme()
        self.stack.setCurrentWidget(self.profile_page)

    def _build_pages(self):
        self.profile_page = ProfilePage(self.theme, self.db)
        self.start_page = StartPage(self.theme, self.assets)
        self.setup_page = SetupPage(self.theme)
        self.simulation_page = SimulationPage(self.theme, self.assets)
        self.history_page = HistoryPage(self.theme, self.db, self.save_manager)
        self.settings_page = SettingsPage(self.theme, self.db)

        for page in (self.profile_page, self.start_page, self.setup_page,
                     self.simulation_page, self.history_page, self.settings_page):
            self.stack.addWidget(page)

        self.profile_page.profile_selected.connect(self._profile_selected)

        self.start_page.new_simulation_requested.connect(lambda: self.stack.setCurrentWidget(self.setup_page))
        self.start_page.continue_requested.connect(self._continue_latest_save)
        self.start_page.history_requested.connect(self._open_history)
        self.start_page.settings_requested.connect(self._open_settings)
        self.start_page.exit_requested.connect(self._exit_clicked)

        self.setup_page.back_requested.connect(lambda: self.stack.setCurrentWidget(self.start_page))
        self.setup_page.start_requested.connect(self._start_new_simulation)

        self.simulation_page.back_to_menu_requested.connect(self._back_to_menu_from_sim)
        self.simulation_page.save_requested.connect(self._save_simulation)
        self.simulation_page.reset_requested.connect(self._reset_simulation)
        self.simulation_page.snapshot_callback = self._on_snapshot_tick
        self.simulation_page.graph_callback = self._on_graph_tick

        self.history_page.back_requested.connect(lambda: self.stack.setCurrentWidget(self.start_page))
        self.history_page.load_requested.connect(self._load_save)

        self.settings_page.back_requested.connect(lambda: self.stack.setCurrentWidget(self.start_page))
        self.settings_page.settings_changed.connect(self._settings_changed)


    def _profile_selected(self, user):
        self.current_user = user
        self.settings_page.set_user(user)
        self.start_page.set_continue_enabled(self.db.has_any_save(user["id"]))
        self.stack.setCurrentWidget(self.start_page)

    def _open_history(self):
        self.history_page.set_user(self.current_user)
        self.stack.setCurrentWidget(self.history_page)

    def _open_settings(self):
        self.settings_page.set_user(self.current_user)
        self.stack.setCurrentWidget(self.settings_page)

    def _settings_changed(self, settings):
        if settings["theme"] != self.theme.mode:
            self.theme.toggle()
            self.assets.invalidate()
            self._apply_theme()
        self.simulation_page.scene.show_vision = settings["show_vision_ranges"]
        self.simulation_page.scene.show_labels = settings["show_entity_labels"]
        self.simulation_page.scene.show_particles = settings["show_weather_particles"]
        if settings["fullscreen"]:
            self.showFullScreen()
        else:
            self.showNormal()
        show_info(self, self.theme, "Settings Saved", "Your settings have been saved.")
        self.stack.setCurrentWidget(self.start_page)

    def _apply_theme(self):
        self.setStyleSheet(self.theme.app_stylesheet())
        self.start_page.refresh_theme()


    def _start_new_simulation(self, config):
        errors = self.save_manager.validate_counts(config["counts"])
        if errors:
            show_error(self, self.theme, "Invalid Configuration", "\n".join(errors))
            return
        engine = self.save_manager.build_engine(config["counts"], config["season"])
        self.last_setup_config = config
        self.active_save_id = None
        self.simulation_page.attach_engine(engine, config["save_name"], config["speed"])
        self.stack.setCurrentWidget(self.simulation_page)

    def _reset_simulation(self):
        if self.last_setup_config:
            engine = self.save_manager.build_engine(self.last_setup_config["counts"], self.last_setup_config["season"])
            self.simulation_page.attach_engine(engine, self.last_setup_config["save_name"], self.last_setup_config["speed"])
        else:
            show_error(self, self.theme, "Cannot Reset", "No initial configuration is available to reset to.")

    def _save_simulation(self):
        if not self.simulation_page.engine or not self.current_user:
            return
        name = self.simulation_page.save_name
        self.active_save_id = self.save_manager.save(self.current_user["id"], name, self.simulation_page.engine)
        show_info(self, self.theme, "Saved", f"Simulation '{name}' saved.")
        self.start_page.set_continue_enabled(True)

    def _continue_latest_save(self):
        saves = self.db.list_saves(self.current_user["id"])
        if not saves:
            show_error(self, self.theme, "No Saves", "No saved simulation was found for this profile.")
            return
        self._load_save(saves[0]["id"])

    def _load_save(self, save_id):
        result = self.save_manager.load(save_id)
        if result is None:
            show_error(self, self.theme, "Load Failed", "Could not load the selected save.")
            return
        engine, record = result
        self.active_save_id = save_id
        self.last_setup_config = None
        self.simulation_page.attach_engine(engine, record["save_name"])
        self.stack.setCurrentWidget(self.simulation_page)

    def _on_snapshot_tick(self, stats):
        if self.active_save_id is None or not self.current_user:
            return
        self.db.save_snapshot(self.active_save_id, stats)

    def _on_graph_tick(self, stats):
        interval = self.settings_page.settings.get("autosave_interval_ticks", 0)
        if interval and self.active_save_id and stats["tick"] % interval == 0:
            self.db.save_full_state(self.current_user["id"], self.simulation_page.save_name, self.simulation_page.engine.save_full_state())

    def _back_to_menu_from_sim(self):
        if self.simulation_page.is_dirty():
            choice = confirm_discard(self, self.theme, "Save this simulation before returning to the menu?")
            if choice == "cancel":
                return
            if choice == "save":
                if self.active_save_id is None:
                    name, ok = ask_text(self, self.theme, "Save Simulation", "Save name:", self.simulation_page.save_name)
                    if not ok:
                        return
                    self.simulation_page.save_name = name
                self._save_simulation()
        self.start_page.set_continue_enabled(self.db.has_any_save(self.current_user["id"]))
        self.stack.setCurrentWidget(self.start_page)

    def _exit_clicked(self):
        if self.simulation_page.engine and self.simulation_page.is_dirty():
            choice = confirm_discard(self, self.theme, "You have an active simulation. Save before exiting?")
            if choice == "cancel":
                return
            if choice == "save":
                self._save_simulation()
        self.close()

    def closeEvent(self, event):
        if self.simulation_page.engine and self.simulation_page.is_dirty() and self.stack.currentWidget() is self.simulation_page:
            choice = confirm_discard(self, self.theme, "You have an active simulation. Save before exiting?")
            if choice == "cancel":
                event.ignore()
                return
            if choice == "save":
                self._save_simulation()
        event.accept()
