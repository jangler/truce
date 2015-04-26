#!/usr/bin/env python

import os.path
import re
import sys

import tkinter as tk
import tkinter.filedialog
import tkinter.scrolledtext

VERSION = [0, 0, 0]


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack(expand=1, fill='both')
        self.createWidgets()
        self.filename = None
        self.settitle()

    def createWidgets(self):
        self.menu = tk.Menu(self)

        filemenu = tk.Menu(self.menu, tearoff=0)
        filemenu.add_command(label='Open', underline=0, command=self.open,
                             accelerator='Ctrl+O')
        self.bind_all('<Control-o>', self.open)
        filemenu.add_command(label='Save', underline=0, command=self.save,
                             accelerator='Ctrl+S')
        self.bind_all('<Control-s>', self.save)
        filemenu.add_command(label='Save As...', underline=5,
                             command=self.saveas, accelerator='Ctrl+Shift+S')
        self.bind_all('<Control-S>', self.saveas)
        filemenu.add_separator()
        filemenu.add_command(label='Quit', underline=0, accelerator='Ctrl+Q',
                             command=self.quit)
        self.bind_all('<Control-q>', self.quit)
        self.menu.add_cascade(label='File', underline=0, menu=filemenu)

        editmenu = tk.Menu(self.menu, tearoff=0)
        editmenu.add_command(label='Undo', underline=0, command=self.undo,
                             accelerator='Ctrl+Z')
        self.bind_all('<Control-z>', self.undo)
        editmenu.add_command(label='Redo', underline=0, command=self.redo,
                             accelerator='Ctrl+Y')
        self.bind_all('<Control-y>', self.redo)
        self.menu.add_cascade(label='Edit', underline=0, menu=editmenu)

        root.config(menu=self.menu)

        self.status = tkinter.Label(self, text='', relief='sunken',
                                    anchor='w')
        self.status.pack(side='bottom', fill='x')

        self.textin = tk.Text(self, height=0, undo=1)
        self.textin.bind('<Return>', self.sendtext)
        self.textin.pack(side='bottom', fill='x')

        self.textout = tkinter.scrolledtext.ScrolledText(self, undo=1)
        self.textout.bind('<Return>', self.autoindent)
        self.textout.pack(side='bottom', expand=1, fill='both')

    def state(self, text=''):
        self.status['text'] = text

    def settitle(self):
        if self.filename:
            self.master.title(os.path.basename(self.filename))
        else:
            self.master.title('{} {}.{}.{}'.format(sys.argv[0], *VERSION))

    def open(self, event=None):
        filename = tkinter.filedialog.askopenfilename()
        if filename:
            self.filename = filename
            self.settitle()
            self.textout.delete('1.0', 'end')
            self.state('Opening...')
            with open(filename) as f:
                self.textout.insert('insert', f.read())
            self.state('Opened "{}".'.format(
                os.path.basename(self.filename)))

    def save(self, event=None):
        if self.filename:
            self.writeout()
        else:
            self.saveas(event)

    def saveas(self, event=None):
        filename = tkinter.filedialog.asksaveasfilename()
        if filename:
            self.filename = filename
            self.settitle()
            self.writeout()

    def writeout(self):
        self.state('Saving...')
        with open(self.filename, 'w') as f:
            f.write(self.textout.get('1.0', 'end'))
        self.state('Saved "{}".'.format(os.path.basename(self.filename)))

    def sendtext(self, event):
        self.textout.insert('end', self.textin.get('1.0', 'end'))
        self.textin.delete('1.0', 'end')
        return 'break'

    def autoindent(self, event):
        line = self.textout.get('insert linestart', 'insert lineend')
        indent = re.match('^[\t ]*', line).group(0)
        self.textout.insert('insert', '\n' + indent)
        return 'break'

    def getundofocus(self):
        widget = self.focus_get()
        if widget not in (self.textin, self.textout):
            widget = self.textout
        return widget

    def undo(self, event=None):
        widget = self.getundofocus()
        try:
            widget.edit_undo()
            self.state()
        except tkinter.TclError as e:
            self.state('Nothing to undo.')

    def redo(self, event=None):
        widget = self.getundofocus()
        try:
            widget.edit_redo()
            self.state()
        except tkinter.TclError as e:
            self.state('Nothing to redo.')


root = tk.Tk()
app = Application(master=root)
app.mainloop()
