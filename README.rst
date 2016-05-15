=======
DFStran
=======
A tool to pack and unpack BBC micro disc images, such as those used by
emulators.  It supports Disc Filing System (DFS) images, such as those
commonly distribued as .ssd files.

At present it's only been tested using on Linux, but it should run on
Windows or RISC OS also, using python 2 or python 3.

TODO: Packing
TODO: dsd files?

Installation
============

This is a python tool so you'll need python installed.  Pick the latest
version of Python 2 or 3 - they should both be able to run this. Most
linux variants and modern BSDs come with python preinstalled.

Almost all of the functionality is contained in 'dfstran.py' - you can
simply save a raw copy and run it with 'python dfstran.py'.  On Unix
systems you can also copy 'dfstran' which is a shell script that runs
dfstran.py for you, and is used in the example commands below. On Windows
you may want to write a batch file to do similar, but I'll leave that up
to you to write.

Or just clone this repository, then you get all the test code too, and the
ability to keep up to date using 'git pull'.

Running tests
=============

You might want to test this software before you run it, for example if
you're running it on an untested platform.  You'll need the full repository
to give you the test_data folder. To run the built-in tests, run::

    python -m unittest dfstran

Provided the output ends with 'OK' the tests have passed.

How to use it
=============

To unpack a BBC Micro ssd disc image, call dfstran with the ssd file
and a non-existant directory to unpack to, for example::

    ./dfstran input.ssd out_dir

To print details of an ssd file (to catalogue it)::

    ./dfstran -c input.ssd

Without any '-v' flags, the output when cataloguing is equivalent to that
output by a BBC Micro's \*CAT command.

With one flag ('-v') dfstran adds details about the claimed disc size.

With two flags ('-vv') it adds details of unused sectors.

With three flags ('-vvv') checking adds what's in those unused places
(warning: this will proably produce lots of output).

When unpacking, by default the tool operates silently.  Adding one
verbose flag adds a note about what it's done.  Adding two adds the
equivalent of cataloguing with no verbose flags, and up to five verbose
flags ('-vvvvv') has incremental effects on verbosity.
