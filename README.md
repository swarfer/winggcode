# Wing G-code Generator

This program generates XYUV G-code for hotwire cutting model airplane wings.
This program requires Python 2.7 to run and will integrate with LinuxCNC's AXIS interface.

It has a database of airfoils in Selig DAT format.  
You can add your own airfoils.

## Install

1. Download the master.zip file
1. Unzip it anywhere you want it for Windows, or into your NC files folder in LinuxCNC
1. 
   1. Windows: double click wing.pyw to run the program
   1. LinuxCNC: rename the file wing.pyw to wing.py and open it in LinuxCNC just like any Gcode file
1. On first run you will need to define the NC and DAT directories from the Edit menu.
   1. The DAT Directory must point at the unzippe 'coord' dirctory where all the .dat files are.
   1. The NC Directory can be anywhere convenient to you.  All Gcode will be saved there.
1. Close and re-open the program and you should see the airfoil lists populated  

## Usage

This is a very simple generator.  Just fill in the various edit fields and click 'Generate Gcode'.
After that you can 'Write Files' (Windows) or use one of the 'Write to Axis' buttons in LinuxCNC.

### The Gcode
You get a xxx-left.nc and an xxx-right.nc where xxx is the name of the model.
You MIGHT get a xxx-both.nc.   This file cuts both wings one above the other and is only generated if the foam is
thick enough.  Despite some internal checks, you should carefully check that the wings do no toouch each other.
In particular when high values of Washout are used the wingtips can collide inside the foam.
The Gcode is very simple and will run on basic controllers like GRBL up to Mach3 and LinuxCNC.

### Cutting 
Before you cut you need to set the wire heat to suite the feedrte you have set.
You can check this by giving a command like
G1 Y20 V20 F50
(use your feedrate!) and hold a peice of foam in the wire path whiel the wire moves up.
Adjust wire heat until you are happy.  The wire must not touch the foam! 

The 0,0 point on the foam block is at the bottom front corner, the corner on the table.   
Set 0,0 with the wire cold.
Now move the wire up and away from the table so it can safely get hot without melting the foam.
Start the cut.
