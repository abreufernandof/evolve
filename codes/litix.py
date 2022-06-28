from tkinter import *
from math import sin, cos, radians
import numpy as np
import pandas as pd
import uuid


class Litix:
    """This class implements a Litix. An unicelular creature from Brorix84
    world that converts organic matter into energy.
    """
    def __init__(
        self,
        canvas: Canvas,
        cell_size: int = None,
        cell_speed: int = None,
        cell_colors: list = None,
        max_memory_size: int = 100,
        max_energy_content: int = None,
        metabolic_cost: int = None,
        sense_range: int = None,
        direction_angle: int = None,
        direction_angle_window: int = None,
        direction_change_prob: float = None,
        center_coordinates: tuple = None
    ):
        """Instantiate an Litix creature. Litix are very simple creatures that
        eat organic matter in order to get energy.

        Args:
            cell_size (int): The size of cells in pixels. It is randomly choosed
                among 14, 16, 18, and 20 if None. Size also defines `cell_speed`
                (defaults to 1.3 * `cell_size`) and `max_energy_content`
                (defaults to `cell_size` ** 2).

            cell_speed (int): The distance runs by the cell at each step.
                Defaults to 1.3 * `cell_size` if None.

            cell_colors (list): A pallete with ten RGB colors to indicate the
                cell `current_energy_content`. Defaults to [ "#f6ac40",
                "#db9a39", "#c18933", "#a8782c", "#906726", "#785620",
                "#62461a", "#4c3715", "#38280f", "#251a05"] if None.

            max_memory_size (int): The maximum history records this cell can
                store. This is used to take decisions, so, bugger mememories
                allows to store more data. Defaults to 100.

            max_energy_content (int): The maximum life points this cell has.
                Defaults to `cell_size` ** 2 if None.

            metabolic_cost (int): How many life points this cell loses every
                time it ages. Defaults to `cell_size` / 100 if None.

            sense_range (int): How far this cell can feel other Brorix84
                creatures. Defaults to `cell_size` * 2 if None.

            direction_angle (int): The initial direction cell follows. If None
                defaults to a random value between 0 and 359.

            center_coordinates (tuple): Tuple of integers representing the
                cell initial coordinates in `canvas`.

            canvas (Tkinter.canvas): The canvas where this cell will be placed.

        """

        self.cell_size = cell_size
        self.cell_speed = cell_speed
        self.cell_colors = cell_colors
        self.max_memory_size = max_memory_size
        self.max_energy_content = max_energy_content
        self.metabolic_cost = metabolic_cost
        self.sense_range = sense_range
        self.direction_angle = direction_angle
        self.direction_angle_window = direction_angle_window
        self.direction_change_prob = direction_change_prob
        self.center_coordinates = center_coordinates
        self.canvas = canvas

        self.age = 0
        self.feeling = None
        self.status = "alive"
        self.tracks = list()
        self.memory = pd.DataFrame()
        self.current_color = self.cell_colors[0]
        self.cell = {"body": None, "sense": None}
        self.energy_content = self.max_energy_content
        self.id = str(uuid.uuid4().hex)

        self._draw_cell()

# ---------------------------------------------------------------------------- #
    def _randomize_direction_angle(self):
        try:
            self.direction_angle = np.random.randint(
                self.direction_angle - self.direction_angle_window,
                self.direction_angle + self.direction_angle_window
            )
        except ValueError:
            self.direction_angle = np.random.randint(
                self.direction_angle + self.direction_angle_window,
                self.direction_angle - self.direction_angle_window
            )

# ---------------------------------------------------------------------------- #
    def _update_direction_angle(self):
        """Update direction follow this policy: If the last result was greater
        than the previous one, increase the chance of keeping this direction,
        otherwise, increase the chance of changing direction.

        Args:
            None.
        Returns:
            None.
        """
        if self.memory.shape[0] > 10:
            long_term_reward = self.memory.long_term_reward.to_list()[-1]

            self.direction_change_prob += long_term_reward

            if np.random.random() >= self.direction_change_prob:
                self.direction_angle_window += 1
                self._randomize_direction_angle()
            else:
                self.direction_angle_window -= 1
        else:
            self._randomize_direction_angle()

