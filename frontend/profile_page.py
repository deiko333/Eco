from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout
)

from frontend.dialogs import confirm, show_error, show_info


class ProfilePage(QWidget):
    profile_selected = pyqtSignal(dict)
    back_requested = pyqtSignal()

    def __init__(self, theme, database):
        super().__init__()
        self.theme = theme
        self.db = database
        self._build()
        self.refresh_users()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 40, 60, 40)
        root.setSpacing(16)

        header = QLabel("Choose Profile")
        header.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {self.theme.colors.forest_dark};")
        root.addWidget(header)

        content = QHBoxLayout()
        root.addLayout(content, stretch=1)

        existing_box = QGroupBox("Existing Profiles")
        existing_layout = QVBoxLayout(existing_box)
        self.user_list = QListWidget()
        existing_layout.addWidget(self.user_list)
        row = QHBoxLayout()
        self.select_button = QPushButton("Select Profile")
        self.delete_button = QPushButton("Delete Profile")
        self.delete_button.setObjectName("dangerButton")
        row.addWidget(self.select_button)
        row.addWidget(self.delete_button)
        existing_layout.addLayout(row)
        content.addWidget(existing_box, stretch=1)

        create_box = QGroupBox("Create New Profile")
        create_layout = QFormLayout(create_box)
        self.username_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("optional")
        create_layout.addRow("Username", self.username_input)
        create_layout.addRow("Email (optional)", self.email_input)
        create_layout.addRow("Password (optional)", self.password_input)
        self.create_button = QPushButton("Create Profile")
        create_layout.addRow(self.create_button)
        content.addWidget(create_box, stretch=1)

        back_row = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("secondaryButton")
        back_row.addWidget(self.back_button)
        back_row.addStretch()
        root.addLayout(back_row)

        self.select_button.clicked.connect(self._select_clicked)
        self.delete_button.clicked.connect(self._delete_clicked)
        self.create_button.clicked.connect(self._create_clicked)
        self.back_button.clicked.connect(self.back_requested.emit)
        self.user_list.itemDoubleClicked.connect(lambda _: self._select_clicked())

    def refresh_users(self):
        self.user_list.clear()
        for user in self.db.list_users():
            item = QListWidgetItem(user["username"])
            item.setData(Qt.UserRole, user)
            self.user_list.addItem(item)

    def _selected_user(self):
        item = self.user_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _select_clicked(self):
        user = self._selected_user()
        if not user:
            show_error(self, self.theme, "No Profile Selected", "Select a profile from the list first.")
            return
        self.profile_selected.emit(user)

    def _delete_clicked(self):
        user = self._selected_user()
        if not user:
            show_error(self, self.theme, "No Profile Selected", "Select a profile from the list first.")
            return
        if confirm(self, self.theme, "Delete Profile", f"Delete profile '{user['username']}' and all of its saves? This cannot be undone.", danger=True):
            self.db.delete_user(user["id"])
            self.refresh_users()

    def _create_clicked(self):
        username = self.username_input.text().strip()
        if not username:
            show_error(self, self.theme, "Missing Username", "Please enter a username.")
            return
        try:
            user_id = self.db.create_user(username, self.email_input.text().strip(), self.password_input.text())
        except ValueError as e:
            show_error(self, self.theme, "Could Not Create Profile", str(e))
            return
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.refresh_users()
        show_info(self, self.theme, "Profile Created", f"Profile '{username}' created.")
