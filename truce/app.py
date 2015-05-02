#!/usr/bin/env python

import argparse
import os.path
import re
import subprocess
import sys
import threading
import traceback

import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.simpledialog

from truce.catcher import Catcher

VERSION = [0, 2, 1]
ABANDON_MSG = 'Abandon unsaved changes?'


def signature():
    return '{} {}.{}.{}'.format(os.path.basename(sys.argv[0]), *VERSION)


ABOUT = """{}

http://github.com/jangler/truce-py""".format(signature())


class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack(expand=1, fill='both')
        self.createWidgets()
        self.filename = None
        self.regexp = None
        self.settitle()
        master.protocol("WM_DELETE_WINDOW", self.quit)

    def createWidgets(self):
        self.menu = tk.Menu(self)

        filemenu = tk.Menu(self.menu, tearoff=0)
        filemenu.add_command(label='New', underline=0, command=self.newfile,
                             accelerator='Ctrl+N')
        self.bind_all('<Control-n>', self.newfile)
        filemenu.add_command(label='Open...', underline=0, command=self.open,
                             accelerator='Ctrl+O')
        self.bind_all('<Control-o>', self.open)
        filemenu.add_separator()
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
        filemenu.add_command(label='Force Quit', underline=0,
                             accelerator='Ctrl+Shift+Q',
                             command=self.powerquit)
        self.bind_all('<Control-Q>', self.powerquit)
        self.menu.add_cascade(label='File', underline=0, menu=filemenu)

        editmenu = tk.Menu(self.menu, tearoff=0)
        editmenu.add_command(label='Undo', underline=0, command=self.undo,
                             accelerator='Ctrl+Z')
        editmenu.add_command(label='Redo', underline=0, command=self.redo,
                             accelerator='Ctrl+Y')
        editmenu.add_separator()
        editmenu.add_command(label='Pipe...', underline=0, command=self.pipe,
                             accelerator='Ctrl+P')
        self.bind_all('<Control-p>', self.pipe)
        self.menu.add_cascade(label='Edit', underline=0, menu=editmenu)

        selectmenu = tk.Menu(self.menu, tearoff=0)
        selectmenu.add_command(label='All', underline=0,
                               command=self.selectall, accelerator='Ctrl+A')
        self.bind_all('<Control-a>', self.selectall)
        selectmenu.add_separator()
        selectmenu.add_command(label='Find...', underline=0, command=self.find,
                               accelerator='Ctrl+F')
        self.bind_all('<Control-f>', self.find)
        self.bind_all('<Control-slash>', self.find)
        selectmenu.add_command(label='Next Match', underline=0,
                               command=self.nextmatch, accelerator='Alt+N')
        self.bind_all('<Alt-n>', self.nextmatch)
        selectmenu.add_command(label='Previous Match', underline=0,
                               command=self.prevmatch,
                               accelerator='Alt+Shift+N')
        self.bind_all('<Alt-N>', self.prevmatch)
        selectmenu.add_separator()
        selectmenu.add_command(label='Go to Line...', underline=0,
                               command=self.gotoline, accelerator='Ctrl+G')
        self.bind_all('<Control-g>', self.gotoline)
        self.menu.add_cascade(label='Select', underline=0, menu=selectmenu)

        helpmenu = tk.Menu(self.menu, tearoff=0)
        helpmenu.add_command(label='About...', underline=0, command=self.about)
        self.menu.add_cascade(label='Help', underline=0, menu=helpmenu)

        root.config(menu=self.menu)

        barframe = tk.Frame(self)
        barframe.pack(side='bottom', fill='x')

        self.status = tkinter.Label(barframe, text='', relief='sunken',
                                    anchor='w')
        self.status.pack(side='left', fill='x', expand=1)

        self.rowcol = tkinter.Label(barframe, text='', relief='sunken',
                                    anchor='e')
        self.rowcol.pack(side='right')
        self.bind_all('<Key>', self.refresh)
        self.bind_all('<Button-1>', self.refresh)
        self.bind_all('<ButtonRelease-1>', self.refresh)

        self.textin = tk.Text(self, height=0, undo=1)
        self.textin.bind('<Return>', self.sendtext)
        # self.textin.pack(side='bottom', fill='x')

        self.textout = tkinter.scrolledtext.ScrolledText(self, undo=1)
        self.textout.bind('<Return>', self.autoindent)
        self.textout.pack(side='bottom', expand=1, fill='both')

        for widget in (self.textin, self.textout):
            widget.bind('<Control-z>', self.undo)
            widget.bind('<Control-y>', self.redo)
            widget.bind('<Control-Z>', self.redo)
            widget.bind('<Control-o>', self.open)
            widget.bind('<Control-v>', self.deletesel)
            widget.bind('<Control-a>', self.selectall)
            widget.bind('<Control-f>', self.find)
            widget.bind('<Control-slash>', self.find)
            widget.bind('<Alt-n>', self.nextmatch)
            widget.bind('<Alt-N>', self.prevmatch)
            widget.bind('<Control-n>', self.newfile)
            widget.bind('<Control-p>', self.pipe)
            widget.bind('<Control-w>', self.deleteword)
            widget.bind('<Control-u>', self.deleteline)

    def refresh(self, event=None):
        self.rowcol['text'] = self.textout.index('insert').replace('.', ', ')

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
        if not (self.filename and self.textout.edit_modified()):
            return True
        elif tkinter.messagebox.askokcancel(ABANDON_MSG, ABANDON_MSG):
            return True
        return False

    def error(self, e):
        self.state()
        traceback.print_exc()
        tkinter.messagebox.showerror(type(e).__name__, str(e))

    def newfile(self, event=None):
        if not self.abandon():
            return 'break'
        self.state()
        self.textout.delete('1.0', 'end')
        self.textout.edit_modified(0)
        self.textout.edit_reset()
        self.filename = None
        self.settitle()

    def readin(self, filename, quiet=False):
        self.state('Opening...')
        try:
            with open(filename) as f:
                text = f.read()
        except Exception as e:
            if quiet:
                self.state('New file "{}".'.format(os.path.basename(filename)))
            else:
                self.error(e)
            return
        self.textout.replace('1.0', 'end', text)
        self.textout.delete('end - 1 char', 'end')  # delete extra newline
        self.state('Opened "{}".'.format(os.path.basename(filename)))
        self.textout.edit_modified(0)
        self.textout.edit_reset()
        self.filename = filename
        self.settitle()
        self.textout.mark_set('insert', '1.0')
        self.textout.see('insert')

    def open(self, event=None):
        if self.abandon():
            filename = tkinter.filedialog.askopenfilename()
            if filename:
                self.readin(filename)
        self.refresh()
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

    def search(self, regexp, backwards=False):
        widget = self.geteditfocus()
        offset = '-1c' if backwards else '+1c'
        index = widget.search(regexp, 'insert{}'.format(offset),
                              backwards=backwards, regexp=True)
        if index:
            widget.mark_set('insert', index)
            widget.see(index)
            widget.tag_remove('sel', '1.0', 'end')
            text = widget.get('insert', 'end')
            match = re.match(regexp, text, flags=re.MULTILINE)
            if match:
                length = len(match.group(0))
                widget.tag_add('sel', 'insert',
                               'insert+{}c'.format(length))
            self.state()
        else:
            self.state('No matches for "{}".'.format(regexp))
        self.regexp = regexp

    def find(self, event=None):
        widget = self.geteditfocus()
        try:
            regexp = tkinter.simpledialog.askstring(
                'Find', 'Search for regexp:')
            if regexp:
                self.search(regexp)
        except tkinter.TclError:
            pass
        widget.focus()
        self.refresh()
        return 'break'

    def refind(self, backwards=False):
        if self.regexp:
            self.search(self.regexp, backwards=backwards)
        else:
            self.state('Nothing to find.')

    def nextmatch(self, event=None):
        self.refind()
        self.refresh()
        return 'break'

    def prevmatch(self, event=None):
        self.refind(backwards=True)
        self.refresh()
        return 'break'

    def gotoline(self, event=None):
        try:
            line = tkinter.simpledialog.askinteger(
                'Go to Line', 'Go to line number:')
            if line or line == 0:
                index = '{}.end'.format(line)
                self.textout.mark_set('insert', index)
                self.textout.see(index)
                self.textout.tag_remove('sel', '1.0', 'end')
        except tkinter.TclError:
            pass
        self.textout.focus()

    def sendtext(self, event):
        self.textout.insert('end', self.textin.get('1.0', 'end'))
        self.textin.delete('1.0', 'end')
        self.refresh()
        return 'break'

    def autoindent(self, event):
        line = self.textout.get('insert linestart', 'insert lineend')
        indent = re.match('^[\t ]*', line).group(0)
        if re.match('^( |\t)+$', line):
            self.textout.replace('insert linestart', 'insert lineend',
                                 '\n' + indent)
        else:
            self.textout.insert('insert', '\n' + indent)
        self.textout.see('insert')
        self.refresh()
        return 'break'

    def geteditfocus(self):
        widget = self.focus_get()
        if widget not in (self.textin, self.textout):
            widget = self.textout
        return widget

    def deletesel(self, event):
        try:
            event.widget.delete('sel.first', 'sel.last')
        except tkinter.TclError:
            pass

    def backup(self, widget, dist, rule):
        while True:
            c = widget.get('insert-{}c'.format(dist + 1),
                           'insert-{}c'.format(dist))
            if not c or not rule(c):
                break
            dist += 1
        return dist, c

    def deleteword(self, event):
        dist, char = self.backup(event.widget, 0, lambda c: c.isspace())
        wordrule = lambda c: c.isalnum() or c == '_'
        nonwordrule = lambda c: not (c.isalnum() or c == '_' or c.isspace())
        if char.isalnum() or char == '_':
            dist, _ = self.backup(event.widget, dist, wordrule) 
            dist, _ = self.backup(event.widget, dist, nonwordrule)
        else:
            dist, _ = self.backup(event.widget, dist, nonwordrule)
            dist, _ = self.backup(event.widget, dist, wordrule)
        event.widget.delete('insert-{}c'.format(dist), 'insert')

    def deleteline(self, event):
        event.widget.delete('insert linestart', 'insert')

    def selectall(self, event=None):
        widget = self.geteditfocus()
        widget.tag_add('sel', '1.0', 'end')
        self.refresh()
        return 'break'

    def pipecmd(self, widget, cmd, intext):
        self.state('Running `{}`...'.format(cmd))
        try:
            text = subprocess.check_output(cmd, input=intext, shell=True,
                                           universal_newlines=True, timeout=5)
        except subprocess.SubprocessError as e:
            self.error(e)
            return
        if text.endswith('\n'):
            text = text[:len(text)-1]
        try:
            widget.mark_set('insert', 'sel.first')
            widget.replace('sel.first', 'sel.last', text)
            widget.tag_add('sel', 'insert-{}c'.format(len(text)), 'insert')
        except tkinter.TclError:
            widget.insert('insert', text)
        self.state()

    def pipe(self, event=None):
        widget = self.geteditfocus()
        try:
            cmd = tkinter.simpledialog.askstring(
                'Pipe', 'Pipe selection through command:')
            if cmd:
                intext = ''
                try:
                    intext = widget.get('sel.first', 'sel.last')
                except tkinter.TclError:
                    pass
                threading.Thread(target=self.pipecmd,
                                 args=[widget, cmd, intext]).start()
        except tkinter.TclError:
            pass
        widget.focus()
        self.refresh()
        return 'break'

    def undo(self, event=None):
        widget = self.geteditfocus()
        try:
            widget.edit_undo()
            self.state()
        except tkinter.TclError as e:
            self.state('{}.'.format(str(e).capitalize()))
        self.refresh()
        return 'break'

    def redo(self, event=None):
        widget = self.geteditfocus()
        try:
            widget.edit_redo()
            self.state()
        except tkinter.TclError as e:
            self.state('{}.'.format(str(e).capitalize()))
        self.refresh()
        return 'break'

    def quit(self, event=None):
        if self.abandon():
            super().quit()

    def powerquit(self, event=None):
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