# ---------------------------------------------------------------------------- #
    def _log_events(self):
        events = {
            "age": self.age,
            "color": self.current_color,
            "energy": self.energy_content / self.max_energy_content,
            "position_x": self.center_coordinates[0],
            "position_y": self.center_coordinates[1],
            "direction": self.direction_angle,
            "in_touch": int(
                "".join([str(len(object_)) for object_ in self.feeling[0].values()])
            ),
            "in_range": int(
                "".join([str(len(object_)) for object_ in self.feeling[1].values()])
            ),
            "status": self.status
        }

        self.memory = self.memory.append(events, ignore_index = True)

        if self.memory.shape[0] > self.max_memory_size:
            self.memory = self.memory.tail(self.max_memory_size)

        self._update_reward()

        if self.age % 10 == 0:
            self.memory.to_csv(f"../data/litix_memory_{self.id}.csv", decimal = ",", index = False)

# ---------------------------------------------------------------------------- #
    def _update_reward(self):

        def short_term_reward_policy(energy_diff):
            return energy_diff

        def long_term_reward_policy(short_term_reward_value):
            return np.mean(
                np.asarray(
                    [
                        strv + (strv * 1 / i)
                        for strv, i in zip(short_term_reward_value, range(1, 11))
                    ]
                )
            )

        self.memory["short_term_reward"] = self.memory.energy.diff().apply(
            lambda x: short_term_reward_policy(x)
        )

        self.memory["long_term_reward"] = self.memory.short_term_reward.rolling(
            window = 10
        ).apply(
            lambda x: long_term_reward_policy(x)
        )

        self.memory["long_term_reward"].fillna(self.memory.long_term_reward.mean(), inplace = True)

# ---------------------------------------------------------------------------- #
    def _update_feeling(self):
        tags = ["scux", "litix", "vohix"]
        body_coords = self.canvas.coords(self.cell["body"])
        sense_coords = self.canvas.coords(self.cell["sense"])

        in_touch_objects = {
            tag: [
                id
                for id in self.canvas.find_overlapping(
                    body_coords[0],
                    body_coords[1],
                    body_coords[2],
                    body_coords[3]
               )
               if id in self.canvas.find_withtag(tag)
               and id not in [self.cell["body"], self.cell["sense"]]
            ]
            for tag in tags
        }

        in_range_objects = {
            tag: [
                id
                for id in self.canvas.find_enclosed(
                    sense_coords[0],
                    sense_coords[1],
                    sense_coords[2],
                    sense_coords[3]
               )
               if id in self.canvas.find_withtag(tag)
               and id not in [self.cell["body"], self.cell["sense"]]
            ]
            for tag in tags
        }

        self.feeling = (in_touch_objects, in_range_objects)

# ---------------------------------------------------------------------------- #
    def __check_canvas_limits(self, value, limit):
        if value > limit:
            return limit
        elif value < 0:
            return  0
        else:
            return int(np.floor(value))

# ---------------------------------------------------------------------------- #
    def _update_current_color(self):
        energy_proportion = self.energy_content / self.max_energy_content
        current_color_index = 10 - int(np.ceil(energy_proportion * 10))

        if current_color_index >= 10:
            current_color_index = 9

        self.current_color = self.cell_colors[current_color_index]

        self.canvas.itemconfig(
            self.cell["body"],
            fill = self.current_color
        )

        self.canvas.itemconfig(
            self.cell["body"],
            outline = self.current_color
        )

        self.canvas.itemconfig(
            self.cell["sense"],
            outline = self.current_color
        )

# ---------------------------------------------------------------------------- #
    def _update_track_list(self, origin, destination):
        self.tracks.append(
            self.canvas.create_line(
                origin[0],
                origin[1],
                destination[0],
                destination[1],
                fill = self.current_color
            )
        )

        if len(self.tracks) > 10:
            self.canvas.delete(self.tracks[0])
            self.tracks.remove(self.tracks[0])
