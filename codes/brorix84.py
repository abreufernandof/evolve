from tkinter import *
from time import sleep
from math import sin, cos, radians
from scux import Scux
from litix import Litix
import numpy as np
import pandas as pd


class Brorix84:
    def __init__(
        self,
        canvas: Canvas
    ):

        # Let's get some definitions:
        self.orbital_period = 360 # days, one "year".
        self.rotation_period = 36 # hours, one "day" + one "night"
        self.average_temperature = 27 # Celsius degrees

        # This colors change with seasons:
        self.colors = [
            "#133c81", "#123a7c", "#113878", "#103674", "#0f346f", "#0f326b",
            "#0e3066", "#0d2e62", "#0d2c5e", "#0d2a59", "#0c2855", "#0c2651",
            "#0b244d", "#0b2348", "#0b2144", "#0b1f40", "#0a1d3c", "#0a1b38",
            "#0a1b38", "#0a1d3c", "#0b1f40", "#0b2144", "#0b2348", "#0b244d",
            "#0c2651", "#0c2855", "#0d2a59", "#0d2c5e", "#0d2e62", "#0e3066",
            "#0f326b", "#0f346f", "#103674", "#113878", "#123a7c", "#133c81"
        ]

        self.day = 0            # Current day
        self.season = "hot"     # Current season
        self.year = 0           # Current year
        self.temperature = 27   # base temperature
        self.day_length = 18    # base day_lenght: day + night = rotation period

        self.scux_list = list()
        self.litix_list = list()

        self.canvas = canvas
        self.canvas.configure(bg = self.colors[0])
        self.canvas.update()
        self.log = pd.DataFrame()
# ---------------------------------------------------------------------------- #

    def _log_events(self):
        if self.day % 10 == 0:
            events = {
                "year": self.year,
                "season": self.season,
                "day": self.day,
                "day_length": self.day_length,
                "temperature": self.temperature,
                "alive_scux": len(self.scux_list),
                "alive_litix": len(self.litix_list),
                "total_scux_energy": sum(
                    [scux.energy_content for scux in self.scux_list]
                ),
                "total_litix_energy": sum(
                    [litix.energy_content for litix in self.litix_list]
                )
            }

            self.log = self.log.append(events, ignore_index = True)
            self.log.to_csv("../data/brorix84_log.csv", decimal = ",", index = False)

    def update_litix_list(self, n_litix):
        # We'll raise litix once.
        if len(self.litix_list) == 0:
            self.litix_list = [
                Litix(canvas = self.canvas)
                for i in range(n_litix)
            ]

        for litix in self.litix_list:
            litix._update_age()

            if litix.status == "dead":
                self.litix_list.remove(litix)

            self.canvas.update()
# ---------------------------------------------------------------------------- #
    def update_scux_list(self, n_scux):
        self.scux_list += [Scux(canvas = self.canvas) for i in range(n_scux)]

        for scux in self.scux_list:
            scux.update_age()

            if scux.status == "dead":
                self.scux_list.remove(scux)

            self.canvas.update()

# ---------------------------------------------------------------------------- #
    def update_appearance(self):
        if self.day % 10 == 0:
            self.canvas.configure(bg = self.colors[int(self.day / 10)-1])
            print (f"day = {self.day}")

# ---------------------------------------------------------------------------- #
    def update_temperature(self):
        self.temperature = 18 * sin(radians(self.day)) + self.average_temperature

# ---------------------------------------------------------------------------- #
    def update_day_length(self):
        self.day_length = sin(radians(self.day)) + (self.rotation_period / 2)

# ---------------------------------------------------------------------------- #
    def update_calendar(self):
        self.day += 1

        # 1. If day count is greater than 179, update season:
        if self.day >= (self.orbital_period / 2) - 1:
            self.season = "cold"
        else:
            self.season = "hot"

        # 2. If day count is greater than 359, update year count:
        if self.day >= self.orbital_period - 1:
            self.day = 0
            self.year += 1

        # 3. Update temperature and daylight time:
        self.update_appearance()
        self.update_temperature()
        self.update_day_length()

        # 4. Calculating constants:
        SCUX_PRODUCTION_RATE = int(2 * self.temperature - self.day_length)
        self.update_scux_list(n_scux = SCUX_PRODUCTION_RATE)
        self.update_litix_list(n_litix = 10)

        # 5. Logging:
        self._log_events()
