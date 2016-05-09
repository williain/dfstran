=======
DFStran
=======
A tool to pack and unpack BBC micro disc images, such as those used by
emulators.  It supports Disc Filing System (DFS) images, such as those
commonly distribued as .ssd files.

At present it's only been tested using python3 on Linux, but it should run
on python2, on Linux, Windows or RISC OS at least.

TODO: Packing
TODO: dsd files?

How to use it
=============

Currently it's just a test script that takes a file called Test.ssd, prints
out some stats about it and dumps it to a folder called unpackd, but the plan
is to give it a command line interface, and make it be able to pack as well
as unpack files.