# ---------------------------------------------------------------------------- #
    def _draw_cell(self):
        self.cell["body"] = self.canvas.create_oval(
            self.center_coordinates[0] - (self.cell_size / 2),
            self.center_coordinates[1] - (self.cell_size / 2),
            self.center_coordinates[0] + (self.cell_size / 2),
            self.center_coordinates[1] + (self.cell_size / 2),
            fill = self.current_color,
            outline = self.current_color,
            tag = ("litix", "body")
        )

        self.cell["sense"] = self.canvas.create_oval(
            self.center_coordinates[0] - self.sense_range,
            self.center_coordinates[1] - self.sense_range,
            self.center_coordinates[0] + self.sense_range,
            self.center_coordinates[1] + self.sense_range,
            outline = self.current_color,
            tag = ("litix", "sense")
        )

# ---------------------------------------------------------------------------- #
    def _update_center_coordinates(self):
        old_x = self.center_coordinates[0]
        old_y = self.center_coordinates[1]

        new_x = self.__check_canvas_limits(
            old_x + self.cell_speed * cos(radians(self.direction_angle)),
            1000
        )

        new_y = self.__check_canvas_limits(
            old_y + self.cell_speed * sin(radians(self.direction_angle)),
            700
        )

        self.center_coordinates = (new_x, new_y)

        # print(f"NC = {(new_x, new_y)}")

        return (old_x, old_y), (new_x, new_y)

# ---------------------------------------------------------------------------- #
    def _update_position(self):
        origin, destination = self._update_center_coordinates()

        self.canvas.coords(
            self.cell["body"],
            self.center_coordinates[0] - (self.cell_size / 2),
            self.center_coordinates[1] - (self.cell_size / 2),
            self.center_coordinates[0] + (self.cell_size / 2),
            self.center_coordinates[1] + (self.cell_size / 2)
        )

        self.canvas.coords(
            self.cell["sense"],
            self.center_coordinates[0] - self.sense_range,
            self.center_coordinates[1] - self.sense_range,
            self.center_coordinates[0] + self.sense_range,
            self.center_coordinates[1] + self.sense_range
        )

        self._update_track_list(origin, destination)
# ---------------------------------------------------------------------------- #
    def _update_energy_content(self):
        # 1. First, let's feed this creature:
        for scux in self.feeling[0]["scux"]:
            scux_coords = self.canvas.coords(scux)
            scux_energy_content = (scux_coords[2] - scux_coords[0]) ** 2

            self.energy_content += scux_energy_content

            if self.energy_content > self.max_energy_content:
                self.energy_content = self.max_energy_content

            self.canvas.delete(scux)

        # 2. Now, let's discount the metabolic cost
        self.energy_content -= self.metabolic_cost

# ---------------------------------------------------------------------------- #
    def _update_status(self):
        if self.energy_content <= 0:
            self.canvas.delete(self.cell["body"])
            self.canvas.delete(self.cell["sense"])
            for track in self.tracks:
                self.canvas.delete(track)

            self.status = "dead"
        else:
            self.sttus = "alive"

# ---------------------------------------------------------------------------- #
    def _update_age(self):
        if self.status == "alive":
            self.age += 1
            self._update_position()
            self._update_feeling()
            self._update_energy_content()
            self._update_current_color()
            self._update_status()
            self._log_events()
            #self.direction_angle = np.random.randint(0, 360)
            self._update_direction_angle()

# ---------------------------------------------------------------------------- #
    @property
    def direction_change_prob(self):
        return self._direction_change_prob

    @direction_change_prob.setter
    def direction_change_prob(self, value):
        assert isinstance(value, float) or value is None, \
            f"<ERROR> `direction_angle_window` must be a float, not {type(value)}"

        if value is None:
            self._direction_change_prob = np.random.uniform(0.4, 0.61)
        else:
            if value < 0.10:
                self._direction_change_prob = 0.10
            elif value > 0.90:
                self._direction_change_prob = 0.90
            else:
                self._direction_change_prob = value

