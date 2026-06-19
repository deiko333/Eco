import random 

class Organism:
    def __init__(self,id,x,y,health,energy,age,speed,vision):
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
    def __init__(self,id,x,y,food_value):
        self.id = id
        self.x = x
        self.y = y
        self.food_value = food_value



class Herbivore(Organism):
    def __init__(self,id,x,y,health,energy,age,speed,vision):
        super().__init__(id,x,y,health,energy,age,speed,vision)
        pass

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

    def spawn_plant(self):
        for i in range(20):
            self.plants.append(
            Plant(
            i, 
            random.randint(0,self.width),
            random.randint(0,self.height),
            10
        )
    )

    def spawn_herbivores(self):
        for i in range(10):
            self.herbivores.append(
                Herbivore
                (i,
                random.randint(0,self.width), 
                random.randint(0, self.height), 100, 100, 0, 2, 50
                )
            )

class SimulationEngine:
    def __init__(self):
        self.world = World()
        self.running = False
        self.current_tick = 0

        self.world.spawn_plant()
        self.world.spawn_herbivores()

    def start(self):
        self.running = True

    def pause(self):
        self.running = False


    def update(self):
        if not self.running:
            return
        self.current_tick += 1
        
        for h in self.world.herbivores:
            h.x += random.randint(-3,3)
            h.y += random.randint(-3,3)



    def get_state(self): 
        data = []

        for p in self.world.plants:
            data.append({
                "type": "plant", 
                "x": p.x, 
                "y": p.y
                })
        for h in self.world.herbivores:
            data.append({
                "type": "rabbit",
                "x": h.x, 
                "y": h.y
                })

        return {
            "tick": self.current_tick,
            "entities": data
        }

