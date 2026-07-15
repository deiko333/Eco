from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QFileDialog, QHeaderView
)

from frontend.dialogs import confirm, show_info, show_error, ask_text


class HistoryPage(QWidget):
    load_requested = pyqtSignal(int)
    back_requested = pyqtSignal()

    def __init__(self, theme, database, save_manager):
        super().__init__()
        self.theme = theme
        self.db = database
        self.save_manager = save_manager
        self.current_user = None
        self._build()

    def _build(self):
        c = self.theme.colors
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(12)

        header = QLabel("Simulation History")
        header.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {c.forest_dark};")
        root.addWidget(header)

        saves_box = QGroupBox("Saved Simulations")
        saves_layout = QVBoxLayout(saves_box)
        self.saves_table = QTableWidget(0, 5)
        self.saves_table.setHorizontalHeaderLabels(["Save Name", "Tick", "Season", "Created", "Updated"])
        self.saves_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.saves_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.saves_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.saves_table.itemSelectionChanged.connect(self._selection_changed)
        saves_layout.addWidget(self.saves_table)

        button_row = QHBoxLayout()
        self.load_button = QPushButton("Load Simulation")
        self.rename_button = QPushButton("Rename")
        self.rename_button.setObjectName("secondaryButton")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("dangerButton")
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setObjectName("secondaryButton")
        self.export_json_button = QPushButton("Export JSON")
        self.export_json_button.setObjectName("secondaryButton")
        for b in (self.load_button, self.rename_button, self.delete_button, self.export_csv_button, self.export_json_button):
            button_row.addWidget(b)
        saves_layout.addLayout(button_row)
        root.addWidget(saves_box, stretch=1)

        snap_box = QGroupBox("Snapshot Statistics")
        snap_layout = QVBoxLayout(snap_box)
        self.snapshots_table = QTableWidget(0, 10)
        self.snapshots_table.setHorizontalHeaderLabels([
            "Tick", "Season", "Plants", "Berries", "Herbivores", "Foxes",
            "Avg Herb Energy", "Avg Fox Energy", "Danger", "Recorded"
        ])
        self.snapshots_table.setEditTriggers(QTableWidget.NoEditTriggers)
        snap_layout.addWidget(self.snapshots_table)
        root.addWidget(snap_box, stretch=1)

        back_row = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("secondaryButton")
        back_row.addWidget(self.back_button)
        back_row.addStretch()
        root.addLayout(back_row)

        self.load_button.clicked.connect(self._load_clicked)
        self.rename_button.clicked.connect(self._rename_clicked)
        self.delete_button.clicked.connect(self._delete_clicked)
        self.export_csv_button.clicked.connect(self._export_csv_clicked)
        self.export_json_button.clicked.connect(self._export_json_clicked)
        self.back_button.clicked.connect(self.back_requested.emit)

    def set_user(self, user):
        self.current_user = user
        self.refresh()

    def refresh(self):
        self.saves_table.setRowCount(0)
        self.snapshots_table.setRowCount(0)
        if not self.current_user:
            return
        saves = self.db.list_saves(self.current_user["id"])
        for save in saves:
            row = self.saves_table.rowCount()
            self.saves_table.insertRow(row)
            values = [save["save_name"], str(save["tick"]), save["season"], save["created_at"][:19], save["updated_at"][:19]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, save["id"])
                self.saves_table.setItem(row, col, item)

    def _selected_save_id(self):
        row = self.saves_table.currentRow()
        if row < 0:
            return None
        item = self.saves_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _selection_changed(self):
        save_id = self._selected_save_id()
        self.snapshots_table.setRowCount(0)
        if save_id is None:
            return
        snapshots = self.db.list_snapshots(save_id)
        for snap in snapshots:
            row = self.snapshots_table.rowCount()
            self.snapshots_table.insertRow(row)
            values = [
                snap["tick"], snap["season"], snap["plants"], snap["berry_bushes"],
                snap["herbivores"], snap["foxes"], f"{snap['avg_herbivore_energy']:.1f}",
                f"{snap['avg_fox_energy']:.1f}", snap["danger_count"], snap["created_at"][:19],
            ]
            for col, value in enumerate(values):
                self.snapshots_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _load_clicked(self):
        save_id = self._selected_save_id()
        if save_id is None:
            show_error(self, self.theme, "No Save Selected", "Select a saved simulation first.")
            return
        self.load_requested.emit(save_id)

    def _rename_clicked(self):
        save_id = self._selected_save_id()
        if save_id is None:
            show_error(self, self.theme, "No Save Selected", "Select a saved simulation first.")
            return
        new_name, ok = ask_text(self, self.theme, "Rename Save", "New save name:")
        if ok and new_name.strip():
            self.db.rename_save(save_id, new_name.strip())
            self.refresh()

    def _delete_clicked(self):
        save_id = self._selected_save_id()
        if save_id is None:
            show_error(self, self.theme, "No Save Selected", "Select a saved simulation first.")
            return
        if confirm(self, self.theme, "Delete Save", "Delete this saved simulation and all its snapshots?", danger=True):
            self.db.delete_save(save_id)
            self.refresh()

    def _export_csv_clicked(self):
        save_id = self._selected_save_id()
        if save_id is None:
            show_error(self, self.theme, "No Save Selected", "Select a saved simulation first.")
            return
        snapshots = self.db.list_snapshots(save_id)
        if not snapshots:
            show_info(self, self.theme, "No Data", "This save has no recorded snapshots yet.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export Snapshot History", "ecobalance_history.csv", "CSV Files (*.csv)")
        if not filename:
            return
        headers = list(snapshots[0].keys())
        rows = [[s[h] for h in headers] for s in snapshots]
        self.save_manager.export_csv(filename, rows, headers)
        show_info(self, self.theme, "Exported", "Snapshot history exported to CSV.")

    def _export_json_clicked(self):
        save_id = self._selected_save_id()
        if save_id is None:
            show_error(self, self.theme, "No Save Selected", "Select a saved simulation first.")
            return
        record = self.db.load_full_state(save_id)
        if record is None:
            show_error(self, self.theme, "Not Found", "Could not load this save.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Export Full State", "ecobalance_save.json", "JSON Files (*.json)")
        if not filename:
            return
        self.save_manager.export_json(filename, record["state"])
        show_info(self, self.theme, "Exported", "Full simulation state exported to JSON.")