# ---------------------------------------------------------------------------- #
    @property
    def direction_angle_window(self):
        return self._direction_angle_window

    @direction_angle_window.setter
    def direction_angle_window(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `direction_angle_window` must be an integer, not {type(value)}"

        if value is None:
            self._direction_angle_window = np.random.randint(30, 90)
        else:
            if value < 30:
                self._direction_angle_window = 30
            elif value > 90:
                self._direction_angle_window = 90
            else:
                self._direction_angle_window = value

# ---------------------------------------------------------------------------- #
    @property
    def direction_angle(self):
        return self._direction_angle

    @direction_angle.setter
    def direction_angle(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `direction_angle` must be an integer, not {type(value)}"

        if value is None:
            self._direction_angle = np.random.randint(0, 360)
        else:
            self._direction_angle = value

# ---------------------------------------------------------------------------- #
    @property
    def center_coordinates(self):
        return self._center_coordinates

    @center_coordinates.setter
    def center_coordinates(self, value):
        assert isinstance(value, tuple) or value is None, \
            f"<ERROR> `center_coordinates` must be an integer, not {type(value)}"

        if value is None:
            self._center_coordinates = (
                np.random.randint(5, 995),
                np.random.randint(5, 700)
            )
        else:
            self._center_coordinates = value

# ---------------------------------------------------------------------------- #
    @property
    def sense_range(self):
        return self._sense_range

    @sense_range.setter
    def sense_range(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `sense_range` must be a tuple of integers, not {type(value)}"

        if value is None:
            self._sense_range = 2 * self.cell_size
        else:
            self._sense_range = value

# ---------------------------------------------------------------------------- #
    @property
    def metabolic_cost(self):
        return self._metabolic_cost

    @metabolic_cost.setter
    def metabolic_cost(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `metabolic_cost` must be an integer, not {type(value)}"

        if value is None:
            self._metabolic_cost = (
                int(self.cell_size / 100)
                if int(self.cell_size / 100) >= 1
                else 1
            )
        else:
            self._metabolic_cost = (
                value
                if value >= 1
                else 1
            )

# ---------------------------------------------------------------------------- #
    @property
    def max_energy_content(self):
        return self._max_energy_content

    @max_energy_content.setter
    def max_energy_content(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `max_energy_content` must be an integer, not {type(value)}"

        if value is None:
            self._max_energy_content = self.cell_size ** 2
        else:
            self._max_energy_content = value

# ---------------------------------------------------------------------------- #
    @property
    def max_memory_size(self):
        return self._max_memory_size

    @max_memory_size.setter
    def max_memory_size(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `max_memory_size` must be an integer, not {type(value)}"

        if value is None:
            self._max_memory_size = 100
        else:
            self._max_memory_size = value

# ---------------------------------------------------------------------------- #
    @property
    def cell_colors(self):
        return self._cell_colors

    @cell_colors.setter
    def cell_colors(self, value):
        assert isinstance(value, list) or value is None, \
            f"<ERROR> `cell_colors` must be a list, not {type(value)}"

        if value is None:
            self._cell_colors = [
                "#ff8b15", "#fe9831", "#fda547", "#fcb15d", "#fbbc72",
                "#fac788", "#fad29e", "#f9dcb4", "#f8e5cb", "#f7efe3"
            ]
        else:
            self._cell_colors = value

# ---------------------------------------------------------------------------- #
    @property
    def cell_speed(self):
        return self._cell_speed

    @cell_speed.setter
    def cell_speed(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `cell_speed` must be an integer, not {type(value)}"

        if value is None:
            self._cell_speed = 1.3 * self.cell_size
        else:
            self._cell_speed = value

# ---------------------------------------------------------------------------- #
    @property
    def cell_size(self):
        return self._cell_size

    @cell_size.setter
    def cell_size(self, value):
        assert isinstance(value, int) or value is None, \
            f"<ERROR> `cell_size` must be an integer, not {type(value)}"

        if value is None:
            self._cell_size = np.random.choice([14, 16, 18, 20])
        else:
            self._cell_size = value if value % 2 == 0 else value + 1

# ---------------------------------------------------------------------------- #
