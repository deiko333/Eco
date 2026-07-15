from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPainter


class IconButton(QPushButton):
    def __init__(self, pixmap, tooltip="", size=38, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self.setObjectName("iconButton")
        self.setToolTip(tooltip)
        self.setFixedSize(size, size)

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)  # background / border / hover states from QSS
        if self._pixmap is None or self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        x = (self.width() - self._pixmap.width()) // 2
        y = (self.height() - self._pixmap.height()) // 2
        painter.drawPixmap(x, y, self._pixmap)
        painter.end()
