#!/usr/bin/env python

# python wing.pyw
# Version self.Id: wing.pyw 1.1 2017/10/23 07:46:09 david Exp self.
# Dec 4 2007
# XYUV wing G-Code Generator for EMC2
# also YZ/XZ for GRBL for straight wings only
"""
    Copyright (C) <2008>  <John Thornton>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http:#www.gnu.org/licenses/>.

    e-mail me any suggestions to "jet1024 at semo dot net"
    If you make money using this software
    you must donate self.20 USD to a local food bank
    or the food police will get you! Think of others from time to time...
    To make it a menu item in Ubuntu use the Alacarte Menu Editor and add
    the command python YourPathToThisFile/face.py
    make sure you have made the file execuatble by right
    clicking and selecting properties then Permissions and Execute
    To use with EMC2 see the instructions at:
    http:#wiki.linuxcnc.org/cgi-bin/emcinfo.pl?Simple_EMC_G-Code_Generators

2008-02-24  Rick Calder "rick at llamatrails dot com"
   Added option/code to select X0-Y0 position: Left-Rear or Left-Front
   To change the default, change line 171: 4=Left-Rear, 5=Left-Front

2010-01-06  Brad Hanken "chembal at gmail dot com"
   Added option and code to change the lead in and lead out amount
   If nothing is entered, the old calculated value of tool radius + .1 is still used

2014-11-00 swarfer:  made metric the default
      add option to cut unidirectional

2017-11-16 swarfer: modified into a wing cutter, based on gwing.php by the swarfer
    python 2.x only...

2018-02-06 swarfer: cut wings in YZ or XZ only, straight wings on a gantry XYZ machine    
2020-05-10 swarfer: add XYUZ output for 4axis GRBL from rckeith
"""

from Tkinter import *
from tkFileDialog import *
from math import *
from SimpleDialog import *
import ConfigParser
from decimal import *
import tkMessageBox
import os
import glob
import string
import re

IN_AXIS = os.environ.has_key("AXIS_PROGRESS_BAR")

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master, width=700, height=400, bd=1)
        self.grid()
        self.createMenu()
        if IN_AXIS:
           self.ext = '.ngc'
        else:
           self.ext = '.nc'
        
        self.inifile = os.path.join('.','wing.ini')
        try:
            self.DatDir = self.GetIniData(self.inifile,'Directories','DatFiles')
        except:
            # does not exist so write a default value
            self.DatDir = os.path.join('.','coord')
            self.WriteIniData(self.inifile,'Directories','DatFiles',self.DatDir)

        try:
           """ save in ini in the NC folder """
           self.NcFileDirectory = self.GetIniData(self.inifile,'Directories','NcFiles')
        except:
           tkMessageBox.showinfo('Missing INI Data', 'You must set the\n' \
                'NC File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/NC Directory\n' \
                'in the menu to set this option')
           return
            
        self.createWidgets()

        #center the window
        self.update_idletasks()
        width = self.winfo_width()
        frm_width = self.winfo_rootx() - self.winfo_x()
        win_width = width + 2 * frm_width
        height = self.winfo_height()
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = self.winfo_screenwidth() # 2 - win_width # 2
        y = self.winfo_screenheight() # 2 - win_height # 2
        #self.At(1060,200)
        #self.deiconify()
        try:    #try to read the last model saved
            modelname = self.GetIniData(self.inifile,'autoload','model')
            filename = os.path.join(self.NcFileDirectory, modelname + '.ini')
            if os.path.exists(filename):
                self.ReadModel(filename)
        except:
            pass

    def createMenu(self):
        #Create the Menu base
        self.menu = Menu(self)
        #Add the Menu
        self.master.config(menu=self.menu)
        #Create our File menu
        self.FileMenu = Menu(self.menu)
        #Add our Menu to the Base Menu
        self.menu.add_cascade(label='File', menu=self.FileMenu)
        #Add items to the menu
        self.FileMenu.add_command(label='New', command=self.Simple)
        self.FileMenu.add_command(label='Open', command=self.Simple)
        self.FileMenu.add_separator()
        self.FileMenu.add_command(label='Quit', command=self.quit)

        self.EditMenu = Menu(self.menu)
        self.menu.add_cascade(label='Edit', menu=self.EditMenu)
        self.EditMenu.add_command(label='Copy', command=self.CopyClpBd)
        self.EditMenu.add_command(label='Select All', command=self.SelectAllText)
        self.EditMenu.add_command(label='Delete All', command=self.ClearTextBox)
        self.EditMenu.add_separator()
        self.EditMenu.add_command(label='Preferences', command=self.Simple)
        self.EditMenu.add_command(label='NC Directory', command=self.NcFileDirectory)
        self.EditMenu.add_command(label='DAT Directory', command=self.DatFileDirectory)

        self.HelpMenu = Menu(self.menu)
        self.menu.add_cascade(label='Help', menu=self.HelpMenu)
        self.HelpMenu.add_command(label='Help Info', command=self.HelpInfo)
        self.HelpMenu.add_command(label='About', command=self.HelpAbout)

    def createWidgets(self):
        self.sp1 = Label(self)
        self.sp1.grid(row=0)

        self.st1 = Label(self, text='Model Name ')
        self.st1.grid(row=1, column=0, sticky=E)
        self.ModelNameVar = StringVar()
        self.ModelNameVar.set('default')
        self.ModelName = Entry(self, width=20, textvariable=self.ModelNameVar)
        self.ModelName.grid(row=1, column=1, sticky=W)
        self.ModelName.focus_set()

        self.SaveModelButton = Button(self, text='Save Model',command=self.SaveModel)
        self.SaveModelButton.grid(row=1, column=2)

        self.LoadModelButton = Button(self, text='Load Model',command=self.LoadModel)
        self.LoadModelButton.grid(row=1, column=3)


        self.st2 = Label(self, text='WingSpan ')
        self.st2.grid(row=2, column=0, sticky=E)
        self.WingSpanVar = StringVar()
        self.WingSpanVar.set('500')
        self.WingSpan = Entry(self, width=10, textvariable=self.WingSpanVar)
        self.WingSpan.grid(row=2, column=1, sticky=W)

        self.st22 = Label(self, text='Washout ')
        self.st22.grid(row=2, column=2, sticky=E)
        self.WashoutVar = StringVar()
        self.WashoutVar.set('0')
        self.Washout = Entry(self, width=10, textvariable=self.WashoutVar)
        self.Washout.grid(row=2, column=3, sticky=W)


        self.st3 = Label(self, text='Root Chord ')
        self.st3.grid(row=3, column=0, sticky=E)
        self.RootChordVar = StringVar()
        self.RootChordVar.set('200')
        self.RootChord = Entry(self, width=10, textvariable=self.RootChordVar)
        self.RootChord.grid(row=3, column=1, sticky=W)

        self.st4 = Label(self, text='Tip Chord ')
        self.st4.grid(row=3, column=2, sticky=E)
        self.TipChordVar = StringVar()
        self.TipChordVar.set('190')
        self.TipChord = Entry(self, width=10, textvariable=self.TipChordVar)
        self.TipChord.grid(row=3, column=3, sticky=W)


        self.profiles = glob.glob(os.path.join(self.DatDir, '*.dat'))
        self.profiles.sort()

        self.st5 = Label(self, text='Root Profile ')
        self.st5.grid(row=4, column=0, sticky=E)
        self.rootScrollbar = Scrollbar(self, orient=VERTICAL)
        self.RootProfilelistbox = Listbox(self, exportselection=0, height=5, width=18, yscrollcommand=self.rootScrollbar.set)
        self.rootScrollbar.config(command=self.RootProfilelistbox.yview)
        self.rootScrollbar.grid(row=4,column=1, sticky=N+S+E)
        self.RootProfilelistbox.grid(row=4, column=1, sticky=W)

        for item in self.profiles:
           nitem = string.replace(item,self.DatDir + os.sep,'')
           self.RootProfilelistbox.insert(END, nitem)
        if (len(self.profiles) > 0):
           self.RootProfilelistbox.selection_set(0)

