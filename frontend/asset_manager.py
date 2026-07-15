import os
import math
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QPolygonF
from PyQt5.QtSvg import QSvgRenderer

ASSETS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

ASSET_FILENAMES = {
    "logo/ecobalance_logo.svg": "512x512",
    "backgrounds/forest_spring.png": "1600x1000",
    "backgrounds/forest_summer.png": "1600x1000",
    "backgrounds/forest_autumn.png": "1600x1000",
    "backgrounds/forest_winter.png": "1600x1000",
    "animals/herbivore_healthy.svg": "64x64",
    "animals/herbivore_tired.svg": "64x64",
    "animals/herbivore_thirsty.svg": "64x64",
    "animals/herbivore_critical.svg": "64x64",
    "animals/herbivore_fleeing.svg": "64x64",
    "animals/herbivore_drinking.svg": "64x64",
    "animals/fox_healthy.svg": "64x64",
    "animals/fox_hungry.svg": "64x64",
    "animals/fox_thirsty.svg": "64x64",
    "animals/fox_critical.svg": "64x64",
    "animals/fox_hunting.svg": "64x64",
    "plants/plant_small.svg": "32x32",
    "plants/plant_medium.svg": "32x32",
    "plants/plant_mature.svg": "32x32",
    "plants/berry_bush.svg": "40x40",
    "environment/water_source.svg": "96x96",
    "environment/shelter.svg": "96x96",
    "icons/play.svg": "24x24",
    "icons/pause.svg": "24x24",
    "icons/reset.svg": "24x24",
    "icons/save.svg": "24x24",
    "icons/settings.svg": "24x24",
    "icons/history.svg": "24x24",
    "icons/back.svg": "24x24",
    "icons/visibility.svg": "24x24",
}


