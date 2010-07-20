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
##  - One: This is a python script. It needs python installed to run. Google it.
##  - The program is designed to take the information from a comma seperated
## file ("CSV"), parse it and reprint the information in DWS (INI) format.
##  - To configure the program, you must first create a CSV file with the correct
## column-headers and values. The CSV file must be in the same directory as this file
## (or vice versa). Then in this file, find the line beginning with "csvfilename = ".
## This defines the name of the CSV file you wish to parse - edit the line so the
## csvfilename variable matches the name of the csv file you wish to use.
## You can also optionally change the name of the DWS output file and change
## the number of the initial header.
## You can also add more CSV to the list: csvfilelist.

## Changelog:
##  StdCmdOpt og NonEmptyOpt for følgende funktioner
##  - PlaceIt (working), PreRun, NumberOfSamples [IMPORTANT, must have]
##  - PostRun, End
##  - Thermomixer, Comment, Wait, UserIntervention
##  AddParams parser:
##  - Parser which can parse especially cells with multi-input.
##  --- Edit: This will not be included. Edit the DWS file manually if very special needs is required.
##  --- Edit2: This is now supported. Just remember to add the header to the getImplodedCmdOpt function for the specific OpcodeStr.
##  Support for input from multiple CSV files

import csv, os, sys
from datetime import datetime, date, time

## Script constants ##
rundatetime = datetime.now()
datehourStr = rundatetime.strftime("%y%m%d-%H%M")
opt_std_implode_seperator = '|'

### Script options: ###
startheader = 1 # Set where to start the DWS section header numbers
csvfilename = 'CSVinput.csv' # CSV input file
placeitcsv = 'WorkspaceInput.csv'
#csvfilelist = [placeitcsv, csvfilename]
csvfilelist = [csvfilename]

### Method options: ###
methodname = 'DWSoutput' # epMotion filenames are maxed at 20 chars :-(
dwsfilename = "".join([methodname, datehourStr, '.dws']) # DWS config file (INI format)
methodcomment = '' # Write a comment to the DWS method. Use \n for breakline

opt_only_include_defaults = 1 # Inner- or outer join with the default command-options.
                              # If set to 0 you risk adding non-valid options to the DWS file!
                              # If you are using imploded arguments, this must be 1!
                              

## Other init stuff: ##
DWSproperties = {'Name': methodname,
                 'Comment': methodcomment,
                 'DWS-ability': '0x0000FF06' }

DWSversion = {'Name': dwsfilename,
              'Struktur': 'PrgStruc 0.21' }

VERBOSE_LEVEL = 0   # How much information to print. All messages below VERBOSE_LEVEL are displayed, those below supressed. Default is 0.
                    # Approximate levels: FatalErrors=-9, Errors=-5, DangerWarnings=-4, Warnings=-1, Notice=+1, Info=+5 
DEBUG_LEVEL = 0 # How much debug information to print. Default is 0.



## Main buissines logic: ##

def main():
    finalCmdOptList = [] # Merged with the "default" input


    for currentcsvname in csvfilelist:
        ### First, load the CSV file info ###
        # This can easily be done using the csv DictReader
        csvfile = open(currentcsvname, newline='') # Default mode is read-only.
        csvreader = csv.DictReader(csvfile)    
        print('Using CSV file:', currentcsvname)

        ### Second, make a valid options-list for every command section from the raw csv row:
        print('Extracting raw parameter data from csv file...')
        for i, rawcmdopt in enumerate(csvreader):
            #print(i) 
            #print(rawcmdopt) # If you get an error that it cannot find some parameter, e.g. 'Opcode', the CSV file may be incorrectly formatted.
            # First, get a list with standard cmd parameters/options (keys and values).
            cmdOpt = getStdCmdOpt(rawcmdopt)
            implodedCmdOpt = getImplodedCmdOpt(rawcmdopt)
            
            if not opt_only_include_defaults:
                # If you want to do it this way, there is a build-in function.
                # Delete empty or invalid dictionary items:
                dellist = []
                for paramName, paramVal in rawcmdopt.items():
                    if paramVal == "" or not type(paramVal)==type(""):
                        dellist.append(paramName)
                for paramName in dellist:
                    del rawcmdopt[paramName]
                cmdOpt.update(rawcmdopt)
            else: # Dvs hvis vi kun vil have standard parametre. Dette burde være sikrest.
                for paramName, paramVal in rawcmdopt.items():
                    if paramName in cmdOpt and not paramVal == "":
                        cmdOpt[paramName] = paramVal
                    elif paramName in implodedCmdOpt:
                        # print("".join(['Testing: ', paramName]))
                        cmdOpt.update(getOptFromImploded(implodedCmdOpt, paramName, paramVal))
                        
                        

            # Do a check of the options before adding it to the final list
            if checkCmdOpt(cmdOpt):
                finalCmdOptList.append(cmdOpt)
            else:
                if VERBOSE_LEVEL > 0:
                    print('NOTICE: Line ', i, 'in file', currentcsvname, 'did not pass checkCmdOpt() and was therefore NOT added to finalCmdOptList.')
    


    ### Third (optionally), add end-codes:
    finalCmdOptList.append(getStdCmdOpt(dict(Opcode='117')))  # PostRun
    finalCmdOptList.append(getStdCmdOpt(dict(Opcode='129')))  # End


    # Furth, print cmds to the DWS output file...
    print('Writing new DWS info to file:', dwsfilename)
    newcfgfile = open(dwsfilename, 'w')

    # 4.a) Print DWS file properties and version
    printIniSection(DWSproperties, '[Properties]', newcfgfile)
    printIniSection(DWSversion, '[Version]', newcfgfile)

    # 4.b) Loop through finalCmdOptList and print to DWS:
    for i, cmdOpt in enumerate(finalCmdOptList):
        sec = str(startheader+i).zfill(3)
        sechead = "".join(['[', sec, ']'])

        printIniSection(cmdOpt, sechead, newcfgfile)

    print('Succes!')
