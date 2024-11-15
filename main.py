"""
Created on Nov 5, 2022

@author: Sangwook Cheon

Hours Spent: 10 Hours

HOW TO PLAY:
This is called "Omok" in Korea, or known as "Gomoku" in Japanese. It is similar to Connect 4, but now the goal is to connect
5 stones in any orientation (horizontal, vertical, diagonal), and the stone can be placed anywhere on a flat board,
in contrast to Connect 4. The first player to connect 5 wins!

I made a semi-intelligent bot that implements general strategies, and starts first as 'white.' You as a player is 'black.'
The bot knows how to
    - Identify situations where it needs to use defensive or offensive tactics.
    - Place stones near other white stones generally to create advantageous positions.

I was so happy to get my basic bot working, but it can be easily made smarter by considering more specific cases, such
as pre-emptively blocking empty spaces between black stones, which, if connected, would cause the opponent to win.

You can press Enter to reset everything.

In the code, you can also change NUM_ROWS and NUM_COLUMNS to anything and the game will automatically adjust to new values.

In the code, Black is represented by 1, White by -1. Empty spaces are 0.


DISCUSSION FIXED VALUES
GRID PADDING:
    - Grid padding was added to allow stones on the edges to be considered without causing index error.
    - 4 Rows and columns were added.
BOT_DELAY_SEC:
    - 1 second delay not only adds an illusion of thinking, but also makes the gameplay smoother.

There were not a whole lot of randomness in this game, but randomness was useful in the bot's algorithm.
    - For the 'LAST RESORT' component, I did random.randint(1, 2) that basically leads to 1 or 2 stones away from a given
    stone for the new stone's location of placement. I also shuffled list of indexes so that the bot makes more unpredictable moves.
"""
import math
import random
import arcade


# Choose a name for your game to appear in the title bar of the game window
GAME_NAME = 'Omok'
# Number of rows and columns can be changed to anything.
NUM_ROWS = 25
NUM_COLUMNS = 25

BOARD_WIDTH = NUM_COLUMNS * 30
BOARD_HEIGHT = NUM_ROWS * 30

# Choose placement of game text
TEXT_OFFSET = 100
SCORE_MARGIN = 80
SCORE_X_OFFSET = 120
SCORE_Y_OFFSET = BOARD_HEIGHT + 40
# Choose the size of your game window
SCREEN_WIDTH = BOARD_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT + SCORE_MARGIN

# This is the amount of time the bot 'thinks' before placing a stone.
BOT_DELAY_SEC = 1

# Grid padding was added to allow stones on the edges to be considered without causing index error.
GRID_PADDING = 4

# Line spacing is for size of the square - spacing between the lines.
LINE_SPACING = BOARD_HEIGHT / NUM_ROWS

# Size of each stone
STONE_SIZE = LINE_SPACING - 10

# Choose piece colors (though black and white are not 'colors' haha)
COLOR_BLACK = arcade.color.BLACK
COLOR_WHITE = arcade.color.WHITE

