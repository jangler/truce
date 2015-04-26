import traceback

import tkinter
import tkinter.messagebox


class Catcher:
    def __init__(self, func, subst, widget):
        self.func = func
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        except Exception as e:
            title = type(e).__name__
            msg = traceback.format_exception_only(type(e), e)
            tkinter.messagebox.showerror(title=title, message=''.join(msg))
