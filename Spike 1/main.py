# import libraries
import random
import time
from collections import deque
# function which prints the board state to the terminal
def print_board(board):
    # dictionary which is used to turn the raw data into board graphics
    player_symbol_of = {1: 'O', -1: 'X', 0: ' '}
    
    # prints the current board state to the terminal
    print(f"""
 {player_symbol_of[board[0]]} | {player_symbol_of[board[1]]} | {player_symbol_of[board[2]]}
---+---+---
 {player_symbol_of[board[3]]} | {player_symbol_of[board[4]]} | {player_symbol_of[board[5]]}
---+---+---
 {player_symbol_of[board[6]]} | {player_symbol_of[board[7]]} | {player_symbol_of[board[8]]}
    """)
# function which checks if the board is in a terminal state and returns the winner if it is
def find_winner(board):
    winning_combos = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8), # 3 in a row
    (0, 3, 6), (1, 4, 7), (2, 5, 8), # 3 in a column
    (0, 4, 8), (2, 4, 6) # 3 in a diagonal
    )
    # logic to check if one of the combos above is on the board
    for combo in winning_combos:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != 0:
            return board[combo[0]]
    # if the board is full and there's no winning player, return a draw
    if 0 not in board:
        return 0
    # if not, keep playing
    return None
# setup the current board state as a node
def create_nodes(board, player):
    # create a list for our nodes
    nodes = []
    # iterates through each available space and creates nodes for them
    for i in range(9):
        if board[i] == 0: # checks if space is empty
            # if it is, create a node and add it to the list of nodes
            new_node = list(board)
            new_node[i] = player
            nodes.append(tuple(new_node))
    return nodes

checked_branch = {}
# minimax logic function
def minimax(board, player):
    # if the board is in a branch which has been checked already, return the branch
    if board in checked_branch:
        return checked_branch[board]
    # if there's a winner on the board, return the winning player
    winner = find_winner(board)
    if winner is not None:
        checked_branch[board] = winner
        return winner
    # if the DFS is checking a node on its own turn, look for a win
    if player == 1: # maximise
        value = -float('inf')
        for node in create_nodes(board, player):
            value = max(value, minimax(node, -player))
    # checking a node on the opposition's turn
    elif player == -1: # minimise
        value = float('inf')
        for node in create_nodes(board, player):
            value = min(value, minimax(node, -player))
    print("DFS AI is looking at:")
    print_board(board)
    time.sleep(0.1)
    checked_branch[board] = value
    return value
# get a move input from a player
def player_move_input(board):
    while True:
        try:
            move_input = int(input("Please input an integer from 1-9:\n")) - 1
            if move_input < 0 or move_input > 8:
                print("Error - Please enter an integer from 1-9.")
            elif board[move_input] != 0:
                print("Error - Please enter a vacant space.")
            else:
                return move_input
            
        except ValueError: # bare except is bad - replaced this with value error handler
            print("Please enter an integer from 1-9.")
# BFS AI logic
def bfs_ai_move(board, player):
    # setup deque - mandatory for BFS
    queue = deque()
    visited = set()
    # randomise so the top row isn't prioritised
    for i in range(9):
        if board[i] == 0:
            new_node = list(board)
            new_node[i] = player
            queue.append((tuple(new_node), -player, i))
        moves = [i for i in range(9) if board[i] == 0]
    random.shuffle(moves)

    for i in moves:
        new_node = list(board)
        new_node[i] = player
        queue.append((tuple(new_node), -player, i))

    winning_moves = set()
    drawing_moves = set()
    # visited logic and choosing a move
    while queue:
        current_board, current_player, first_move = queue.popleft()

        if current_board in visited:
            continue
        visited.add(current_board)

        winner = find_winner(current_board)

        if winner == player:
            winning_moves.add(first_move)
            continue
        
        if winner == 0:
            drawing_moves.add(first_move)
            continue

        # expand BFS
        for node in create_nodes(current_board, current_player):
            queue.append((node, -current_player, first_move))

    # choose the best outcome
    if winning_moves:
        return random.choice(list(winning_moves))
    
    if drawing_moves:
        return random.choice(list(drawing_moves))
    
    # fallback move
    return random.choice(moves)
# use the minimax logic to make a move
def dfs_ai_move(board, player):
    best_score = -float('inf')
    move = None

    for i in range(9):
        if board[i] == 0:
            new_node = list(board)
            new_node[i] = player
            score = minimax(tuple(new_node), -player)

            if score > best_score:
                best_score = score
                move = i
    
    return move
