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


class Herbivore(Organism):
    def __init__(self, id, x, y, health, energy, age, speed, vision):
        super().__init__(id, x, y, health, energy, age, speed, vision)
        self.wander_dx = random.uniform(-1, 1)
        self.wander_dy = random.uniform(-1, 1)
        self.nearest_fox_distance = float("inf")


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


class SimulationEngine:
    def __init__(self):
        self.world = World()
        self.running = False
        self.current_tick = 0

        self.world.spawn_plants()
        self.world.spawn_herbivores()
        self.world.spawn_berry_bushes()
        self.world.spawn_foxes()

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

            for plant in self.world.plants + self.world.berry_bushes:

                distance = (
                    (herbivore.x - plant.x) ** 2 +
                    (herbivore.y - plant.y) ** 2
                ) ** 0.5

                if distance < herbivore.vision and distance < closest_distance:
                    closest_distance = distance
                    closest_plant = plant

            
            # flee from nearby fox
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

            if nearest_fox:
                herbivore.nearest_fox_distance = nearest_fox_distance
                dx = herbivore.x - nearest_fox.x
                dy = herbivore.y - nearest_fox.y
                dist = (dx*dx + dy*dy) ** 0.5
                if dist > 0:
                    herbivore.x += (dx / dist) * herbivore.speed * 1.2
                    herbivore.y += (dy / dist) * herbivore.speed * 1.2
                    
            # move toward food if exists
            elif closest_plant:

                dx = closest_plant.x - herbivore.x
                dy = closest_plant.y - herbivore.y

                dist = (dx*dx + dy*dy) ** 0.5

                if dist > 0:
                    herbivore.x += (dx / dist) * herbivore.speed
                    herbivore.y += (dy / dist) * herbivore.speed
            # fallback random movement
            else:
                if random.random() < 0.1:
                    herbivore.wander_dx = random.uniform(-1, 1)
                    herbivore.wander_dy = random.uniform(-1, 1)
                herbivore.x += herbivore.wander_dx * herbivore.speed
                herbivore.y += herbivore.wander_dy * herbivore.speed

            # bounds
            herbivore.x = max(0, min(herbivore.x, self.world.width))
            herbivore.y = max(0, min(herbivore.y, self.world.height))

            age_penalty = herbivore.age / herbivore.max_age * 0.2
            herbivore.energy = min(herbivore.energy, 300)
            herbivore.energy -= (0.25 + herbivore.speed * 0.03 + age_penalty)

            # eat plant
            if closest_plant and closest_distance < 25:
                herbivore.energy += closest_plant.food_value
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

            if herbivore.energy > 250 and herbivore.reproduce_cooldown <= 0 and herbivore.age > 150:
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
            else:
                if random.random() < 0.15:
                    fox.wander_dx = random.uniform(-1, 1)
                    fox.wander_dy = random.uniform(-1, 1)
                fox.x += fox.wander_dx * fox.speed
                fox.y += fox.wander_dy * fox.speed

            fox.x = max(0, min(fox.x, self.world.width))
            fox.y = max(0, min(fox.y, self.world.height))

            fox.energy -= (0.15 + fox.speed * 0.01)
            fox.hunger += 1

            if fox.hunger > 300:
                fox.energy -= 5

            #hunt
            if closest_prey and closest_distance < 22:
                fox.energy += 150
                fox.hunger = 0
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
                        100,
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
                    for _ in range(12):
                        self.world.plants.append(
                            Plant(
                                self.current_tick,
                                random.randint(0, self.world.width),
                                random.randint(0, self.world.height),
                                20
                            )
                        )
                if len(self.world.berry_bushes) < 15:
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

        for herbivore in self.world.herbivores:
            data.append({
                "type": "herbivore",
                "x": herbivore.x,
                "y": herbivore.y,
                "energy": herbivore.energy,
                "speed": round(herbivore.speed, 2),
                "vision": round(herbivore.vision, 1),
                "age": herbivore.age,
                "nearest_fox_dist": round(herbivore.nearest_fox_distance, 1)

            })

        for fox in self.world.foxes:
            data.append({
                "type" : "fox",
                "x" : fox.x,
                "y" : fox.y,
                "energy" : fox.energy,
                "hunger" : fox.hunger,
                "age" : fox.age,
                "vision": round(herbivore.vision, 1)

            })

        return {
            "tick": self.current_tick,
            "entities": data,
            "counts": {
                "plants": len(self.world.plants),
                "herbivores": len(self.world.herbivores),
                "berry_bushes" : len(self.world.berry_bushes),
                "foxes" : len(self.world.foxes)
    }       
}
