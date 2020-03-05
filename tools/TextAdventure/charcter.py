class charcter:
    def __init__(self):
        self.health = 100
        self.inventory = []

    async def checkItem(self, item):
        if item in self.inventory:
            return True
        return False

    async def addItem(self, item):
        self.inventory.append(item)

    async def removeIItem(self, item):
        if item in self.inventory:
            self.inventory.remove(item)

    async def heal(self, health):
        self.health = self.health - health

    async def damage(self, damage):
        self.health = self.health - damage
