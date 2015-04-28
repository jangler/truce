Truce
=====

An experimental text editor and/or shell (alpha status). Currently, it's
essentially just a minimal text editor with the ability to pipe selected
text through an arbitrary shell command.

Future plans include the ability to use the editor as a filter in
pipes, and the ability use it to interact with shell-like or REPL-like
programs.

Installation
------------

::

	[sudo] pip[3] install truce

Usage
-----

::

	usage: truce [-h] [--version] [file]
	
	positional arguments:
	  file        file to edit
	
	optional arguments:
	  -h, --help  show this help message and exit
	  --version   show program's version number and exit
