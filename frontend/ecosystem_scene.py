import math
import random

from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QColor, QPen, QBrush, QRadialGradient, QLinearGradient, QPainter
from PyQt5.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsItem,
)


SEASON_OVERLAY = {
    "spring": QColor(160, 220, 130, 40),
    "summer": QColor(255, 220, 120, 25),
    "autumn": QColor(210, 120, 40, 55),
    "winter": QColor(210, 230, 255, 70),
}

SEASON_TERRAIN = {
    "spring": (QColor("#DCEFC7"), QColor("#8FBF7A")),
    "summer": (QColor("#C9E4B0"), QColor("#5FA05C")),
    "autumn": (QColor("#EAD3A0"), QColor("#B97B3E")),
    "winter": (QColor("#EAF2F7"), QColor("#C3D6E0")),
}


def herbivore_state(entity):
    if entity.get("health", 100) < 100:
        return "sick"
    if entity.get("is_drinking"):
        return "drinking"
    if entity.get("nearest_fox_dist", 9999) < 100:
        return "fleeing"
    if entity.get("thirst", 0) > 220:
        return "thirsty"
    if entity.get("energy", 300) <= 50:
        return "critical"
    if entity.get("energy", 300) <= 110:
        return "tired"
    if entity.get("max_age") and entity.get("age", 0) > entity["max_age"] * 0.85:
        return "old"
    return "healthy"


def fox_state(entity):
    if entity.get("health", 100) < 100:
        return "sick"
    if entity.get("thirst", 0) > 260:
        return "thirsty"
    if entity.get("energy", 300) <= 60:
        return "critical"
    if entity.get("hunger", 0) > 250:
        return "hungry"
    if entity.get("is_hunting"):
        return "hunting"
    if entity.get("max_age") and entity.get("age", 0) > entity["max_age"] * 0.85:
        return "old"
    return "healthy"


class EntityItem(QGraphicsPixmapItem):
    def __init__(self, entity_type):
        super().__init__()
        self.entity_type = entity_type
        self.entity_data = {}
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue({"water": 1, "shelter": 1, "plant": 2, "berry_bush": 2,
                         "herbivore": 3, "fox": 3}.get(entity_type, 2))

    def hoverEnterEvent(self, event):
        self.setToolTip(self._tooltip_text())
        super().hoverEnterEvent(event)

    def _id_suffix(self):
        entity_id = self.entity_data.get("id")
        return f" #{entity_id}" if entity_id is not None else ""

    def _tooltip_text(self):
        d = self.entity_data
        t = self.entity_type
        if t == "herbivore":
            return (f"Herbivore{self._id_suffix()}\nAge {d.get('age')}\n"
                     f"Energy {d.get('energy', 0):.0f}  Thirst {d.get('thirst', 0):.0f}\n"
                     f"Nearest fox: {d.get('nearest_fox_dist')}")
        if t == "fox":
            return (f"Fox{self._id_suffix()}\nAge {d.get('age')}\n"
                     f"Energy {d.get('energy', 0):.0f}  Hunger {d.get('hunger', 0):.0f}  "
                     f"Thirst {d.get('thirst', 0):.0f}")
        if t == "plant":
            return f"Plant{self._id_suffix()}\nAge {d.get('age')}\nFood value {d.get('food_value')}"
        if t == "berry_bush":
            return f"Berry bush{self._id_suffix()}\nFood value {d.get('food_value')}"
        if t == "tree":
            return f"Tree{self._id_suffix()}\nAge {d.get('age')}\nHeight {d.get('height')}"
        if t == "water":
            return f"Water source{self._id_suffix()}\nRadius {d.get('radius')}"
        if t == "shelter":
            return f"Shelter{self._id_suffix()}\nRadius {d.get('radius')}"
        return t


