import sys
import pyglet
#import graphics
import game

if __name__ == '__main__':
    #filename = input("Please input the file name of the map text file:\n")
    filename = 'Lab 3/map1.txt'

    game.game = game.Game(filename)
    pyglet.app.run()