#        self.st6 = Label(self, text='Tip Profile ')
#        self.st6.grid(row=4, column=2, sticky=E)
#        self.TipProfileVar = StringVar()
#        self.TipProfile = Entry(self, width=10, textvariable=self.TipProfileVar)
#        self.TipProfile.grid(row=4, column=3, sticky=W)

        self.st6 = Label(self, text='Tip Profile ')
        self.st6.grid(row=4, column=2, sticky=E)
        self.tipScrollbar = Scrollbar(self, orient=VERTICAL)
        self.TipProfilelistbox = Listbox(self, exportselection=0, height=5,  yscrollcommand=self.tipScrollbar.set)
        self.tipScrollbar.config(command=self.TipProfilelistbox.yview)
        self.tipScrollbar.grid(row=4,column=4, sticky=N+S+W)
        self.TipProfilelistbox.grid(row=4, column=3, sticky=W)

        for item in self.profiles:
           nitem = string.replace(item,self.DatDir + os.sep,'')
           self.TipProfilelistbox.insert(END, nitem)
        if (len(self.profiles) > 0):
           self.TipProfilelistbox.selection_set(0)

        self.st7 = Label(self, text='Foam Chord ')
        self.st7.grid(row=5, column=0, sticky=E)
        self.FoamChordVar = StringVar()
        self.FoamChordVar.set(220)
        self.FoamChord = Entry(self, width=10, textvariable=self.FoamChordVar)
        self.FoamChord.grid(row=5, column=1, sticky=W)

        self.st8 = Label(self, text='Foam Thickness ')
        self.st8.grid(row=5, column=2, sticky=E)
        self.FoamThicknessVar = StringVar()
        self.FoamThicknessVar.set(50)
        self.FoamThickness = Entry(self, width=10, textvariable=self.FoamThicknessVar)
        self.FoamThickness.grid(row=5, column=3, sticky=W)


        self.st9 = Label(self, text='Trailing Edge Limit ')
        self.st9.grid(row=6, column=0, sticky=E)
        self.TrailingEdgeLimitVar = StringVar()
        self.TrailingEdgeLimitVar.set(3)
        self.TrailingEdgeLimit = Entry(self, width=10, textvariable=self.TrailingEdgeLimitVar)
        self.TrailingEdgeLimit.grid(row=6, column=1, sticky=W)

        self.st10 = Label(self, text='Leading Edge Sweep ')
        self.st10.grid(row=6, column=2, sticky=E)
        self.LeadingEdgeSweepVar = StringVar()
        self.LeadingEdgeSweepVar.set(5)
        self.LeadingEdgeSweep = Entry(self, width=10, textvariable=self.LeadingEdgeSweepVar)
        self.LeadingEdgeSweep.grid(row=6, column=3, sticky=W)


        self.st11 = Label(self, text='Gantry Length ')
        self.st11.grid(row=7, column=0, sticky=E)
        self.GantryLengthVar = StringVar()
        self.GantryLengthVar.set(600)
        self.GantryLength = Entry(self, width=10, textvariable=self.GantryLengthVar)
        self.GantryLength.grid(row=7, column=1, sticky=W)

        self.st12 = Label(self, text='Feedrate ')
        self.st12.grid(row=7, column=2, sticky=E)
        self.FeedrateVar = StringVar()
        self.FeedrateVar.set(50)
        self.Feedrate = Entry(self, width=10, textvariable=self.FeedrateVar)
        self.Feedrate.grid(row=7, column=3, sticky=W)

#these two need to be radio boxes

# Units Radiobutton Callback # 5
#    def radCallUnit():
#        radSel=radVar.get()
#        if radSel == 1: win.configure(background=COLOR1)
#        elif radSel == 2: win.configure(background=COLOR2)
#        elif radSel == 3: win.configure(background=COLOR3)

# create two Radiobuttons
        self.XYsideVar = IntVar()  # 0 for XY right, 1 for XY left
        self.st13 = Label(self, text='XY side ')
        self.st13.grid(row=8, column=0, sticky=E)
        urad1 = Radiobutton(self, text='Right', variable=self.XYsideVar, value=0)
        urad1.grid(row=8, column=1, sticky=E)
        urad2 = Radiobutton(self, text='Left', variable=self.XYsideVar, value=1)
        urad2.grid(row=8, column=1, sticky=W)
        self.XYsideVar.set(0)

        self.st14=Label(self,text='Units : ')
        self.st14.grid(row=8,column=2)
        UnitOptions=[('Inch',1,'E'),('MM',0,'W')]
        self.UnitVar = IntVar()
        for text, value, side in UnitOptions:
            Radiobutton(self, text=text,value=value, variable=self.UnitVar,indicatoron=0,width=6,).grid(row=8, column=3,sticky=side)
        self.UnitVar.set(0)
# XYUV/YZ/XZ
        self.XYUVVar = IntVar()  # 0 for XYUV , 1 for YZ, 2 for XZ, 3 for XYUZ (GRBL mode)
        self.st13 = Label(self, text='XYUV/YZ/XZ/XYUZ ')
        self.st13.grid(row=9, column=0, sticky=E)
        urad1 = Radiobutton(self, text='XYUV', variable=self.XYUVVar, value=0)
        urad1.grid(row=9, column=1, sticky=W)
        urad2 = Radiobutton(self, text='YZ only', variable=self.XYUVVar, value=1)
        urad2.grid(row=9, column=2, sticky=W)
        urad1 = Radiobutton(self, text='XZ only', variable=self.XYUVVar, value=2)
        urad1.grid(row=9, column=3, sticky=W)
        urad3 = Radiobutton(self, text='XYUZ(GRBL)', variable=self.XYUVVar, value=3)
        urad3.grid(row=9, column=4, sticky=W)
        self.XYUVVar.set(0)

        self.spacer3 = Label(self, text='')
        self.spacer3.grid(row=10, column=0, columnspan=5)
# gcode block
        self.g_code = Text(self,width=30,height=14,bd=3)
        self.g_code.grid(row=11, column=0, columnspan=4, sticky=E+W+N+S)
        self.tbscroll = Scrollbar(self,command = self.g_code.yview)
        self.tbscroll.grid(row=11, column=4, sticky=N+S+W)
        self.g_code.configure(yscrollcommand = self.tbscroll.set)

        self.sp4 = Label(self)
        self.sp4.grid(row=12)

        #make sure these exist so pressing save button before generate does not crash
        self.g_code_left = list()
        self.g_code_right = list()
        self.g_code_both = list()

        self.GenButton = Button(self, text='Generate G-Code',command=self.GenCode)
        self.GenButton.grid(row=12, column=0)

#        self.GenButton = Button(self, text='Generate G-Code bi',command=self.GenCode2)
#        self.GenButton.grid(row=12, column=1)