class EcosystemScene(QGraphicsScene):
    def __init__(self, asset_manager, world_width=1000, world_height=700):
        super().__init__()
        self.assets = asset_manager
        self.world_width = world_width
        self.world_height = world_height
        self.show_vision = True
        self.show_labels = False
        self.show_particles = True
        self.show_status_rings = True
        self.items_by_id = {}
        self._vision_rings = []
        self._status_rings = []
        self._particles = []
        self._disaster_effects = []
        self._disaster_items = []
        self._effect_phase = 0
        self._particle_seed = [(random.random(), random.random(), random.random()) for _ in range(70)]
        self.setSceneRect(0, 0, world_width, world_height)
        self._terrain_item = QGraphicsRectItem(0, 0, world_width, world_height)
        self._terrain_item.setZValue(-10)
        self.addItem(self._terrain_item)
        self._overlay_item = QGraphicsRectItem(0, 0, world_width, world_height)
        self._overlay_item.setZValue(-5)
        self._overlay_item.setPen(QPen(Qt.NoPen))
        self.addItem(self._overlay_item)
        self._season = "summer"
        self.set_season("summer")

    def set_world_size(self, w, h):
        if (w, h) != (self.world_width, self.world_height):
            self.world_width, self.world_height = w, h
            self.setSceneRect(0, 0, w, h)
            self._terrain_item.setRect(0, 0, w, h)
            self._overlay_item.setRect(0, 0, w, h)

    def set_season(self, season):
        self._season = season
        floor_color, edge_color = SEASON_TERRAIN.get(season, SEASON_TERRAIN["summer"])
        grad = QLinearGradient(0, 0, 0, self.world_height)
        grad.setColorAt(0, floor_color.lighter(106))
        grad.setColorAt(1, edge_color)
        self._terrain_item.setBrush(QBrush(grad))
        self._terrain_item.setPen(QPen(Qt.NoPen))
        self._overlay_item.setBrush(QBrush(SEASON_OVERLAY.get(season, SEASON_OVERLAY["summer"])))

    def add_disaster_effect(self, disaster_type, x=None, y=None, duration=90):
        if disaster_type == "drought":
            x = self.world_width / 2
            y = self.world_height / 2
        
        self._disaster_effects.append({
        "type": disaster_type,
        "x": float(x or 0),
        "y": float(y or 0),
        "remaining": int(duration),
        })
        self._redraw_disaster_effects()

    def advance_effects(self):
        self._effect_phase = (self._effect_phase + 1) % 360
        active_effects = []
        for effect in self._disaster_effects:
            effect["remaining"] -= 1
            if effect["remaining"] > 0:
                active_effects.append(effect)
        self._disaster_effects = active_effects
        self._redraw_disaster_effects()

    def clear_disaster_effects(self):
        self._disaster_effects.clear()
        self._redraw_disaster_effects()

    def _redraw_disaster_effects(self):
        for item in self._disaster_items:
            self.removeItem(item)
        self._disaster_items = []
        for effect in self._disaster_effects:
            disaster_type = effect["type"]
            x = effect["x"]
            y = effect["y"]
            remaining = effect["remaining"]

            pulse = 1.0 + 0.08 * math.sin(
                math.radians(self._effect_phase * 8)
            )

            if disaster_type == "wildfire":
                radius = 150 * pulse

                
                burn_area = QGraphicsEllipseItem(
                    -radius,
                    -radius,
                    radius * 2,
                    radius * 2,
                )
                burn_area.setPos(x, y)
                burn_area.setPen(
                    QPen(QColor(255, 90, 20, 170), 3)
                )
                burn_area.setBrush(
                    QBrush(QColor(185, 55, 20, 75))
                )
                burn_area.setZValue(40)

                self.addItem(burn_area)
                self._disaster_items.append(burn_area)

                
                for i in range(16):
                    angle = (
                        i * 22.5 +
                        self._effect_phase * 4
                    ) % 360

                    particle_radius = 35 + (i % 4) * 18

                    flame_x = (
                        x +
                        math.cos(math.radians(angle)) *
                        particle_radius
                    )
                    flame_y = (
                        y +
                        math.sin(math.radians(angle)) *
                        particle_radius *
                        0.55
                    )

                    flame = QGraphicsEllipseItem(
                        -8,
                        -14,
                        16,
                        28,
                    )
                    flame.setPos(flame_x, flame_y)
                    flame.setPen(QPen(Qt.NoPen))
                    flame.setBrush(
                        QBrush(
                            QColor(
                                255,
                                120 + (i % 3) * 35,
                                20,
                                210,
                            )
                        )
                    )
                    flame.setZValue(45)

                    self.addItem(flame)
                    self._disaster_items.append(flame)

                
                for i in range(10):
                    smoke = QGraphicsEllipseItem(
                        -10,
                        -10,
                        20,
                        20,
                    )

                    smoke_x = x - 60 + i * 13
                    smoke_y = (
                        y -
                        55 -
                        (
                            (
                                self._effect_phase * 2 +
                                i * 17
                            ) % 70
                        )
                    )

                    smoke.setPos(smoke_x, smoke_y)
                    smoke.setPen(QPen(Qt.NoPen))
                    smoke.setBrush(
                        QBrush(QColor(70, 70, 70, 105))
                    )
                    smoke.setZValue(46)

                    self.addItem(smoke)
                    self._disaster_items.append(smoke)

            elif disaster_type == "plague":
                radius = 150 * pulse

                plague_cloud = QGraphicsEllipseItem(
                    -radius,
                    -radius,
                    radius * 2,
                    radius * 2,
                )
                plague_cloud.setPos(x, y)
                plague_cloud.setPen(
                    QPen(
                        QColor(117, 76, 158, 180),
                        3,
                        Qt.DashLine,
                    )
                )
                plague_cloud.setBrush(
                    QBrush(QColor(112, 180, 80, 55))
                )
                plague_cloud.setZValue(40)

                self.addItem(plague_cloud)
                self._disaster_items.append(plague_cloud)

                
                for i in range(18):
                    angle = (
                        i * 20 +
                        self._effect_phase * 2
                    )

                    particle_radius = 25 + (i % 5) * 21

                    bubble_x = (
                        x +
                        math.cos(math.radians(angle)) *
                        particle_radius
                    )
                    bubble_y = (
                        y +
                        math.sin(math.radians(angle)) *
                        particle_radius
                    )

                    bubble = QGraphicsEllipseItem(
                        -6,
                        -6,
                        12,
                        12,
                    )
                    bubble.setPos(bubble_x, bubble_y)
                    bubble.setPen(QPen(Qt.NoPen))
                    bubble.setBrush(
                        QBrush(QColor(130, 75, 165, 145))
                    )
                    bubble.setZValue(44)

                    self.addItem(bubble)
                    self._disaster_items.append(bubble)

            elif disaster_type == "drought":              
                drought_overlay = QGraphicsRectItem(
                    0,
                    0,
                    self.world_width,
                    self.world_height,
                )

                alpha = max(
                    20,
                    min(90, remaining),
                )

                drought_overlay.setPen(QPen(Qt.NoPen))
                drought_overlay.setBrush(
                    QBrush(QColor(176, 120, 50, alpha))
                )
                drought_overlay.setZValue(39)

                self.addItem(drought_overlay)
                self._disaster_items.append(drought_overlay)

    def sync(self, state):

        entities = state.get("entities", [])
        season = state.get("season", "summer")
        if season != self._season:
            self.set_season(season)

        seen_ids = set()
        type_counters = {}
        for entity in entities:
            etype = entity["type"]
            idx = type_counters.get(etype, 0)
            type_counters[etype] = idx + 1
            key = (etype, entity.get("id", idx))
            seen_ids.add(key)
            item = self.items_by_id.get(key)
            if item is None:
                item = EntityItem(etype)
                self.items_by_id[key] = item
                self.addItem(item)
            item.entity_data = entity
            self._update_item_visual(item, entity)

        stale = [k for k in self.items_by_id if k not in seen_ids]
        for k in stale:
            item = self.items_by_id.pop(k)
            self.removeItem(item)

        self._update_vision_rings(entities)
        self._update_status_rings(entities)
        if self.show_particles:
            self._update_particles()
        else:
            for p in self._particles:
                self.removeItem(p)
            self._particles = []

    def _update_item_visual(self, item, entity):
        etype = entity["type"]
        x, y = entity.get("x", 0), entity.get("y", 0)
        if etype == "herbivore":
            state = herbivore_state(entity)
            size = 36
            pixmap = self.assets.get_pixmap("animals", "herbivore", size=size, state=state)
        elif etype == "fox":
            state = fox_state(entity)
            size = 40
            pixmap = self.assets.get_pixmap("animals", "fox", size=size, state=state)
        elif etype == "plant":
            fv = entity.get("food_value", 10)
            maturity = "plant_mature" if fv > 30 else "plant_medium" if fv > 18 else "plant_small"
            size = 18 if fv > 30 else 15 if fv > 18 else 12
            pixmap = self.assets.get_pixmap("plants", maturity, size=size)
        elif etype == "berry_bush":
            size = 22
            pixmap = self.assets.get_pixmap("plants", "berry_bush", size=size)
        elif etype == "water":
            size = max(24, int(entity.get("radius", 40) * 2))
            pixmap = self.assets.get_pixmap("environment", "water_source", size=size)
        elif etype == "shelter":
            size = max(24, int(entity.get("radius", 50) * 2))
            pixmap = self.assets.get_pixmap("environment", "shelter", size=size)
        elif etype == "tree":
            size = max(30, int(entity.get("radius", 40) * 1.8))
            pixmap = self.assets.get_pixmap("environment", "tree", size=size)
        else:
            return

        if item.pixmap().cacheKey() != pixmap.cacheKey():
            item.setPixmap(pixmap)
            item.setOffset(-pixmap.width() / 2, -pixmap.height() / 2)
        item.setPos(x, y)

    def _update_vision_rings(self, entities):
        for ring in self._vision_rings:
            self.removeItem(ring)
        self._vision_rings = []
        if not self.show_vision:
            return
        for entity in entities:
            if entity["type"] not in ("herbivore", "fox"):
                continue
            vision = entity.get("vision", 0)
            if not vision:
                continue
            color = QColor(90, 90, 90, 26) if entity["type"] == "herbivore" else QColor(230, 100, 20, 30)
            ring = QGraphicsEllipseItem(-vision, -vision, vision * 2, vision * 2)
            ring.setPos(entity.get("x", 0), entity.get("y", 0))
            ring.setPen(QPen(color, 1))
            ring.setBrush(QBrush(Qt.NoBrush))
            ring.setZValue(0.5)
            self.addItem(ring)
            self._vision_rings.append(ring)

    def _update_status_rings(self, entities):
        for ring in self._status_rings:
            self.removeItem(ring)
        self._status_rings = []
        if not self.show_status_rings:
            return
        for entity in entities:
            if entity["type"] == "herbivore":
                state = herbivore_state(entity)
                radius = 20
            elif entity["type"] == "fox":
                state = fox_state(entity)
                radius = 22
            else:
                continue
            color = self.assets.status_ring_color(state)
            ring = QGraphicsEllipseItem(-radius, -radius, radius * 2, radius * 2)
            ring.setPos(entity.get("x", 0), entity.get("y", 0))
            pen = QPen(color, 2.4)
            if state == "hunting":
                pen.setStyle(Qt.DashLine)
            ring.setPen(pen)
            ring.setBrush(QBrush(Qt.NoBrush))
            ring.setZValue(4)
            self.addItem(ring)
            self._status_rings.append(ring)

    def _update_particles(self):
        for p in self._particles:
            self.removeItem(p)
        self._particles = []
        if self._season == "winter":
            color = QColor(255, 255, 255, 210)
            for i, (rx, ry, rs) in enumerate(self._particle_seed):
                x = rx * self.world_width
                y = ((ry * self.world_height) + i * 3) % self.world_height
                dot = QGraphicsEllipseItem(x, y, 2 + rs * 2, 2 + rs * 2)
                dot.setBrush(QBrush(color))
                dot.setPen(QPen(Qt.NoPen))
                dot.setZValue(50)
                self.addItem(dot)
                self._particles.append(dot)
        elif self._season == "autumn":
            color = QColor(180, 96, 30, 210)
            for i, (rx, ry, rs) in enumerate(self._particle_seed[:36]):
                x = rx * self.world_width
                y = ((ry * self.world_height) + i * 5) % self.world_height
                leaf = QGraphicsEllipseItem(x, y, 5 + rs * 4, 3 + rs * 2)
                leaf.setBrush(QBrush(color))
                leaf.setPen(QPen(Qt.NoPen))
                leaf.setRotation(rs * 360)
                leaf.setZValue(50)
                self.addItem(leaf)
                self._particles.append(leaf)


