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


class Herbivore(Organism):
    def __init__(self, id, x, y, health, energy, age, speed, vision):
        super().__init__(id, x, y, health, energy, age, speed, vision)

    def find_food(self):
        pass

    def eat(self):
        pass


class World:
    def __init__(self):
        self.plants = []
        self.herbivores = []
        self.width = 1000
        self.height = 700

    def spawn_plants(self):
        for i in range(20):
            self.plants.append(
                Plant(
                    i,
                    random.randint(0, self.width),
                    random.randint(0, self.height),
                    10
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
                    100,
                    0,
                    2,
                    50
                )
            )


class SimulationEngine:
    def __init__(self):
        self.world = World()
        self.running = False
        self.current_tick = 0

        self.world.spawn_plants()
        self.world.spawn_herbivores()

    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def update(self):
        if not self.running:
            return

        self.current_tick += 1

        for herbivore in self.world.herbivores[:]:

            herbivore.x += random.randint(-3, 3)
            herbivore.y += random.randint(-3, 3)

            herbivore.x = max(0, min(herbivore.x, self.world.width))
            herbivore.y = max(0, min(herbivore.y, self.world.height))

            herbivore.energy -= 1

            for plant in self.world.plants[:]:

                distance = (
                    (herbivore.x - plant.x) ** 2
                    + (herbivore.y - plant.y) ** 2
                ) ** 0.5

                if distance < 15:
                    herbivore.energy += plant.food_value
                    self.world.plants.remove(plant)
                    break

            if herbivore.energy <= 0:
                self.world.herbivores.remove(herbivore)

        if self.current_tick % 50 == 0:
            self.world.plants.append(
                Plant(
                    self.current_tick,
                    random.randint(0, self.world.width),
                    random.randint(0, self.world.height),
                    10
                )
            )

    def get_state(self):
        data = []

        for plant in self.world.plants:
            data.append({
                "type": "plant",
                "x": plant.x,
                "y": plant.y
            })

        for herbivore in self.world.herbivores:
            data.append({
                "type": "herbivore",
                "x": herbivore.x,
                "y": herbivore.y,
                "energy": herbivore.energy
            })

        return {
            "tick": self.current_tick,
            "entities": data
        }