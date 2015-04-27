#!/usr/bin/env python

import argparse
import os.path
import re
import sys
import traceback

import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext

from truce.catcher import Catcher

VERSION = [0, 1, 0]
ABANDON_MSG = 'Abandon unsaved changes?'


def signature():
    return '{} {}.{}.{}'.format(os.path.basename(sys.argv[0]), *VERSION)


ABOUT = """{}

http://github.com/jangler/truce""".format(signature())


class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack(expand=1, fill='both')
        self.createWidgets()
        self.filename = None
        self.settitle()
        master.protocol("WM_DELETE_WINDOW", self.quit)

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
        editmenu.add_command(label='Redo', underline=0, command=self.redo,
                             accelerator='Ctrl+Y')
        self.menu.add_cascade(label='Edit', underline=0, menu=editmenu)

        helpmenu = tk.Menu(self.menu, tearoff=0)
        helpmenu.add_command(label='About', underline=0, command=self.about)
        self.menu.add_cascade(label='Help', underline=0, menu=helpmenu)

        root.config(menu=self.menu)

        self.status = tkinter.Label(self, text='', relief='sunken',
                                    anchor='w')
        self.status.pack(side='bottom', fill='x')

        self.textin = tk.Text(self, height=0, undo=1)
        self.textin.bind('<Return>', self.sendtext)
        self.textin.bind('<Control-z>', self.undo)
        self.textin.bind('<Control-y>', self.redo)
        self.textin.bind('<Control-Z>', self.redo)
        self.textin.bind('<Control-o>', self.open)
        self.textin.pack(side='bottom', fill='x')

        self.textout = tkinter.scrolledtext.ScrolledText(self, undo=1)
        self.textout.bind('<Return>', self.autoindent)
        self.textout.bind('<Control-z>', self.undo)
        self.textout.bind('<Control-y>', self.redo)
        self.textout.bind('<Control-Z>', self.redo)
        self.textout.bind('<Control-o>', self.open)
        self.textout.pack(side='bottom', expand=1, fill='both')

    def about(self):
        tkinter.messagebox.showinfo('About', ABOUT)

    def state(self, text=''):
        self.status['text'] = text

    def settitle(self):
        if self.filename:
            self.master.title(os.path.basename(self.filename))
        else:
            self.master.title(signature())

    def abandon(self):
        if not self.textout.edit_modified():
            return True
        elif tkinter.messagebox.askokcancel(ABANDON_MSG, ABANDON_MSG):
            return True
        return False

    def error(self, e):
        self.state()
        traceback.print_exc()
        tkinter.messagebox.showerror(type(e).__name__, str(e))

    def readin(self, filename, quiet=False):
        self.state('Opening...')
        try:
            with open(filename) as f:
                text = f.read()
        except Exception as e:
            if not quiet:
                self.error(e)
            return
        self.textout.delete('1.0', 'end')
        self.textout.insert('insert', text)
        self.state('Opened "{}".'.format(os.path.basename(filename)))
        self.textout.edit_modified(0)
        self.filename = filename
        self.settitle()

    def open(self, event=None):
        if self.abandon():
            filename = tkinter.filedialog.askopenfilename()
            if filename:
                self.readin(filename)
        return 'break'

    def save(self, event=None):
        if self.filename:
            self.writeout(self.filename)
        else:
            self.saveas(event)

    def saveas(self, event=None):
        filename = tkinter.filedialog.asksaveasfilename()
        if filename:
            self.writeout(filename)

    def writeout(self, filename):
        self.state('Saving...')
        try:
            with open(filename, 'w') as f:
                f.write(self.textout.get('1.0', 'end'))
            self.state('Saved "{}".'.format(os.path.basename(filename)))
            self.textout.edit_modified(0)
            self.filename = filename
            self.settitle()
        except Exception as e:
            self.error(e)

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
            self.state('{}.'.format(str(e).capitalize()))
        return 'break'

    def redo(self, event=None):
        widget = self.getundofocus()
        try:
            widget.edit_redo()
            self.state()
        except tkinter.TclError as e:
            self.state('{}.'.format(str(e).capitalize()))
        return 'break'

    def quit(self, event=None):
        if self.abandon():
            super().quit()


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=signature())
    parser.add_argument('file', type=str, nargs='?', help='file to edit')
    return parser.parse_args()


def main():
    global root
    args = parseargs()
    root = tk.Tk()
    tk.CallWrapper = Catcher
    app = App(master=root)

    def excepthook(exctype, value, traceback):
        app.error(value)
    sys.excepthook = excepthook

    if args.file:
        app.readin(args.file, quiet=True)
        app.filename = args.file
        app.settitle()

    try:
        app.mainloop()
    except KeyboardInterrupt:
        super(tk.Frame, app).quit()
        print()