class EcosystemView(QGraphicsView):
    entity_selected = pyqtSignal(dict)
    map_clicked_for_disaster = pyqtSignal(float, float)
    map_clicked_for_placement = pyqtSignal(float, float)
    interaction_cancelled = pyqtSignal()

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self._selection_ring = None
        self.disaster_mode = None
        self.placement_mode = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        if (
            event.button() == Qt.RightButton
            and (
                self.disaster_mode is not None
                or self.placement_mode is not None
            )
        ):
            self.cancel_interaction()
            return

        if self.disaster_mode is not None:
            self.map_clicked_for_disaster.emit(
                scene_pos.x(),
                scene_pos.y(),
            )
            return

        if self.placement_mode is not None:
            self.map_clicked_for_placement.emit(
                scene_pos.x(),
                scene_pos.y(),
            )
            return

        entity_item = None
        for item in self.scene().items(scene_pos):
            if isinstance(item, EntityItem):
                entity_item = item
                break

        if entity_item is not None:
            self._show_selection(entity_item)
            self.entity_selected.emit(dict(entity_item.entity_data))
        super().mousePressEvent(event)

    def _show_selection(self, item):
        if self._selection_ring:
            self.scene().removeItem(self._selection_ring)
            self._selection_ring = None
        r = max(item.pixmap().width(), item.pixmap().height()) / 2 + 4
        ring = QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
        ring.setPos(item.pos())
        ring.setPen(QPen(QColor("#4C8CA6"), 2.4))
        ring.setZValue(99)
        self.scene().addItem(ring)
        self._selection_ring = ring

    def cancel_interaction(self):
        self.disaster_mode = None
        self.placement_mode = None
        self.setCursor(Qt.ArrowCursor)
        self.interaction_cancelled.emit()


    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_Escape
            and (
                self.disaster_mode is not None
                or self.placement_mode is not None
            )
        ):
            self.cancel_interaction()
            event.accept()
            return

        super().keyPressEvent(event)