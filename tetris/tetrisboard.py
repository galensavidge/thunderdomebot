# tetrisboard.py

from tetris.grid import Grid, GridObject
from tetris.asciigraphics import Frame

# Grid board class
class Board(Grid):

    def __init__(self, width, height, square_width, square_height):
        Grid.__init__(self, width, height)
        self.square_width = square_width
        self.square_height = square_height
        self.frame = Frame(width*square_width, height*square_height)

    def rowFull(self, row):
        for col in range(self.width):
            if self.getObject(col, row) is None:
                return False

        return True
    
    def draw(self):
        self.frame.clear()
        for b in self.getAllObjects():
            b.draw()

    def __str__(self):
        return str(self.frame)
    
    def print(self):
        for i in range(self.height):
            for j in range(self.width):
                o = self.getObject(j, i)
                if o is not None:
                    print("~",end="")
                else:
                    print(" ",end="")
            print("")
        print("----------")


# Base block class
class Block(GridObject):

    def __init__(self, board, x, y, char):
        GridObject.__init__(self, board, x, y)
        board.blocks.append(self)
        self.board = board
        self.old_x = x
        self.old_y = y
        self.char = char

    def update(self):
        return

    def draw(self):
        if self.x != self.old_x or self.y != self.old_y:
            self.erase_rect()
            self.draw_rect()
            self.old_x = self.x
            self.old_y = self.y

    def draw_rect(self):
        self.board.frame.fill(self.x*self.board.square_width, self.y*self.board.square_height, self.board.square_width, self.board.square_height, self.char)

    def erase_rect(self):
        self.board.frame.erase(self.old_x*self.board.square_width, self.old_y*self.board.square_height, self.board.square_width, self.board.square_height)

    def changeBoard(self, board, x, y):
        # Erase self from board
        self.erase_rect()

        # Change board references
        if self.grid.getObject(self.x, self.y) == self:
            self.grid.setObject(self.x, self.y, None)
        self.grid = board
        self.grid.setObject(x, y, self)

        # Reset position
        self.x = x
        self.y = y
        self.old_x = self.x
        self.old_y = self.y

        # Draw new rectangle
        self.draw_rect()
    
    def delete(self):
        GridObject.delete(self)
        self.erase_rect()
        self.board.blocks.remove(self)