#        self.CopyButton = Button(self, text='Select All & Copy',command=self.SelectCopy)
#        self.CopyButton.grid(row=12, column=2)

        self.WriteButton = Button(self, text='Write to Files',command=self.WriteToFile)
        self.WriteButton.grid(row=12, column=1)

        if IN_AXIS:
            self.quitButton1 = Button(self, text='Write LEFT to AXIS and Quit',  command=self.WriteLeftToAxis)
            self.quitButton1.grid(row=12, column=2, sticky=E)
            self.quitButton2 = Button(self, text='Write RIGHT to AXIS and Quit', command=self.WriteRightToAxis)
            self.quitButton2.grid(row=12, column=3, sticky=E)
            self.quitButton3 = Button(self, text='Write BOTH to AXIS and Quit',       command=self.WriteBothToAxis)
            self.quitButton3.grid(row=12, column=4, sticky=E)
        else:
            self.quitButton = Button(self, text='Quit', command=self.MyQuit)
            self.quitButton.grid(row=12, column=4, sticky=E)

    def MyQuit(self):
        sys.stdout.write('%')
        self.quit()

    #python makes number formatting so hard....
    def Format(self,val,dec):
       s = '%0.' + str(int(dec)) + 'f'
       return s % val

    #get all the values from the widgets
    def GetWValues(self):
        self.modelname = self.ModelNameVar.get()
        self.wingspan = self.FToD(self.WingSpanVar.get())
        self.washout = self.FToD(self.WashoutVar.get())
        self.rootchord = self.FToD(self.RootChordVar.get())
        self.tipchord  = self.FToD(self.TipChordVar.get())

        items =  self.RootProfilelistbox.curselection()
        self.rootfile = self.RootProfilelistbox.get(items[0])
        #do not use ACTIVE for this        
        items =  self.TipProfilelistbox.curselection()
        self.tipfile  = self.TipProfilelistbox.get(items[0])
                                                   
        self.foamchord = self.FToD(self.FoamChordVar.get())
        self.foamthickness = self.FToD(self.FoamThicknessVar.get())
        self.trail = self.FToD(self.TrailingEdgeLimitVar.get())
        self.sweep = self.FToD(self.LeadingEdgeSweepVar.get())
        self.gantry = self.FToD(self.GantryLengthVar.get())
        self.feedrate = self.FToD(self.FeedrateVar.get())
        if self.feedrate == 0:
           self.feedrate = 1
           self.g_code.insert(END,'WARNING: feedrate cannot be ZERO\n')
        self.xy = self.XYsideVar.get()
        self.xyuv = self.XYUVVar.get()
        if self.xyuv == 3:
           self.xyuv = 0
           self.grblmode = True
        else:
           self.grblmode = False
        self.unit = self.UnitVar.get()
        if self.unit:
           self.units = '"'
        else:
           self.units = 'mm'


    def Header(self,alist):
        alist.append('%\n')
        line = 'G90 '
        if self.UnitVar.get()==1:
            line = line + 'G20 '
            dec = 3
            self.Safe = 0.1  # 0.1 inch
        else:
            line = line + 'G21 '
            self.Safe = 1  #1 mm
            dec = 1
        line = line + 'M3 S100 '
        if len(self.FeedrateVar.get())>0:
            line = line +  'F%s\n' % self.FeedrateVar.get()
        else:
            line = line + '\n'
        alist.append(line)

        #these tell LinuxCNC where to put the XY and UV on the screen
        line = "(AXIS,XY_Z_POS,0)\n"
        alist.append(line)
        line = "(AXIS,UV_Z_POS,%.3f)\n" % (self.gantry)
        alist.append(line)
        
        alist.append('(modelname ' + self.modelname + ')\n')

        alist.append('(wingspan ' + self.Format(self.wingspan,dec)  + ')\n')
        alist.append('(rootchord ' + self.Format(self.rootchord,dec) + ')\n')
        alist.append('(tipchord ' + self.Format(self.tipchord,dec)  + ')\n')
        alist.append('(rootfile ' + self.rootfile  + ')\n')
        alist.append('(tipfile ' + self.tipfile   + ')\n')
        alist.append('(foamchord ' + self.Format(self.foamchord,dec)  + ')\n')
        alist.append('(foamthickness ' + self.Format(self.foamthickness,dec)  + ')\n')
        alist.append('(trail ' + self.Format(self.trail,dec)  + ')\n')
        alist.append('(sweep ' + self.Format(self.sweep,dec)  + ')\n')
        alist.append('(washout ' + self.Format(self.washout,dec)  + ')\n')
        alist.append('(gantry ' + self.Format(self.gantry,dec)  + ')\n')
        alist.append('(feedrate ' + self.Format(self.feedrate,dec)  + ')\n')
        if (self.xy == 0):
            alist.append('(xy right)\n')
        else:
            alist.append('(xy left)\n')
        if (self.unit == 0):
           alist.append('(unit MM)\n')
        else:
           alist.append('(unit inch)\n')
        alist.append('(NOTE 0,0 is wire on table at front foam corner)\n')


    def GenCode(self):
         """ will generate all three gcode files as string lists """
         self.g_code_left = []
         self.g_code_right = []
         self.g_code_both = []
         self.g_code.delete("1.0",END)
         self.GetWValues()
         if (self.wingspan >= self.gantry):
            self.g_code.insert(END,"PANIC: wingspan greater than gantry separation\n")
            return None
         #print "sweep %f" % self.sweep
         self.gap = (self.gantry - self.wingspan) / 2 # gap between end of wing and gantry on each side
         self.teoff = self.rootchord - self.sweep - self.tipchord # opposite of sweep
         if (self.teoff < 0):
            self.g_code.insert(END, "   Swept Wing\n")
         #print "teoff %f" %self.teoff
         
         self.t1 = atan(self.sweep / self.wingspan)
         self.t2 = atan(self.teoff / self.wingspan)
         self.E1 = tan(self.t1) * self.gap
         self.E2 = tan(self.t2) * self.gap
         self.E3 = tan(self.t1) * (self.wingspan + self.gap)
         self.E4 = tan(self.t2) * (self.wingspan + self.gap)
         self.debug = 0
         if self.debug:
            print("E1 %0.4f" % self.E1)
            print("E2 %0.4f" % self.E2)
            print("E3 %0.4f" % self.E3)
            print("E4 %0.4f" % self.E4)

         self.rootlength = self.rootchord + self.E1 + self.E2 # gantry movement for root
         if (self.teoff < 0):
            self.waste = self.E1 #       # wastage at trailing edge of tip profile
         else:
            self.waste = self.E2 #       # wastage at trailing edge of root profile
         self.tiplength  = self.rootchord - self.E3 - self.E4 # gantry movement for tip

         if (self.debug):
            print("rootlength %0.4f" % self.rootlength)
            print("tiplength  %0.4f" % self.tiplength)

         if (self.tiplength < 0):
            self.g_code.insert(END, "\n   PANIC: tip length is negative, I cannot plot this,\n you need to put the gantry closer together\n")
            return None

         self.toffset = self.E2 + self.E4   # tip offset for tip gantry
         if (self.debug):
            print "toffset %0.4f" % self.toffset

         self.g_code.insert(END, "rootfile " + self.rootfile + '\n')
         self.g_code.insert(END, "tipfile  " + self.tipfile  + '\n')

         #root file
         if not(os.path.exists(self.rootfile)):
            self.rootfile =  os.path.join(self.DatDir, self.rootfile)
         #tip
         if not(os.path.exists(self.tipfile)):
            self.tipfile  =  os.path.join(self.DatDir,self.tipfile)
         if (not(os.path.exists(self.rootfile)) or not(os.path.exists(self.tipfile))):
            self.g_Code.insert(END, "   PANIC:  either root or tip file not found\n")
            return None


         # trailing edge thickness limit, does not work if number of points is low
         if (self.trail > 0):
            self.g_code.insert(END,"   Trailing edge " + str(self.trail) + '\n' )

         # foam management
         self.skintop = 0
         self.skinbot = 0

         # assume start at trailing edge on root and tip+self.toffset profile, wire on platten at 0,0
         # then feed top surface
         # then bottom
         # then feed out

         with open(self.rootfile) as f:
             self.rootprofile = f.read().splitlines()
         with open(self.tipfile) as f:
             self.tipprofile = f.read().splitlines()

         self.rootprofile = self.stripfile(self.rootprofile)
         self.tipprofile = self.stripfile(self.tipprofile)  # get rid of comment lines

         if (len(self.rootprofile) != len(self.tipprofile)):
            #self.g_code.insert(END,"   ERROR profile point counts not equal (%d,%d)\n" % (len(self.rootprofile) , len(self.tipprofile)))
            #return None
            if (len(self.rootprofile) >  len(self.tipprofile)):
                self.g_code.insert(END, "root bigger, resampling tip")
                self.tipprofile = self.resample(self.rootprofile, self.tipprofile)
            else:
                self.g_code.insert(END,"tip bigger, resmapling root")
                self.rootprofile = self.resample(self.tipprofile, self.rootprofile)

         self.FindThicknessesRoot()
         if self.debug: print("Actualrootthick " + str(self.actualrootthick))
         self.CreateTip()
         if self.washout != 0.0:
            self.tip = self.rotatePolygon(self.tip, -self.washout) # rotate nose down, keep trailing edge straight
         self.FindThicknessesTip()

         self.TrailingEdgeLimits2()
         self.FindStartPoints()

         # info
         self.g_code.insert(END, "   startpoint sp= %0.3f%s above platten\n" % (self.sp, self.units) )
         if self.need == 0:
            self.g_code.insert(END, "      startpoint spL= %0.3f%s above platten\n" % (self.spl, self.units))
            self.g_code.insert(END, "      startpoint spR= %0.3f%s above platten\n" % (self.spr, self.units))
         self.l = self.rootchord + self.waste
         if (self.debug):
            print("L %.2f  waste %.2f" % (self.l,self.waste))
         if (self.l > self.foamchord):
            self.g_code.insert(END, "WARNING: root length + waste(%.2f) is greater than the foam chord(%.2f) you specified\n" % (self.l, self.foamchord))
         
         # Generate the G-Codes
         self.Header(self.g_code_left)
         self.Header(self.g_code_right)
         self.Header(self.g_code_both)

         if self.xy:
            self.g_code.insert(END, 'XY gantry left\n')
         else:
            self.g_code.insert(END, 'XY gantry right\n')
         # os.path.join(self.NcFileDirectory, self.modelname, '-right' + self.ext)           
         # os.path.join(self.NcFileDirectory, self.modelname, '-left' + self.nc)
         # os.path.join(self.NcFileDirectory, self.modelname,'-both' + self.nc)
         
         if (self.xy):  #XY on left
            self.plot(self.root, self.tip, 'right',   self.g_code_right,  self.sp, 1, 0)
            self.plot(self.tip,  self.root,'left' ,   self.g_code_left,   self.sp, 1, 0)
            if (self.need == 0):
               self.g_code.insert(END, "Doing BOTH file\n")
               self.plot(self.root, self.tip, 'right',  self.g_code_both, self.spl,  1, 1)
               self.plot(self.root, self.tip, 'right' , self.g_code_both, self.spr, -1, 1)
            else:
               self.g_code.insert(END, "Did not output BOTH file since foam is not thick enough\n")
         else:   #XY on right
            self.plot(self.root, self.tip, 'left',   self.g_code_left,    self.sp, 1, 0)
            self.plot(self.tip,  self.root,'right' , self.g_code_right,   self.sp, 1, 0)
            
            # output combined foils for GRBL XYUV
            if (self.need == 0):
               self.g_code.insert(END, "Doing BOTH file\n")
               self.plot(self.root, self.tip, 'left',  self.g_code_both, self.spl,  1, 1)
               self.plot(self.root, self.tip, 'left' , self.g_code_both, self.spr, -1, 1)
            else:
               self.g_code.insert(END, "Did not output BOTH file since foam is not thick enough\n")
           

         #for line in self.g_code_left:
         #   self.g_code.insert(END, line)
    """
    p1 first airfoil data
    p2 seconds airfoil data
    direc 'left' or 'right' for direction
    fname the filename
    sp start point , distance above X Zero
    invert 1 for normal, -1 for invert
    flag 0 for normal, 1 for BOTH mode
    """
    def plot(self, p1, p2, direc, flist, sp, invert, flag):
      #global $inch, $units, $trail, $E2, $wingspan, $params, $rootymax, $rootymin, $tipymax, $tipymin, self.toffset, $feedspeed, $rootlength, $tiplength, $waste, $foamthick, $foamchord, $skintop, $skinbot, $xy;
