import csv
import json
import random

from backend.engine import SimulationEngine, Plant, BerryBush, Herbivore, Fox, WaterSource, Shelter, Tree

PRESETS = {
    "Balanced Forest": dict(plants=150, berry_bushes=15, herbivores=10, foxes=4, water_sources=5, shelters=4),
    "Predator Pressure": dict(plants=140, berry_bushes=10, herbivores=14, foxes=9, water_sources=5, shelters=4),
    "Food Scarcity": dict(plants=40, berry_bushes=4, herbivores=14, foxes=3, water_sources=5, shelters=4),
    "Water Scarcity": dict(plants=150, berry_bushes=15, herbivores=12, foxes=4, water_sources=1, shelters=4),
    "Herbivore Boom": dict(plants=220, berry_bushes=20, herbivores=30, foxes=2, water_sources=7, shelters=5),
}

SAFE_LIMITS = {
    "plants": (0, 1000), "berry_bushes": (0, 100), "herbivores": (0, 250),
    "foxes": (0, 90), "water_sources": (0, 35), "shelters": (0, 25),
}


class SaveManager:
    def __init__(self, database):
        self.db = database

    def validate_counts(self, counts):
        errors = []
        for key, (lo, hi) in SAFE_LIMITS.items():
            value = counts.get(key, 0)
            if value < lo or value > hi:
                errors.append(f"{key.replace('_', ' ').title()} must be between {lo} and {hi} (got {value}).")
        return errors

    def build_engine(self, counts, season="summer"):
        engine = SimulationEngine()
        world = engine.world
        world.plants, world.herbivores, world.berry_bushes = [], [], []
        world.foxes, world.water_sources, world.shelters = [], [], []

        w, h = world.width, world.height
        for i in range(counts.get("plants", 0)):
            world.plants.append(Plant(i, random.randint(0, w), random.randint(0, h), 20))
        for i in range(counts.get("berry_bushes", 0)):
            world.berry_bushes.append(BerryBush(100000 + i, random.randint(0, w), random.randint(0, h)))
        for i in range(counts.get("herbivores", 0)):
            world.herbivores.append(Herbivore(i, random.randint(0, w), random.randint(0, h), 100, 150, 0, 3, 150))
        for i in range(counts.get("foxes", 0)):
            world.foxes.append(Fox(200000 + i, random.randint(0, w), random.randint(0, h), 100, 0, 200, 0, 4, 200))
        for i in range(counts.get("water_sources", 0)):
            world.water_sources.append(WaterSource(300000 + i, random.randint(100, max(101, w - 100)), random.randint(100, max(101, h - 100)), 40))
        for i in range(counts.get("shelters", 0)):
            world.shelters.append(Shelter(400000 + i, random.randint(100, max(101, w - 100)), random.randint(100, max(101, h - 100)), 50))

        engine.current_tick = 0
        engine.season = season
        engine.season_tick = 0
        engine.pause()
        return engine

    def save(self, user_id, save_name, engine):
        return self.db.save_full_state(user_id, save_name, engine.save_full_state())

    def load(self, save_id):
        record = self.db.load_full_state(save_id)
        if record is None:
            return None
        engine = SimulationEngine()
        engine.load_full_state(record["state"])
        engine.pause()
        return engine, record

    def export_csv(self, filepath, rows, headers):
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    def export_json(self, filepath, data):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
