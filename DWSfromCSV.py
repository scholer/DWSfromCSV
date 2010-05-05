#! /usr/bin/env python3.0
##    Copyright 2010 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
## 
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Note:    This software is beta software. It is provided "AS IS", and
##          while it has been tested, no guarantee about quality or safety
##          can be assured. Use at own risk.
##
## Usage:
##  - The program is designed to take the information from a comma seperated
## file ("CSV"), parse it and reprint the information in DWS (INI) format.
##  - To configure the program, you must first create a CSV file with the correct
## column-headers and values. The CSV file must be in the same directory as this file
## (or vice versa). Then in this file, find the line beginning with "csvfilename = ".
## This defines the name of the CSV file you wish to parse - edit the line so the
## csvfilename variable matches the name of the csv file you wish to use.
## You can also optionally change the name of the DWS output file and change
## the number of the initial header.

import csv, os

### Script options: ###
startheader = 1 # Set where to start the DWS section header numbers 
csvfilename = 'CSVinput.csv'
newcfgname = 'DWSoutput.dws'


### Global variable declarations ###
csvfile = open(csvfilename, newline='')
#dwscmdlistraw = [] # Empty list (direct output) - bruges ikke; bruger DictReader
finalCmdOptList = [] # Merged with the "default" input
opt_only_include_defaults = 1 # Inner- or outer join with the default command-options.


### First, load the CSV file info ###
# This can easily be done using the csv DictReader
csvreader = csv.DictReader(csvfile)



# Main buissines logic:
def main():
    print('Using CSV file:', csvfilename)

    ### 1) Make a valid options-list for every command section from the raw csv row:
    print('Extracting raw parameter data from csv file...')
    for i, rawcmdopt in enumerate(csvreader):
        cmdOpt = getStdCmdOpt(rawcmdopt) # Standard cmd options (parameters)

        if not opt_only_include_defaults:
            # Der findes en indbygget funktion i dette tilfælde
            cmdOpt.update(rawcmdopt)
        else: # Dvs hvis vi kun vil have standard parametre. Dette burde være sikrest.
            for paramName, paramVal in rawcmdopt.items():
                if paramName in cmdOpt and not paramVal == "":
                    cmdOpt[paramName] = paramVal

        # Evt. lav check?
        finalCmdOptList.append(cmdOpt)

    ### 2) Optionally, add end-codes:
    finalCmdOptList.append(getStdCmdOpt(dict(Opcode='117')))
    finalCmdOptList.append(getStdCmdOpt(dict(Opcode='129')))

    # Print finalCmdOptList til filen...
    print('Writing new DWS info to file:', newcfgname)
    newcfgfile = open(newcfgname, 'w')
    for i, cmdOpt in enumerate(finalCmdOptList):
        sec = str(startheader+i).zfill(3)
        sechead = "".join(['\n[', sec, ']\n'])
        newcfgfile.write(sechead)
        
        for paramName, paramValue in cmdOpt.items():
            newcfgfile.write("".join([paramName, "=", paramValue, '\n']))

    newcfgfile.write("\n")

    print('Succes!')
### End of main()



def checkCmdOpt(cmdOpt):
    # Check that all required fields have been set
    # (Many do not have defaults)

    isOk = 1
    nonEmptyOpt = getNonEmptyOpt()
    
    for key, val in cmdOpt:
        if key in nonEmptyOpt:
            if val == "" or not type(val) == type(""):
                isOk = 0
                break


    return isOk
        
### End of checkCmdOpt



