import random

class Organism:
    def __init__(self, id, x, y, health, energy, age, speed, vision):
        self.id = id
        self.x = x
        self.y = y
        self.health = health
        self.energy = energy
        self.age = age
        self.speed = speed
        self.vision = vision
        self.reproduce_cooldown = 0
        self.max_age = random.randint(800, 1500)
        self.thirst = 0


class Plant:
    START_FOOD_VALUE = 20
    MAX_FOOD_VALUE = 40
    GROWTH_RATE = 0.05
    def __init__(self, id, x, y, food_value):
        self.id = id
        self.x = x
        self.y = y
        self.food_value = food_value
        self.age = 0

class Tree:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.radius = 40
        self.age = 0
        self.height = 1

class BerryBush:
    FOOD_VALUE = 50

    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.food_value = self.FOOD_VALUE
        self.age = 0

class WaterSource:
    def __init__(self, id, x, y, radius):
        self.id = id
        self.x = x
        self.y = y
        self.radius = radius

class Shelter:
    def __init__(self, id, x, y, radius):
        self.id = id
        self.x = x
        self.y = y
        self.radius = radius

class Herbivore(Organism):
    MAX_ENERGY = 300
    def __init__(self, id, x, y, health, energy, age, speed, vision):
        super().__init__(
            id, 
            x, 
            y, 
            health, 
            energy, 
            age, 
            speed, 
            vision
        )

        self.wander_dx = random.uniform(-1, 1)
        self.wander_dy = random.uniform(-1, 1)

        self.nearest_fox_distance = float("inf")

        self.memory_x = None
        self.memory_y = None
        self.memory_timer = 0

        self.water_memory_x = None
        self.water_memory_y = None
        self.water_memory_timer = 0

        self.is_drinking = False
        self.drinking_at_x = None
        self.drinking_at_y = None


    def update_behavior(self, world, season):
        closest_plant = None
        closest_distance = float("inf")

        for plant in world.plants + world.berry_bushes:
            distance = (
                (self.x - plant.x) ** 2 +
                (self.y - plant.y) ** 2
            ) ** 0.5

            if distance < self.vision and distance < closest_distance:
                closest_distance = distance
                closest_plant = plant
        
        self.thirst += 1
        nearest_fox = None
        nearest_fox_distance = float("inf")
        danger_radius = 200

        for fox in world.foxes:
            dist_to_fox = (
                (self.x - fox.x) ** 2 +
                (self.y - fox.y) ** 2
            ) ** 0.5
            if dist_to_fox < danger_radius and dist_to_fox < nearest_fox_distance:
                nearest_fox_distance = dist_to_fox
                nearest_fox = fox

        # flee from nearby fox
        if nearest_fox and (nearest_fox_distance < 100 or self.thirst < 80):
            self.nearest_fox_distance = nearest_fox_distance
            self.memory_x = None
            self.memory_y = None
            self.memory_timer = 0
            dx = self.x - nearest_fox.x
            dy = self.y - nearest_fox.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist > 0:
                self.x += (dx / dist) * self.speed * 1.2
                self.y += (dy / dist) * self.speed * 1.2

        # Drinking state machine
        elif self.thirst > 150 and self.energy > 80:
            if self.is_drinking:
                self.thirst = max(0, self.thirst - 25)
                if self.thirst < 80:
                    self.is_drinking = False
                    self.water_memory_x = self.drinking_at_x
                    self.water_memory_y = self.drinking_at_y
                    self.water_memory_timer = 800
                    self.energy += 10
            else:
                nearest_water = None
                nearest_water_dist = float("inf")
                for water in world.water_sources:
                    d = ((self.x - water.x)**2 + (self.y - water.y)**2) ** 0.5
                    if d < nearest_water_dist:
                        nearest_water_dist = d
                        nearest_water = water

                if nearest_water is None and self.water_memory_x is not None:
                    nearest_water_dist = ((self.x - self.water_memory_x)**2 + (self.y - self.water_memory_y)**2) ** 0.5
                    nearest_water = type('W', (), {'x': self.water_memory_x, 'y': self.water_memory_y, 'radius': 40})()

                if nearest_water:
                    if nearest_water_dist < nearest_water.radius:
                        self.is_drinking = True
                        self.drinking_at_x = nearest_water.x
                        self.drinking_at_y = nearest_water.y
                    else:
                        dx = nearest_water.x - self.x
                        dy = nearest_water.y - self.y
                        dist = (dx*dx + dy*dy) ** 0.5
                        if dist > 0:
                            self.x += (dx / dist) * self.speed
                            self.y += (dy / dist) * self.speed

        elif season == "winter" and self.energy > 100 and not closest_plant:
            nearest_shelter = None
            nearest_shelter_dist = float("inf")
            for shelter in world.shelters:
                d = ((self.x - shelter.x)**2 + (self.y - shelter.y)**2) ** 0.5
                if d < self.vision and d < nearest_shelter_dist:
                    nearest_shelter_dist = d
                    nearest_shelter = shelter
            if nearest_shelter and nearest_shelter_dist > nearest_shelter.radius:
                dx = nearest_shelter.x - self.x
                dy = nearest_shelter.y - self.y
                dist = (dx*dx + dy*dy) ** 0.5
                if dist > 0:
                    self.x += (dx / dist) * self.speed
                    self.y += (dy / dist) * self.speed

        # move toward food if exists
        elif closest_plant:
            dx = closest_plant.x - self.x
            dy = closest_plant.y - self.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
        else:
            if self.memory_x is not None and self.memory_timer > 0:
                self.memory_timer -= 1
                dx = self.memory_x - self.x
                dy = self.memory_y - self.y
                dist = (dx*dx + dy*dy) ** 0.5
                if dist > 60:
                    target_dx = dx / dist
                    target_dy = dy / dist
                    strength = min(0.05, dist / 1000)
                    self.wander_dx += (target_dx - self.wander_dx) * strength
                    self.wander_dy += (target_dy - self.wander_dy) * strength
                else:
                    self.memory_x = None
                    self.memory_y = None
            else:
                if random.random() < 0.05:
                    self.wander_dx += random.uniform(-0.3, 0.3)
                    self.wander_dy += random.uniform(-0.3, 0.3)
                    total = (self.wander_dx**2 + self.wander_dy**2) ** 0.5
                    if total > 0:
                        self.wander_dx /= total
                        self.wander_dy /= total
            self.x += self.wander_dx * self.speed
            self.y += self.wander_dy * self.speed
        
        # bounds
        self.x = max(0, min(self.x, world.width))
        self.y = max(0, min(self.y, world.height))

        age_penalty = self.age / self.max_age * 0.2
        self.energy = min(self.energy, Herbivore.MAX_ENERGY)
        in_shelter = any(
            ((self.x - s.x)**2 + (self.y - s.y)**2) ** 0.5 < s.radius
            for s in world.shelters
        )
        winter_penalty = (0.01 if in_shelter else 0.02) if season == "winter" else 0.01 if season == "autumn" else -0.08 if season == "spring" else 0
        self.energy -= (0.25 + self.speed * 0.03 + age_penalty + winter_penalty)

        # eat plant
        if closest_plant and closest_distance < 25:
            self.energy += closest_plant.food_value
            self.memory_x = self.x
            self.memory_y = self.y
            self.memory_timer = 500
            if closest_plant in world.plants:
                    try:
                        world.plants.remove(closest_plant)
                    except ValueError:
                        pass
            elif closest_plant in world.berry_bushes:
                try:
                    world.berry_bushes.remove(closest_plant)
                except ValueError:
                    pass
        self.reproduce_cooldown -= 1

        if self.energy > 250 and self.reproduce_cooldown <= 0 and self.age > 150 and season != "winter":
            self.energy -= 120
            self.reproduce_cooldown = 130

            world.herbivores.append(
                Herbivore(
                    random.randint(100000, 999999),
                    self.x + random.randint(-10, 10),
                    self.y + random.randint(-10, 10),
                    100,
                    70,   
                    0,
                    max(1, self.speed + random.uniform(-0.3, 0.3)),
                    max(20, self.vision + random.randint(-5, 5))
                )
            )

        # death
        self.age += 1
        if self.energy <= 0 or self.age >= self.max_age:
            try:
                world.herbivores.remove(self)
            except ValueError:
                pass