### End of main()


# printIniSection prints a INI-formatted section using pHeader as
# INI section header and (key,value) pairs from the dict.
# If a file object is provided, the section is written to this file,
# otherwise sys.stdout is used.
def printIniSection(pDict, pHeader, pFile=None):

    if not type(pFile).__name__=='TextIOWrapper':
        pFile=sys.stdout
    
    pFile.write("".join([pHeader, '\n']))
    
    for paramName, paramValue in pDict.items():
        pFile.write("".join([paramName, "=", paramValue, '\n']))

    pFile.write('\n')

# End printIniSection function

def checkCmdOpt(cmdOpt):
    # Check that all required fields have been set
    # (Many do not have defaults)

    isOk = 1
    nonEmptyOpt = getNonEmptyOpt(cmdOpt)

    if nonEmptyOpt==0:
        print('checkCmdOpt Warning: Opcode', cmdOpt['Opcode'], 'not recognized. Using empty check list.')
        nonEmptyOpt = []      

    
    for key in nonEmptyOpt:
        if not key in nonEmptyOpt or not type(cmdOpt[key]) == type("") or cmdOpt[key]=="":
            isOk = 0
            break


    return isOk
        
### End of checkCmdOpt


# Used to add imploded options to the cmd dict.
def getOptFromImploded(implodedCmdOpt, paramName, implodedString):
    # implodedCmdOpt has info about any prefix. (Usually, is the string is a packed list, it has 0='lds'|1='ldsf', etc...)
    sep = opt_std_implode_seperator
    options = dict()
    # print("".join(['implodeString: ', implodedString]))
    optPairsList = implodedString.split(sep)
    # print(optPairsList)
    # print(len(optPairsList))
    for optPair in optPairsList:
        optKeyVal = optPair.split('=')
        # print(optKeyVal)
        if len(optKeyVal) != 2: # In case the string is empty...
            #print(" ".join(['Error, optKeyVal has length different from 2: ', str(len(optKeyVal))]))
            pass
        else:
            key = "".join([implodedCmdOpt[paramName], optKeyVal[0]])
            options[key] = optKeyVal[1]

    return options

# end addImplosionToCmdOpt

# Used to get a list of imploded commands, that is, columns that needs unpacking of arguments.
# I currently use a dict where the keys are the expected column header, and the values are prefixes. I don't know if this is ideal, but let's see...
def getImplodedCmdOpt(rawcmdopt):

    implodedCmdOpt = dict()
    
    if rawcmdopt['Opcode'] == '115' or rawcmdopt['OpcodeStr'] == 'Place It' :
        implodedCmdOpt = {'ReagenzNamen':'ReagenzName_',
                          'StartVolumen': 'StartVolumenNanoliter_',
                          'StartVolumenNanoliter': 'StartVolumenNanoliter_'}
        

    return implodedCmdOpt

