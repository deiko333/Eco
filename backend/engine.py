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

    def move(self):
        pass

    def update(self):
        pass

    def die(self):
        pass


class Plant:
    def __init__(self, id, x, y, food_value):
        self.id = id
        self.x = x
        self.y = y
        self.food_value = food_value
        self.age = 0

class BerryBush:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.food_value = 50
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
    def __init__(self, id, x, y, health, energy, age, speed, vision):
        super().__init__(id, x, y, health, energy, age, speed, vision)
        self.wander_dx = random.uniform(-1, 1)
        self.wander_dy = random.uniform(-1, 1)
        self.nearest_fox_distance = float("inf")
        self.memory_x = None
        self.memory_y = None
        self.memory_timer = 0
        self.water_memory_x = None
        self.water_memory_y = None
        self.water_memory_timer = 0


    def find_food(self):
        pass

    def eat(self):
        pass

class Fox(Organism):
    def __init__(self, id, x, y, health, hunger, energy, age, speed, vision):
        super().__init__(id, x,y,health,energy,age,speed,vision)
        self.hunger = hunger
        self.wander_dx = random.uniform(-1, 1)
        self.wander_dy = random.uniform(-1, 1)
        self.memory_x = None
        self.memory_y = None
        self.memory_timer = 0
        self.water_memory_x = None
        self.water_memory_y = None
        self.water_memory_timer = 0

    def find_prey(self):
        pass

    def hunt(self):
        pass



