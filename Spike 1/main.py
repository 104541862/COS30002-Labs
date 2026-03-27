import random
import time

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

def find_winner(board):
    winning_combos = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8), # 3 in a row
    (0, 3, 6), (1, 4, 7), (2, 5, 8), # 3 in a column
    (0, 4, 8), (2, 4, 6) # 3 in a diagonal
    )

    for combo in winning_combos:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != 0:
            return board[combo[0]]
    if 0 not in board:
        return 0
    
    return None

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

def minimax(board, player):
    # if the board is in a branch which has been checked already, return the branch
    if board in checked_branch:
        return checked_branch[board]
    
    winner = find_winner(board)
    if winner is not None:
        checked_branch[board] = winner
        return winner
    
    if player == 1: # maximise
        value = -float('inf')
        for node in create_nodes(board, player):
            value = max(value, minimax(node, -player))
    elif player == -1: # minimise
        value = float('inf')
        for node in create_nodes(board, player):
            value = min(value, minimax(node, -player))
    
    checked_branch[board] = value
    return value

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

def dfs_ai_move(board, player):
    best_score = -float('inf')
    move = None

    for i in range(9):
        if board[i] == 0:
            board_list = list(board)
            board_list[i] = player
            score = minimax(tuple(board_list), -player)

            if score > best_score:
                best_score = score
                move = i
    
    return move

def main():
    board = (0,0,0,
             0,0,0,
             0,0,0)
    
    print("""Welcome to Edward's SPIKE tic-tac-toe, featuring the latest and greatest AI.
Inputs are integers from 1-9, corresponding to the following board spaces:
          
   1 | 2 | 3
  ---+---+---
   4 | 5 | 6 
  ---+---+---
   7 | 8 | 9 
          
(for now) You are X and our NEVALOSE™ AI is O.
""")
    player_name = input("What is your name?\n")

    while True:

        # player's move
        move = player_move_input(board)
        board = list(board)
        board[move] = -1
        board = tuple(board)

        if find_winner(board) is not None:
            break

        print(f"{player_name}'s move:")
        print_board(board)

        ai_move = dfs_ai_move(board, 1)
        board = list(board)
        board[ai_move] = 1
        board = tuple(board)

        if find_winner(board) is not None:
            break

        print(f"NEVALOSE™ AI's move:")
        print_board(board)
    
    print_board(board)

    game_winner = find_winner(board)
    if game_winner == 1:
        print("NEVALOSE™ AI always wins.")
    elif game_winner == -1:
        print("How did you win‽")
    else: 
        print("It's a draw. Not big surprise.")

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