class Fox(Organism):
    MAX_ENERGY = 400
    def __init__(self, id, x, y, health, hunger, energy, age, speed, vision):
        super().__init__(
            id, 
            x,
            y,
            health,
            energy,
            age,
            speed,
            vision
        )
        self.hunger = hunger
        self.wander_dx = random.uniform(-1, 1)
        self.wander_dy = random.uniform(-1, 1)

        self.memory_x = None
        self.memory_y = None
        self.memory_timer = 0

        self.water_memory_x = None
        self.water_memory_y = None
        self.water_memory_timer = 0

        self.is_drinking = False
        self.drinking_at_x = None
        self.drinking_at_y = None


    def update_behavior(self, world, season):
        closest_prey = None
        closest_distance = float("inf")
        for herbivore in world.herbivores:
            distance = (
                (self.x - herbivore.x) ** 2 +
                (self.y - herbivore.y) ** 2
            ) ** 0.5
            if distance < self.vision and distance < closest_distance:
                closest_distance = distance
                closest_prey = herbivore

        # Drinking State Machine
        if self.thirst > 300 and self.energy > 100:
            if self.is_drinking:
                self.thirst = max(0, self.thirst - 25)
                if self.thirst < 80:
                    self.is_drinking = False
                    self.water_memory_x = self.drinking_at_x
                    self.water_memory_y = self.drinking_at_y
                    self.water_memory_timer = 800
                    self.energy += 10
            else:
                nearest_water = None
                nearest_water_dist = float("inf")
                for water in world.water_sources:
                    d = ((self.x - water.x)**2 + (self.y - water.y)**2) ** 0.5
                    if d < nearest_water_dist:
                        nearest_water_dist = d
                        nearest_water = water

                if nearest_water is None and self.water_memory_x is not None:
                    nearest_water_dist = ((self.x - self.water_memory_x)**2 + (self.y - self.water_memory_y)**2) ** 0.5
                    nearest_water = type('W', (), {'x': self.water_memory_x, 'y': self.water_memory_y, 'radius': 40})()

                if nearest_water:
                    if nearest_water_dist < nearest_water.radius:
                        self.is_drinking = True
                        self.drinking_at_x = nearest_water.x
                        self.drinking_at_y = nearest_water.y
                    else:
                        dx = nearest_water.x - self.x
                        dy = nearest_water.y - self.y
                        dist = (dx*dx + dy*dy) ** 0.5
                        if dist > 0:
                            self.x += (dx / dist) * self.speed
                            self.y += (dy / dist) * self.speed

        elif closest_prey:
            dx = closest_prey.x - self.x
            dy = closest_prey.y - self.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

        elif season == "winter" and self.energy > 100:
            nearest_shelter = None
            nearest_shelter_dist = float("inf")
            for shelter in world.shelters:
                d = ((self.x - shelter.x)**2 + (self.y - shelter.y)**2) ** 0.5
                if d < self.vision and d < nearest_shelter_dist:
                    nearest_shelter_dist = d
                    nearest_shelter = shelter
            if nearest_shelter and nearest_shelter_dist > nearest_shelter.radius:
                dx = nearest_shelter.x - self.x
                dy = nearest_shelter.y - self.y
                dist = (dx*dx + dy*dy) ** 0.5
                if dist > 0:
                    self.x += (dx / dist) * self.speed
                    self.y += (dy / dist) * self.speed

        else:
            if self.memory_x is not None and self.memory_timer > 0:
                self.memory_timer -= 1
                dx = self.memory_x - self.x
                dy = self.memory_y - self.y
                dist = (dx*dx + dy*dy) ** 0.5
                if dist > 60:
                    target_dx = dx / dist
                    target_dy = dy / dist
                    strength = min(0.05, dist / 1000)
                    self.wander_dx += (target_dx - self.wander_dx) * strength
                    self.wander_dy += (target_dy - self.wander_dy) * strength
                else:
                    self.memory_x = None
                    self.memory_y = None
            else:
                if random.random() < 0.05:
                    self.wander_dx += random.uniform(-0.3, 0.3)
                    self.wander_dy += random.uniform(-0.3, 0.3)
                    total = (self.wander_dx**2 + self.wander_dy**2) ** 0.5
                    if total > 0:
                        self.wander_dx /= total
                        self.wander_dy /= total
            self.x += self.wander_dx * self.speed
            self.y += self.wander_dy * self.speed

        self.x = max(0, min(self.x, world.width))
        self.y = max(0, min(self.y, world.height))

        in_shelter = any(
            ((self.x - s.x)**2 + (self.y - s.y)**2) ** 0.5 < s.radius
            for s in world.shelters
        )
        fox_winter_penalty = (0.01 if in_shelter else 0.02) if season == "winter" else 0.01 if season == "autumn" else -0.04 if season == "spring" else 0
        self.energy = min(self.energy, Fox.MAX_ENERGY)
        self.energy -= (0.15 + self.speed * 0.01 + fox_winter_penalty)
        self.hunger += 1
        self.thirst += 1

        if self.hunger > 300:
            self.energy -= 5

        if closest_prey and closest_distance < 22:
            self.energy += 150
            self.hunger = 0
            self.memory_x = self.x
            self.memory_y = self.y
            self.memory_timer = 500
            if closest_prey in world.herbivores:
                try:
                    world.herbivores.remove(closest_prey)
                except ValueError:
                    pass

        self.reproduce_cooldown -= 1

        # eat berries if hungry and nearby
        for bush in world.berry_bushes[:]:
            dist_to_bush = (
                (self.x - bush.x) ** 2 +
                (self.y - bush.y) ** 2
            ) ** 0.5
            if dist_to_bush < 25 and self.hunger > 100:
                self.energy += 30
                self.hunger = max(0, self.hunger - 50)
                try:
                    world.berry_bushes.remove(bush)
                except ValueError:
                    pass
                break

        if self.energy > 300 and self.reproduce_cooldown <= 0 and self.age > 150 and len(world.foxes) < len(world.herbivores) // 6:
            self.energy -= 150
            self.reproduce_cooldown = 350
            world.foxes.append(
                Fox(
                    random.randint(100000, 999999),
                    self.x + random.randint(-10, 10),
                    self.y + random.randint(-10, 10),
                    100,
                    0,
                    150,
                    0,
                    max(1, self.speed + random.uniform(-0.3, 0.3)),
                    max(20, self.vision + random.randint(-5, 5))
                )
            )

        self.age += 1
        if self.energy <= 0 or self.age >= self.max_age:
            try:
                world.foxes.remove(self)
            except ValueError:
                pass



