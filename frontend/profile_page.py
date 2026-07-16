from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QFormLayout,
)

from frontend.dialogs import confirm, show_error, show_info
from frontend.theme import apply_soft_shadow


class ProfilePage(QWidget):
    profile_selected = pyqtSignal(dict)
    back_requested = pyqtSignal()

    def __init__(self, theme, database):
        super().__init__()

        self.theme = theme
        self.db = database

        self._build()
        self._connect_signals()
        self.refresh_users()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(55, 35, 55, 35)
        root.setSpacing(20)

        root.addLayout(self._create_header())

        content = QHBoxLayout()
        content.setSpacing(22)

        content.addWidget(
            self._create_existing_profiles_card(),
            stretch=1,
        )
        content.addWidget(
            self._create_new_profile_card(),
            stretch=1,
        )

        root.addLayout(content, stretch=1)

        bottom_row = QHBoxLayout()

        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("secondaryButton")
        self.back_button.setMinimumWidth(120)
        self.back_button.setCursor(Qt.PointingHandCursor)

        self.profile_count_label = QLabel()
        self.profile_count_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )
        self.profile_count_label.setObjectName("profileCount")

        bottom_row.addWidget(self.back_button)
        bottom_row.addStretch()
        bottom_row.addWidget(self.profile_count_label)

        root.addLayout(bottom_row)

        self._apply_local_styles()

    def _create_header(self):
        layout = QHBoxLayout()
        layout.setSpacing(16)

        badge = QLabel("EB")
        badge.setFixedSize(62, 62)
        badge.setAlignment(Qt.AlignCenter)
        badge.setObjectName("profileBadge")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.header_label = QLabel("Choose your profile")
        self.header_label.setObjectName("profileHeader")

        self.subtitle_label = QLabel(
            "Select an existing profile or create a new one "
            "to start your ecosystem journey."
        )
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setObjectName("profileSubtitle")

        text_layout.addWidget(self.header_label)
        text_layout.addWidget(self.subtitle_label)

        layout.addWidget(badge)
        layout.addLayout(text_layout)
        layout.addStretch()

        return layout

    def _create_existing_profiles_card(self):
        self.existing_card = QFrame()
        self.existing_card.setObjectName("profileCard")

        layout = QVBoxLayout(self.existing_card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        title = QLabel("Your profiles")
        title.setObjectName("profileCardTitle")

        description = QLabel(
            "Choose one of your saved profiles to continue."
        )
        description.setWordWrap(True)
        description.setObjectName("profileCardDescription")

        self.user_list = QListWidget()
        self.user_list.setObjectName("profileList")
        self.user_list.setSpacing(4)

        empty_hint = QLabel(
            "Double-click a profile to open it."
        )
        empty_hint.setAlignment(Qt.AlignCenter)
        empty_hint.setObjectName("profileHint")

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.select_button = QPushButton("Open Profile")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("dangerButton")

        self.select_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setCursor(Qt.PointingHandCursor)

        button_row.addWidget(self.select_button, stretch=2)
        button_row.addWidget(self.delete_button, stretch=1)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(4)
        layout.addWidget(self.user_list, stretch=1)
        layout.addWidget(empty_hint)
        layout.addLayout(button_row)

        apply_soft_shadow(
            self.existing_card,
            blur=25,
            y_offset=5,
            alpha=40,
        )

        return self.existing_card

    def _create_new_profile_card(self):
        self.create_card = QFrame()
        self.create_card.setObjectName("profileCard")

        layout = QVBoxLayout(self.create_card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        title = QLabel("Create a new profile")
        title.setObjectName("profileCardTitle")

        description = QLabel(
            "Your saved simulations and preferences will be "
            "connected to this profile."
        )
        description.setWordWrap(True)
        description.setObjectName("profileCardDescription")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(10)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(13)

        self.username_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()

        self.username_input.setPlaceholderText(
            "Enter a profile name"
        )
        self.email_input.setPlaceholderText(
            "Optional email address"
        )
        self.password_input.setPlaceholderText(
            "Optional password"
        )

        self.password_input.setEchoMode(QLineEdit.Password)

        form.addRow("Username", self.username_input)
        form.addRow("Email", self.email_input)
        form.addRow("Password", self.password_input)

        layout.addLayout(form)
        layout.addSpacing(8)

        privacy_note = QLabel(
            "Profile information is stored locally on this computer."
        )
        privacy_note.setWordWrap(True)
        privacy_note.setObjectName("profileHint")

        self.create_button = QPushButton("Create Profile")
        self.create_button.setMinimumHeight(46)
        self.create_button.setCursor(Qt.PointingHandCursor)

        layout.addWidget(privacy_note)
        layout.addStretch()
        layout.addWidget(self.create_button)

        apply_soft_shadow(
            self.create_card,
            blur=25,
            y_offset=5,
            alpha=40,
        )

        return self.create_card

    def _connect_signals(self):
        self.select_button.clicked.connect(
            self._select_clicked
        )
        self.delete_button.clicked.connect(
            self._delete_clicked
        )
        self.create_button.clicked.connect(
            self._create_clicked
        )
        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.user_list.itemDoubleClicked.connect(
            lambda _: self._select_clicked()
        )

        self.username_input.returnPressed.connect(
            self._create_clicked
        )
        self.email_input.returnPressed.connect(
            self._create_clicked
        )
        self.password_input.returnPressed.connect(
            self._create_clicked
        )

    def _apply_local_styles(self):
        c = self.theme.colors

        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QFrame#profileCard {{
                background-color: {c.panel};
                border: 1px solid {c.border};
                border-radius: 24px;
            }}

            QLabel#profileBadge {{
                background-color: {c.accent};
                color: white;
                border-radius: 21px;
                font-size: 18px;
                font-weight: 800;
            }}

            QLabel#profileHeader {{
                color: {c.forest_dark};
                font-size: 28px;
                font-weight: 800;
            }}

            QLabel#profileSubtitle {{
                color: {c.muted};
                font-size: 12px;
            }}

            QLabel#profileCardTitle {{
                color: {c.forest_dark};
                font-size: 18px;
                font-weight: 700;
            }}

            QLabel#profileCardDescription {{
                color: {c.muted};
                font-size: 11px;
            }}

            QLabel#profileHint {{
                color: {c.muted};
                font-size: 10px;
                padding: 3px;
            }}

            QLabel#profileCount {{
                color: {c.muted};
                font-size: 11px;
            }}

            QListWidget#profileList {{
                background-color: {c.panel_alt};
                border: 1px solid {c.border};
                border-radius: 15px;
                padding: 8px;
                outline: none;
            }}

            QListWidget#profileList::item {{
                background-color: {c.panel};
                color: {c.text};
                border: 1px solid {c.border};
                border-radius: 11px;
                padding: 12px;
                margin: 3px;
            }}

            QListWidget#profileList::item:hover {{
                background-color: {c.sage};
                color: white;
                border-color: {c.sage};
            }}

            QListWidget#profileList::item:selected {{
                background-color: {c.accent};
                color: white;
                border-color: {c.accent};
            }}
            """
        )

    def refresh_users(self):
        self.user_list.clear()

        users = self.db.list_users()

        for user in users:
            item = QListWidgetItem()

            username = user.get("username", "Unnamed Profile")
            email = user.get("email", "")

            if email:
                item.setText(f"{username}\n{email}")
            else:
                item.setText(username)

            item.setData(Qt.UserRole, user)
            item.setTextAlignment(
                Qt.AlignLeft | Qt.AlignVCenter
            )
            item.setSizeHint(item.sizeHint())

            self.user_list.addItem(item)

        profile_word = "profile" if len(users) == 1 else "profiles"
        self.profile_count_label.setText(
            f"{len(users)} {profile_word} available"
        )

        has_users = len(users) > 0
        self.select_button.setEnabled(has_users)
        self.delete_button.setEnabled(has_users)

    def _selected_user(self):
        item = self.user_list.currentItem()

        if item:
            return item.data(Qt.UserRole)

        return None

    def _select_clicked(self):
        user = self._selected_user()

        if not user:
            show_error(
                self,
                self.theme,
                "No Profile Selected",
                "Select a profile from the list first.",
            )
            return

        self.profile_selected.emit(user)

    def _delete_clicked(self):
        user = self._selected_user()

        if not user:
            show_error(
                self,
                self.theme,
                "No Profile Selected",
                "Select a profile from the list first.",
            )
            return

        username = user["username"]

        message = (
            f"Delete profile '{username}' and all of its saved "
            "simulations?\n\nThis action cannot be undone."
        )

        should_delete = confirm(
            self,
            self.theme,
            "Delete Profile",
            message,
            danger=True,
        )

        if not should_delete:
            return

        self.db.delete_user(user["id"])
        self.refresh_users()

        show_info(
            self,
            self.theme,
            "Profile Deleted",
            f"Profile '{username}' was deleted.",
        )

    def _create_clicked(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not username:
            show_error(
                self,
                self.theme,
                "Missing Username",
                "Please enter a username.",
            )
            self.username_input.setFocus()
            return

        if len(username) < 2:
            show_error(
                self,
                self.theme,
                "Username Too Short",
                "The username must contain at least two characters.",
            )
            self.username_input.setFocus()
            return

        try:
            self.db.create_user(
                username,
                email,
                password,
            )
        except ValueError as error:
            show_error(
                self,
                self.theme,
                "Could Not Create Profile",
                str(error),
            )
            return

        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()

        self.refresh_users()

        show_info(
            self,
            self.theme,
            "Profile Created",
            f"Profile '{username}' was created successfully.",
        )

    def refresh_theme(self):
        self._apply_local_styles()