#      if (flag):
#         if (invert == 1):
#            flist.append("%%\n")  
#      else:
#         flist.append( "%%\n");
      flist.append( "(Generated by wing.py. David the Swarfer, 2017)\n")
      flist.append( "(from ini file root " + os.path.basename(self.rootfile) + " tip " + os.path.basename(self.tipfile) + " offset %.2f )\n" % (self.toffset))
      if (self.toffset > 0):
         flist.append( "(minimum material chord is %0.1f with wastage of %.3f at trailing edge)\n" % (self.rootlength, self.waste)) 
      else:
         mmc = self.rootchord + self.waste
         w =  -self.E2
         flist.append( "(Swept Wing)\n")
         flist.append( "(minimum material chord is %0.3f%s with wastage of %0.3f%s at trailing edge)\n" % (mmc, self.units,w,self.units))
         if (self.xyuv != 0):
             flist.append("(generating cartesian gantry, taper ignored)\n")
      
      flist.append( "(root gantry thickness = %0.1f%s)\n" % (self.rootymax - self.rootymin, self.units))
      flist.append( "(tip gantry thickness = %0.1f%s)\n" % (self.tipymax - self.tipymin, self.units))
      if (self.rootlength != self.tiplength):
         flist.append( "(above sizes are for gantry travel, actual wing will be thinner)\n")
      if (self.foamchord and  self.foamthickness):
         ws = self.wingspan
         flist.append( "(foam block %.3f'wingspan' x %.3f x %.3f%s)\n" % (ws,self.foamchord,self.foamthickness,self.units));
      if (self.xyuv == 0):
         if (self.xy):
            flist.append( "(XY gantry left)\n")
         else:
            flist.append( "(XY gantry right)\n")
      else:
         if (self.xyuv == 1):
            self.g_code.insert(END, "YZ")
            flist.append( "(YZ gantry)\n")
         else:
            self.g_code.insert(END, "XZ" )
            flist.append( "(XZ gantry)\n")      
      #z = 0 - self.rootymin
      flist.append( "(trailing edge will be AT LEAST %0.1f%s above bottom of panel)\n" % (self.sp, self.units))
      #if (self.trail > 0):
      #   flist.append( "(Trailing edge limit %0.2f%s)\n" % (self.trail, self.units))
      if (self.unit):   
         flist.append( "G20\n");  # inch mode
         prec = '%0.4f'  # thous/10 for inch mode
         retract = -0.25
      else:   
         flist.append( "G21\n")  # metric mode
         prec = '%0.3f'  # 1/1000 mm for metricmode
         retract = -5.0

      if (self.xyuv == 0):
         flist.append( "G90\n")
         if self.grblmode == False:
            flist.append("G49 G64 P0.01\n") 
      else:
         flist.append( "G90 G49\n")

       
      if self.debug: print("prec " + str(prec))
      # you will need to add in any other header codes you need, here
         
      if self.debug:
          print(retract)
          print(sp)
          print(self.feedrate)
      if (self.xyuv == 0):
         if self.grblmode:
            fmt = "G00 X"+prec+" Y"+prec+" U"+prec+" Z"+prec+" F%0.1f\n"
         else:
            fmt = "G00 X"+prec+" Y"+prec+" U"+prec+" V"+prec+" F%0.1f\n"
      else:
          if (self.xyuv == 1): # YZ
              fmt = "G00 Y"+prec+" Z"+prec+" F%0.1f\n"
          else:  #XZ
              fmt = "G00 X"+prec+" Z"+prec+" F%0.1f\n"
      #start heights, sp + offset of first point on top surface
      if flag and (invert == -1):
          #doing an upside down profile, do lower side first, ie run loop backwards
          start = len(p1) - 1
      else:
          start = 0
      if (self.xy):	# XY gantry on left
            if (direc == 'right'):  # means second profile is smaller, 
               shXY = sp + p1[start][1]
               shUV = sp + p2[start][1]
            else:
               shXY = sp + p2[start][1]
               shUV = sp + p1[start][1]
      else:	# XY gantry on right
            if (direc == 'left'):  # means second profile is smaller, 
               shXY = sp + p1[start][1]
               shUV = sp + p2[start][1]
            else:
               shXY = sp + p2[start][1]
               shUV = sp + p1[start][1]
      flist.append("(seek to start height)\n")
      if (self.xyuv == 0):
          flist.append( fmt  % (retract,shXY,retract,shUV,self.feedrate)) # EMC bleats if no feed speed on first G0 instructions
      else:
          flist.append( fmt  % (retract,shXY,self.feedrate))
      spt = [0,shXY,0,shUV]
      # do skins and then cut, assume wire 0,0 on surface of platten
      self.g_code.insert(END, "   doing '%s' with Foamthick %.3f%s\n" % (direc,self.foamthickness, self.units))
      """      
      if (($skintop > 0) || ($skinbot > 0) && (  ($foamthick >0) && ($foamchord > 0) ))
         {
         fprintf($of, "(skinning $skintop $skinbot on block $wingspan x $foamchord x $foamthick)\n");
         $top = $foamthick - $skintop;
         fprintf($of,"G00 Y%0.2f V%0.2f\n",$top,$top);
         $fc = $foamchord + 5;
         fprintf($of,"G01 X%0.1f U%0.1f\n",$fc,$fc);
         fprintf($of,"G00 Y%0.2f V%0.2f\n",$skinbot,$skinbot);
         fprintf($of,"G01 X-5 U-5\n");
         fprintf($of,"G00 Y%0.2f V%0.2f\n",$sp,$sp);
         }  
      else
         fprintf($of, "(no skins)\n");
      """		
      # seek to start point
      # must create the format string before using it
      if (self.xyuv == 0):
         if self.grblmode:
            fmt = "G01 X"+prec+" Y"+prec+" U"+prec+" Z"+prec+"\n"
         else:
            fmt = "G01 X"+prec+" Y"+prec+" U"+prec+" V"+prec+"\n"
      else:
          if (self.xyuv == 1):
              fmt = "G01 Y"+prec+" Z"+prec+"\n"
          else:
              fmt = "G01 X"+prec+" Z"+prec+"\n"
      if (self.xyuv != 0) and (self.toffset != 0):
          flist.append("(Need a Straight wing please)\n")
          self.g_code.insert(END, "  Straight wings only! aborting")
          return
      #else:
          #flist.append("(do we need a seek to trailing edge here?)\n")
          
      if (self.toffset > 0):
         flist.append("(seek to trailing edge)\n")
         if (self.xy):	# XY gantry on left
            if (direc == 'right'):  # means second profile is smaller,
              spt = [0,shXY, self.toffset, shUV]  
              flist.append( fmt % (0,shXY, self.toffset, shUV))
            else:
              spt = [self.toffset,shXY,0,shUV]
              flist.append( fmt % (self.toffset,shXY,0,shUV))		# first profile smaller
         else:	# XY gantry on right
            if (direc == 'left'):  # means second profile is smaller,
              spt = [0,shXY,self.toffset,shUV]
              flist.append( fmt % (0,shXY,self.toffset,shUV))
            else:
              spt = [ self.toffset,shXY,0,shUV] 
              flist.append( fmt % (self.toffset,shXY,0,shUV))		# first profile smaller
      if (self.toffset < 0):
         flist.append("(seek to trailing edge, swept)\n" )
         if (self.xy):	# XY gantry on left
            if (direc == 'right'):  # means second profile is smaller,
               spt = [-self.toffset, shXY,0,shUV]
               flist.append( fmt % (-self.toffset, shXY,0,shUV))
            else:
               spt = [ 0,shXY,-self.toffset,shUV]
               flist.append( fmt % (0,shXY,-self.toffset,shUV))		# first profile smaller
         else:	# XY gantry on right
            if (direc == 'left'):  # means second profile is smaller,
               spt = [-self.toffset,shXY,0,shUV] 
               flist.append( fmt % (-self.toffset,shXY,0,shUV))
            else:
               spt =[0,shXY,-self.toffset,shUV]
               flist.append( fmt % (0,shXY,-self.toffset,shUV))		# first profile smaller

      #$xoffset = ($toffset < 0) ? -$toffset : 0;
      #$uoffset = ($toffset < 0) ? 0 : $toffset ;

      if (self.toffset < 0):
          xoffset = -self.toffset
          uoffset = 0
      else:
          xoffset = 0
          uoffset = self.toffset 
       
      if flag and (invert == -1):
          #doing an upside down profile, do lower side first, ie run loop backwards
          start = len(p1) - 1
          end = -1
          step = -1
      else:
          #do top surface first as normal
          start = 0
          end = len(p1)
          step = 1
      #print "%d %d %d" %(start,end,step)
      #print len(p1), len(p2)
      flist.append("(do profile)\n" ) 
      for idx in range(start, end, step):
         #print "idx %d" % idx
         if (self.xyuv == 0):
             if (self.xy): # XY gantry on left
                if (direc == 'right'):
                   flist.append(fmt % (p1[idx][0] + xoffset, sp + p1[idx][1] * invert, p2[idx][0] + uoffset, sp + p2[idx][1] * invert))
                else:
                   flist.append(fmt % (p1[idx][0] + uoffset, sp + p1[idx][1] * invert, p2[idx][0] + xoffset, sp + p2[idx][1] * invert))   
             else:	# XY gantry on right
                if (direc == 'left'):
                   flist.append(fmt % (p1[idx][0] + xoffset, sp + p1[idx][1] * invert, p2[idx][0] + uoffset, sp + p2[idx][1] * invert))
                else:
                   flist.append(fmt % (p1[idx][0] + uoffset, sp + p1[idx][1] * invert, p2[idx][0] + xoffset, sp + p2[idx][1] * invert))
         else:
            #self.g_code.insert(END, fmt)  
            flist.append(fmt % (p1[idx][0] + xoffset, sp + p1[idx][1] * invert  ))             
         #end idx loop

      #close the trailing edge by going back to start point
      flist.append("(close trailing edge)\n" )        
      if (self.xyuv == 0):
         flist.append( fmt  % (spt[0], spt[1], spt[2], spt[3]) )
      else:
         flist.append( fmt  % (spt[0], spt[1]) )
      if (self.xyuv != 0):
         flist.append("G4 P0.075\n")
      if self.unit:
         retract = -0.25
      else:
         retract = -5
      #retract
      flist.append("(retract out of foam)\n" )
      if (self.xyuv == 0):
          flist.append( fmt % (retract,shXY,retract,shUV))
      else:
          flist.append( fmt % (retract*2,shXY))
      flist.append("G4 P0.075\n")
      if ( not(flag) or  ( (invert == -1) and  flag)):
         if (self.xyuv == 0):
            if self.grblmode:
               fmt0 =  "G00 X"+prec+" Y"+prec+" U"+prec+" Z"+prec+"\n"
            else:
               fmt0 =  "G00 X"+prec+" Y"+prec+" U"+prec+" V"+prec+"\n"
            flist.append( fmt0 % (2*retract,-2*retract,2*retract,-2*retract))
         else:
            if (self.xyuv == 1):
               fmt0 =  "G00 Y"+prec+" Z"+prec+"\n"
            else:
               fmt0 =  "G00 X"+prec+" Z"+prec+"\n"
            flist.append( fmt0 % (2*retract,-2*retract))
      if (flag):
         if (invert == -1):
            flist.append("M5\nM30\n")
            flist.append("%\n")
      else:
         flist.append("M5\nM30\n")
         flist.append("%\n")
      #end of plot()

    def WriteLeftToAxis(self):
        for line in self.g_code_left:
           sys.stdout.write(line)
        self.quit()
 
    def WriteRightToAxis(self):
        for line in self.g_code_right:
           sys.stdout.write(line)
        self.quit()

    def WriteBothToAxis(self):
        if len(self.g_code_both) > 100:
           for line in self.g_code_both:
              sys.stdout.write(line)
           self.quit()
        else:
            self.g_code.insert(END,'ERROR: no BOTH data to write')

    def SaveModel(self):
      """ save an ini file like this
      [drunk]
      wingspan=770
      root=340
      tip=150
      trail=1
      sweep=50
      gantry=900
      rootfile=e374.dat
      tipfile=e374.dat
      foamchord=410
      foamthick=50
      feedspeed=345
      xy=0
      inch=0
      """

      try:
         """ save in ini in the NC folder """
         self.NcFileDirectory = self.GetIniData(self.inifile,'Directories','NcFiles')
      except:
         tkMessageBox.showinfo('Missing INI Data', 'You must set the\n' \
                'NC File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/NC Directory\n' \
                'in the menu to set this option')
         return

      modelname = self.ModelNameVar.get()
      modelname = modelname.strip()
      if (modelname == ''):
         tkMessageBox.showinfo('Need a model name in order to save a model')
         return

      inifile = self.NcFileDirectory +'/'+ modelname + '.ini'

      config = ConfigParser.SafeConfigParser()

      # When adding sections or items, add them in the reverse order of
      # how you want them to be displayed in the actual file.
      # In addition, please note that using RawConfigParser's and the raw
      # mode of ConfigParser's respective set functions, you can assign
      # non-string values to keys internally, but will receive an error
      # when attempting to write to a file or when you get it in non-raw
      # mode. SafeConfigParser does not allow such assignments to take place.
      config.add_section(modelname)
      config.set(modelname, 'wingspan', self.WingSpanVar.get())
      config.set(modelname, 'washout',  self.WashoutVar.get())
      config.set(modelname, 'root',     self.RootChordVar.get())
      config.set(modelname, 'tip' ,     self.TipChordVar.get())
      items =  self.RootProfilelistbox.curselection()
      item = self.RootProfilelistbox.get(items[0])
      config.set(modelname, 'rootfile', item)
      items =  self.TipProfilelistbox.curselection()
      item = self.TipProfilelistbox.get(items[0])
      config.set(modelname, 'tipfile',  item)
      config.set(modelname, 'foamchord', self.FoamChordVar.get())
      config.set(modelname, 'foamthick', self.FoamThicknessVar.get())
      config.set(modelname, 'trail',     self.TrailingEdgeLimitVar.get())
      config.set(modelname, 'sweep',     self.LeadingEdgeSweepVar.get())
      config.set(modelname, 'gantry',    self.GantryLengthVar.get())
      config.set(modelname, 'feedspeed', self.FeedrateVar.get())
      xy = self.XYsideVar.get()
      config.set(modelname, 'xy',        str(xy))
      unit = self.UnitVar.get()
      config.set(modelname, 'inch',      str(unit))

      # Writing our configuration file to 'example.cfg'
      with open(inifile, 'wb') as configfile:
          config.write(configfile)
      self.g_code.insert(END, 'Saved model\n')
      self.WriteIniData(self.inifile,'autoload','model',modelname)      #write for autoload

    def ReadModel(self, filename):
        config = ConfigParser.SafeConfigParser()
        config.read(filename)
        #get the model name from the filename
        modelname = os.path.splitext(os.path.basename(filename))[0]
        if (config.has_section(modelname)):
            self.ModelNameVar.set(modelname)
            self.WingSpanVar.set( config.get(modelname, 'wingspan'))
            try:
                self.WashoutVar.set( config.get(modelname, 'washout'))
            except:
                self.WashoutVar.set('0')
            self.RootChordVar.set(config.get(modelname, 'root'))
            self.TipChordVar.set( config.get(modelname, 'tip' ))

            item = config.get(modelname, 'rootfile')
            item = os.path.join(self.DatDir, item)
            last = len(self.profiles) - 1
            self.RootProfilelistbox.selection_clear(0, last)
            self.RootProfilelistbox.selection_set(self.profiles.index(item))

            item = config.get(modelname, 'tipfile')
            item = os.path.join(self.DatDir, item )
            self.TipProfilelistbox.selection_clear(0, last)
            self.TipProfilelistbox.selection_set(self.profiles.index(item))

            self.FoamChordVar.set( config.get(modelname, 'foamchord'))
            self.FoamThicknessVar.set( config.get(modelname, 'foamthick'))
            self.TrailingEdgeLimitVar.set( config.get(modelname, 'trail'))
            self.LeadingEdgeSweepVar.set(  config.get(modelname, 'sweep'))
            self.GantryLengthVar.set(      config.get(modelname, 'gantry'))
            self.FeedrateVar.set(          config.get(modelname, 'feedspeed'))
            self.XYsideVar.set( config.getint(modelname, 'xy'))
            self.UnitVar.set(   config.getint(modelname, 'inch'))
            self.g_code.insert(END, 'loaded model ' + modelname + "\n")
            self.modelname = modelname
            return 1
        else:
            return 0

    def LoadModel(self):
      try:
         """ save in ini in the NC folder """
         self.NcFileDirectory = self.GetIniData(self.inifile,'Directories','NcFiles')
      except:
         tkMessageBox.showinfo('Missing INI Data', 'You must set the\n' \
                'NC File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/NC Directory\n' \
                'in the menu to set this option')
         return
      filename = askopenfilename(initialdir=self.NcFileDirectory,defaultextension='.ini',filetypes=[('INI','*.ini')])
      if self.ReadModel(filename):
         #write this modelname to the ini file for autoload at startup
         self.WriteIniData(self.inifile,'autoload','model',self.modelname)
         
         
    """
        def WriteToAxis(self):
            sys.stdout.write(self.g_code.get(0.0, END))
            self.quit()
    """