class World:
    def __init__(self):
        self.plants = []
        self.trees = []
        self.herbivores = []
        self.berry_bushes = []
        self.foxes = []
        self.water_sources = []
        self.shelters = []
        self.width = 1000
        self.height = 700

    def spawn_plants(self):
        for i in range(150):
            self.plants.append(
                Plant(
                    i,
                    random.randint(0, self.width),
                    random.randint(0, self.height),
                    Plant.START_FOOD_VALUE
                )
            )

    def spawn_herbivores(self):
        for i in range(10):
            self.herbivores.append(
                Herbivore(
                    i,
                    random.randint(0, self.width),
                    random.randint(0, self.height),
                    100,
                    150,
                    0,
                    3,
                    150
                )
            )

    def spawn_berry_bushes(self):
        for i in range(15):
            self.berry_bushes.append(
                BerryBush(
                    i,
                    random.randint(0, self.width),
                    random.randint(0, self.height)
                )
            )
    def spawn_trees(self):
        for i in range(50):
            self.trees.append(
                Tree(
                    i,
                    random.randint(0, self.width),
                    random.randint(0, self.height)
                )
            )
    def spawn_shelters(self):
        for i in range(4):
            self.shelters.append(
                Shelter(
                    i,
                    random.randint(100, self.width - 100),
                    random.randint(100, self.height - 100),
                    50
                )
            )

    def spawn_foxes(self):
        for i in range(4):
            self.foxes.append(
                Fox(
                    i,
                    random.randint(0, self.width),
                    random.randint(0, self.height),
                    100,
                    0,
                    200,
                    0,
                    4,
                    200
                )
            )
    def spawn_water_sources(self):
        for i in range(5):
            self.water_sources.append(
                WaterSource(
                    i,
                    random.randint(100, self.width - 100),
                    random.randint(100, self.height - 100),
                    40
                )
            )

