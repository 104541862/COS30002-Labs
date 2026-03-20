import random

# create a register of all the possible winning combinations of positions on the board
WINNING_COMBOS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8), # 3 in a row
    (0, 3, 6), (1, 4, 7), (2, 5, 8), # 3 in a column
    (0, 4, 8), (2, 4, 6) # 3 in a diagonal
)

board = [' ', ' ', ' ',
         ' ', ' ', ' ',
         ' ', ' ', ' ']

current_player = ''

player_name = input("What is your name?\n")

while True:
    ai_choice = int(input("Choose your AI opponent. (0 for random AI, 1 for intelligent AI)\n"))
    if ai_choice == 0:
        ai_name = "Randrew"
        break
    elif ai_choice == 1:
        ai_name = "Magnus Carlsen"
        break
    else:
        print("Error - Please input 0 or 1.")
        pass

o_mode = False

while True:
    o_mode_input = input("Would you like to play as Os? (y/n)\n")
    if o_mode_input == 'y':
        o_mode = True
        break
    elif o_mode_input == 'n':
        break
    else: 
        print("Please enter a valid input (y/n).")
        pass

if o_mode:
    players = {
        'x': ai_name,
        'o': player_name,  # final comma is optional, but doesn't hurt
    }
else:
    players = {
        'x': player_name,
        'o': ai_name,
    }

game_winner = None
move_input = None

HR = '-' * 40

def get_human_move():
    return input("Please input a number from 1-9:\n")

def get_ai_move():
    # Randrew's AI - simply random, picks any random available square (availability is checked within AI logic)
    if ai_choice == 0:
        # Pick any empty square
        available = [i for i, v in enumerate(board) if v == ' ']
        move = random.choice(available)
        print(f"Randrew likes this move! Move: {move + 1}")
        return move + 1

    # Magnus Carlsen's AI - checks for moves in descending order of urgency
    elif ai_choice == 1:
        # check for winning moves by using the list of winning combos. 
        # if two spaces in one of the combos are the same as Magnus and the third is empty, it must be filled in to win
        for combo in WINNING_COMBOS:
            if board[combo[1]] == current_player and board[combo[2]] == current_player and board[combo[0]] == ' ':
                move = combo[0]
                print(f"Winning the game. (empty space at index 0). Move: {move + 1}")
                return move + 1
            elif board[combo[0]] == current_player and board[combo[2]] == current_player and board[combo[1]] == ' ':
                move = combo[1]
                print(f"Winning the game. (empty space at index 1). Move: {move + 1}")
                return move + 1
            elif board[combo[0]] == current_player and board[combo[1]] == current_player and board[combo[2]] == ' ':
                move = combo[2]
                print(f"Winning the game. (empty space at index 2). Move: {move + 1}")
                return move + 1
            
        # check for blocking moves by using the list of winning combos. 
        # if two spaces in one of the combos are the player's and the third is empty, it must be filled in to block
        if current_player == 'x':
            opposite_player = 'o'
        elif current_player == 'o':
            opposite_player = 'x'

        for combo in WINNING_COMBOS:
            if board[combo[1]] == opposite_player and board[combo[2]] == opposite_player and board[combo[0]] == ' ':
                move = combo[0]
                print(f"Blocking you from winning. (empty space at index 0). Move: {move + 1}")
                return move + 1
            elif board[combo[0]] == opposite_player and board[combo[2]] == opposite_player and board[combo[1]] == ' ':
                move = combo[1]
                print(f"Blocking you from winning. (empty space at index 1). Move: {move + 1}")
                return move + 1
            elif board[combo[0]] == opposite_player and board[combo[1]] == opposite_player and board[combo[2]] == ' ':
                move = combo[2]
                print(f"Blocking you from winning. (empty space at index 2). Move: {move + 1}")
                return move + 1

        # check the center. If it's free, take it.
        if board[4] == ' ':
            move = 4
            print(f"Taking the center. Move: {move + 1}")
            return move + 1

        # check all four corners to ensure there's at least one available. If there is an available corner, take it.
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if board[c] == ' ']
        if available_corners:
            move = random.choice(available_corners)
            print(f"Taking a corner. Move: {move + 1}")
            return move + 1

        # check all four edges to ensure there's at least one available. If there is an available edge, take it.
        edges = [1, 3, 5, 7]
        available_edges = [e for e in edges if board[e] == ' ']
        if available_edges:
            move = random.choice(available_edges)
            print(f"Taking an edge. Move: {move + 1}")
            return move + 1

        # if all of the above somehow don't give a move, select a random square.
        available = [i for i, v in enumerate(board) if v == ' ']
        if available:
            move = random.choice(available)
            print(f"No preferred move found. Picking available square. Move: {move + 1}")
            return move + 1

        # Should never happen, board is full
        print("Error: No valid moves.")
        return None

    else:
        print("Error: Invalid AI choice.")
        return None

def legit_move_input():

    global move_input, move

    try:
        move_input = int(move_input)

        move = move_input - 1
        if board[move] == ' ':
            return True
        else:
            print("Please enter a vacant position on the board.")
            return False
        
    except ValueError: # bare except was bad - replaced this with value error handler
        print("Please enter an integer from 1-9.")
        return False
    except TypeError: # ditto but with type error handler
        print("Please enter an integer from 1-9")
        return False

def find_winner():

    for combo in WINNING_COMBOS:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
            return board[combo[0]]
    if ' ' not in board:
        return "tie"
    
    return None

def get_current_input():

    global move_input, o_mode
    if o_mode:
        if current_player == 'x':
            move_input = get_ai_move()
        else:
            move_input = get_human_move()
    else:
        if current_player == 'x':
            move_input = get_human_move()
        else:
            move_input = get_ai_move()
    
def update_board_state():

    global game_winner, current_player, move

    if legit_move_input():
        board[move] = current_player
        game_winner = find_winner()

        if current_player == 'x':
            current_player = 'o'
        else:
            current_player = 'x'
    else:
        print("Please enter a valid input.")

def render_board_state():
    if game_winner is None: 
        # current player is currently the opposite of the player being displayed in this message
        # since it was flipped before this whole function was called
        # so this logic flips the message so that it is correct
        if current_player == 'x':
            print(f"{players['o']}'s move:")
        elif current_player == 'o':
            print(f"{players['x']}'s move:")

    # this print statement is intentionally less elegant to favour beginner readability
    print(f" {board[0]} | {board[1]} | {board[2]} \n-----------\n {board[3]} | {board[4]} | {board[5]} \n-----------\n {board[6]} | {board[7]} | {board[8]} ")

def show_help():
    help_text = '''Each move, please enter a number from 1-9, corresponding to the board positions like so:
     1 | 2 | 3 
    -----------
     4 | 5 | 6 
    -----------
     7 | 8 | 9 '''
    print(help_text)
    print(HR)

if __name__ == '__main__':
    # print a welcome message
    print("Welcome to the tic-tac-toe AI showcase.")
    show_help()

    current_player = 'x'

    while game_winner is None:
        get_current_input()
        update_board_state()
        render_board_state()
    
    print(HR)
    if game_winner == 'tie':
        print("It's a tie. Not big surprise.")
    elif game_winner in players:
        print(f"{players[game_winner]} wins.")
    print(HR)
    print("End of game.")