#what code is this?
    def FToD(self,s): # Float To Decimal
        """
        Returns a decimal with 4 place precision
        valid imputs are any fraction, whole number space fraction
        or decimal string. The input must be a string!
        """
        s = s.strip(' ') # remove any leading and trailing spaces
        if s == '': # make sure it does not crash on empty string
            s = '0'
        D=Decimal # Save typing
        P=D('0.000001') # Set the precision wanted
        if ' ' in s: # if it is a whole number with a fraction
            w,f=s.split(' ',1)
            w=w.strip(' ') # make sure there are no extra spaces
            f=f.strip(' ')
            n,d=f.split('/',1)
            ret = D(D(n)/D(d)+D(w)).quantize(P)
            return float(ret)
        elif '/' in s: # if it is just a fraction
            n,d=s.split('/',1)
            ret =  D(D(n)/D(d)).quantize(P)
            return float(ret)
        ret = D(s).quantize(P) # if it is a decimal number already
        return float(ret)

    def GetIniData(self,FileName,SectionName,OptionName):
        """
        Returns the data in the file, section, option if it exists
        of an .ini type file created with ConfigParser.write()
        If the file is not found or a section or an option is not found
        returns an exception
        """
        self.cp = ConfigParser.SafeConfigParser()
        try:
            self.cp.read(FileName)
            try:
                self.cp.has_section(SectionName)
                try:
                    IniData=self.cp.get(SectionName,OptionName)
                except ConfigParser.NoOptionError:
                    raise Exception,'NoOptionError'
            except ConfigParser.NoSectionError:
                raise Exception,'NoSectionError'
        except IOError:
            raise Exception,'NoFileError'
        return IniData

    def WriteIniData(self,FileName,SectionName,OptionName,OptionData):
        """
        Pass the file name, section name, option name and option data
        When complete returns 'sucess'
        """
        self.cp = ConfigParser.SafeConfigParser()
        self.cp.read(FileName)  # read existing stuff and add to it
        if not self.cp.has_section(SectionName):
            self.cp.add_section(SectionName)
        self.cp.set(SectionName,OptionName,OptionData)
        with open(FileName, 'wb') as configfile:
           self.cp.write(configfile)


    def GetDirectory(self):
        self.DirName = askdirectory(initialdir='/home',title='Please select a directory')
        if len(self.DirName) > 0:
            return self.DirName

    def CopyClpBd(self):
        self.g_code.clipboard_clear()
        self.g_code.clipboard_append(self.g_code.get(0.0, END))

    def WriteToFile(self):
        try:
            self.NcFileDirectory = self.GetIniData(self.inifile,'Directories','NcFiles')
        except:
            tkMessageBox.showinfo('Missing INI', 'You must set the\n' \
                'NC File Directory\n' \
                'before saving a file.\n' \
                'Go to Edit/NC Directory\n' \
                'in the menu to set this option')
