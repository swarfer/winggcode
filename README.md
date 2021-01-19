# Wing G-code Generator

This program generates XYUV G-code for hotwire cutting model airplane wings.
This program requires Python 3.9 or later to run and will integrate with LinuxCNC's AXIS interface.

It can also be used alone on any environment (Mac|Win|Linux with Python 3.

It has a database of airfoils in Selig DAT format.  
You can add your own airfoils.

## Install

1. Download the master.zip file
1. Unzip it anywhere you want it for Windows, or into your NC files folder in LinuxCNC
1. 
   1. Windows: double click wing.pyw to run the program (after you install Python3 of course)
   1. LinuxCNC: rename the file wing.pyw to wing.py and open it in LinuxCNC just like any Gcode file
1. On first run you will need to define the NC and DAT directories from the Edit menu.
   1. The DAT Directory must point at the unzipped 'coord' directory where all the .dat files are.
   1. The NC Directory can be anywhere convenient to you.  All Gcode will be saved there.
1. Close and re-open the program and you should see the airfoil lists populate.

## Usage

This is a very simple generator.  Just fill in the various edit fields and click 'Generate Gcode'.
After that you can 'Write Files' (Windows) or use one of the 'Write to Axis' buttons in LinuxCNC.

### The Gcode
You get a xxx-left.nc and an xxx-right.nc where xxx is the name of the model.
You MIGHT get a xxx-both.nc.   This file cuts both wings one above the other and is only generated if the foam is
thick enough.  Despite some internal checks, you should carefully check that the wings do no touch each other.
In particular when high values of Washout are used the wingtips can collide inside the foam.
The Gcode is very simple and will run on basic controllers like [GRBL](https://rckeith.co.uk/grbl-hotwire-mega-5x-for-cnc-foam-cutters/) up to Mach3 and [LinuxCNC](https://rckeith.co.uk/download/linuxcnc-foam-cutter-hal-file/).

### Cutting 
Before you cut you need to set the wire heat to suite the feedrate you have set.
You can check this by giving a command like
G1 Y20 V20 F50
(use your feedrate!) and hold a piece of foam in the wire path while the wire moves up.
Adjust wire heat until you are happy.  The wire must not touch the foam!  Not ever!

The 0,0 point on the foam block is at the bottom front corner, the corner 'on the table'.   
Set 0,0 with the wire cold.
Now jog the wire up and away from the table so it can safely get hot without melting the foam.
Start the cut.  There is never any cut actually *at* 0,0 so this is a safe zero setting.

### XYUV/XZ/YZ/XYUZ
These options let you choose various forms of output.
0. XYUV - the normal selection for a LinuxCNC dual gantry setup
0. XZ - run a bow on XZ on a router style machine
0. YZ - run a bow on YZ on a router style machine
0. XYUZ - run a GRBL controlled dual gantry machine using [4 axis GRBL](https://www.rckeith.co.uk/how-to-build-a-usb-cnc-hot-wire-foam-cutter/).

