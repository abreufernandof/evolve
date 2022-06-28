from tkinter import *
from time import sleep

from brorix84 import Brorix84

tk = Tk()
canvas = Canvas(tk, width=1000, height=700, bg="#27505c")
canvas.pack()

planet = Brorix84(canvas = canvas)

for i in range(36000):
    planet.update_calendar()
    sleep(0.01)

tk.mainloop()
