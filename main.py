#!/usr/bin/env python3
"""
Main entry point for the 3D Hunting Simulator Game.
Initializes the game engine and starts the main game loop.
"""

import sys
from direct.showbase.ShowBase import ShowBase
from core.game import Game

class MainApp(ShowBase):
    """Main application class that initializes Panda3D and starts the game."""

    def __init__(self):
        """Initialize the Panda3D application and game."""
        ShowBase.__init__(self)
        self.game = Game(self)
        self.game.start()

def main():
    """Main function to run the application."""
    app = MainApp()
    app.run()

if __name__ == "__main__":
    main()