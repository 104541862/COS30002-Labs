import sys
import pyglet
#import graphics
import game

if __name__ == '__main__':
    #filename = input("Please input the file name of the map text file:\n")
    filename = 'C:/Users/User/OneDrive/Desktop/COS 30002 Labs/COS30002-Labs/Lab 3/map2.txt'

    game.game = game.Game(filename)
    pyglet.app.run()