# End of getImplodedCmdOpt


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

    elif rawcmdopt['Opcode'] == '112':
        stdCmdOpt = dict(   OpcodeStr='Wait',
                            Opcode='112',
                            Bezeichner='',
                            WaitMinute='0',
                            WaitSekunde='0',
                            WaitTemp='0',
                            WaitTempPos='',
                            WaitCycler='0')
                                             
    elif rawcmdopt['Opcode'] == '113':
        stdCmdOpt = dict(   OpcodeStr='Comment',
                            Opcode='113',
                            Bezeichner='')
        
    elif rawcmdopt['Opcode'] == '114':
        stdCmdOpt = dict(   OpcodeStr='UserIntervention',
                            Opcode='114',
                            Bezeichner='',
                            Alarm='0')

    elif rawcmdopt['Opcode'] == '115':
        stdCmdOpt = dict(   OpcodeStr='Place it',
                            Opcode='115',
                            Bezeichner='',
                            MatDatei='',        # ./top/dws/trth/SAR_Rack_1_5ml
                            MatName='',         # SAR_Rack_1_5ml
                            BehaelterName='',   # Stocks
                            EnumMatType='',     # 512
                            EnumSlotNr='',      # 152
                            Stapelindex='0',
                            RackLevelSensor='0',
                            RackTemperatur='0')
        
    elif rawcmdopt['Opcode'] == '116':
        stdCmdOpt = dict(   OpcodeStr='PreRun',
                            Opcode='116',
                            Bezeichner='')

    elif rawcmdopt['Opcode'] == '117':
        stdCmdOpt = dict(   OpcodeStr='PostRun',
                            Opcode='117',
                            Bezeichner='')
        
    elif rawcmdopt['Opcode'] == '118':
        stdCmdOpt = dict(   OpcodeStr='NumberOfSamples',
                            Opcode='118',
                            Bezeichner='',
                            Fest='1',
                            festeProbenzahl='1',
                            maxProbenzahl='0')

    elif rawcmdopt['Opcode'] == '123':
        stdCmdOpt = dict(   OpcodeStr='Thermomixer',
                            Opcode='123',
                            Bezeichner='',
                            WithTemplate='1',
                            TemplateDatei='top/dws/tmx/',
                            TemplateName='PCR 96',
                            EditTempPar='1',
                            SpeedOn='1',
                            MixSpeed='1500',
                            MixTimeMinute='2',
                            MixTimeSecond='0',
                            TempOn='1',
                            Temperature='25',
                            TempHold='1')
                                
    elif rawcmdopt['Opcode'] == '129':
        stdCmdOpt = dict(   OpcodeStr='End',
                            Opcode='129')
        
    else: # If no opcode could be found, set the opcode to 101 and try again.
        rawcmdopt['Opcode'] = '101'
        stdCmdOpt = getStdCmdOpt(rawcmdopt)

    return stdCmdOpt

# End of getStdCmdOpt


# getNonEmptyOpt: returns a list of the parameter options which must NOT be empty.
# Note: This check is meant to ensure that the DWS file can actually load in epBlue.
# It does NOT care whether or not the keys are set to a default non-empty value when fetching the standard option dict.
def getNonEmptyOpt(cmdOpt):
    #print('begin gneo')
    if cmdOpt['Opcode']=='101': # SampleTransfer
        nonEmptyOpt = ['OpcodeStr','Opcode', 
                       'Source1', 'Source_Pat_Z1', 'Source_Pat_S1', 'Source_Pat_T1', 
                       'Destination1', 'Destination_Pat_Z1', 'Destination_Pat_S1', 'Destination_Pat_T1', 
                       'TransferVolumenNanoliter', 'Filter',
                       'LiqName', 'LiqDatei', 
                       'ToolName', 'ToolDatei', 
                       'Source_Pat_AnzDup', 'Source_Pat_Vorhanden', 
                       'Destination_Pat_AnzDup', 'Destination_Pat_Vorhanden' ]

    elif cmdOpt['Opcode'] == '112':  # Wait
        nonEmptyOpt = ['OpcodeStr', 'Opcode']

    elif cmdOpt['Opcode'] == '113':  # Comment
        nonEmptyOpt = ['OpcodeStr', 'Opcode']

    elif cmdOpt['Opcode'] == '114':  # UserIntervention
        nonEmptyOpt = ['OpcodeStr', 'Opcode']
        
    elif cmdOpt['Opcode'] == '115': # Place It
        nonEmptyOpt = ['OpcodeStr', 'Opcode',
                       'MatDatei', 'MatName','BehaelterName',
                       'EnumMatType', 'EnumSlotNr']
        
    elif cmdOpt['Opcode'] == '116':  # PreRun
        nonEmptyOpt = ['OpcodeStr', 'Opcode']
        
    elif cmdOpt['Opcode'] == '117': # PostRun
        nonEmptyOpt = ['OpcodeStr', 'Opcode']
        
    elif cmdOpt['Opcode'] == '118': # NumberOfSamples
        nonEmptyOpt = ['OpcodeStr', 'Opcode', 'Fest', 'festeProbenzahl', 'maxProbenzahl']

    elif cmdOpt['Opcode'] == '123': # Thermomixer
        nonEmptyOpt = [ 'OpcodeStr', 'Opcode' ]
                      
    elif cmdOpt['Opcode'] == '129': # End
        nonEmptyOpt = ['OpcodeStr', 'Opcode']
        
    else:
        nonEmptyOpt = 0
                            
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
