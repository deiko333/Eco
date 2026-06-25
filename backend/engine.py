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
        for i in range(150):
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
                    150,
                    0,
                    3,
                    100
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

        # HERBIVORES
        for herbivore in self.world.herbivores[:]:

            closest_plant = None
            closest_distance = float("inf")

            for plant in self.world.plants:

                distance = (
                    (herbivore.x - plant.x) ** 2 +
                    (herbivore.y - plant.y) ** 2
                ) ** 0.5

                if distance < closest_distance:
                    closest_distance = distance
                    closest_plant = plant

            # move toward food if exists
            if closest_plant:

                if herbivore.x < closest_plant.x:
                    herbivore.x += herbivore.speed
                elif herbivore.x > closest_plant.x:
                    herbivore.x -= herbivore.speed

                if herbivore.y < closest_plant.y:
                    herbivore.y += herbivore.speed
                elif herbivore.y > closest_plant.y:
                    herbivore.y -= herbivore.speed

            else:
                # fallback random movement
                herbivore.x += random.randint(-3, 3)
                herbivore.y += random.randint(-3, 3)

            # bounds
            herbivore.x = max(0, min(herbivore.x, self.world.width))
            herbivore.y = max(0, min(herbivore.y, self.world.height))

            herbivore.energy -= 0.3

            # eat plant
            if closest_plant and closest_distance < 25:
                herbivore.energy += closest_plant.food_value
                if closest_plant in self.world.plants:
                    self.world.plants.remove(closest_plant)

            # death
            if herbivore.energy <= 0:
                self.world.herbivores.remove(herbivore)

        # plant regrowth
        if self.current_tick % 2 == 0:
            for _ in range(3):
                self.world.plants.append(
                    Plant(
                        self.current_tick,
                        random.randint(0, self.world.width),
                        random.randint(0, self.world.height),
                        25
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
            "entities": data,
            "counts": {
                "plants": len(self.world.plants),
                "herbivores": len(self.world.herbivores)
    }
}