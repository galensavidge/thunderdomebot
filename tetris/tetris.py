# tetris.py

import discord
from discord.ext import commands
from discord.ext.commands import Cog
import random, threading, time, asyncio

from tetris.tetrisboard import Board, Tetromino
from tetris.asciigraphics import Frame


class TetrisCog(Cog):

    # up, down, left, right, cw, ccw, save, quit
    emoji_list = ["\u2B06", "\u2B07", "\u2B05", "\u27A1", "\u21A9", "\u21AA", "\u2705", "\u274C"]

    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # Format: {message id : game}
    
    @commands.command(name="tetris", help="Starts an inline Tetris game here!")
    async def play_tetris(self, ctx):
        message = await ctx.send("Game starting...")
        await TetrisCog.add_all_emoji(message)
        game = Tetris(ctx, message)
        self.active_games[message.id] = game
        game.run()
    
    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print("Tetris reaction add event!")
        if user != self.bot:
            game = self.active_games.get(reaction.message.id, None)
            if game is not None and str(reaction.emoji) in TetrisCog.emoji_list:
                game.controlEvent(str(reaction.emoji))
                await reaction.message.remove_reaction(reaction, user)
            else:
                print("Game not found")
    
    @staticmethod
    async def add_all_emoji(message: discord.Message):
        await message.clear_reactions()
        for emoji in TetrisCog.emoji_list:
            await message.add_reaction(emoji)