class Tetromino:

    # Sets of (x, y) coordinates to build each type of tetromino
    layouts = {"I" : ((0, 0),(-1, 0),(1, 0),(2, 0)), \
               "J" : ((0, 0),(-1, 0),(1, 0),(-1, -1)), \
               "L" : ((0, 0),(-1, 0),(1, 0),(1, -1)), \
               "O" : ((0, 0),(1, 0),(0, 1),(1, 1)), \
               "S" : ((0, 0),(-1, 0),(0, -1),(1, -1)), \
               "T" : ((0, 0),(-1, 0), (0, -1), (1, 0)), \
               "Z" : ((0, 0),(0, -1),(-1, -1),(1, 0))}

    chars = {"I" : "@", "J" : "#", "L" : "$", "O" : "%", "S" : "^", "T" : "&", "Z" : "*"}

    # Pairs of (cos(theta), sin(theta)) for each rotation 0-3
    rot_pairs = ((1, 0),(0, 1),(-1, 0),(0, -1))

    # Sets of kick data sorted by original rotation and then final rotation
    kicks = {0 : \
                {1 : ((0, 0),(-1, 0),(-1, 1),(0, -2),(-1, -2)), \
                 3 : ((0, 0),(1, 0),(1, 1),(0, -2),(1, -2))}, \
             1 : \
                {0 : ((0, 0),(1, 0),(1, -1),(0, 2),(1, 2)), \
                 2 : ((0, 0),(1, 0),(1, -1),(0, 2),(1, 2))}, \
             2 : \
                {1 : ((0, 0),(-1, 0),(-1, 1),(0, -2),(-1, -2)), \
                 3 : ((0, 0),(1, 0),(1, 1),(0, -2),(1, -2))}, \
             3 : \
                {0 : ((0, 0),(-1, 0),(-1, -1),(0, 2),(-1, 2)), \
                 2 : ((0, 0),(-1, 0),(-1, -1),(0, 2),(-1, 2))}}
    
    I_kicks = {0 : \
                {1 : ((0, 0),(-2, 0),(1, 0),(-2, -1),(1, 2)), \
                 3 : ((0, 0),(-1, 0),(2, 0),(-1, 2),(2, -1))}, \
               1 : \
                {0 : ((0, 0),(2, 0),(-1, 0),(2, 1),(-1, -2)), \
                 2 : ((0, 0),(-1, 0),(2, 0),(-1, 2),(2, -1))}, \
               2 : \
                {1 : ((0, 0),(1, 0),(-2, 0),(1, -2),(-2, 1)), \
                 3 : ((0, 0),(2, 0),(-1, 0),(2, 1),(-1, -2))}, \
               3 : \
                {0 : ((0, 0),(1, 0),(-2, 0),(1, -2),(-2, 1)), \
                 2 : ((0, 0),(-2, 0),(1, 0),(-2, -1),(1, 2))}}
    
    def __init__(self, board, x, y, typ):
        self.board = board
        
        # Coordinates
        self.x = x
        self.y = y

        # Number of clockwise rotations from default (0-3)
        self.rot = 0

        # Tetromino type
        self.type = typ

        # Set up Tetromino
        self.layout = Tetromino.layouts[self.type]
        self.blocks = list()
        for coordinate in self.layout:
            b = Block(board, x+coordinate[0], y+coordinate[1], Tetromino.chars[typ])
            self.blocks.append(b)

    # Moves the Tetromino to board at position (x, y)
    def spawnOnBoard(self, board, x, y):
        self.board = board
        self.x = x
        self.y = y
        self.rot = 0
        
        for i in range(len(self.blocks)):
            b = self.blocks[i]
            coordinate = self.layout[i]
            b.changeBoard(board, x+coordinate[0], y+coordinate[1])
    
    # Checks whether a block from this Tetromino would collide with anything at (x, y)
    def checkCollision(self, x, y):
        # Check that the coordinates are inside the grid
        if self.board.checkBounds(x, y) == False:
            return True

        # Check if there is an object at that space that isn't part of this Tetromino
        o = self.board.getObject(x, y)
        if o is not None and self.blocks.count(o) == 0:
            return True
        else:
            return False
    
    # Returns True if moving by (dx, dy) would collide with a block or the edge of the grid
    def checkTranslation(self, dx, dy):
        for b in self.blocks:
            # Check if b could be moved by (dx, dy)
            new_x = b.x + dx
            new_y = b.y + dy
            if self.checkCollision(new_x, new_y):
                return True

        # Return False once all blocks have been checked
        return False

    # Returns True if the Tetromino successfully moved by (dx, dy) and False otherwise
    def move(self, dx, dy):
        if self.checkTranslation(dx, dy) == False:
            self.x += dx
            self.y += dy
            for b in self.blocks:
                b.move(b.x + dx, b.y + dy)
            return True
        else:
            return False

    # Returns True if there are any collisions at the (x, y) pairs in new_coords
    def checkRotation(self, new_coords):
        for c in new_coords:
            if self.checkCollision(c[0], c[1]):
                return True

        return False
    
    def rotate(self, clockwise):
        # Determine old and new rotation state
        old_rot = self.rot
        if clockwise:
            new_rot = self.rot + 1
            if new_rot > 3:
                new_rot = 0
        else:
            new_rot = self.rot - 1
            if new_rot < 0:
                new_rot = 3

        # Get the proper set of kick checks
        if self.type == "O":
            kicks = ((0, 0),(0, 0))
        elif self.type == "I":
            kicks = Tetromino.I_kicks[old_rot][new_rot]
        else:
            kicks = Tetromino.kicks[old_rot][new_rot]

        # Get the corresponding rotation matrix for this rotation
        r = Tetromino.rot_pairs[new_rot]
        
        # Check each (x, y) translation pair in kicks
        for k in kicks:
            
            # New Tetromino coordinates including the kick
            new_x = self.x + k[0]
            new_y = self.y - k[1] # Y coordinate is inverted in kick data
            
            # I and O do not rotate around the "center" so they need an extra translation
            if self.type == "I" or self.type == "O":
                if clockwise:
                    new_x += r[1]
                    new_y -= r[0]
                else:
                    new_x -= r[0]
                    new_y -= r[1]

            # Calculate new position of each block accounting for rotation and kick
            new_coords = list()
            
            for i in range(len(self.blocks)):
                l = self.layout[i]
                
                # Calculate positions of blocks using a 2D rotation matrix
                x = new_x + l[0]*r[0] - l[1]*r[1]
                y = new_y + l[0]*r[1] + l[1]*r[0]

                # Record new position of b
                new_coords.append((x, y)) 

            # Check for collisions at this rotation
            if self.checkRotation(new_coords) == False:
                # If there are no collisions, apply rotation
                self.rot = new_rot
                self.x = new_x
                self.y = new_y
                for i in range(len(self.blocks)):
                    x = new_coords[i][0]
                    y = new_coords[i][1]
                    self.blocks[i].move(x, y)
                return True
        
        return False

    # Moves the Tetromino down until it collides with something
    def drop(self):
        while self.checkTranslation(0, 1) == False:
            self.move(0, 1)

    def draw(self):
        for block in self.blocks:
            block.draw()