# good ol' Randy chooses a random spot in the current board state
def randy_move(board, player):
    nodes = create_nodes(board, player)

    random_node = random.choice(nodes)

    for i in range(9):
        if board[i] != random_node[i]:
            return i
# get all of the choices from the player
def setup():
    while True:
        try:
            player_1 = int(input("Who will player 1 (Xs) be?\n1 - Random AI\n2 - NEVALOSE™ DFS AI\n3 - MAYBELOSE™ BFS AI\n4 - Human\n"))
            if player_1 == 1 or player_1 == 2 or player_1 == 3 or player_1 == 4:
                break
            else:
                print("Please try again - enter a number from 1-4.")
        except ValueError:
            print("Please try again - enter a number from 1-4.")

    while True:
        try:
            player_2 = int(input("Who will player 2 (Os) be?\n1 - Random AI\n2 - NEVALOSE™ DFS AI\n3 - MAYBELOSE™ BFS AI\n4 - Human\n"))
            if player_2 == 1 or player_2 == 2 or player_2 == 3 or player_2 == 4:
                break
            else:
                print("Please try again - enter a number from 1-4.")
        except ValueError:
            print("Please try again - enter a number from 1-4.")

    if player_1 == 1:
        player_1_name = "Randy"
    elif player_1 == 2:
        player_1_name = "NEVALOSE™ DFS AI"
    elif player_1 == 3:
        player_1_name = "MAYBELOSE™ BFS AI"
    elif player_1 == 4:
        player_1_name = input("What is player 1's name?\n")

    if player_2 == 1:
        if player_2 == player_1:
            player_2_name = "Randolph"
        else:
            player_2_name = "Randy"
    elif player_2 == 2:
        player_2_name = "NEVALOSE™ DFS AI"
    elif player_2 == 3:
        player_2_name = "MAYBELOSE™ BFS AI"
    elif player_2 == 4:
        player_2_name = input("What is player 2's name?\n")

    return player_1, player_2, player_1_name, player_2_name

def main():
    board = (0,0,0,
             0,0,0,
             0,0,0)
    # welcome text
    print("""Welcome to Edward's SPIKE tic-tac-toe, featuring the latest and greatest AI.
Inputs are integers from 1-9, corresponding to the following board spaces:
          
   1 | 2 | 3
  ---+---+---
   4 | 5 | 6 
  ---+---+---
   7 | 8 | 9 
          
You can choose to hop into the ring, or have our AIs duke it out.
""")
    # get player preferences here
    player_1, player_2, player_1_name, player_2_name = setup()
    # game loop
    while True:

        # player 1's move
        if player_1 == 1:
            move = randy_move(board, 1)
        elif player_1 == 2:
            move = dfs_ai_move(board, 1)
        elif player_1 == 3:
            move = bfs_ai_move(board, 1)
        elif player_1 == 4:
            move = player_move_input(board)

        board = list(board)
        board[move] = -1
        board = tuple(board)

        if find_winner(board) is not None:
            break

        print(f"{player_1_name}'s move:")
        print_board(board)

        time.sleep(2)

        # player 2's move
        if player_2 == 1:
            move2 = randy_move(board, 1)
        elif player_2 == 2:
            move2 = dfs_ai_move(board, 1)
        elif player_2 == 3:
            move2 = bfs_ai_move(board, 1)
        elif player_2 == 4:
            move2 = player_move_input(board)
        board = list(board)
        board[move2] = 1
        board = tuple(board)

        if find_winner(board) is not None:
            break

        print(f"{player_2_name}'s move:")
        print_board(board)
        # wait between moves to see logic in action
        time.sleep(2)

    game_winner = find_winner(board)
    if game_winner == 1:
        print(f"{player_2_name} wins.")
    elif game_winner == -1:
        print(f"{player_1_name} wins.")
    else: 
        print("It's a draw. Not big surprise.")
    
    print_board(board)

if __name__ == "__main__":
    main()

''' # testing the print board function
board = [0, -1, 0, 1, 1, 1, 0, -1, 0]
print_board(board)

# testing the find winner function
result = find_winner(board)
if result == 1:
    print("1 winner")
elif result == -1:
    print("-1 winner")
else:
    print("0 draw") '''