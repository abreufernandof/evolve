from tkinter import *
import numpy as np
from time import sleep, time

class Scux:
    def __init__(
        self,
        canvas: Canvas
    ):

        # Some characteristics first: size, energy content, color...
        self.age = 0                        # It's a newborn
        self.size = np.random.randint(3, 7) # Size may change from 3 to 7
        self.energy_content = self.size ** 2 # minimum 9, maximum 49

        # The colors change as the scux gets older.
        self.colors = [
            "#a1ff26", "#a6e91f", "#a4d319", "#a3bd13", "#9fa70e",
            "#918c0a", "#7a6b06", "#644d03", "#4e3601", "#382100",

        ]

        # The initial position is random:
        self.initial_position = tuple(
            np.random.choice(
                np.random.randint(5, 995, 100),
                2
            )
        )

        self.status = "alive"
        self.canvas = canvas

        # Body is a rectangle:
        self.body = self.canvas.create_rectangle(
            self.initial_position[0] - (self.size / 2),
            self.initial_position[1] - (self.size / 2),
            self.initial_position[0] + (self.size / 2),
            self.initial_position[1] + (self.size / 2),
            fill = self.colors[0],
            outline = self.colors[0],
            tag = "scux"
        )

        self.canvas.update()

# ---------------------------------------------------------------------------- #
    def update_energy_content(self):
        MAX_ENERGY_CONTENT = self.size ** 2
        DECREMENT = np.ceil(MAX_ENERGY_CONTENT * 0.10)

        self.energy_content = MAX_ENERGY_CONTENT - (self.age * DECREMENT)

        if self.energy_content < 0:
            self.energy_content = 0

# ---------------------------------------------------------------------------- #
    def update_appearance(self):
        self.canvas.itemconfig(
            self.body,
            fill = self.colors[self.age] if self.age < 10 else self.colors[-1]
        )

        self.canvas.itemconfig(
            self.body,
            outline = self.colors[self.age] if self.age < 10 else self.colors[-1]
        )

        self.canvas.update()

# ---------------------------------------------------------------------------- #
    def die(self):
        self.canvas.delete(self.body)
        self.canvas.update()
        self.status = "dead"

# ---------------------------------------------------------------------------- #
    def update_age(self):
        self.age += 1
        self.update_energy_content()
        self.update_appearance()

        if self.energy_content == 0:
            self.die()
