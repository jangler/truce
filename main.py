#!/usr/bin/env python

import sys

import tkinter as tk
import tkinter.font
import tkinter.scrolledtext

VERSION = [0, 0, 0]

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack(expand=1, fill='both')
        self.createWidgets()
        self.master.title('{} {}.{}.{}'.format(sys.argv[0], *VERSION))

    def createWidgets(self):
        self.menu = tk.Menu(self)

        filemenu = tk.Menu(self.menu, tearoff=0)
        filemenu.add_command(label='Exit', command=root.quit)
        self.menu.add_cascade(label='File', menu=filemenu)
        root.config(menu=self.menu)

        self.status = tkinter.Label(self, text='', relief='sunken',
                anchor='w')
        self.status.pack(side='bottom', fill='x')

        self.textin = tk.Text(self)
        self.textin['height'] = tkinter.font.nametofont(
                self.textin['font'])['size']
        self.textin['height'] = 0
        self.textin.pack(side='bottom', fill='x')

        self.textout = tkinter.scrolledtext.ScrolledText(self)
        self.textout.pack(side='bottom', expand=1, fill='both')


root = tk.Tk()
app = Application(master=root)
app.mainloop()
