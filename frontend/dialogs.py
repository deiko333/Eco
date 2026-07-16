from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit


def _style_box(box, theme):
    c = theme.colors
    box.setStyleSheet(f"""
        QMessageBox {{ background-color: {c.surface}; }}
        QLabel {{ color: {c.text}; font-size: 13px; }}
        QPushButton {{
            background-color: {c.accent}; color: white; border-radius: 8px;
            padding: 8px 16px; min-width: 70px;
        }}
        QPushButton:hover {{ background-color: {c.accent_hover}; }}
    """)


def confirm(parent, theme, title, message, danger=False):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Warning if danger else QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    _style_box(box, theme)
    return box.exec_() == QMessageBox.Yes


def confirm_discard(parent, theme, message="You have unsaved changes. Save before continuing?"):
    box = QMessageBox(parent)
    box.setWindowTitle("Unsaved Changes")
    box.setText(message)
    box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    _style_box(box, theme)
    result = box.exec_()
    if result == QMessageBox.Save:
        return "save"
    if result == QMessageBox.Discard:
        return "discard"
    return "cancel"


def show_error(parent, theme, title, message):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Warning)
    box.setStandardButtons(QMessageBox.Ok)
    _style_box(box, theme)
    box.exec_()


def show_info(parent, theme, title, message):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Information)
    box.setStandardButtons(QMessageBox.Ok)
    _style_box(box, theme)
    box.exec_()


def ask_text(parent, theme, title, label, default=""):
    dialog = QInputDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setTextValue(default)
    dialog.setInputMode(QInputDialog.TextInput)
    c = theme.colors
    dialog.setStyleSheet(f"""
        QInputDialog {{ background-color: {c.surface}; }}
        QLabel {{ color: {c.text}; }}
        QLineEdit {{ background-color: {c.panel}; border: 1.5px solid {c.border}; border-radius: 8px; padding: 6px; }}
        QPushButton {{ background-color: {c.accent}; color: white; border-radius: 8px; padding: 8px 16px; }}
    """)
    ok = dialog.exec_()
    return dialog.textValue(), ok == QInputDialog.Accepted