class AssetManager:
    def __init__(self, theme):
        self.theme = theme
        self._cache = {}

    def invalidate(self):
        self._cache.clear()

    def status_ring_color(self, state):
        return self._state_color(state, self.theme.colors)

    def get_pixmap(self, category, name, size=64, state=None):
        key = (category, name, state, size, self.theme.mode)
        if key in self._cache:
            return self._cache[key]

        disk_path_svg = os.path.join(ASSETS_ROOT, category, f"{name}.svg")
        disk_path_png = os.path.join(ASSETS_ROOT, category, f"{name}.png")

        pixmap = None
        try:
            if os.path.isfile(disk_path_svg):
                renderer = QSvgRenderer(disk_path_svg)
                if renderer.isValid():
                    pixmap = QPixmap(size, size)
                    pixmap.fill(Qt.transparent)
                    p = QPainter(pixmap)
                    p.setRenderHint(QPainter.Antialiasing)
                    renderer.render(p)
                    p.end()
            elif os.path.isfile(disk_path_png):
                loaded = QPixmap(disk_path_png)
                if not loaded.isNull():
                    pixmap = loaded.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception:
            pixmap = None

        if pixmap is None:
            pixmap = self._draw_fallback(category, name, state, size)

        self._cache[key] = pixmap
        return pixmap

    def _draw_fallback(self, category, name, state, size):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        c = self.theme.colors
        rect = QRectF(2, 2, size - 4, size - 4)

        drawers = {
            "herbivore": self._draw_herbivore,
            "fox": self._draw_fox,
            "plant": self._draw_plant,
            "berry_bush": self._draw_berry_bush,
            "water": self._draw_water,
            "shelter": self._draw_shelter,
        }
        icon_drawers = {
            "play": self._icon_play,
            "pause": self._icon_pause,
            "reset": self._icon_reset,
            "save": self._icon_save,
            "settings": self._icon_settings,
            "history": self._icon_history,
            "back": self._icon_back,
            "visibility": self._icon_visibility,
            "logo": self._icon_logo,
        }

        if category == "animals" or name in drawers:
            drawers.get(name, self._draw_generic_dot)(painter, rect, state, c)
        elif category == "icons" or name in icon_drawers:
            icon_drawers.get(name, self._icon_generic)(painter, rect, c)
        elif category == "plants":
            self._draw_plant(painter, rect, name, c)
        elif category == "environment":
            (self._draw_water if "water" in name else self._draw_shelter)(painter, rect, state, c)
        else:
            self._draw_generic_dot(painter, rect, state, c)

        painter.end()
        return pixmap

    def _state_color(self, state, c):
        return {
            "healthy": QColor(c.success),
            "tired": QColor(c.warning),
            "thirsty": QColor(c.lake),
            "critical": QColor(c.danger),
            "fleeing": QColor(c.danger),
            "drinking": QColor(c.lake),
            "hungry": QColor(c.warning),
            "hunting": QColor(c.danger),
            "old": QColor(c.muted),
        }.get(state, QColor(c.forest))

    def _draw_herbivore(self, p, rect, state, c):
        body_color = QColor("#E9CBA3") if state not in ("critical", "fleeing") else QColor("#D8B389")
        ear_inner = QColor("#F6E4CC")
        accent = self._state_color(state, c)
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() / 2.6

        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(body_color.darker(112)))
        p.drawEllipse(QPointF(cx - r * 0.32, cy + r * 0.98), r * 0.24, r * 0.16)
        p.drawEllipse(QPointF(cx + r * 0.32, cy + r * 0.98), r * 0.24, r * 0.16)

  
        p.setBrush(QBrush(body_color))
        p.drawEllipse(QPointF(cx, cy + r * 0.62), r * 0.72, r * 0.55)

        for side in (-1, 1):
            p.save()
            p.translate(cx + side * r * 0.32, cy - r * 0.55)
            p.rotate(side * 14)
            p.setBrush(QBrush(body_color))
            p.drawRoundedRect(QRectF(-r * 0.17, -r * 0.62, r * 0.34, r * 0.66), r * 0.16, r * 0.16)
            p.setBrush(QBrush(ear_inner))
            p.drawRoundedRect(QRectF(-r * 0.09, -r * 0.48, r * 0.18, r * 0.46), r * 0.09, r * 0.09)
            p.restore()


        p.setBrush(QBrush(body_color))
        p.drawEllipse(QPointF(cx, cy - r * 0.18), r * 0.82, r * 0.78)

 
        p.setBrush(QBrush(QColor(255, 176, 176, 130)))
        p.drawEllipse(QPointF(cx - r * 0.44, cy + r * 0.02), r * 0.15, r * 0.1)
        p.drawEllipse(QPointF(cx + r * 0.44, cy + r * 0.02), r * 0.15, r * 0.1)

        p.setBrush(QBrush(QColor("#2B2117")))
        p.drawEllipse(QPointF(cx - r * 0.27, cy - r * 0.14), r * 0.15, r * 0.19)
        p.drawEllipse(QPointF(cx + r * 0.27, cy - r * 0.14), r * 0.15, r * 0.19)
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(QPointF(cx - r * 0.22, cy - r * 0.2), r * 0.045, r * 0.05)
        p.drawEllipse(QPointF(cx + r * 0.32, cy - r * 0.2), r * 0.045, r * 0.05)

        p.setBrush(QBrush(QColor("#D98A8A")))
        p.drawEllipse(QPointF(cx, cy + r * 0.06), r * 0.06, r * 0.045)

        if state == "drinking":
            p.setPen(QPen(Qt.NoPen))
            p.setBrush(QBrush(QColor(c.lake)))
            p.drawEllipse(QPointF(cx + r * 0.7, cy + r * 1.05), r * 0.13, r * 0.13)

    def _draw_fox(self, p, rect, state, c):
        body_color = QColor("#E8895A") if state != "critical" else QColor("#CE7A50")
        muzzle_color = QColor("#FBEEE0")
        accent = self._state_color(state, c)
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() / 2.6

        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(body_color))
        p.drawEllipse(QPointF(cx - r * 0.95, cy + r * 0.3), r * 0.5, r * 0.32)
        p.setBrush(QBrush(muzzle_color))
        p.drawEllipse(QPointF(cx - r * 1.22, cy + r * 0.26), r * 0.2, r * 0.16)

        p.setBrush(QBrush(body_color.darker(112)))
        p.drawEllipse(QPointF(cx - r * 0.3, cy + r * 0.98), r * 0.22, r * 0.15)
        p.drawEllipse(QPointF(cx + r * 0.3, cy + r * 0.98), r * 0.22, r * 0.15)

        p.setBrush(QBrush(body_color))
        p.drawEllipse(QPointF(cx, cy + r * 0.6), r * 0.68, r * 0.5)

        for side in (-1, 1):
            p.setBrush(QBrush(body_color))
            outer = QPolygonF([
                QPointF(cx + side * r * 0.32, cy - r * 0.5),
                QPointF(cx + side * r * 0.58, cy - r * 1.05),
                QPointF(cx + side * r * 0.1, cy - r * 0.62),
            ])
            p.drawPolygon(outer)
            p.setBrush(QBrush(QColor("#3C2A1F")))
            inner = QPolygonF([
                QPointF(cx + side * r * 0.34, cy - r * 0.58),
                QPointF(cx + side * r * 0.5, cy - r * 0.9),
                QPointF(cx + side * r * 0.2, cy - r * 0.64),
            ])
            p.drawPolygon(inner)

        p.setBrush(QBrush(body_color))
        p.drawEllipse(QPointF(cx, cy - r * 0.15), r * 0.8, r * 0.74)


        p.setBrush(QBrush(muzzle_color))
        p.drawEllipse(QPointF(cx, cy + r * 0.14), r * 0.42, r * 0.32)


        p.setBrush(QBrush(QColor(255, 150, 150, 120)))
        p.drawEllipse(QPointF(cx - r * 0.5, cy + r * 0.04), r * 0.13, r * 0.09)
        p.drawEllipse(QPointF(cx + r * 0.5, cy + r * 0.04), r * 0.13, r * 0.09)


        p.setBrush(QBrush(QColor("#2B2117")))
        p.drawEllipse(QPointF(cx - r * 0.28, cy - r * 0.1), r * 0.14, r * 0.18)
        p.drawEllipse(QPointF(cx + r * 0.28, cy - r * 0.1), r * 0.14, r * 0.18)
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(QPointF(cx - r * 0.23, cy - r * 0.16), r * 0.04, r * 0.045)
        p.drawEllipse(QPointF(cx + r * 0.33, cy - r * 0.16), r * 0.04, r * 0.045)


        p.setBrush(QBrush(QColor("#2B2117")))
        p.drawEllipse(QPointF(cx, cy + r * 0.2), r * 0.06, r * 0.045)

    def _draw_plant(self, p, rect, maturity, c):
        cx = rect.center().x()
        base = rect.bottom()
        scale = {"plant_small": 0.55, "plant_medium": 0.8, "plant_mature": 1.0}.get(maturity, 0.8)
        leaf_color = QColor(c.forest)
        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(leaf_color))
        for angle_deg, sign in ((20, 1), (-20, -1), (0, 1)):
            path = QPainterPath()
            tip = QPointF(cx + sign * rect.width() * 0.28 * scale, base - rect.height() * 0.85 * scale)
            path.moveTo(cx, base)
            path.cubicTo(cx + sign * rect.width() * 0.35, base - rect.height() * 0.5,
                         tip.x(), tip.y() + rect.height() * 0.1, tip.x(), tip.y())
            path.cubicTo(tip.x() - sign * rect.width() * 0.1, tip.y() + rect.height() * 0.2,
                         cx, base - rect.height() * 0.15, cx, base)
            p.drawPath(path)

    def _draw_berry_bush(self, p, rect, state, c):
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() / 2.3
        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(QColor(c.forest)))
        p.drawEllipse(QPointF(cx, cy), r, r * 0.85)
        p.setBrush(QBrush(QColor("#6C3B6E")))
        for dx, dy in ((-0.3, -0.1), (0.3, -0.1), (0, 0.3), (-0.15, 0.15), (0.15, -0.35)):
            p.drawEllipse(QPointF(cx + r * dx, cy + r * dy), r * 0.14, r * 0.14)

    def _draw_water(self, p, rect, state, c):
        p.setPen(QPen(QColor(c.lake).darker(115), 1.5))
        p.setBrush(QBrush(QColor(c.lake)))
        p.setOpacity(0.55)
        p.drawEllipse(rect)
        p.setOpacity(1.0)
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.28
        path = QPainterPath()
        path.moveTo(cx - r, cy)
        path.cubicTo(cx - r * 0.5, cy - r * 0.4, cx - r * 0.2, cy + r * 0.4, cx + r * 0.3, cy)
        path.cubicTo(cx + r * 0.6, cy - r * 0.3, cx + r * 0.9, cy + r * 0.2, cx + r, cy)
        p.setOpacity(0.7)
        p.drawPath(path)
        p.setOpacity(1.0)

    def _draw_shelter(self, p, rect, state, c):
        cx, cy = rect.center().x(), rect.center().y()
        w, h = rect.width(), rect.height()
        p.setPen(QPen(QColor("#5D4630"), 1.5))
        p.setBrush(QBrush(QColor("#8A6644")))
        roof = QPolygonF([QPointF(cx - w * 0.35, cy + h * 0.05), QPointF(cx, cy - h * 0.32), QPointF(cx + w * 0.35, cy + h * 0.05)])
        p.drawPolygon(roof)
        p.setBrush(QBrush(QColor("#6E4E33")))
        p.drawRect(QRectF(cx - w * 0.22, cy + h * 0.02, w * 0.44, h * 0.28))
        p.setBrush(QBrush(QColor("#3C2A1B")))
        p.drawRect(QRectF(cx - w * 0.06, cy + h * 0.14, w * 0.12, h * 0.16))

    def _draw_generic_dot(self, p, rect, state, c):
        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(QColor(c.moss)))
        p.drawEllipse(rect)

    def _icon_play(self, p, rect, c):
        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(QColor(c.text)))
        cx, cy, s = rect.center().x(), rect.center().y(), rect.width() * 0.32
        p.drawPolygon(QPolygonF([QPointF(cx - s * 0.6, cy - s), QPointF(cx - s * 0.6, cy + s), QPointF(cx + s, cy)]))

    def _icon_pause(self, p, rect, c):
        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(QColor(c.text)))
        w = rect.width() * 0.18
        cx, cy, h = rect.center().x(), rect.center().y(), rect.height() * 0.34
        p.drawRoundedRect(QRectF(cx - w * 2, cy - h, w, h * 2), 1, 1)
        p.drawRoundedRect(QRectF(cx + w * 0.6, cy - h, w, h * 2), 1, 1)

    def _icon_reset(self, p, rect, c):
        p.setPen(QPen(QColor(c.text), 2))
        p.setBrush(QBrush(Qt.NoBrush))
        r = rect.adjusted(3, 3, -3, -3)
        p.drawArc(r, 30 * 16, 300 * 16)
        cx = rect.center().x() + r.width() * 0.42
        cy = rect.top() + 3
        p.setBrush(QBrush(QColor(c.text)))
        p.setPen(QPen(Qt.NoPen))
        p.drawPolygon(QPolygonF([QPointF(cx - 5, cy), QPointF(cx + 5, cy), QPointF(cx, cy + 7)]))

    def _icon_save(self, p, rect, c):
        p.setPen(QPen(QColor(c.text), 1.6))
        p.setBrush(QBrush(Qt.NoBrush))
        r = rect.adjusted(3, 3, -3, -3)
        p.drawRoundedRect(r, 3, 3)
        p.drawRect(QRectF(r.left() + r.width() * 0.22, r.top(), r.width() * 0.56, r.height() * 0.35))

    def _icon_settings(self, p, rect, c):
        p.setPen(QPen(QColor(c.text), 1.8))
        p.setBrush(QBrush(Qt.NoBrush))
        cx, cy, r = rect.center().x(), rect.center().y(), rect.width() * 0.22
        p.drawEllipse(QPointF(cx, cy), r, r)
        for i in range(8):
            a = math.radians(i * 45)
            x1, y1 = cx + math.cos(a) * r * 1.3, cy + math.sin(a) * r * 1.3
            x2, y2 = cx + math.cos(a) * r * 1.7, cy + math.sin(a) * r * 1.7
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _icon_history(self, p, rect, c):
        p.setPen(QPen(QColor(c.text), 1.8))
        p.setBrush(QBrush(Qt.NoBrush))
        r = rect.adjusted(3, 3, -3, -3)
        p.drawEllipse(r)
        cx, cy = r.center().x(), r.center().y()
        p.drawLine(QPointF(cx, cy), QPointF(cx, cy - r.height() * 0.28))
        p.drawLine(QPointF(cx, cy), QPointF(cx + r.width() * 0.2, cy))

    def _icon_back(self, p, rect, c):
        p.setPen(QPen(QColor(c.text), 2.2))
        cx, cy = rect.center().x(), rect.center().y()
        s = rect.width() * 0.22
        p.drawLine(QPointF(cx + s, cy - s), QPointF(cx - s, cy))
        p.drawLine(QPointF(cx - s, cy), QPointF(cx + s, cy + s))

    def _icon_visibility(self, p, rect, c):
        p.setPen(QPen(QColor(c.text), 1.8))
        p.setBrush(QBrush(Qt.NoBrush))
        r = rect.adjusted(2, 6, -2, -6)
        p.drawEllipse(r)
        p.setBrush(QBrush(QColor(c.text)))
        p.drawEllipse(r.center(), r.width() * 0.16, r.width() * 0.16)

    def _icon_logo(self, p, rect, c):
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() / 2.2
        p.setPen(QPen(Qt.NoPen))
        p.setBrush(QBrush(QColor(c.forest)))
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setBrush(QBrush(QColor(c.sage)))
        p.drawEllipse(QPointF(cx - r * 0.25, cy - r * 0.1), r * 0.55, r * 0.55)
        p.setBrush(QBrush(QColor(c.sand)))
        p.drawEllipse(QPointF(cx + r * 0.3, cy + r * 0.25), r * 0.28, r * 0.28)

    def _icon_generic(self, p, rect, c):
        p.setPen(QPen(QColor(c.text), 1.5))
        p.setBrush(QBrush(Qt.NoBrush))
        p.drawRoundedRect(rect, 4, 4)