#        try:
        # os.path.join(self.NcFileDirectory, self.modelname, '-right.nc')           
        # os.path.join(self.NcFileDirectory, self.modelname, '-left.nc')
        # os.path.join(self.NcFileDirectory, self.modelname,'-both.nc')
        if (self.xyuv == 0 ):
           fname = os.path.join(self.NcFileDirectory, self.modelname+ '-right' + self.ext)
           of = open(fname,'w')
           for line in self.g_code_right:
              of.write(line)
           of.close()
           self.g_code.insert(END, 'Right file written ' + fname + '\n')

           fname = os.path.join(self.NcFileDirectory, self.modelname + '-left' + self.ext)
           of = open(fname,'w')
           for line in self.g_code_left:
              of.write(line)
           of.close()
           self.g_code.insert(END, 'Left file written ' + fname + '\n')

           both = os.path.join(self.NcFileDirectory, self.modelname + '-both' + self.ext)
           if self.need == 0:    
              of = open(both,'w')
              for line in self.g_code_both:
                  of.write(line)
              of.close()
              self.g_code.insert(END, 'Both file written ' + both + '\n')
           else:
               if os.path.exists(both):
                   os.unlink(both)
        else:  # write one file for cartesian cutter
            if (self.xyuv == 1 ):
               tag = 'YZ'
            else:
               tag = 'XZ'
            fname = os.path.join(self.NcFileDirectory, self.modelname + '-'+tag + self.ext)
            of = open(fname,'w')
            for line in self.g_code_left:
               of.write(line)
            of.close()
            self.g_code.insert(END, 'Cartesian written ' + fname + '\n')
           
        #self.NewFileName = asksaveasfile(initialdir=self.NcFileDirectory,mode='w', master=self.master,title='Create NC File',defaultextension='.ngc')
        #self.NewFileName.write(self.g_code.get(0.0, END))
        #self.NewFileName.close()