class Tetris(threading.Thread):

    update_time = 1

    # Main board
    grid_x = 10
    grid_y = 22
    square_width = 3
    square_height = 2
    board_position_x = 4
    board_position_y = 1
    spawn_x = 5
    spawn_y = 1

    # GUI
    gui_grid_x = 40
    gui_grid_y = 46
    gui_square_width = 1
    gui_squre_height = 1
    saved_x = 3
    saved_y = 3
    queue_x = 37
    queue_y = 3
    queue_spacing = 6
    
    # Number of tetrominos to queue on screen
    next_length = 6

    # How often to bump up difficulty
    difficulty_level_time = 5 # In seconds
    
    def __init__(self, ctx, message):
        self.ctx = ctx
        self.message = message

        # State
        self.playing = True

        # Boards
        self.main_board = Board(self.grid_x, self.grid_y, Tetris.square_width, Tetris.square_height)
        self.gui_board = Board(self.gui_grid_x, self.gui_grid_y, Tetris.gui_square_width, Tetris.gui_squre_height)
        
        # Control emoji pairs
        self.actions = \
           {TetrisCog.emoji_list[0] : self.up,    TetrisCog.emoji_list[1] : self.down, \
            TetrisCog.emoji_list[2] : self.left,  TetrisCog.emoji_list[3] : self.right, \
            TetrisCog.emoji_list[4] : self.cw,    TetrisCog.emoji_list[5] : self.ccw, \
            TetrisCog.emoji_list[6] : self.save,  TetrisCog.emoji_list[7] : self.quit}

        # General game timer
        self.timer = 0
        
        # Timer for automatic drop
        self.drop_timer = 0
        self.drop_timer_duration = 3

        # Timer for placement
        self.palce_timer = 0
        self.place_timer_duration = 2

        # Timer to prevent double dropping
        self.spawning = True
        self.spawn_timer = 0
        self.spawn_timer_duration = 0.5

        # The tetromino saved using the save key
        self.saved = None
        self.can_save = True

        # Queue of tetrominos
        self.next = list()

        # Longer queue of tetromino types
        self.next_batch = list()

        print("Enqueuing Tetromino...")

        # Set up tetromino queue and pop first tetromino
        while len(self.next) < self.next_length:
            self.enqueueTetromino()
        print("Popping Tetromino...")
        self.popTetromino()

    def run(self):
        asyncio.get_event_loop().run_until_complete(self.loop())

    async def loop(self):
        '''Runs the game thread.'''

        print("Started a Tetris game!")
        while self.playing:
            # General timer
            self.timer += Tetris.update_time

            # Slowly drop controlled tetromino
            self.drop_timer += Tetris.update_time
            if self.drop_timer >= self.drop_timer_duration:
                self.drop_timer = 0
                self.t.move(0, 1)
            
            # Automatically place controlled tetromino
            if self.t.checkTranslation(0, 1) == True:
                self.place_timer += Tetris.update_time
                if self.place_timer >= self.place_timer_duration:
                    self.place_timer = 0
                    self.placeTetromino()
            else:
                self.place_timer = 0
            
            # Spawn timer to prevent accidental double dropping
            if self.spawning:
                self.spawn_timer += Tetris.update_time
                if self.spawn_timer >= self.spawn_timer_duration:
                    self.spawning = False
            else:
                self.spawn_timer = 0

            print("Updating message...")
            await self.updateMessage()

            time.sleep(Tetris.update_time)
        
        print("Finished a Tetris game!")

    async def updateMessage(self):
        '''Updates the game boards and pushes any changes to the message.'''

        # Update main board
        self.main_board.draw()

        # Draw main board on GUI board
        if self.main_board.frame.updated:
            self.gui_board.frame.drawFrame(Tetris.board_position_x, Tetris.board_position_y, self.main_board.frame)
        
        # Update GUI board
        self.gui_board.draw()

        # Update message
        if self.gui_board.frame.updated:
            self.gui_board.frame.drawRectangle(Tetris.board_position_x-1, Tetris.board_position_y-1, \
                Tetris.grid_x*Tetris.square_width+1, Tetris.grid_y*Tetris.square_height+1)
            text = "```{}```".format(self.gui_board)
            await self.message.edit(content=text)

    def controlEvent(self, action: str):
        self.actions[action]()
        self.updateMessage()

    def cw(self):
        if self.t.rotate(True): # Rotate clockwise
            self.place_timer = 0
    
    def ccw(self):
        if self.t.rotate(False): # Rotate ccw
            self.place_timer = 0

    def up(self):
        if not self.spawning:
            self.t.drop()
            self.placeTetromino()
    
    def down(self):
        if self.t.move(0, 1):
            self.place_timer = 0

    def left(self):
        self.t.move(-1, 0)

    def right(self):
        self.t.move(1, 0)

    def save(self):
        if self.can_save:
            self.saveTetromino()

    def quit(self):
        self.playing = False
    
    def enqueueTetromino(self):
        # Check if there are any tetrominos left in the last batch
        if len(self.next_batch) == 0:
            # Make a new batch of tetrominos countaing 2x of each type
            types = list(Tetromino.layouts.keys())
            
            for t in types:
                self.next_batch.append(t)
                self.next_batch.append(t)

            random.shuffle(self.next_batch)

        new_type = self.next_batch.pop(0)
        
        self.next.append(Tetromino(self.gui_board, Tetris.queue_x, Tetris.queue_y + len(self.next)*Tetris.queue_spacing, new_type))
    
    def popTetromino(self):
        self.t = self.next.pop(0)
        self.t.spawnOnBoard(self.main_board, Tetris.spawn_x, Tetris.spawn_y)

        for t in self.next:
            t.move(0, -1*Tetris.queue_spacing)
        self.enqueueTetromino()
        
        # Reset drop timer and spawn timer
        self.drop_timer = 0
        self.spawn_timer = 0

        # Reset save flag
        self.can_save = True

    def saveTetromino(self):
        if self.t is not None:
            if self.saved is None:
                self.saved = self.t
                self.popTetromino()
            else:
                t = self.t
                self.t = self.saved
                self.saved = t
                self.t.spawnOnBoard(self.main_board, Tetris.spawn_x, Tetris.spawn_y)

                # Reset drop timer
                self.drop_timer = 0

                # Set save flag
                self.can_save = False

            self.saved.spawnOnBoard(self.gui_board, Tetris.saved_x, Tetris.saved_y)
        
    def placeTetromino(self):
        # Check if the game is over
        for b in self.t.blocks:
            if b.y <= Tetris.spawn_y:
                self.quit()
                return
        
        # Check for filled rows
        filled_rows = 0
        
        for y in range(Tetris.grid_y):
            if self.main_board.rowFull(y):
                filled_rows += 1
                
                # Delete objects in this row
                for x in range(Tetris.grid_x):
                    self.main_board.getObject(x, y).delete()

                # Move blocks above this down by one space
                for j in range(y, -1, -1):
                    for x in range(Tetris.grid_x):
                        o = self.main_board.getObject(x, j)
                        if o is not None:
                            self.main_board.getObject(x, j).move(o.x, o.y + 1)
        
        # Take a Tetromino from the queue
        self.popTetromino()
