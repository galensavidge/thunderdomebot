# grid.py

# Class that holds references to grid objects
class Grid:
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.objects = [[None for i in range(width)] for j in range(height)]

    def setObject(self, x, y, obj):
        if self.checkBounds(x, y):
            self.objects[y][x] = obj

    def getObject(self, x, y):
        if self.checkBounds(x, y):
            return self.objects[y][x]
        else:
            return None

    def checkBounds(self, x, y):
        return x >= 0 and x < self.width and y >= 0 and y < self.height

# GridObject(grid, x, y)
class GridObject(object):

    def __init__(self, grid, xpos, ypos):
        self.grid = grid
        self.x = xpos
        self.y = ypos
        self.move(self.x, self.y)

    # Moves the object to another location on the grid
    def move(self, xpos, ypos):
        if self.grid.getObject(self.x, self.y) == self:
            self.grid.setObject(self.x, self.y, None)
        self.grid.setObject(xpos, ypos, self)
        self.x = xpos
        self.y = ypos

    def delete(self):
        if self.grid.getObject(self.x, self.y) == self:
            self.grid.setObject(self.x, self.y, None)

# Test code
if __name__ == "__main__":
    g = Grid(3, 2)
    o = GridObject(g, 0, 0)
    for row in g.objects:
        print(row)
    o.move(o.x+1, o.y)
    for row in g.objects:
        print(row)