def getStdCmdOpt(rawcmdopt):

    if rawcmdopt['Opcode'] == '101':
        stdCmdOpt = dict(OpcodeStr='SampleTransfer', \
                         Source1='',               # Must be set. \
                         Source_Pat_Z1='',         # Row, e.g. 'A' in 'A3' . must be set.
                         Source_Pat_S1='',         # Column (saule), e.g. '3' in 'A3'
                         Source_Pat_T1='1',        # T: Tray, e.g. T1=1 er den første på "source racks" listen. (Vi har som regl kun én.)
                         Destination1='', 
                         Destination_Pat_Z1='', 
                         Destination_Pat_S1='', 
                         Destination_Pat_T1='1', 
                         TransferVolumenNanoliter='',  # Must be set.
                         Filter='0',                   # Not required in DWS.
                         LiqName='Water', 
                         Bezeichener='',               # Not required in DWS.
                         Opcode='101', 
                         ToolName='TS_50', 
                         ToolDatei='./top/dws/tools/TS_50', 
                         LiqDatei='./top/dws/liquids/Water', 
                         TransferVolumenUnit='0',      # Not required in DWS.
                         Source_Pat_AnzDup='1',        # Required in DWS. Not set by CSV but
                         Source_Pat_Anz='1',           # Not required in DWS.
                         Source_Pat_Vorhanden='1',     # Required in DWS. Not set by CSV.
                         Destination_Pat_AnzDup='1',   # Required in DWS. Not set by CSV.
                         Destination_Pat_Anz='1',      # Not required in DWS.
                         Destination_Pat_Vorhanden='1',# Required in DWS. Not set by CSV.
                         IrregularPattern='1',         # Not required in DWS.
                         IrregularSrcPattern='1',         # Not required in DWS.
                         IrregularDesPattern='1')          # Not required in DWS.
                         

    elif rawcmdopt['Opcode'] == '115':
        stdCmdOpt = dict(   OpcodeStr='Place it',
                            Opcode='115',
                            Bezeichner='',
                            MatDatei='./top/dws/trth/SAR_Rack_1_5ml',
                            MatName='SAR_Rack_1_5ml',
                            BehaelterName='Stocks',
                            EnumMatType='512',
                            EnumSlotNr='152',
                            Stapelindex='0',
                            RackLevelSensor='0',
                            RackTemperatur='0')

    elif rawcmdopt['Opcode'] == '117':
        stdCmdOpt = dict(   OpcodeStr='PostRun',
                            Opcode='117',
                            Bezeichner='')
    
    elif rawcmdopt['Opcode'] == '129':
        stdCmdOpt = dict(   OpcodeStr='End',
                            Opcode='129')
    else:
        rawcmdopt['Opcode'] == '101'
        stdCmdOpt = getCmdOpt(rawcmdopt)

    return stdCmdOpt

# End of getStdCmdOpt


# getNonEmptyOpt: returns a list of the parameter options which must NOT be empty.
def getNonEmptyOpt(cmdOpt):
    nonEmptyOpt = ['SampleTransfer', 
                   'Opcode', 
                   'Source1', 
                   'Source_Pat_Z1', 
                   'Source_Pat_S1', 
                   'Source_Pat_T1', 
                   'Destination1', 
                   'Destination_Pat_Z1', 
                   'Destination_Pat_S1', 
                   'Destination_Pat_T1', 
                   'TransferVolumenNanoliter', 
                   'Filter', 
                   'LiqName', 
                   'LiqDatei', 
                   'ToolName', 
                   'ToolDatei', 
                   'Source_Pat_AnzDup', 
                   'Source_Pat_Vorhanden', 
                   'Destination_Pat_AnzDup', 
                   'Destination_Pat_Vorhanden' ]
    
    return nonEmptyOpt

# End of getNonEmptyOpt


### Hvis du insisterer på at have en bestemt orden, så kan du evt. lave en ordnet liste:
def getOptKeyPrintList():
    printList = ['OpcodeStr', 'Opcode', 
                 'Bezeichner', 'ToolDatei', 'ToolName', 
                 'Filter', 'TransferVolumenNanoliter', 'TransferVolumenUnit', 
                 'EnumDosierart', 'Source1', 'Destination1', 
                 'LiqDatei', 'LiqName', 'EditDosPar', 
                 'SrcSimple', 'DesSimple', 'Elution', 
                 'MixAfter', 'MixBefore', 'EnumEjectTips', 
                 'EjectAnzAufnahmen', 'IrregularPattern', 'IrregularSrcPat', 
                 'IrregularDesPat', 'StandardPattern', 'EnumStdRichtung', 
                 'EnumMusterTyp', 'Source_Pat_Anz', 'Source_Pat_AnzDup', 
                 'Source_Pat_RasterX', 'Source_Pat_RasterY', 'Source_Pat_Kanalzahl', 
                 'Source_Pat_AnzRacks', 'Source_Pat_AnzSpalten', 'Source_Pat_AnzZeilen', 
                 'Source_Pat_T1', 'Source_Pat_S1', 'Source_Pat_Z1', 
                 'Source_Pat_Vorhanden', 'Destination_Pat_Type', 'Destination_Pat_MaxDir', 
                 'Destination_Pat_AnzModule', 'Destination_Pat_Anz', 'Destination_Pat_AnzDup', 
                 'Destination_Pat_RasterX', 'Destination_Pat_RasterY', 'Destination_Pat_Kanalzahl', 
                 'Destination_Pat_AnzRacks', 'Destination_Pat_AnzSpalten', 'Destination_Pat_AnzZeilen', 
                 'Destination_Pat_T1', 'Destination_Pat_S1', 'Destination_Pat_Z1', 
                 'Destination_Pat_Vorhanden']

# End of getOptKeyPrintList

                 
main()