#        except:
 #           tkMessageBox.showinfo('broken','something broke while writing files\n')

    def NcFileDirectory(self):
        DirName = self.GetDirectory()
        if len(DirName) > 0:
            self.WriteIniData(self.inifile,'Directories','NcFiles',DirName)

    # this is the folder where we find our .dat files for foil shapes
    def DatFileDirectory(self):
        DirName = self.GetDirectory()
        if len(DirName) > 0:
            self.WriteIniData(self.inifile,'Directories','DatFiles',DirName)

    def Simple(self):
        tkMessageBox.showinfo('Feature', 'Sorry this Feature has\nnot been programmed yet.')

    def ClearTextBox(self):
        self.g_code.delete(1.0,END)

    def SelectAllText(self):
        self.g_code.tag_add(SEL, '1.0', END)

    def SelectCopy(self):
        self.SelectAllText()
        self.CopyClpBd()

    def HelpInfo(self):
        SimpleDialog(self,
            text='See the github page for help.\n',
            buttons=['Ok'],
            default=0,
            title='User Info').go()
    def HelpAbout(self):
        tkMessageBox.showinfo('Help About', 'Programmed by\n'
            'the Swarfer\n'
            'Version 1.0.1')

    # take an array read from a dat file and strip out all comments so we only have the co-ord numbers on return
    def stripfile(self, thefile):
      done = 0
      while not(done):
         done = 1
         bits = 0
         for key in range(0, len(thefile)-1):
            line = thefile[key]
            bits = string.strip(line)
            bits = string.split(bits) #(preg_split('/[ ]+|\t/',trim(self.line));
            for idx in range(0, len(bits)-1): # prevent losing lines like '0 0'
               if (bits[idx] == '0'):
                  bits[idx] = '0.0'
            if (len(bits) == 3) and (re.search('[a-d]|[f-z]', line) == None ): # some files have 3 fields, remove first one, the line number
               bits.remove( bits[0])
            if ( re.search('[a-d]|[f-z]|[A-D]|[F-Z]',line) != None ):
               thefile.remove(line)
               done = 0
               break
            if ( line == ''):
               thefile.remove(line)
               done = 0
               break
            thefile[key] = string.strip(line)
      return thefile

    #creates the self.root array of cordinates
    def FindThicknessesRoot(self):
      idx = 0
      self.tipymax = self.rootymax = 0
      self.tipymin = self.rootymin = 10000
      self.idxl = len(self.rootprofile) / 4  # trailing edge limiting index limit
      self.actualrootthickmax = 0        # find the actual root thickness max
      self.actualrootthickmin = 10000    # find the actual root thickness min

      self.root = list()
      div = 0.0  # if first value is not 1.0 then set this so that all values can be scaled to 1

      for line in self.rootprofile:
         bits = line.split()
         if len(bits):

            #scaling, some dat files are 0..1 and some are 0..100
            if div == 0.0:
                div = float(bits[0])
             
            x = 1 - float(bits[0]) / div
            y = float(bits[1]) / div
            self.root.append( [0,0] )
            self.root[idx][0] = x * self.rootlength
            self.root[idx][1] = y * self.rootlength
            # want to know the actual root profile thickness to crosscheck against foamthick
            art = y * self.rootchord
            if self.actualrootthickmax < art:
               self.actualrootthickmax = art
            if self.actualrootthickmin > art:
               self.actualrootthickmin = art

            if self.rootymax < self.root[idx][1]:
               self.rootymax = self.root[idx][1]
            if self.rootymin > self.root[idx][1]:
               self.rootymin = self.root[idx][1]

            idx = idx + 1

      self.actualrootthick = self.actualrootthickmax - self.actualrootthickmin;
      #end FindThicknessRoot

    # creates the self.tip array of coordinates
    def CreateTip(self):
      idx = 0
      self.tgtravel = 0  # tip gantry travel, essentially tip length at gantry
      self.tip = list()
      div = -1
      for line in self.tipprofile:
         bits = line.split()
         if len(bits):
            if div == -1:
               div = float(bits[0])
            x = 1 - float(bits[0]) / div   #bits[0] is x
            y = float(bits[1]) / div       #bits[1] is y
            self.tip.append( [0,0] )
            self.tip[idx][0] = x * self.tiplength
            self.tip[idx][1] = y * self.tiplength

            idx = idx + 1
      #end CreateTip

    #find the thicknesses for tip, do this after rotate!, coords are in mm
    def FindThicknessesTip(self):
        idx = 0
        self.tgtravel = 0  # tip gantry travel, essentially tip length at gantry
        self.tipymax = 0
        self.tipymin = 10000

        for tip in self.tip:
            x = tip[0]  #is x
            y = tip[1]  #is y
            # tip gantry travel   - for drawing
            if (x > self.tgtravel):
               self.tgtravel = x

            if self.tipymax < y:
               self.tipymax = y
            if self.tipymin > y:
               self.tipymin = y

            idx = idx + 1
        #end FindThicknessTip

    def TrailingEdgeLimits1(self):
      # do trailing edge limiting for both profiles
      c = len(self.tip) -1
      for idx in range(2, self.idxl): 
        other = c - idx;
        dist = self.tip[idx][1] - self.tip[other][1]
        if (dist < self.trail):
            adjust = (self.trail - dist) / 2
            self.tip[idx][1] += adjust
            self.tip[other][1] -= adjust

        dist = self.root[idx][1] - self.root[other][1]
        if (dist < self.trail):
            adjust = (self.trail - dist) / 2;
            self.root[idx][1] += adjust;
            self.root[other][1] -= adjust;
      #end TrailingEdgeLimits

    #new way, move the top to be trail above the bottom surface
    def TrailingEdgeLimits2(self):
      # do trailing edge limiting for both profiles
        for this in range(0, self.idxl):
            other = len(self.root) - 1 - this   # index of the bottom surface point
            dist = self.root[this][1] - self.root[other][1]
            if dist < self.trail:
                self.root[this][1] = self.root[other][1] + self.trail
            dist = self.tip[this][1] - self.tip[other][1]
            if dist < self.trail:
                self.tip[this][1] = self.tip[other][1] + self.trail
            
      #end TrailingEdgeLimits

    def FindStartPoints(self):
      # do foam stuff and calc start height
      # might need to adjust this to account for rotation of the tip profile putting its max/min beyond the root profile
      if self.unit:
         off = 0.25
      else:
         off = 6    #min offet from outside of foam
      if (self.foamthickness == 0):
         print "foamthick = 0" 
         self.foamthickness = self.rootymax - self.rootymin + off
         self.g_code.insert(END, "   foamthickness calculated at " + self.Format(self.foamthickness,2) + self.units) 
         self.sp = ((self.foamthickness - self.skintop - self.skinbot) * -self.rootymin / (self.rootymax - self.rootymin)) + self.skinbot
      else:
         if (self.actualrootthick > (self.foamthickness - self.skintop - self.skinbot) ):
            print "too thick"
            self.g_code.insert(END,"      ERROR: actualroothickness %.2f EXCEEDS foamthickness %.2f" % (self.actualrootthick, self.foamthickness))
            self.g_code.insert(END,"		Recalculating foamthickness\n")
            self.foamthickness = round(self.actualrootthick + off,0)
            self.skintop = self.skinbot = 0
            self.sp = ((self.foamthickness - self.skintop - self.skinbot) * -self.rootymin / (self.rootymax - self.rootymin)) + self.skinbot
         else:
            # startpoint, calculate it to put wing centered in foamthick less skins
            self.rt = self.rootymax - self.rootymin
            self.g_code.insert(END, "\n   root thickness %f%s\n   foamthickness %f%s\n" % (self.actualrootthick,self.units, self.foamthickness,self.units))
            if (self.skintop or self.skinbot):
               t = self.foamthickness - self.skintop - self.skinbot
               self.g_code.insert(END," (%f after skinning)",(t))
           
            #max height of profiles
            rat = max(self.rootymax,self.tipymax) - min(self.rootymin, self.tipymin)
            #max off set from bottom
            h = -min(self.rootymin , self.tipymin)
            #print "rat %.3f  h %.3f" % (rat, h)
            leftover = (self.foamthickness - self.skintop - self.skinbot) - rat
            self.sp = leftover/2 + h + self.skinbot
            
            #now check that it still fits the foam
            if ((self.sp + self.rootymax) > self.foamthickness) or (self.sp + self.tipymax > self.foamthickness):
               self.g_code.insert(END, "ERROR: top of profile will exit the foam, need thicker foam!\n")
            
      # do some calcs for the BOTH output
      self.need = 0
      if ( (rat*2+2*off) > (self.foamthickness - self.skintop - self.skinbot) )      :
         self.g_code.insert(END,"   WARNING: FOAMTHICK is not enough to cut BOTH panels\n") 
         self.need = rat*2 + off*2
         self.g_code.insert(END, "   WARNING: need foam at least %0.2f%s thick\n" % (self.need, self.units) )
      self.fth = (self.foamthickness / 2)
      
      self.spl = self.fth + ( (self.fth-self.skintop) - rat)/2 + h   # left start point in top half
      self.spr = self.fth - ( (self.fth-self.skinbot) - rat)/2 - h   # right start point in bottom half

      bottomoftop = self.spl + min(self.rootymin, self.tipymin)
      topofbottom = self.spr - min(self.rootymin, self.tipymin)
      #print "spl %.3f spr %.3f bottomoftop %.3f topofbottom %.3f" % (self.spl, self.spr, bottomoftop, topofbottom)
      
      if (bottomoftop < topofbottom):
          self.g_code.insert(END, "ERROR: sections are colliding in BOTH, need thicker foam by %.3f \n" % (topofbottom - bottomoftop))
             
      #end of FindStartPoints

    #RESAMPLE stuff
      
    #calculate new y for this $x, from the points on the line x1,y1 to x2,y2
    def newy(self, x1,y1,x2,y2,x):
        m = (y2-y1) / (x2-x1)
        c = y1 - m * x1
        y = m * x + c
        return y

    #resample sla to have the same number of points as master
    #master must have more points than slave
    # the two lists are the raw lines from the dat file
    def resample(self, mas,sla):
        #mmin point in master
        mmin = 1000
        prec = 7
        idx = 0
        midx = -1
        mdiv = -1
        for m in mas:
            bits = m.split()
            if mdiv < 0:
               mdiv = float(bits[0]) 
            x = float(bits[0]) / mdiv   # must scale all values
            y = float(bits[1]) / mdiv

            if x < mmin:
                midx = idx
                mmin = x
            idx = idx + 1
        #print("mmin %0.7s midx %d  mdiv %0.7f" % (mmin,midx,mdiv))
        #find smin point in sla
        idx = 0
        smin = 1000
        sdiv = -1
        for s in sla:
            bits = s.split()
            if sdiv < 0 :
                sdiv = float(bits[0]) 
            x = float(bits[0]) / sdiv
            y = float(bits[1]) / sdiv
            if x < smin:
                smin = x
                sidx = idx
            idx = idx + 1
        #print("smin %0.7s sidx %d    sdiv %0.7f   mdiv %0.7f" % (smin,sidx,sdiv,mdiv))

        new = list()
        top = 1
        idx = 0
        for m in mas:
            #if top: print "%d %s %d" %(idx,m, top)
            bits = m.split()
            cx = float(bits[0]) / mdiv
            cy = float(bits[1]) / mdiv
            #print "cx %.7f  top %d" % (cx,top)
            if (cx < (mmin + 0.00000001)):
              top = 0
              #print str(cx) + " change to bottom" + str(top) + " idx = " + str(idx) + "\n"
            if (top == 1):
              for i in range(0,sidx+1):
                 bits = sla[i].split()
                 sx = float(bits[0]) / sdiv
                 sy = float(bits[1]) / sdiv
                  
                 if abs(cx - sx) < 0.000001:
                    #print "%d cx=sx appending sla %f,%f" % (idx,sx,sy)
                    new.append("%0.7f %0.7f" % (sx,sy))                   #            echo "top equal\n";
                    break

                 bits1 = sla[i+1].split()  #split next line
                 sx1 = float(bits1[0]) / sdiv
                 sy1 = float(bits1[1]) / sdiv

                 if mmin < smin:
                    if (abs(cx - mmin) < 0.001):
                        #print "sx %.7f  smin %.7f" % (sx,smin)
                        if (abs(sx - smin) < 0.001):
                          #print "   sx == smin" 
                          new.append("%0.7f %0.7f" % (cx , sy))
                          break
                 if (cx > sx1):
                    if abs(sx - sx1) < 0.000001:
                        #print "%d sx = sx1 appending sla %f,%f" % (idx,cx,sy)
                        new.append("%0.7f %0.7f" % (cx , sy))
                    else:
                        # calculate a new Y at this X
                        y = self.newy(sx1,sy1, sx, sy, cx )
                        #print "%d calc new Y at %f = %f,%f " %(idx, cx,cx,y)
                        new.append("%0.7f %0.7f" % (cx, y))       #            echo "top new $cx $y\n";
                    break
            if top == 0:                      #      echo "bottom ";
              for i in range(sidx, len(sla)-1):
                 #print "i %d" % i
                 bits = sla[i].split()
                 sx = float(bits[0]) / sdiv
                 sy = float(bits[1]) / sdiv
                 if abs(cx - sx) < 0.000001:
                    #print "%d CX=SX appending sla %f,%f" % (idx,sx,sy)
                    new.append("%0.7f %0.7f" % (sx,sy))                   #            echo "top equal\n";
                    break

                 bits1 = sla[i+1].split()  #split next line
                 sx1 = float(bits1[0]) / sdiv
                 sy1 = float(bits1[1]) / sdiv
                 
                 if (cx < sx1):
                    if abs(sx - sx1) < 0.000001:
                        #print "%d SX=SX1 %.7f,%.7f appending sla %f,%f" % (idx,sx,sx1, sx,sy)
                        new.append("%0.7f %0.7f" % (cx , sy))
                    else:     
                        # calculate a new Y at this X
                        #print "%d sx %.6f sx1 %.6f" % (idx,sx,sx1)
                        y = self.newy(sx,sy, sx1, sy1, cx )
                        #print "%d CALC new Y at %f = %f,%f " %(idx, cx,cx,y)
                        new.append("%0.7f %0.7f" % (cx , y))
                    break
            idx = idx + 1
        # now add last one
        #print new
        bits = sla[ len(sla)-1].split()
        sx = float(bits[0]) / sdiv
        sy = float(bits[1]) / sdiv
        #print "%d CX=sx appending sla %f,%f" % (idx,sx,sy)
        new.append("%0.7f %0.7f" % (sx,sy))
        #print len(mas), len(sla), len(new)   
        return new        
        #end resample

    #ROTATE
    #from the web https://stackoverflow.com/questions/20023209/function-for-rotating-2d-objects
    def rotatePolygon(self,polygon,theta):
        """Rotates the given polygon which consists of corners represented as (x,y),
        around the ORIGIN, clock-wise, theta degrees"""
        theta = radians(theta)
        rotatedPolygon = list()
        for corner in polygon :
            rotatedPolygon.append([ corner[0]*cos(theta)-corner[1]*sin(theta) , corner[0]*sin(theta)+corner[1]*cos(theta)] )
        return rotatedPolygon

        
app = Application()
app.master.title('Wing hotwire G-Code Generator')
app.mainloop()
