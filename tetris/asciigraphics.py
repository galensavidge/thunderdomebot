# asciigraphics.py

import discord

class Frame:

    def __init__ (self, width, height):
        self.width = width
        self.height = height
        self.contents = [[" " for j in range(0, width)] for i in range(0, height)]  # contents[row][col] aka contents[y][x]
    

    def drawChar(self, x, y, char: str):
        '''Draws one character at position (x, y) on the Frame. If len(char) > 1 only the first character of char is drawn.'''

        if x in range(0, self.width) and y in range(0, self.height):
            self.contents[y][x] = char[0]


    def fill(self, x, y, width, height, char: str):
        '''Fills a width by height area with top left corner at (x, y) with char.'''

        for ypos in range(y, y+height):
            for xpos in range(x, x+width):
                self.drawChar(xpos, ypos, char)
    

    def erase(self, x, y, width, height):
        '''Erases a width by height area with top left corner at (x, y).''' 

        self.fill(x, y, width, height, " ")
    
    
    def clear(self):
        '''Clears the contents of the Frame.'''

        self.erase(0, 0, self.width, self.height)
    

    def drawRectangle(self, x, y, width, height):
        '''Draws a width by height unfilled rectangle with top left corner at (x, y). Minimum size is 3x3.'''

        if width < 3 or height < 3:
            return
        
        h = " "+"-"*(width-1)+" "
        self.drawString(x, y, h)
        self.drawString(x, y+height, h)
        
        for ypos in range(y+1, y+height):
            self.drawChar(x, ypos, "|")
            self.drawChar(x+width, ypos, "|")
    

    def drawString(self, x, y, string: str):
        '''Draws a string at position (x, y).'''

        strings = string.split("\n")
        ypos = y
        for s in strings:
            for i in range(0, len(s)):
                self.drawChar(x+i, ypos, s[i])
            ypos += 1


    def drawFrame(self, x, y, f):
        '''Draws the contents of another Frame in this Frame with top left corner at (x, y).'''

        self.drawString(x, y, str(f))


    def __str__(self):
        s = ""
        for row in self.contents:
            s += "".join(row)+"\n"
        return s


# Unit test
if __name__ == "__main__":
    f = Frame(10, 20)
    print(f)
    print("\n")

    f.fill(2, 2, 4, 4, "%")
    f.fill(7, 18, 5, 5, "#")
    f.fill(22, 50, 4, 4, "!")
    f.drawString(5, 8, "123")
    f.drawString(3, 3, "12345678901234567890")
    f.drawString(4, 10, "Hi\nthere!")
    print(f)
    print("\n")

    b = Frame(15, 25)
    b.drawFrame(3, 3, f)
    b.drawRectangle(2, 2, f.width+1, f.height+1)
    print(b)
    print("\n")    