class SimulationEngine:
    def __init__(self):
        self.world = World()
        self.running = False
        self.current_tick = 0
        self.season = "summer"
        self.season_tick = 0

        self.world.spawn_plants()
        self.world.spawn_herbivores()
        self.world.spawn_berry_bushes()
        self.world.spawn_foxes()
        self.world.spawn_water_sources()
        self.world.spawn_shelters()
        self.world.spawn_trees()


    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def update(self):
        if not self.running:
            return
        
        self.current_tick +=1

        self.update_season()
        self.update_herbivores()
        self.update_foxes()
        self.reintroduce_foxes()
        self.regrow_resources()
        

        # age plants and grow food value
        for plant in self.world.plants:
            plant.age += 1
            plant.food_value = min(
                Plant.MAX_FOOD_VALUE, 
                Plant.START_FOOD_VALUE + plant.age * Plant.GROWTH_RATE
            )


    def update_season(self):

        self.season_tick += 1

        if self.season_tick >= 1000:
            self.season_tick = 0

            seasons = [
            "spring",
            "summer",
            "autumn",
            "winter"
            ]

            current_index = seasons.index(self.season)
            self.season = seasons[(current_index + 1) % 4]


    def update_herbivores(self): 
        for herbivore in self.world.herbivores[:]:
            herbivore.update_behavior(self.world, self.season)


    def update_foxes(self):
        for fox in self.world.foxes[:]:
            fox.update_behavior(self.world, self.season)

    def reintroduce_foxes(self):
         # fox reintroduction if extinct
        if len(self.world.foxes) == 0 and len(self.world.herbivores) > 30:
            for _ in range(2):
                self.world.foxes.append(
                    Fox(
                        random.randint(100000, 999999),
                        random.randint(0, self.world.width),
                        random.randint(0, self.world.height),
                        100,
                        0,
                        200,
                        0,
                        4,
                        150
                    )
                )

    def regrow_resources(self):
        # plant regrowth
        if self.current_tick % 5 == 0:
            if len(self.world.plants) < 500:
                    for _ in range(6 if self.season == "winter" else 6 if self.season == "autumn" else 15 if self.season == "spring" else 12):
                        self.world.plants.append(
                            Plant(
                                self.current_tick,
                                random.randint(0, self.world.width),
                                random.randint(0, self.world.height),
                                Plant.START_FOOD_VALUE
                            )
                        )
            if self.season in ("summer", "spring") and len(self.world.berry_bushes) < 15:
                if random.random() < 0.3:
                        self.world.berry_bushes.append(
                            BerryBush(
                                random.randint(100000, 999999),
                                random.randint(0, self.world.width),
                                random.randint(0, self.world.height)
                            )
                        )


    def save_full_state(self):
        return {
            "tick": self.current_tick,
            "season": self.season,
            "season_tick": self.season_tick,
            "plants": [
                {
                    "id": p.id, 
                    "x": p.x, 
                    "y": p.y, 
                    "food_value": p.food_value, 
                    "age": p.age
                    } 
                    for p in self.world.plants
                ],
            "berry_bushes": [
                {
                    "id": b.id, 
                    "x": b.x, 
                    "y": b.y
                    } 
                    for b in self.world.berry_bushes
                ],
            "water_sources": [
                {
                    "id": w.id, 
                    "x": w.x, 
                    "y": w.y, 
                    "radius": w.radius
                    } for w in self.world.water_sources
                ],
            "shelters": [
                {
                    "id": s.id, 
                    "x": s.x, 
                    "y": s.y, 
                    "radius": s.radius
                    } for s in self.world.shelters
                ],
            "herbivores": [
                {
                    "id": h.id,
                    "x": h.x, 
                    "y": h.y, 
                    "health": h.health, 
                    "energy": h.energy, 
                    "age": h.age, 
                    "speed": h.speed, 
                    "vision": h.vision, 
                    "thirst": h.thirst,
                    "memory_x": h.memory_x, 
                    "memory_y": h.memory_y, 
                    "memory_timer": h.memory_timer, 
                    "water_memory_x": h.water_memory_x, 
                    "water_memory_y": h.water_memory_y, 
                    "water_memory_timer": h.water_memory_timer, 
                    "reproduce_cooldown": h.reproduce_cooldown, 
                    "max_age": h.max_age,
                    "wander_dx": h.wander_dx, 
                    "wander_dy": h.wander_dy, 
                    "is_drinking": h.is_drinking,
                    "drinking_at_x": h.drinking_at_x,
                    "drinking_at_y": h.drinking_at_y
                    } for h in self.world.herbivores
                ],
            "foxes": [
                {
                    "id": f.id, 
                    "x": f.x, 
                    "y": f.y, 
                    "health": f.health, 
                    "energy": f.energy, 
                    "age": f.age, 
                    "speed": f.speed, 
                    "vision": f.vision, 
                    "thirst": f.thirst, 
                    "hunger": f.hunger, 
                    "memory_x": f.memory_x, 
                    "memory_y": f.memory_y, 
                    "memory_timer": f.memory_timer, 
                    "water_memory_x": f.water_memory_x, 
                    "water_memory_y": f.water_memory_y, 
                    "water_memory_timer": f.water_memory_timer, 
                    "reproduce_cooldown": f.reproduce_cooldown, 
                    "max_age": f.max_age, 
                    "wander_dx": f.wander_dx, 
                    "wander_dy": f.wander_dy,
                    "is_drinking": f.is_drinking,
                    "drinking_at_x": f.drinking_at_x,
                    "drinking_at_y": f.drinking_at_y
                    } for f in self.world.foxes
                ],
            "trees" : [
                {
                    "id": t.id,
                    "x": t.x,
                    "y": t.y,
                    "age": t.age,
                    "height": t.height
                } for t in self.world.trees
            ],
        }

    def load_full_state(self, data):
        self.current_tick = data["tick"]
        self.season = data["season"]
        self.season_tick = data["season_tick"]

        self.world.plants = [
            Plant(p["id"], p["x"], p["y"], p["food_value"]) 
            for p in data["plants"]
        ]
        
        for i, plant in enumerate(self.world.plants):
            plant.age = data["plants"][i]["age"]

        self.world.berry_bushes = [
            BerryBush(b["id"], b["x"], b["y"]) 
            for b in data["berry_bushes"]
        ]

        self.world.water_sources = [
            WaterSource(w["id"], w["x"], w["y"], w["radius"]) 
            for w in data["water_sources"]
        ]

        self.world.shelters = [
            Shelter(s["id"], s["x"], s["y"], s["radius"]) 
            for s in data["shelters"]
        ]
        self.world.trees = [
            Tree(t["id"], t["x"], t["y"]) 
            for t in data["trees"]
        ]

        for i, tree in enumerate(self.world.trees):
            tree.age = data["trees"][i]["age"]
            tree.height = data["trees"][i]["height"]



        self.world.herbivores = []
        for h in data["herbivores"]:
            herb = Herbivore(
                h["id"], 
                h["x"], 
                h["y"], 
                h["health"], 
                h["energy"], 
                h["age"], 
                h["speed"], 
                h["vision"]
            )

            herb.thirst = h["thirst"]
            herb.memory_x = h["memory_x"]
            herb.memory_y = h["memory_y"]
            herb.memory_timer = h["memory_timer"]
            herb.water_memory_x = h["water_memory_x"]
            herb.water_memory_y = h["water_memory_y"]
            herb.water_memory_timer = h["water_memory_timer"]
            herb.reproduce_cooldown = h["reproduce_cooldown"]
            herb.max_age = h["max_age"]
            herb.wander_dx = h["wander_dx"]
            herb.wander_dy = h["wander_dy"]
            herb.is_drinking = h["is_drinking"]
            herb.drinking_at_x = h.get("drinking_at_x", None)
            herb.drinking_at_y = h.get("drinking_at_y", None)

            self.world.herbivores.append(herb)
        self.world.foxes = []
        for f in data["foxes"]:
            fox = Fox(
                f["id"], 
                f["x"], 
                f["y"], 
                f["health"], 
                f["hunger"], 
                f["energy"], 
                f["age"], 
                f["speed"], 
                f["vision"]
            )

            fox.thirst = f["thirst"]
            fox.memory_x = f["memory_x"]
            fox.memory_y = f["memory_y"]
            fox.memory_timer = f["memory_timer"]
            fox.water_memory_x = f["water_memory_x"]
            fox.water_memory_y = f["water_memory_y"]
            fox.water_memory_timer = f["water_memory_timer"]
            fox.reproduce_cooldown = f["reproduce_cooldown"]
            fox.max_age = f["max_age"]
            fox.wander_dx = f["wander_dx"]
            fox.wander_dy = f["wander_dy"]
            fox.is_drinking = f.get("is_drinking", False)
            fox.drinking_at_x = f.get("drinking_at_x", None)
            fox.drinking_at_y = f.get("drinking_at_y", None)

            self.world.foxes.append(fox)
        
    def get_state(self):
        data = []

        for plant in self.world.plants:
            data.append({
                "type": "plant",
                "x": plant.x,
                "y": plant.y,
                "age": plant.age,
                "food_value": round(plant.food_value,1)
            })
        
        for bush in self.world.berry_bushes:
            data.append({
                "type" : "berry_bush",
                "x" : bush.x,
                "y" : bush.y,
                "food_value" : round(bush.food_value, 1)                                     
            })
        
        for tree in self.world.trees:
            data.append({
                "type": "tree",
                "x": tree.x,
                "y": tree.y,
                "radius": tree.radius,
                "age": tree.age,
                "height": tree.height

            }

            )

        for water in self.world.water_sources:
            data.append({
                "type": "water",
                "x": water.x,
                "y": water.y,
                "radius": water.radius
            })

        for shelter in self.world.shelters:
            data.append({
                "type": "shelter",
                "x": shelter.x,
                "y": shelter.y,
                "radius": shelter.radius
            })

        for herbivore in self.world.herbivores:
            data.append({
                "type": "herbivore",
                "x": herbivore.x,
                "y": herbivore.y,
                "energy": herbivore.energy,
                "speed": round(herbivore.speed, 2),
                "vision": round(herbivore.vision, 1),
                "age": herbivore.age,
                "nearest_fox_dist": round(herbivore.nearest_fox_distance, 1),
                "thirst": herbivore.thirst


            })

        for fox in self.world.foxes:
            data.append({
                "type" : "fox",
                "x" : fox.x,
                "y" : fox.y,
                "energy" : fox.energy,
                "hunger" : fox.hunger,
                "age" : fox.age,
                "vision": round(fox.vision, 1),
                "thirst" : fox.thirst

            })
        

        return {
            "tick": self.current_tick,
            "season" : self.season,
            "season_tick": self.season_tick,
            "entities": data,
            "counts": {
                "plants": len(self.world.plants),
                "herbivores": len(self.world.herbivores),
                "berry_bushes" : len(self.world.berry_bushes),
                "foxes" : len(self.world.foxes),
                "water_sources": len(self.world.water_sources),
                "shelters" : len(self.world.shelters),
                "trees": len(self.world.trees)

    }       
}