# 2D Data structure representing each game state in a grid
class Grid:
    def __init__(self, num_rows, num_columns):
        self.spaces = []
        self.num_rows = num_rows
        self.num_columns = num_columns

        # Record all the center points of each space in terms of x, y coordinate, which will stay constant throughout the game
        # The indexes match with the actual indices represented in self.spaces, so I can place stones with ease.
        self.centers = []

        for row in range(self.num_rows + 5):
            self.centers.append([])

            for col in range(self.num_columns):
                # Populate the list with center positions
                self.centers[row].append([col * LINE_SPACING + LINE_SPACING // 2, (NUM_ROWS - row - 1) * LINE_SPACING + LINE_SPACING // 2, ])

        self.reset()

    def reset(self):
        """
        Reset clears the board
        """
        self.spaces.clear()

        # The GRID_PADDING is to add padding to the grid so that connected stones can be analyzed without having index error.
        for row in range(self.num_rows + GRID_PADDING):
            self.spaces.append([])
            for col in range(self.num_columns + GRID_PADDING):
                if row >= self.num_rows:
                    # Adding arbitrary number 2 that won't affect the grid analysis done with 0, 1, and -1.
                    self.spaces[row].append(2)
                elif col >= self.num_columns:
                    self.spaces[row].append(2)
                else:
                    self.spaces[row].append(0)

    def count_stone_index(self, pieceNum):
        """
        Important function that returns a list of index of all stones of a particular color.
        """

        index_list = []

        for i, row in enumerate(self.spaces):
            for j, num in enumerate(row):
                if num == pieceNum:
                    index_list.append([i, j])

        return index_list


    def print(self):
        """
        Print the 2D grid one row per line with values evenly spaced across the row.
        """
        for listOfSpaces in self.spaces:
            for space in listOfSpaces:
                # align the output by formatting the value to always take up 4 spaces
                print(f"{space:2}", end='')
            print()
        print()


class Stone(arcade.SpriteCircle):
    def __init__(self, pieceNum, list_pos):
        super().__init__(int(STONE_SIZE // 2), arcade.color.WHITE)
        self.center_x = list_pos[0]
        self.center_y = list_pos[1]
        self.pieceNum = pieceNum

    def draw(self):
        self.color = COLOR_BLACK if self.pieceNum == 1 else COLOR_WHITE
        super().draw()


class InstructionsView(arcade.View):
    """
    This class represents a screen that displays text for the game instructions until the user clicks the mouse.
    Overrides typical methods:
    - setting up any objects to appear in game
    - drawing them (in method on_draw)
    - responding to mouse input (in method on_mouse_press)
    """
    def __init__(self):
        super().__init__()
        # game instructions, could be read from a file instead
        self.instructions = "Welcome to Omok! \n You win by connecting \n 5 stones in any orientation. " \
                            "\n Press ENTER to reset game at any time."
        # set background color just once
        arcade.set_background_color(arcade.color.DUKE_BLUE)

    def on_draw(self):
        """
        Draw the instructions on the screen.
        """
        self.clear()
        # draw the instruction text from the top to bottom (higher to lower Y coordinate)
        for i, line in enumerate(self.instructions.split('\n')):
            arcade.draw_text(line, BOARD_WIDTH // 2, (3 - i) * TEXT_OFFSET + BOARD_HEIGHT // 2,
                             arcade.color.WHITE, font_size=28, anchor_x='center')

        # tell player how to start the game
        arcade.draw_text('Click to Start', BOARD_WIDTH // 2, -TEXT_OFFSET + BOARD_HEIGHT / 2,
                         arcade.color.WHITE, font_size=36, anchor_x='center')

    def on_mouse_press(self, x, y, button, modifiers):
        """
        Called whenever the mouse is pressed --- anywhere is fine.
        """
        # create and show a new instance of the game to get it started
        self.window.show_view(GameView())


class GameOverView(arcade.View):
    """
    This class represents a screen that displays the score, winning or losing message, and instructions for restarting.
    Overrides typical methods:
    - setting up any objects to appear in game
    - drawing them (in method on_draw)
    - responding to key input (in method on_key_press)
    """
    def __init__(self, pieceNum, b_score, w_score):
        super().__init__()
        if pieceNum == 1:
            self.message = 'You Won! Click to continue.'
        elif pieceNum == -1:
            self.message = 'Bot Won. Click to continue.'
        else:
            self.message = 'Test'

        self.black_score = b_score
        self.white_score = w_score

        # set background color just once
        arcade.set_background_color(arcade.color.BABY_BLUE_EYES)

    def on_draw(self):
        """
        Draw the results on the screen.
        """
        # DO NOT CHANGE -- always clear the screen as the FIRST step
        self.clear()

        arcade.draw_text(self.message, BOARD_WIDTH // 2, -TEXT_OFFSET + BOARD_HEIGHT / 2,
                         arcade.color.DUKE_BLUE, font_size=36, anchor_x='center')

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """
        Called whenever a key is pressed -- anywhere is fine.
        """
        # create and show a new instance of the game to restart it
        self.window.show_view(GameView(self.black_score, self.white_score))



class GameView(arcade.View):
    """
    Where the game happens.
    Also contains main logic for the bot.
    """
    def __init__(self, b_score=0, w_score=0):
        # no need to pass size and title since this is just a view within the window
        super().__init__()
        # create the 2D data structure that represents the game board
        self.board = Grid(NUM_ROWS, NUM_COLUMNS)

        self.stones = []

        self.timer = 0

        self.black_score = b_score
        self.white_score = w_score

        # 1 is black, -1 is white
        self.turn = -1

        arcade.set_background_color(arcade.color.CARROT_ORANGE)


    def setup(self):
        """
        Set up the beginning game state
        """
        self.board.reset()
        self.black_score = 0
        self.white_score = 0
        self.stones.clear()
        self.turn = 1
        self.timer = 0

    def check_mouse_position(self, x, y):
        """
        Check mouse position and return an index that represents that space clicked.
        """
        for i, row in enumerate(self.board.centers):
            for j, lstr in enumerate(row):
                dist = math.sqrt((lstr[0]-x)**2 + (lstr[1]-y)**2)
                if dist < LINE_SPACING // 2:
                    return [i, j]

        else:
            return []


    def check_stone_connection(self, connectNum, pieceNum):
        """
        Important function that returns representative list that shows a given stone's index and all of its connected
        stones based on connectNum. If connectNum is 3, it returns all 3-stone connections and their orientation.
        """
        grid = self.board.spaces
        checklist = []
        connected = []
        temp_list = []

        # Check every space on the grid.
        for i in range(len(grid) - GRID_PADDING):
            for j in range(len(grid[i]) - GRID_PADDING):

                # Big debugging - I did not clear my checklist for every piece, so it got cluttered with useless checklists!
                checklist.clear()
                for k in range(8):
                    checklist.append([])

                # If a given stone is a desired color, proceed with checking connections.
                if grid[i][j] == pieceNum:

                    for n in range(connectNum):

                        # The following 8 cases are all possible orientation for connected stones.
                        checklist[0].append(grid[i][j+n])
                        checklist[1].append(grid[i+n][j+n])
                        checklist[2].append(grid[i+n][j])
                        checklist[3].append(grid[i-n][j+n])
                        checklist[4].append(grid[i][j-n])
                        checklist[5].append(grid[i-n][j-n])
                        checklist[6].append(grid[i-n][j])
                        checklist[7].append(grid[i+n][j-n])

                    # print(checklist)

                    for n, nums in enumerate(checklist):
                        temp_list = [i, j]
                        if len(set(nums)) == 1:
                            temp_list.append(n)

                        if len(temp_list) > 2:
                            connected.append(temp_list)
        # print(connected)
        return connected

    def assign_next_move(self, i, j, checkNum, numConnected):
        """
        This function allows the next move to be assigned based on orientation of the connection and number of stones
        connected, and the i, j index of a stone, on which connection is made.
        """

        if checkNum == 0:
            return [i, j+numConnected]
        if checkNum == 1:
            return [i+numConnected, j+numConnected]
        if checkNum == 2:
            return [i+numConnected, j]
        if checkNum == 3:
            return [i-numConnected, j+numConnected]
        if checkNum == 4:
            return [i, j-numConnected]
        if checkNum == 5:
            return [i-numConnected, j-numConnected]
        if checkNum == 6:
            return [i-numConnected, j]
        if checkNum == 7:
            return [i+numConnected, j-numConnected]


    # Brute force check five (in case needed).
    # def check_five(self):
    #     grid = self.board.spaces
    #     for i in range(len(grid) - GRID_PADDING):
    #         for j in range(len(grid[i]) - GRID_PADDING):
    #             if grid[i][j] != 0:
    #                 # Check horizontal and vertical five
    #                 if grid[i][j] == grid[i][j+1] == grid[i][j+2] == grid[i][j+3] == grid[i][j+4]:
    #                     return grid[i][j]
    #                 if grid[i][j] == grid[i][j-1] == grid[i][j-2] == grid[i][j-3] == grid[i][j-4]:
    #                     return grid[i][j]
    #                 if grid[i][j] == grid[i+1][j] == grid[i+2][j] == grid[i+3][j] == grid[i+4][j]:
    #                     return grid[i][j]
    #                 if grid[i][j] == grid[i-1][j] == grid[i-2][j] == grid[i-3][j] == grid[i-4][j]:
    #                     return grid[i][j]
    #             if grid[i][j] != 0:
    #                 # Check diagonal five
    #                 if grid[i][j] == grid[i+1][j+1] == grid[i+2][j+2] == grid[i+3][j+3] == grid[i+4][j+4]:
    #                     return grid[i][j]
    #                 if grid[i][j] == grid[i-1][j+1] == grid[i-2][j+2] == grid[i-3][j+3] == grid[i-4][j+4]:
    #                     return grid[i][j]
    #                 if grid[i][j] == grid[i-1][j-1] == grid[i-2][j-2] == grid[i-3][j-3] == grid[i-4][j-4]:
    #                     return grid[i][j]
    #                 if grid[i][j] == grid[i+1][j-1] == grid[i+2][j-2] == grid[i+3][j-3] == grid[i+4][j-4]:
    #                     return grid[i][j]
    #
    #     else:
    #         return 0

    def bot_create_stone(self, index):

        # Simplifies creating the stone.

        if index[0] < NUM_ROWS and index[1] < NUM_COLUMNS:
            pos = self.board.centers[index[0]][index[1]]
            circle = Stone(self.turn, pos)
            self.stones.append(circle)
            self.board.spaces[index[0]][index[1]] = -1

    # def bot_make_dumb_move(self):
    #     # Random for now
    #     # Must choose places that are not taken.
    #     if self.timer > BOT_DELAY_SEC and self.turn == -1:
    #         x_index = random.randint(0, NUM_ROWS-1)
    #         y_index = random.randint(0, NUM_COLUMNS-1)
    #         pos = self.board.centers[x_index][y_index]
    #         circle = Stone(self.turn, pos)
    #         self.stones.append(circle)
    #         self.board.spaces[x_index][y_index] = -1
    #
    #         self.turn = 1

    def is_space_available(self, index):
        """
        Check if a space is available - if it is already taken by a stone, return False.
        """

        if self.board.spaces[index[0]][index[1]] == 0:
            return True
        else:
            return False

    def bot_make_move(self):
        """
        This is a huge function that is the brain of the bot. It first starts with defensive tactics, and makes offensive
        moves if possible.
        """

        if self.timer > BOT_DELAY_SEC and self.turn == -1:

            # First three moves of the bot are determined below. First move is right at the center of the board.

            count_b = self.board.count_stone_index(1)

            # White starts first.
            if len(count_b) == 0:
                self.bot_create_stone([NUM_ROWS // 2, NUM_COLUMNS // 2])
                self.turn = 1

            # After first black stone is placed, place a stone close to that stone.
            if len(count_b) == 1:
                index = self.assign_next_move(count_b[0][0], count_b[0][1], random.randint(0,7), random.randint(1, 2))
                self.bot_create_stone(index)
                self.turn = 1

            # Third white move is placing a stone near other white stones.
            if len(count_b) == 2:

                count_w = self.board.count_stone_index(-1)

                for i in range(7):
                    index = self.assign_next_move(count_w[0][0], count_w[0][1], i, 1)

                    if self.is_space_available(index) and self.turn == -1:
                        self.bot_create_stone(index)
                        self.turn = 1

            """
            DEFENSIVE MOVES 
            """
            # If it sees four black stones in connection, stop it as a priority.
            check_four = self.check_stone_connection(4, 1)
            if len(check_four) > 0 and self.turn == -1:
                for i in range(len(check_four)):
                    index1 = self.assign_next_move(check_four[i][0], check_four[i][1], check_four[i][2], 3)
                    index2 = self.assign_next_move(check_four[i][0], check_four[i][1], check_four[i][2], -1)

                    if self.is_space_available(index1) and self.turn == -1:
                        self.bot_create_stone(index1)
                        self.turn = 1

                    elif self.is_space_available(index2) and self.turn == -1:
                        self.bot_create_stone(index2)
                        self.turn = 1

            # If see three black stones in connection, stop it only if both ends are empty.
            check_three = self.check_stone_connection(3, 1)
            if len(check_three) > 0 and self.turn == -1:
                for i in range(len(check_three)):
                    index1 = self.assign_next_move(check_three[i][0], check_three[i][1], check_three[i][2], 3)
                    index2 = self.assign_next_move(check_three[i][0], check_three[i][1], check_three[i][2], -1)

                    # only if both ends are free, block the three
                    if self.is_space_available(index1) and self.is_space_available(index2) and self.turn == -1:
                        self.bot_create_stone(index1)
                        self.turn = 1

                    # elif self.board.spaces[index2[0]][index2[1]] == 0 and self.turn == -1:
                    #     pos = self.board.centers[index2[0]][index2[1]]
                    #     circle = Stone(self.turn, pos)
                    #     self.stones.append(circle)
                    #     self.board.spaces[index2[0]][index2[1]] = self.turn
                    #     self.turn *= -1


            """
            OFFENSIVE MOVES 
            """

            # When there are four stone connections, win the game.
            check_four_off = self.check_stone_connection(4, -1)
            if len(check_four_off) > 0 and self.turn == -1:
                for i in range(len(check_four_off)):
                    index1 = self.assign_next_move(check_four_off[i][0], check_four_off[i][1], check_four_off[i][2], 2)
                    index2 = self.assign_next_move(check_four_off[i][0], check_four_off[i][1], check_four_off[i][2], -1)

                    if self.is_space_available(index1) and self.turn == -1:
                        self.bot_create_stone(index1)
                        self.turn = 1

                    elif self.is_space_available(index2) and self.turn == -1:
                        self.bot_create_stone(index2)
                        self.turn = 1


            # When there are three stone connections, extend that connection.
            check_three_off = self.check_stone_connection(3, -1)
            if len(check_three_off) > 0 and self.turn == -1:
                for i in range(len(check_three_off)):
                    index1 = self.assign_next_move(check_three_off[i][0], check_three_off[i][1], check_three_off[i][2], 2)
                    index2 = self.assign_next_move(check_three_off[i][0], check_three_off[i][1], check_three_off[i][2], -1)

                    if self.is_space_available(index1) and self.turn == -1:
                        self.bot_create_stone(index1)
                        self.turn = 1

                    elif self.is_space_available(index2) and self.turn == -1:
                        self.bot_create_stone(index2)
                        self.turn = 1

            # When two connections are detected, extend that connection.
            check_two_off = self.check_stone_connection(2, -1)
            if len(check_two_off) > 0 and self.turn == -1:
                for i in range(len(check_two_off)):
                    index1 = self.assign_next_move(check_two_off[i][0], check_two_off[i][1], check_two_off[i][2], 2)

                    if self.is_space_available(index1) and self.turn == -1:
                        self.bot_create_stone(index1)
                        self.turn = 1


            # LAST RESORT: Reasonable and random moves to try making more connected white stones.
            count_w = self.board.count_stone_index(-1)
            # Prevent looking at only few stones at the beginning of the list.
            random.shuffle(count_w)

            for index in count_w:
                nums = [i for i in range(7)]
                random.shuffle(nums)
                for i in nums:
                    index_assign = self.assign_next_move(index[0], index[1], i, random.randint(1, 2))

                    if self.is_space_available(index_assign) and self.turn == -1:
                        self.bot_create_stone(index_assign)
                        self.turn = 1



            # if self.turn == -1:
            #     self.bot_make_dumb_move()




    def on_update(self, dt):

        self.timer += dt

        # # Let the bot automatically take the turn when it is -1
        if self.turn == -1:
            self.bot_make_move()

        five_white = self.check_stone_connection(5, -1)

        if len(five_white) > 0:
            self.white_score += 1
            self.window.show_view(GameOverView(-1, self.black_score, self.white_score))

    def on_draw(self):

        self.clear()

        # Draw the Board

        for i in range(int(BOARD_HEIGHT // LINE_SPACING)):
            arcade.draw_line(0, (i+1) * LINE_SPACING, BOARD_WIDTH, (i+1) * LINE_SPACING, arcade.color.BLACK, 2)

        for i in range(int(BOARD_WIDTH // LINE_SPACING)):
            arcade.draw_line(i * LINE_SPACING, 0, i * LINE_SPACING, BOARD_HEIGHT, arcade.color.BLACK, 2)

        # Draw the pieces on the board
        for stone in self.stones:
            stone.draw()

        # Draw Score (draw player turn as well)
        arcade.draw_text('(You) BLACK: ' + str(self.black_score), SCORE_X_OFFSET, SCORE_Y_OFFSET,
                         arcade.color.BLACK, font_size=20, anchor_x='center')

        arcade.draw_text('(Bot) WHITE: ' + str(self.white_score), BOARD_WIDTH - SCORE_X_OFFSET, SCORE_Y_OFFSET,
                         arcade.color.WHITE, font_size=20, anchor_x='center')

        # Draw Turn
        if self.turn == 1:
            arcade.draw_text('Your turn!', SCORE_X_OFFSET, SCORE_Y_OFFSET - 25,
                             arcade.color.RED, font_size=15, anchor_x='center')
        if self.turn == -1:
            arcade.draw_text('Thinking...', BOARD_WIDTH - SCORE_X_OFFSET, SCORE_Y_OFFSET - 25,
                             arcade.color.RED, font_size=15, anchor_x='center')

        ## Test if centers are correct
        # for lstr in self.board.centers:
        #     for i in lstr:
        #         circle = arcade.SpriteCircle(2, arcade.color.BLACK)
        #         circle.center_x = i[0]
        #         circle.center_y = i[1]
        #         circle.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self.setup()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):

        # Noticed that mouse position starts from bottom left, while my centers grid had values starting from top left.

        pos = self.check_mouse_position(x, y)

        if self.turn == 1:
            if len(pos) != 0 and self.board.spaces[pos[0]][pos[1]] == 0:
                circle = Stone(self.turn, [self.board.centers[pos[0]][pos[1]][0], self.board.centers[pos[0]][pos[1]][1]])
                self.stones.append(circle)
                self.board.spaces[pos[0]][pos[1]] = self.turn

                # Reset timer so that there's buffer to bot's move.
                self.timer = 0

                self.turn = -1

        # Check win for black and white

        five_black = self.check_stone_connection(5, 1)

        if len(five_black) > 0:
            self.black_score += 1
            self.window.show_view(GameOverView(1, self.black_score, self.white_score))

        # Print the board for debugging
        # self.board.print()




# Setting up the game
window = arcade.Window(BOARD_WIDTH, BOARD_HEIGHT + SCORE_MARGIN, GAME_NAME)

window.show_view(InstructionsView())

arcade.run()