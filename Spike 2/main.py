import os
import sys
import pyglet
#import graphics
import game

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        base_dir = os.path.dirname(__file__)
        filename = os.path.join(base_dir, "map3.txt")

    game.game = game.Game(filename)
    pyglet.app.run()