class World:
    def __init__(self):
        self.plants = []
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
                    20
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


    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def update(self):
        if not self.running:
            return

        self.current_tick += 1
        # season cycle
        self.season_tick += 1
        if self.season_tick >= 1000:
            self.season_tick = 0
            seasons = ["spring", "summer", "autumn", "winter"]
            current_index = seasons.index(self.season)
            self.season = seasons[(current_index + 1) % 4]

        # HERBIVORES
        for herbivore in self.world.herbivores[:]:


            closest_plant = None
            closest_distance = float("inf")

            for plant in self.world.plants + self.world.berry_bushes:

                distance = (
                    (herbivore.x - plant.x) ** 2 +
                    (herbivore.y - plant.y) ** 2
                ) ** 0.5

                if distance < herbivore.vision and distance < closest_distance:
                    closest_distance = distance
                    closest_plant = plant

            
            # flee from nearby fox
            herbivore.thirst += 1
            nearest_fox = None
            nearest_fox_distance = float("inf")
            danger_radius = 200

            for fox in self.world.foxes:
                dist_to_fox = (
                    (herbivore.x - fox.x) ** 2 +
                    (herbivore.y - fox.y) ** 2
                ) ** 0.5
                if dist_to_fox < danger_radius and dist_to_fox < nearest_fox_distance:
                    nearest_fox_distance = dist_to_fox
                    nearest_fox = fox

            if nearest_fox and (nearest_fox_distance < 100 or herbivore.thirst < 80):
                herbivore.nearest_fox_distance = nearest_fox_distance
                herbivore.memory_x = None
                herbivore.memory_y = None
                herbivore.memory_timer = 0
                dx = herbivore.x - nearest_fox.x
                dy = herbivore.y - nearest_fox.y
                dist = (dx*dx + dy*dy) ** 0.5
                if dist > 0:
                    herbivore.x += (dx / dist) * herbivore.speed * 1.2
                    herbivore.y += (dy / dist) * herbivore.speed * 1.2

            elif herbivore.thirst > 150 and herbivore.energy > 80:
                # find nearest water — use memory first, else scan
                nearest_water = None
                nearest_water_dist = float("inf")

                for water in self.world.water_sources:
                    d = ((herbivore.x - water.x)**2 + (herbivore.y - water.y)**2) ** 0.5
                    if d < nearest_water_dist:
                        nearest_water_dist = d
                        nearest_water = water

                # if no water found by scan, use memory
                if nearest_water is None and herbivore.water_memory_x is not None:
                    class FakeWater:
                        pass
                    nearest_water = FakeWater()
                    nearest_water.x = herbivore.water_memory_x
                    nearest_water.y = herbivore.water_memory_y
                    nearest_water.radius = 40
                    nearest_water_dist = ((herbivore.x - nearest_water.x)**2 + (herbivore.y - nearest_water.y)**2) ** 0.5

                if nearest_water:
                    dx = nearest_water.x - herbivore.x
                    dy = nearest_water.y - herbivore.y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist > 0:
                        herbivore.x += (dx / dist) * herbivore.speed
                        herbivore.y += (dy / dist) * herbivore.speed
                    if nearest_water_dist < nearest_water.radius:
                        herbivore.x = nearest_water.x + (herbivore.x - nearest_water.x) * 0.5
                        herbivore.y = nearest_water.y + (herbivore.y - nearest_water.y) * 0.5
                        herbivore.thirst = max(0, herbivore.thirst - 20)
                        if herbivore.thirst < 80:
                            herbivore.water_memory_x = nearest_water.x
                            herbivore.water_memory_y = nearest_water.y
                            herbivore.water_memory_timer = 800
                            herbivore.energy += 10
            elif self.season == "winter" and herbivore.energy > 100 and not closest_plant:
                nearest_shelter = None
                nearest_shelter_dist = float("inf")
                for shelter in self.world.shelters:
                    d = ((herbivore.x - shelter.x)**2 + (herbivore.y - shelter.y)**2) ** 0.5
                    if d < herbivore.vision and d < nearest_shelter_dist:
                        nearest_shelter_dist = d
                        nearest_shelter = shelter
                if nearest_shelter and nearest_shelter_dist > nearest_shelter.radius:
                    dx = nearest_shelter.x - herbivore.x
                    dy = nearest_shelter.y - herbivore.y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist > 0:
                        herbivore.x += (dx / dist) * herbivore.speed
                        herbivore.y += (dy / dist) * herbivore.speed
            # move toward food if exists
            elif closest_plant:

                dx = closest_plant.x - herbivore.x
                dy = closest_plant.y - herbivore.y

                dist = (dx*dx + dy*dy) ** 0.5

                if dist > 0:
                    herbivore.x += (dx / dist) * herbivore.speed
                    herbivore.y += (dy / dist) * herbivore.speed
            else:
                if herbivore.memory_x is not None and herbivore.memory_timer > 0:
                    herbivore.memory_timer -= 1
                    dx = herbivore.memory_x - herbivore.x
                    dy = herbivore.memory_y - herbivore.y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist > 60:
                        target_dx = dx / dist
                        target_dy = dy / dist
                        strength = min(0.05, dist / 1000)
                        herbivore.wander_dx += (target_dx - herbivore.wander_dx) * strength
                        herbivore.wander_dy += (target_dy - herbivore.wander_dy) * strength
                    else:
                        herbivore.memory_x = None
                        herbivore.memory_y = None
                else:
                    if random.random() < 0.05:
                        herbivore.wander_dx += random.uniform(-0.3, 0.3)
                        herbivore.wander_dy += random.uniform(-0.3, 0.3)
                        total = (herbivore.wander_dx**2 + herbivore.wander_dy**2) ** 0.5
                        if total > 0:
                            herbivore.wander_dx /= total
                            herbivore.wander_dy /= total
                herbivore.x += herbivore.wander_dx * herbivore.speed
                herbivore.y += herbivore.wander_dy * herbivore.speed
            
            # bounds
            herbivore.x = max(0, min(herbivore.x, self.world.width))
            herbivore.y = max(0, min(herbivore.y, self.world.height))

            age_penalty = herbivore.age / herbivore.max_age * 0.2
            herbivore.energy = min(herbivore.energy, 300)
            in_shelter = any(
                ((herbivore.x - s.x)**2 + (herbivore.y - s.y)**2) ** 0.5 < s.radius
                for s in self.world.shelters
            )
            winter_penalty = (0.01 if in_shelter else 0.02) if self.season == "winter" else 0.01 if self.season == "autumn" else -0.08 if self.season == "spring" else 0
            herbivore.energy -= (0.25 + herbivore.speed * 0.03 + age_penalty + winter_penalty)
            # eat plant
            if closest_plant and closest_distance < 25:
                herbivore.energy += closest_plant.food_value
                herbivore.memory_x = herbivore.x
                herbivore.memory_y = herbivore.y
                herbivore.memory_timer = 500
                if closest_plant in self.world.plants:
                        try:
                            self.world.plants.remove(closest_plant)
                        except ValueError:
                            pass
                elif closest_plant in self.world.berry_bushes:
                    try:
                        self.world.berry_bushes.remove(closest_plant)
                    except ValueError:
                        pass
            herbivore.reproduce_cooldown -= 1

            if herbivore.energy > 250 and herbivore.reproduce_cooldown <= 0 and herbivore.age > 150 and self.season != "winter":
                herbivore.energy -= 120
                herbivore.reproduce_cooldown = 130

                self.world.herbivores.append(
                    Herbivore(
                        random.randint(100000, 999999),
                        herbivore.x + random.randint(-10, 10),
                        herbivore.y + random.randint(-10, 10),
                        100,
                        70,   
                        0,
                        max(1,herbivore.speed + random.uniform(-0.3, 0.3)),
                        max(20,herbivore.vision + random.randint(-5, 5))
                    )
                )
            # death
            herbivore.age +=1
            if herbivore.energy <= 0 or herbivore.age >= herbivore.max_age:
                self.world.herbivores.remove(herbivore)

        # age plants and grow food value
        for plant in self.world.plants:
            plant.age += 1
            plant.food_value = min(40, 10 + plant.age * 0.05)

        #foxes
        for fox in self.world.foxes[:]:
            closest_prey = None
            closest_distance = float("inf")
            for herbivore in self.world.herbivores:
                distance = (
                    (fox.x - herbivore.x) ** 2 +
                    (fox.y - herbivore.y) ** 2
                ) ** 0.5
                if distance < fox.vision and distance < closest_distance:
                    closest_distance = distance
                    closest_prey = herbivore

            if closest_prey:
                dx = closest_prey.x - fox.x
                dy = closest_prey.y - fox.y
                dist = (dx*dx + dy*dy) ** 0.5
                if dist > 0:
                    fox.x += (dx / dist) * fox.speed
                    fox.y += (dy / dist) * fox.speed

            elif self.season == "winter" and fox.energy > 100:
                nearest_shelter = None
                nearest_shelter_dist = float("inf")
                for shelter in self.world.shelters:
                    d = ((fox.x - shelter.x)**2 + (fox.y - shelter.y)**2) ** 0.5
                    if d < fox.vision and d < nearest_shelter_dist:
                        nearest_shelter_dist = d
                        nearest_shelter = shelter
                if nearest_shelter and nearest_shelter_dist > nearest_shelter.radius:
                    dx = nearest_shelter.x - fox.x
                    dy = nearest_shelter.y - fox.y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist > 0:
                        fox.x += (dx / dist) * fox.speed
                        fox.y += (dy / dist) * fox.speed

            else:
                if fox.memory_x is not None and fox.memory_timer > 0:
                    fox.memory_timer -= 1
                    dx = fox.memory_x - fox.x
                    dy = fox.memory_y - fox.y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist > 60:
                        target_dx = dx / dist
                        target_dy = dy / dist
                        strength = min(0.05, dist / 1000)
                        fox.wander_dx += (target_dx - fox.wander_dx) * strength
                        fox.wander_dy += (target_dy - fox.wander_dy) * strength
                    else:
                        fox.memory_x = None
                        fox.memory_y = None
                else:
                    if random.random() < 0.05:
                        fox.wander_dx += random.uniform(-0.3, 0.3)
                        fox.wander_dy += random.uniform(-0.3, 0.3)
                        total = (fox.wander_dx**2 + fox.wander_dy**2) ** 0.5
                        if total > 0:
                            fox.wander_dx /= total
                            fox.wander_dy /= total
                fox.x += fox.wander_dx * fox.speed
                fox.y += fox.wander_dy * fox.speed

            fox.x = max(0, min(fox.x, self.world.width))
            fox.y = max(0, min(fox.y, self.world.height))

            in_shelter = any(
                ((fox.x - s.x)**2 + (fox.y - s.y)**2) ** 0.5 < s.radius
                for s in self.world.shelters
            )
            fox_winter_penalty = (0.01 if in_shelter else 0.02) if self.season == "winter" else 0.01 if self.season == "autumn" else -0.04 if self.season == "spring" else 0
            fox.energy = min(fox.energy, 400)
            fox.energy -= (0.15 + fox.speed * 0.01 + fox_winter_penalty)
            fox.hunger += 1
            fox.thirst += 1

            if fox.thirst > 300 and fox.energy > 100:
                nearest_water = None
                nearest_water_dist = float("inf")
                if fox.water_memory_x is not None and fox.water_memory_timer > 0:
                    fox.water_memory_timer -= 1
                    dx = fox.water_memory_x - fox.x
                    dy = fox.water_memory_y - fox.y
                    dist = (dx*dx + dy*dy) ** 0.5
                    if dist > 0:
                        fox.x += (dx / dist) * fox.speed
                        fox.y += (dy / dist) * fox.speed
                else:
                    for water in self.world.water_sources:
                        d = ((fox.x - water.x)**2 + (fox.y - water.y)**2) ** 0.5
                        if d < nearest_water_dist:
                            nearest_water_dist = d
                            nearest_water = water
                    if nearest_water:
                        dx = nearest_water.x - fox.x
                        dy = nearest_water.y - fox.y
                        dist = (dx*dx + dy*dy) ** 0.5
                        if dist > 0:
                            fox.x += (dx / dist) * fox.speed
                            fox.y += (dy / dist) * fox.speed
                        if nearest_water_dist < nearest_water.radius:
                            fox.x = nearest_water.x + (fox.x - nearest_water.x) * 0.5
                            fox.y = nearest_water.y + (fox.y - nearest_water.y) * 0.5
                            fox.thirst = max(0, fox.thirst - 20)
                            if fox.thirst == 0:
                                fox.water_memory_x = nearest_water.x
                                fox.water_memory_y = nearest_water.y
                                fox.water_memory_timer = 800

            if fox.hunger > 300:
                fox.energy -= 5

            if closest_prey and closest_distance < 22:
                fox.energy += 150
                fox.hunger = 0
                fox.memory_x = fox.x
                fox.memory_y = fox.y
                fox.memory_timer = 500
                if closest_prey in self.world.herbivores:
                    try:
                        self.world.herbivores.remove(closest_prey)
                    except ValueError:
                        pass

            fox.reproduce_cooldown -= 1

            # eat berries if hungry and nearby
            for bush in self.world.berry_bushes[:]:
                dist_to_bush = (
                    (fox.x - bush.x) ** 2 +
                    (fox.y - bush.y) ** 2
                ) ** 0.5
                if dist_to_bush < 25 and fox.hunger > 100:
                    fox.energy += 30
                    fox.hunger = max(0, fox.hunger - 50)
                    try:
                        self.world.berry_bushes.remove(bush)
                    except ValueError:
                        pass
                    break

            if fox.energy > 300 and fox.reproduce_cooldown <= 0 and fox.age > 150 and len(self.world.foxes) < len(self.world.herbivores) // 6:
                fox.energy -= 150
                fox.reproduce_cooldown = 350
                self.world.foxes.append(
                    Fox(
                        random.randint(100000, 999999),
                        fox.x + random.randint(-10, 10),
                        fox.y + random.randint(-10, 10),
                        100,
                        0,
                        150,
                        0,
                        max(1, fox.speed + random.uniform(-0.3, 0.3)),
                        max(20, fox.vision + random.randint(-5, 5))
                    )
                )

            fox.age += 1
            if fox.energy <= 0 or fox.age >= fox.max_age:
                self.world.foxes.remove(fox)

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

        # plant regrowth
        if self.current_tick % 5 == 0:
                if len(self.world.plants) < 500:
                    for _ in range(6 if self.season == "winter" else 6 if self.season == "autumn" else 15 if self.season == "spring" else 12):
                        self.world.plants.append(
                            Plant(
                                self.current_tick,
                                random.randint(0, self.world.width),
                                random.randint(0, self.world.height),
                                20
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
                "shelters" : len(self.world.shelters)

    }       
}
