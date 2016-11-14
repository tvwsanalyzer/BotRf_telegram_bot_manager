#!/usr/bin/python3
# ---------------------------------------------------
# Copyright 2016 Marco Rainone, for ICTP Wireless Laboratory.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
# ---------------------------------------------------
#
# splatbot.py
# ===========
# Source of telegram bot manager.
# This is part of BotRf telegram bot, tool for the electromagnetic spectrum analysis 
# of Terrain, loss, and RF Signal Propagation.
# 
# ver. 01.00.95, 2016/11/09
#
# NOTE:
# to relaunch this script after modifications, stop the process with the command
# pkill -9 splatbot.py
# To get the pid of this script, use the command:
# pgrep splatbot.py
#
import sys
import asyncio
import json
import math
import random
import glob
import telepot
from telepot.delegate import per_chat_id
from telepot.async.delegate import create_open

import os
import os.path
import traceback
import contextlib

# -----------------------------------------------------
# global variables
flag_SetPos = False

# -----------------------------------------------------
# command list
lst_cmd = {'keyboard': [[
    (
    'getlang'
    ), 
    (
    'setlang it'
    ),
    (
    'setlang eng'
    ), 
    (
    'hidekbd'
    ),
    (
    'site'
    ),
    (
    'earth'
    ),
    (
    'freq'
    ),
    (
    'perc'
    )
    ]]}

# -----------------------------------------------------
# help dictionary
cmd_dict = {
    "calc": 
        (
        'path profile between Site1 and Site2 with obstruction report'
        ), 
    "site": 
        (
        'Site values'
        ),
    "freq": 
        (
        'frequency (MHz) for calculations'
        ),
    "earth": 
        (
        'earth radius multiplier'
        ),
    "perc": 
        (
        'Fresnel zone clearance percentage'
        ),
    "rep": 
        (
        'path profile between Site1 and Site2 with full report'
        ),
    "pow": 
        (
        'graph of power versus distance for wireless link'
        ),
    "ant": 
        (
        'Change antenna height of an existing site'
        ),
    "list": 
        (
        'displays the sites created by the user'
        ),
    "del": 
        (
        'delete a site created by the user'
        ),
    "cnv": 
        (
        'dimensional conversion command'
        )
    }


hlp_dict = {
    "calc": 
        (
        'calc (c): path profile between Site1 and Site2.\n'
        'Use:\n'
        'calc DataSite1 DataSite2\n'
        'The function generate a png graph output named:\n'
        '      DataSite1_DataSite2.png\n'
        'and short report listing the obstructions.\n'
        'To obtain the full report, instead of calc use the report command.\n'
        '\nExample:\n'
        'calc marmolada site2\n'
        '      The output generated is marmolada_site2.png\n'
        'For calculations, the calc function uses this additional parameter:\n'
        '    - frequency (MHz) for calculations (default: 5800)\n'
        '    - earth radius multiplier (default: 1.3333)\n'
        '    - Fresnel zone clearance percentage (default: 60%)\n'
        'The default value can be changed through this command:\n'
        '    - freq:  change frequency (MHz) for calculations\n'
        '    - earth: change earth radius multiplier\n'
        '    - perc:  change Fresnel zone clearance percentage (default: 60%)\n'
        ), 
    "site": 
        (
        'site (s): site parameters used in calc function.\n'
        'Use:\n'
        'site <site name> <latitude> <longitude> <antenna height>\n'
        '\nExample:\n'
        'site remote 42.972000 13.257400 2.5\n'
        ),
    "freq": 
        (
        'freq (f): command to change the frequency (MHz) used in link or '
        'rep command functions calculation (default: 5800)\n'
        'Use:\n'
        'freq <value>\n'
        'Example:\n'
        'freq 5900.0\n'
        'If not set, the calc function uses the default value\n'
        ),
    "earth": 
        (
        'earth (k): advanced command to change earth radius multiplier '
        'used in calc function (default: 1.3333)\n'
        'Use:\n'
        'earth <value>\n'
        'Example:\n'
        'earth 1.3450\n'
        'If not set, the calc function uses the default value\n'
        ),
    "perc": 
        (
        'perc (p): advanced command to change Fresnel zone clearance percentage '
        'used in calc function (default: 60)\n'
        'Use:\n'
        'perc <value>\n'
        'Example:\n'
        'perc 75\n'
        'If not set, the calc function uses the default value\n'
        ),
    "rep": 
        (
        'rep (r): command similar to calc, which generates the full report.\n'
        'Use:\n'
        'rep DataSite1 DataSite2\n'
        'The function generate a png graph output named:\n'
        '      DataSite1_DataSite2.png\n'
        'and the full report.\n'
        'Example:\n'
        'rep marmolada site2\n'
        '      the function generates marmolada_site2.png and the full report.\n'
        ),
    "pow": 
        (
        'pow (w): graph of power versus distance for wireless link.\n'
        'Use:\n'
        'pow Site1 Site2 TxPw TxCl TxAg RxAg RxCl RxSe\n'
        'where:\n'
        'TxPw: transmitter power (dBm)\n'
        'TxCl: transmitter cable loss (dB)\n'
        'TxAg: transmitter Antenna gain (dBi)\n'
        'RxAg: receiver Antenna gain (dBi)\n'
        'RxCl: receiver cable loss (dB)\n'
        'RxSe: receiver sensitivity\n'
        'pow DataSite1 DataSite2 TxPw TxCl TxAg RxAg RxCl RxSe\n'
        'The function generate a png graph output named:\n'
        '      DataSite1_DataSite2_pow.png\n'
        'Example:\n'
        'pow marmolada remote2 18.0 -2.0 14.0 11.0 -1.0 -90.0\n'
        '      generate the power graph for a marmolada to remote2 link.\n'
        ),
    "ant": 
        (
        'ant (a): Change antenna height of an existing site\n'
        'Use:\n'
        'ant DataSite <new antenna height value>\n'
        'Example:\n'
        'ant marmolada 18\n'
        '      the function change the antenna height to 18m in marmolada data site.\n'
        ),
    "list": 
        (
        'list (i): displays the sites created by the user'
        'Use:\n'
        'list\n'
        'Displays the sites currently created and the data in them:\n'
        'marmolada           46.434022     11.861450       2m\n'
        'remote2             42.972000     13.257400       2m\n'
        'etioga             -16.146100     11.157800       2m\n'
        'boubaque           -15.833400     11.300700       2m\n'
        'sitechk1            45.708964     13.717670      12m\n'
        'sitechk2            45.704283     13.719938      13m\n'        
        ),
    "del": 
        (
        'del (d): delete a site created by the user\n'
        'Use:\n'
        'del DataSite\n'
        'Example:\n'
        'del sitechk1\n'
        '      the function delete the sitechk11 data site.\n'
        ),
    "cnv":
        (
        'cnv (v): dimensional conversion command.\n'
        'Use:\n'
        'cnv <value> <units> <result units>\n'
        'Conversions implemented:\n'
        'cnv value mw dbm        : convert value from mW to dBm\n'
        'cnv value dbm mw        : convert value from dBm to mW\n'
        'cnv value khz m         : convert freq. value in KHz to wavelenght in m\n'
        'cnv value mhz m         : convert freq. value in MHz to wavelenght in m\n'
        'cnv value mhz mm        : convert freq. value in MHz to wavelenght in mm\n'
        'cnv value khz m         : convert freq. value in kHz to wavelength in m\n'
        'cnv value mhz m         : convert freq. value in MHz to wavelength in m\n'
        'cnv value mhz mm        : convert freq. value in MHz to wavelength in mm\n'
        'cnv value uv mw         : convert value in microvolts on 50 ohm to mW\n'
        'cnv value uv dbm        : convert value in microvolts on 50 ohm to dBm\n'
        'cnv value m mhz         : convert wavelength value in m to freq. in MHz\n'
        'cnv value cm ghz        : convert wavelength value in cm to freq. in GHz\n'
        'cnv value pwrr db       : convert power ratio to dB\n'
        'cnv value db pwrr       : convert dB to power ratio\n'
        'cnv value dbd dbi       : convert dBd (dB with respect to a half wavelength dipole antenna) to dBi (dB over isotropic antenna)\n'
        'cnv d:m:s[nswe] dms deg : convert lat lon degrees:minutes:seconds to decimal degrees\n'
        'cnv dd deg dms          : convert decimal degrees to degrees:minutes:seconds format\n'
        'example:\n'
        'cnv 30 dbm mw\n'
        'result:\n'
        '30 dbm = 1000.0 mw\n'
        )
    }

# -----------------------------------------------------
# floating functions

# convert ',' separator to '.'
def us_decimal_sep(strnum):
    ris = strnum.replace(',', '.')
    return ris

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# -----------------------------------------------------
def hlp(self, key):
    if key in hlp_dict:
        yield from self.sender.sendMessage(key + '\n')
        yield from self.sender.sendMessage(hlp_dict[key] + '\n')

# -----------------------------------------------------
# check the command
def check_cmd(command, full, abbr):
    full2='/'+full
    abbr2='/'+abbr
    if command == full or command == abbr:
        return True
    if command == full2 or command == abbr2:
        return True
    return False        
        
# -----------------------------------------------------
# create a directory from filename path, if not exist
def mkdir_p(filename):
    try:
        folder=os.path.dirname(filename)  
        if not os.path.exists(folder):  
            os.makedirs(folder)
        return True
    except:
        return False        
        
# -----------------------------------------------------
# check if file exist
def ChkFileExist(filename):
    if os.path.isfile(filename) and os.access(filename, os.R_OK):
        # File exists and is readable
        return True
    else:
        # Either file is missing or is not readable
        return False

# -----------------------------------------------------
# remove file
def silentremove(filename):
    with contextlib.suppress(FileNotFoundError):
        os.remove(filename)
        
# -----------------------------------------------------
# list of files in directory with extension
def ListOfFiles(dir, filter, flag_basename):
    # get the full path with file filter
    fullpath = dir + '/' + filter
    if flag_basename == True:
        # get only basename
        names = [os.path.basename(x) for x in glob.glob(fullpath)]
    else:
        names = [x for x in glob.glob(fullpath)]
    
    return names

# -----------------------------------------------------
def readTextFile(filename):
    data = ""
    if os.path.isfile(filename) and os.access(filename, os.R_OK):
        with open(filename, 'rt') as myfile:
            data=myfile.read()
            # data=data.replace('\t', '    ')
            print(data)
    return data
    
# -----------------------------------------------------
def getcfgvalue(filename, defval):
    cfgvalue = defval
    if os.path.isfile(filename) and os.access(filename, os.R_OK):
        # cfg file exists and is readable
        with open(filename, 'r') as f:
            cfgvalue = f.readline()
    return cfgvalue

# -----------------------------------------------------
def setQthFile(dir, id, outQth, info, lat, lon, hAntenna):
    dirUser = dir + '/user/' + str(id) + '/'
    lat = float(lat)
    lon = float(lon)
    outfile = dirUser + outQth + '.qth'
    if lon > 0.0:
        lon = (360.0-lon)
    else:
        lon = -lon
    # add meter measurement units
    mt_antenna =  hAntenna + 'm'
    # Write a file
    out_file = open(outfile, 'wt')
    print(info, file=out_file)
    print(str(lat), file=out_file)
    print(str(lon), file=out_file)
    print(mt_antenna, file=out_file)
    out_file.flush()
    out_file.close()
         
# -----------------------------------------------------
def setPos2Qth(dir, id, outQth, info, hAntenna):
    # read data
    dirUser = dir + '/user/' + str(id) + '/'
    # read earth, earth radius multiplier (float)
    filename = dirUser + 'location.txt'
    if os.path.isfile(filename) and os.access(filename, os.R_OK):
        # cfg file exists and is readable
        with open(filename, 'r') as f:
            lat = f.readline()
            lon = f.readline()
            f.close()
        setQthFile(dir, id, outQth, info, lat, lon, hAntenna)

# -----------------------------------------------------
def setTxRwPowFile(dir, id, outPow, TxPw, TxCl, TxAg, RxAg, RxCl, RxSe):
    dirUser = dir + '/user/' + str(id) + '/'
    outfile = dirUser + outPow + '.txt'
    # Write a file
    out_file = open(outfile, 'wt')
    print(str(TxPw), file=out_file)
    print(str(TxCl), file=out_file)
    print(str(TxAg), file=out_file) 
    print(str(RxAg), file=out_file) 
    print(str(RxCl), file=out_file) 
    print(str(RxSe), file=out_file)
    out_file.flush()
    out_file.close()
        
# -----------------------------------------------------
# return the file name removing path and extension
def file_name(filename):
    # filename without path
    base = os.path.basename(filename)
    fname = os.path.splitext(base)[0]
    return fname

# -----------------------------------------------------
# return the values stored in qth file
def DecodeQth(filename):
    qthpar = str()          # empty string
    if os.path.isfile(filename) and os.access(filename, os.R_OK):
        # cfg file exists and is readable
        with open(filename, 'r') as f:
            note = f.readline()
            lat = f.readline()
            lat = float(lat)
            lon = f.readline()
            lon = float(lon)
            if (lon >= 0) and (lon < 180):
                lon = -lon
            elif (lon >= 180) and (lon <= 360):
                lon = (360.0-lon)
            else:
                lon = 0.0
            ant = f.readline().rstrip()
            f.close()
            # filename without path
            base = os.path.basename(filename)
            fname = os.path.splitext(base)[0]
            # create string qthpar
            # the float values has 6 decimal places
            qthpar = fname.ljust(15)    + ' '
            qthpar = qthpar + "{0:.6f}".format(lat).rjust(13) + ' ' 
            qthpar = qthpar + "{0:.6f}".format(lon).rjust(13) + ' '
            qthpar = qthpar + ant.rjust(8)
    # print(qthpar)
    return qthpar;

# -----------------------------------------------------
# return the values stored in qth file
def ModifyQthHeight(filename, hAntenna):
    # add meter measurement units
    mt_antenna =  hAntenna + 'm'
    if os.path.isfile(filename) and os.access(filename, os.R_OK):
        # cfg file exists and is readable
        with open(filename, 'r') as f:
            info = f.readline().rstrip()
            lat = f.readline().rstrip()
            lon = f.readline().rstrip()
            f.close()
            # Write a file
            out_file = open(filename, 'wt')
            print(info, file=out_file)
            print(str(lat), file=out_file)
            print(str(lon), file=out_file)
            print(mt_antenna, file=out_file)
            out_file.flush()
            out_file.close()
    
# -----------------------------------------------------
def cmdRfProbe(dir, id, txqth, rxqth, outimg):
    dirUser = dir + '/user/' + str(id) + '/'
    # read earth, earth radius multiplier (float)
    filecfg = dirUser + 'earth.cfg'
    mkdir_p(filecfg)                    # if not exist, create dir that contain file
    earth = float( getcfgvalue(filecfg, 1.3333) )
    # read freq, frequency (MHz) for zone calculations (float)
    filecfg = dirUser + 'freq.cfg'
    freq = float( getcfgvalue(filecfg, 5800.0) )
    # read perc, Fresnel zone clearance percentage
    filecfg = dirUser + 'perc.cfg'
    perc = float( getcfgvalue(filecfg, 60.0) )

    # path relative to the rfprobe path
    rp_qthtr_qth='user/' + str(id) + '/' + txqth + '.qth'     # relative path qth transmitter
    rp_qthrx_qth='user/' + str(id) + '/' + rxqth + '.qth'     # relative path qth receiver
    rp_out_png='user/' + str(id) + '/' + outimg + '.png'      # relative path output png
    
    # set command:
    # fullpath_rfprobe -t rp_qthtr_qth -r rp_qthrx_qth -m earth -d maps -metric -gpsav -p -e -f $8 -fz $9 -h $rp_out_png

    # fullpath_rfprobe
    cmd = dir + '/' + 'rfprobe '
    # -t $rp_qthtr_qth
    cmd = cmd + '-t ' + rp_qthtr_qth + ' '
    # -r $rp_qthrx_qth
    cmd = cmd + '-r ' + rp_qthrx_qth + ' '
    # -m earth -d maps -metric -gpsav -p -e 
    cmd = cmd + '-m ' + str(earth) + ' -d maps -metric -gpsav -p -e '
    # -f freq
    cmd = cmd + '-f ' + str(freq) + ' '
    # -fz perc
    cmd = cmd + '-fz ' + str(perc) + ' '
    # -h $rp_out_png
    cmd = cmd + '-H ' + rp_out_png
    
    return cmd
    
# -----------------------------------------------------
def cmdRfPower(dir, id, txqth, rxqth, outimg):
    dirUser = dir + '/user/' + str(id) + '/'
    # read earth, earth radius multiplier (float)
    filecfg = dirUser + 'earth.cfg'
    mkdir_p(filecfg)                    # if not exist, create dir that contain file
    earth = float( getcfgvalue(filecfg, 1.3333) )
    # read freq, frequency (MHz) for zone calculations (float)
    filecfg = dirUser + 'freq.cfg'
    freq = float( getcfgvalue(filecfg, 5800.0) )
    # read perc, Fresnel zone clearance percentage
    filecfg = dirUser + 'perc.cfg'
    perc = float( getcfgvalue(filecfg, 60.0) )

    # path relative to the rfprobe path
    rp_qthtr_qth='user/' + str(id) + '/' + txqth + '.qth'     # relative path qth transmitter
    rp_qthrx_qth='user/' + str(id) + '/' + rxqth + '.qth'     # relative path qth receiver
    # rp_out ='user/' + str(id) + '/' + outimg + '.png'           # relative path output
    rp_out ='user/' + str(id) + '/' + outimg + '.txt'         # relative path output
    
    # set command:
    # fullpath_rfprobe -t rp_qthtr_qth -r rp_qthrx_qth -m earth -d maps -metric -gpsav -p -e -f $8 -fz $9 -h $rp_out_png

    # fullpath_rfprobe
    cmd = dir + '/' + 'rfprobe '
    # -t $rp_qthtr_qth
    cmd = cmd + '-t ' + rp_qthtr_qth + ' '
    # -r $rp_qthrx_qth
    cmd = cmd + '-r ' + rp_qthrx_qth + ' '
    # -m earth -d maps -metric -gpsav -p -e 
    cmd = cmd + '-m ' + str(earth) + ' -d maps -metric -gpsav -p -e '
    # -f freq
    cmd = cmd + '-f ' + str(freq) + ' '
    # -fz perc
    cmd = cmd + '-fz ' + str(perc) + ' '
    # -h $rp_out_png
    cmd = cmd + '-pw ' + rp_out
    
    return cmd
    
# -----------------------------------------------------

try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract

class SplatBot(telepot.helper.ChatHandler):
    # ==========================================================
    def __init__(self, seed_tuple, timeout):
        super(SplatBot, self).__init__(seed_tuple, timeout)
        self._lang = 'eng'

    # ==========================================================
    # aux functions
    #
    # private function to set config data
    def set_cfg(self, dir, id, cfgvar, strvalue):
        fileName = cfgvar
        cfgFile = dir + '/user/' + str(id) + '/' + fileName + '.cfg'
        mkdir_p(cfgFile)                    # if not exist, create dir that contain file
        yield from self.sender.sendMessage(cfgFile)
        # yield from self.sender.sendMessage('sono qui')
        # get value
        value = (strvalue);
        value = float(value)
        # Write the cfg file
        out_file = open(cfgFile, 'wt')
        print(str(value), file=out_file)
        out_file.flush()
        out_file.close()
        
    # ==========================================================
    @asyncio.coroutine
    def on_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        #------------------------------------------------
        dirname = os.path.dirname(os.path.abspath(__file__))
        #------------------------------------------------
        global flag_SetPos

        if flag_SetPos == True:
            # original enabled.
            # flag_SetPos = False
            # modify 12/07
            # the flag_SetPos has moved inside test
            if content_type == 'text':
                yield from self.sender.sendMessage(msg['text'].strip().lower())
                commands = msg['text'].strip().lower().split()
                # check n. parameters:
                nCmdFields = len(commands)
                if nCmdFields < 2:
                    yield from self.sender.sendMessage('Wrong parameters. To create the site data file, enter:\n<name> <antenna height>')
                    return;
                # check antenna height
                hAntenna = us_decimal_sep(commands[1]);
                if is_number(hAntenna) == False:
                    msg = 'the antenna height is not correct: ' + hAntenna + '.\n'
                    msg = msg + 'To create the site data file, enter:\n<name> <antenna height>'
                    yield from self.sender.sendMessage( msg )
                    return;
                value = float(hAntenna)
                if (value<0.0) or (value>300.0):
                    msg = 'Invalid antenna height: ' + str(value) + '.\nHeight must be greater than 0 and  should be less than 300m.\n'
                    msg = msg + 'To create the site data file, enter:\n<name> <antenna height>'
                    yield from self.sender.sendMessage( msg )
                    return;
                
                # modify 12/07 flag_SetPos moved here
                flag_SetPos = False
                yield from self.sender.sendMessage('Values inserted: [' + commands[0] + '][' + commands[1] + ']')
                setPos2Qth(dirname, chat_id, commands[0] , commands[0], commands[1])
                yield from self.sender.sendMessage('Site file ' + commands[0] + ' created')
            
            else:
                # command different to text
                flag_SetPos = False
            
            return;
        
        if content_type == 'location':
            # ------------------------------------------------------
            # content_type location
            #
            # send the user location(only smartphones
            # see: https://wptele.ga/docs/get-use-user-location/
            # format:
            # "{\"update_id\":2129@@@@@,\n\"message\":
            # {\"message_id\":14@@,\"from\":{\"id\":63480@@@,
            # \"first_name\":\"Marco\",\"last_name\":\"M\",
            # \"username\":\"Mil@@@\"},\"chat\":{\"id\":63480@@@,
            # \"first_name\":\"Marco\",\"last_name\":\"M\",\"username\":\"Mil@@@\",
            # \"type\":\"private\"},\"date\":1452263@@@,\"location\":
            # {\"longitude\":10.50,\"latitude\":50.8080}}}"
            #
            yield from self.sender.sendMessage('Send location')
            # msg['location'] oK funziona!!!
            # format: {"latitude":28.665689,"longitude":11.825371}
            # see: http://xahlee.info/perl-python/python_json_tutorial.html
            # from Python Object to JSON
            jstring = json.dumps(msg['location'])
            # yield from self.sender.sendMessage('Position inserted: ' + msg['location'])
            yield from self.sender.sendMessage('Position inserted: ' + jstring)
            outfile = dirname + '/user/' + str(chat_id) + '/' + 'location.txt'
            out_file = open(outfile, 'wt')
            # print(jstring, file=out_file)
            loc_dict = json.loads(jstring)
            global lon
            global lat
            # rint(len(loc_dict), file=out_file)
            print(loc_dict['latitude'], file=out_file)
            print(loc_dict['longitude'], file=out_file)
            out_file.flush()
            out_file.close()
            
            flag_SetPos = True
            yield from self.sender.sendMessage('To create the site data file, enter:\n<name> <antenna height>')
            return
        
        elif content_type == 'photo':
            # ------------------------------------------------------
            # content_type photo
            return;                 # command disabled
            
            # command photo:
            yield from self.sender.sendMessage(msg['photo'])
            photo_id = msg['photo'][-1:][0]['file_id']
            width = msg['photo'][-1:][0]['width']
            height = msg['photo'][-1:][0]['height']
            to_save = './downloads/' + photo_id
            yield from self.sender.sendMessage('Trying to download the file({}*{}) you sent...'.format(width, height))
            yield from bot.download_file(photo_id, to_save)
            yield from self.sender.sendMessage('Download complete. Start OCR...')
            try:
                text = pytesseract.image_to_string(Image.open(to_save), lang=self._lang)
            except:
                yield from self.sender.sendMessage('Failed to process OCR')
                traceback.print_exc()
                os.remove(to_save)
                return;

            os.remove(to_save)
            yield from self.sender.sendMessage('Done. Removed the temp file. Here is the result:')
            yield from self.sender.sendMessage(text)
            return

        elif content_type == 'text':
            # ------------------------------------------------------
            # content_type text
            
            yield from self.sender.sendMessage(msg['text'].strip().lower())
            
            commands = msg['text'].strip().lower().split()
            nCmdFields = len(commands)

           #------------------------------------------------
            # convert commands[0] to lower case
            # str = commands[0].lower()
            # commands[0] = str

            if check_cmd(commands[0], 'hlp', 'h') == True:
                yield from self.sender.sendMessage('This bot is an opensource tool for the electromagnetic spectrum analysis of Terrain, loss, and RF Signal Propagation.')
                yield from self.sender.sendMessage('List of bot commands (sorted alphabetically):')
                # help command
                s = sorted(hlp_dict.keys())
                # for key in iter(hlp_dict.keys()):
                hlp = ''
                for key in iter(s):
                    hlp = hlp + key + '\n'
                    hlp = hlp + hlp_dict[key] + '\n'
                    if (len(hlp)>2048):
                        yield from self.sender.sendMessage(hlp)
                        hlp = ''
                   # yield from self.sender.sendMessage(key + '\n')
                   # yield from self.sender.sendMessage(hlp_dict[key] + '\n')
                # yield from self.sender.sendMessage('----------------\n')
                hlp = hlp + '\n'
                yield from self.sender.sendMessage(hlp + '\n')
                # for key in hlp_dict:
                #     print(key + '\n\n')
                #     print(hlp_dict[key] + '\n\n')
                #     yield from self.sender.sendMessage(key + '\n')
                #     yield from self.sender.sendMessage(hlp_dict[key] + '\n')
                return;
                
            elif check_cmd(commands[0], 'site', 's') == True:
                # modify 27/07:
                # if the user don't insert antenna height, use a default of 30m
                # n. full parameters. 5
                # site name lat lon height
                # original if nCmdFields < 5:
                # modify 27/07
                if nCmdFields < 4:
                    yield from self.sender.sendMessage(hlp_dict['site'] + '\n')
                    return;
                    
                # generate qth file
                # filename
                outQth = dirname + '/user/' + str(chat_id) + '/' + commands[1] + '.qth'
                mkdir_p(outQth)                 # if not exist, create dir that contain file
                # convert lan, lon
                
                # latitude
                lat = us_decimal_sep(commands[2]);
                if is_number(lat) == False:
                    msg = 'Invalid latitude value: ' + str(lat) + '.\nLatitude must be within -90 and +90 degrees'
                    print(msg)
                    yield from self.sender.sendMessage( msg )
                    return;
                    
                lat = float(lat)
                if (lat<-90.0) or (lat>90.0):
                    msg = 'Invalid latitude value: ' + str(lat) + '.\nLatitude must be within -90 and +90 degrees'
                    print(msg)
                    yield from self.sender.sendMessage( msg )
                    return;
                
                # longitude
                lon = us_decimal_sep(commands[3]);
                if is_number(lon) == False:
                    msg = 'Invalid longitude value: ' + str(lon) + '.\nLongitude must be within -180 and +180 degrees'
                    print(msg)
                    yield from self.sender.sendMessage( msg )
                    return;
                    
                lon = float(lon)
                if (lon<-180.0) or (lon>180.0):
                    msg = 'Invalid longitude value: ' + str(lon) + '.\nLongitude must be within -180 and +180 degrees'
                    print(msg)
                    yield from self.sender.sendMessage( msg )
                    return;
                
                # save data in qth
                if lon > 0.0:
                    lon = (360.0-lon)
                else:
                    lon = -lon
                
                # antenna height
                # modify 27/07
                if nCmdFields >= 5:
                    # use user antenna value
                    hAntenna = us_decimal_sep(commands[4]);
                else:
                    # use antenna default
                    hAntenna = '3'
                    
                if is_number(hAntenna) == False:
                    msg = 'the antenna height is not correct: ' + hAntenna
                    print(msg)
                    yield from self.sender.sendMessage( msg )
                    return;
                value = float(hAntenna)
                if (value<0.0) or (value>300.0):
                    msg = 'Invalid antenna height: ' + str(value) + '.\nHeight must be greater than 0 and  should be less than 300m'
                    print(msg)
                    yield from self.sender.sendMessage( msg )
                    return;
                
                # add meter measurement units
                hAntenna =  hAntenna + 'm'
                # set first row of qth file.
                # If there are no other parameters, the first row is the qth file name
                # yield from self.sender.sendMessage(str(nCmdFields))
                
                msg = ''
                if nCmdFields >= 6:
                    msg = commands[5]
                    for num in range(6,nCmdFields):
                        msg = msg + ' ' + commands[num]
                else:
                    msg = commands[1]
                
                cmd = str(chat_id) + ' ' + msg  + ' ' + str(lat) + ' ' + str(lon)
                # include full path of outimg

                # Write a file
                out_file = open(outQth, 'wt')
                print(msg, file=out_file)
                print(str(lat), file=out_file)
                print(str(lon), file=out_file)
                print(str(hAntenna), file=out_file)
                out_file.flush()
                out_file.close()
                
                yield from self.sender.sendMessage(cmd_dict['site'] + ' ' +commands[1] + ' created')
                return; 
            
            elif check_cmd(commands[0], 'list', 'l') == True:
                dirUser = dirname + '/user/' + str(chat_id)
                names = ListOfFiles(dirUser, '*.qth', False)
                # from list get the string of names
                # strNames = "\n".join(str(x) for x in names)
                # strNames = "\n".join(file_name(str(x)) for x in names)
                # yield from self.sender.sendMessage(strNames)
                #-------------------
                # original:
                # strContents = "\n".join(DecodeQth(str(x)) for x in names)
                # yield from self.sender.sendMessage(strContents)
                # new 09/08
                strContents=''
                for x in names:
                    strContents = strContents + DecodeQth(str(x)) + '\n'
                    if (len(strContents)>2048):
                        yield from self.sender.sendMessage(strContents)
                        strContents = ''
                yield from self.sender.sendMessage(strContents)
                return;
                
            elif check_cmd(commands[0], 'del', 'd') == True:
                if nCmdFields < 2:
                    yield from self.sender.sendMessage(hlp_dict['del'] + '\n')
                    return;
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[1] + '.qth'
                silentremove(filename)
                yield from self.sender.sendMessage('Data file ' + commands[1] + ' removed')
                return;
                
            elif check_cmd(commands[0], 'ant', 'a') == True:
                if nCmdFields < 2:
                    yield from self.sender.sendMessage(hlp_dict['ant'] + '\n')
                    return;
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[1] + '.qth'
                ModifyQthHeight(filename, commands[2])
                yield from self.sender.sendMessage('In file ' + commands[1] + ' antenna height is ' + commands[2] + 'm')
                return;
                
            elif check_cmd(commands[0], 'earth', 'k') == True:
            # Ermanno request: 'e' to 'k'
            # if commands[0] == '/earth' or commands[0] == 'earth':
                if nCmdFields < 2:
                    yield from self.sender.sendMessage(hlp_dict['earth'] + '\n')
                    return;
                    
                # earth radius multiplier (float)
                ## dont work!!!!!
                ## self.set_cfg(dirname, chat_id, 'earth', commands[1])
                # filename
                fileName = 'earth'
                cfgFile = dirname + '/user/' + str(chat_id) + '/' + fileName + '.cfg'
                mkdir_p(cfgFile)                    # if not exist, create dir that contain file
                # yield from self.sender.sendMessage(cfgFile)
                # get value
                value = (commands[1]);
                value = float(value)
                # Write the cfg file
                out_file = open(cfgFile, 'wt')
                print(str(value), file=out_file)
                out_file.flush()
                out_file.close()
                
                yield from self.sender.sendMessage('Value of ' + cmd_dict['earth'] + ' set to ' + str(value) )
                return;

            elif check_cmd(commands[0], 'freq', 'f') == True:
                if nCmdFields < 2:
                    yield from self.sender.sendMessage(hlp_dict['freq'] + '\n')
                    return;
                    
                # frequency (MHz) for zone calculations (float)
                # filename
                fileName = 'freq'
                cfgFile = dirname + '/user/' + str(chat_id) + '/' + fileName + '.cfg'
                mkdir_p(cfgFile)                    # if not exist, create dir that contain file
                # yield from self.sender.sendMessage(cfgFile)
                # get value
                value = (commands[1]);
                value = float(value)
                # Write the cfg file
                out_file = open(cfgFile, 'wt')
                print(str(value), file=out_file)
                out_file.flush()
                out_file.close()
                
                yield from self.sender.sendMessage('Value of ' + cmd_dict['freq'] + ' set to ' + str(value) )
                return;

            elif check_cmd(commands[0], 'perc', 'p') == True:
                if nCmdFields < 2:
                    yield from self.sender.sendMessage(hlp_dict['perc'] + '\n')
                    return;
                    
                # Fresnel zone clearance percentage
                # filename
                fileName = 'perc'
                cfgFile = dirname + '/user/' + str(chat_id) + '/' + fileName + '.cfg'
                mkdir_p(cfgFile)                    # if not exist, create dir that contain file
                # get value
                value = (commands[1]);
                value = float(value)
                # Write the cfg file
                out_file = open(cfgFile, 'wt')
                print(str(value), file=out_file)
                out_file.flush()
                out_file.close()
                
                yield from self.sender.sendMessage('Value of ' + cmd_dict['perc'] + ' set to ' + str(value) )
                return;
                
            elif check_cmd(commands[0], 'calc', 'c') == True: 
                # check if the two files .spl was defined
                if nCmdFields < 3:
                    yield from self.sender.sendMessage(hlp_dict['calc'] + '\n')
                    return;
                
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[1] + '.qth'
                if not ChkFileExist(filename):
                    yield from self.sender.sendMessage('Parameter error: file ' + commands[1] + ' does not exist !!!')
                    return;
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[2] + '.qth'
                if not ChkFileExist(filename):
                    yield from self.sender.sendMessage('Parameter error: file ' + commands[2] + ' does not exist !!!')
                    return;
                #
                outfile=commands[1] + '_' + commands[2]
                # original cmdspl=cmdRfProbe(dirname, chat_id, commands[2], commands[1], outfile)
                # mr 07: inverted graph in rfprobe tool
                cmdspl=cmdRfProbe(dirname, chat_id, commands[1], commands[2], outfile)
                
                os.system(cmdspl)
                
                # show image
                outImg= dirname + '/user/' + str(chat_id) + '/' + outfile + '.png'
                mkdir_p(outImg)                 # if not exist, create dir that contain file
                # Send a file that is stored locally.
                # check for debug: insert full path
                # outImg='/home/marco/Documenti/rfprobe/' + commands[10] + '.png'
                f = open(outImg, 'rb')  # image file on local disk
                yield from bot.sendPhoto(chat_id, f)
                yield from self.sender.sendMessage("Results")
                
                # show the reduced report
                ReportRed = dirname + '/user/' + str(chat_id) + '/' + outfile + '_red.txt'
                data = readTextFile(ReportRed)
                # divide report in tokens 
                reprt = data.split("\nObstructions:\n")
                for curr_piece in reprt:
                    if len(curr_piece) > 0:
                        yield from self.sender.sendMessage(curr_piece)
                
                return;

            elif check_cmd(commands[0], 'cnv', 'v') == True:
            # conversion command
                if nCmdFields < 4:
                    yield from self.sender.sendMessage(hlp_dict['cnv'] + '\n')
                    return;
                # check the units
                listUnit=['deg', 'dms', 'mw', 'pwrr', 'db', 'dbd', 'dbi', 'dbm', 'khz', 'mhz', 'ghz', 'm' , 'mm', 'cm', 'uv']              
                srcUnit = (commands[2])
                if (srcUnit in listUnit) == False:
                    msg = 'The unit ' + srcUnit + ' is not correct.\n'
                    msg = msg + hlp_dict['cnv'] + '\n'
                    yield from self.sender.sendMessage( msg )
                    return;
                dstUnit = (commands[3])
                if (dstUnit in listUnit) == False:
                    msg = 'The unit ' + dstUnit + ' is not correct.\n'
                    msg = msg + hlp_dict['cnv'] + '\n'
                    yield from self.sender.sendMessage( msg )
                    return;
                cmd = srcUnit + dstUnit
            
                nDigits = 2         # n. digits after comma
                # check if the value is numeric
                if cmd != 'dmsdeg':
                    # the conversion is different from degrees,first,seconds and degrees unit
                    # check input value
                    strVal = us_decimal_sep(commands[1]);
                    if is_number(strVal) == False:
                        msg = 'The value to convert is not correct: ' + strVal + '.\n'
                        msg = msg + hlp_dict['cnv'] + '\n'
                        yield from self.sender.sendMessage( msg )
                        return;
                    value = float(strVal)
                else:
                    strVal = commands[1];
                    
                SpeedLight=299792458        # m/s
                errType = -1
                # degrees first seconds <-> degrees
                if (cmd=='dmsdeg'):
                    # degrees first seconds --> degrees
                    nDigits = 5         # n. digits after comma result
                    # Separate on ':'.
                    strDfs = strVal.split(":")
                    result=0.0
                    numStr=0
                    # Loop for each element.
                    sign=1
                    for elementDfs in strDfs:
                        if (numStr==0):
                            # degrees
                            result=float(elementDfs)
                            if (result<0.0):
                                result = -result
                                sign = -1
                            numStr = numStr + 1
                        elif (numStr==1):
                            # first
                            value=float(elementDfs)
                            value=value / 60.0
                            result=result + value
                            numStr = numStr + 1
                        elif (numStr==2):
                            # seconds
                            direction = elementDfs[-1].lower()      # get last char in lower case
                            if (direction!='s') and (direction!='w') and (direction!='n') and (direction!='e'):
                                seconds = elementDfs
                                # msg = 'The direction of coordinate ' + strVal + ' is not correct.\n'
                                # msg = msg + 'Correct directions are: N, S, E, W\n'
                                # yield from self.sender.sendMessage( msg )
                                # return;
                            else:
                                seconds = elementDfs[:-1]           # get string without last char
                            value = float(seconds)
                            value = value / 3600.0
                            result = result + value
                            result = sign * result
                            if (direction=='s') or (direction=='w'):
                                result = -result
                            numStr = numStr + 1
                elif (cmd=='degdms'):
                    # degrees --> degrees first seconds
                    if (value < 0.0):
                        sign = '-'
                        value = -value
                    else:
                        sign = '+'
                    # divide number in degrees and dec part
                    decimal, intVal = math.modf(value)
                    degrees = int(intVal)
                    value = decimal * 60.0
                    # divide number in first and dec part
                    decimal, intVal = math.modf(value)
                    first = int(intVal)
                    seconds = decimal * 60.0
                    strResult = sign + format(degrees, '02d') + ' ' + format(first, '02d') + '\' ' + str(seconds) + '"'
                # milliwatt <-> dbm
                elif (cmd=='mwdbm'):
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  10.0 * math.log10(value)
                elif (cmd=='dbmmw'): 
                    result =  math.pow(10.0, (value/10.0))
                # wavelen <-> freq
                elif (cmd=='mkhz') : 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight * 1.0e-3)/(value)
                elif (cmd=='mmhz') : 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight * 1.0e-6)/(value)
                elif (cmd=='mmkhz'): 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight * 1)/(value)
                elif (cmd=='cmghz'): 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight * 1.0e-7)/(value)
                elif (cmd=='mmmhz'): 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight * 1.0e-3)/(value)
                elif (cmd=='khzm') : 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight)/(1.0e3 * value)
                elif (cmd=='mhzm') : 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight)/(1.0e6 * value)
                elif (cmd=='khzmm'): 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight)/(1 * value)
                elif (cmd=='mhzmm'): 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight)/(1.0e-3 * value)
                elif (cmd=='ghzcm') : 
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  (SpeedLight)/(1.0e-7 * value)
                # dbd <-> dbi
                elif (cmd=='dbidbd'): 
                    result = value - 2.15
                elif (cmd=='dbddbi'): 
                    result = value + 2.15
                # pwrr <-> db
                elif (cmd=='pwrrdb'):
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  10.0 * math.log10(value)
                elif (cmd=='dbpwrr'): 
                    result =  math.pow(10.0, (value/10.0))
                # uv <-> dBm for 50Ohm impedance
                elif (cmd=='uvdbm'):
                    if (value <= 0.0):
                        errType = 0         # value <= 0
                    else:
                        result =  10.0 * math.log10(value * value * 1.0e-9 / 50)
                # microvolt <-> milliwatt for 50Ohm impedance
                elif (cmd=='uvmw') : 
                    result =  (value * value * 1.0e-9 / 50)
                else:
                    errType = 1
                    result = 'the conversion between units can not be performed'

                # print results
                if (cmd=='degdms'):
                    # for deg -> dms conversion
                    msg = strVal + ' ' + srcUnit + ' = ' + strResult + ' ' + dstUnit
                    
                else:
                    # for all other conversions
                    if (errType<0):
                        # result = round(result, nDigits)
                        if(cmd=='dmsdeg'):
                            result = round(result, 6)
                            strResult = str(result)
                        else:
                            chk = math.fabs(result)
                            if (chk>0.1):
                                result = round(result, 2)
                                strResult = str(result)
                            else:   
                                # use scientific notation
                                strResult = "{0:.2e}".format(result)
                        msg = strVal + ' ' + srcUnit + ' = ' + strResult + ' ' + dstUnit
                    elif (errType==0):
                        msg = 'The value ' + str(value) + ' ' + 'is lower or below 0 and cannot be converted'
                    else:
                        msg = 'the conversion between ' + srcUnit + ' and ' + dstUnit + ' units can not be performed'

                yield from self.sender.sendMessage(msg)
                return;

            elif check_cmd(commands[0], 'rep', 'r') == True:
                # analysis with full report
                if nCmdFields < 3:
                    yield from self.sender.sendMessage(hlp_dict['rep'] + '\n')
                    return;
                # check if the two files .spl was defined
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[1] + '.qth'
                if not ChkFileExist(filename):
                    yield from self.sender.sendMessage('Error: site file ' + commands[1] + ' not exist !!!')
                    return;
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[2] + '.qth'
                if not ChkFileExist(filename):
                    yield from self.sender.sendMessage('Error: site file ' + commands[2] + ' not exist !!!')
                    return;
                #
                outfile=commands[1] + '_' + commands[2]
                # original cmdspl=cmdRfProbe(dirname, chat_id, commands[2], commands[1], outfile)
                # mr 07: inverted graph in rfprobe tool
                cmdspl=cmdRfProbe(dirname, chat_id, commands[1], commands[2], outfile)
                
                os.system(cmdspl)
                
                # show image
                outImg= dirname + '/user/' + str(chat_id) + '/' + outfile + '.png'
                mkdir_p(outImg)                 # if not exist, create dir that contain file
                # Send a file that is stored locally.
                f = open(outImg, 'rb')  # image file on local disk
                yield from bot.sendPhoto(chat_id, f)
                yield from self.sender.sendMessage("Results")
                
                # show the full report
                ReportFull = dirname + '/user/' + str(chat_id) + '/' + outfile + '.txt'
                data = readTextFile(ReportFull)
                # divide report in tokens 
                reprt = data.split("\nObstructions:\n")
                for curr_piece in reprt:
                    if len(curr_piece) > 0:
                        yield from self.sender.sendMessage(curr_piece)
                
                return;
                
            elif check_cmd(commands[0], 'pow', 'w') == True:
                # power graph
                if nCmdFields < 9:
                    yield from self.sender.sendMessage(hlp_dict['pow'] + '\n')
                    return;
                # check if the two files .spl was defined
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[1] + '.qth'
                if not ChkFileExist(filename):
                    yield from self.sender.sendMessage('Error: site file ' + commands[1] + ' not exist !!!')
                    return;
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[2] + '.qth'
                if not ChkFileExist(filename):
                    yield from self.sender.sendMessage('Error: site file ' + commands[2] + ' not exist !!!')
                    return;
                #
                outfile=commands[1] + '_' + commands[2] + '_pow'
                # ------------------------------
                # get values
                TxPw = (commands[3]);
                TxPw = float(TxPw)
                # yield from self.sender.sendMessage('TxPw ' + str(TxPw))
                TxCl = (commands[4]);
                TxCl = float(TxCl)
                # modify TxCl 08/11: correct value is <= 0.0
                if (TxCl > 0.0):
                    yield from self.sender.sendMessage('Error: TxCl (transmitter cable loss) value is ' + str(TxCl) + '. It must be <= 0 !!!')
                    return;
                TxAg = (commands[5]);
                TxAg = float(TxAg)
                RxAg = (commands[6]);
                RxAg = float(RxAg)
                RxCl = (commands[7]);
                RxCl = float(RxCl)
                # modify RxCl 08/11: correct value is <= 0.0
                if (RxCl > 0.0):
                    yield from self.sender.sendMessage('Error: RxCl (receiver cable loss) value is ' + str(RxCl) + '. It must be <= 0 !!!')
                    return;
                RxSe = (commands[8]);
                RxSe = float(RxSe)
                # modify RxSe 08/11: correct value is < 0.0
                if (RxSe >= 0.0):
                    yield from self.sender.sendMessage('Error: RxSe (receiver sensitivity) value is ' + str(RxSe) + '. It must be < 0 !!!')
                    return;
                setTxRwPowFile(dirname, chat_id, outfile, TxPw, TxCl, TxAg, RxAg, RxCl, RxSe)
                # ------------------------------    
                cmdspl=cmdRfPower(dirname, chat_id, commands[1], commands[2], outfile)
                # yield from self.sender.sendMessage(cmdspl)
                
                os.system(cmdspl)
                
                # show image
                outImg= dirname + '/user/' + str(chat_id) + '/' + outfile + '.png'
                mkdir_p(outImg)                 # if not exist, create dir that contain file
                # Send a file that is stored locally.
                f = open(outImg, 'rb')  # image file on local disk
                yield from bot.sendPhoto(chat_id, f)
                
                return;


            # ------------------------------------------------------
            # commands disabled: used to test new code
            # ------------------------------------------------------
            #
            elif commands[0] == '/helpchk' or commands[0] == 'helpchk':
                return;         # cmd disabled
                yield from self.sender.sendMessage('command rfprobe (or /rfprobe)') 
                yield from self.sender.sendMessage('  rfprobe $1 $2 $3 $4 $5 $6 $7 $8 $9 $10') 
                yield from self.sender.sendMessage('  where:') 
                yield from self.sender.sendMessage('    $1:  latitude transmitter') 
                yield from self.sender.sendMessage('    $2:  longitude transmitter') 
                yield from self.sender.sendMessage('    $3:  transmitter antenna height (m)') 
                yield from self.sender.sendMessage('    $4:  latitude receiver') 
                yield from self.sender.sendMessage('    $5:  longitude receiver') 
                yield from self.sender.sendMessage('    $6:  receiver antenna height (m)') 
                yield from self.sender.sendMessage('    $7:  earth radius multiplier (float)') 
                yield from self.sender.sendMessage('    $8:  frequency (MHz) for zone calculations (float)') 
                yield from self.sender.sendMessage('    $9:  Fresnel zone clearance percentage') 
                yield from self.sender.sendMessage('    $10: name of png output file') 
                yield from self.sender.sendMessage('  example:') 
                yield from self.sender.sendMessage('  rfprobe 42.888006 11.62498 12 40.8531 9.1749 8 1.333333 5800.000 75 outimg') 
                return;
                
            elif commands[0] == '/chkrfprobe' or commands[0] == 'chkrfprobe':
                return;         # cmd disabled
                yield from self.sender.sendMessage('chat_id=[' + str(chat_id) + ']')
                #
                outImg= dirname + '/user/' + str(chat_id) + '/' + commands[10] + '.png'
                mkdir_p(outImg)                 # if not exist, create dir that contain file
                # outImg= commands[10] + '.png'
                cmd = dirname + '/' + 'spn.sh '
                for num in range(1,nCmdFields):
                    cmd = cmd + ' ' + commands[num]
                # include user id
                cmd = cmd + ' ' + str(chat_id)
                # include full path of outimg
                # cmd = cmd + ' ' + outImg
                yield from self.sender.sendMessage(cmd) 
                os.system(cmd)
                yield from self.sender.sendMessage('...rfprobe analysis executed')
                yield from self.sender.sendMessage('Send image ' + outImg)
                # Send a file that is stored locally.
                # for debug: full path
                f = open(outImg, 'rb')  # image file on local disk
                yield from bot.sendPhoto(chat_id, f)
                yield from self.sender.sendMessage("Results")
                return;

            elif commands[0] == '/get' or commands[0] == 'get':
                return;         # cmd disabled
                f = open(dirname + '/giuseppe.png', 'rb')  # image file on local disk
                yield from bot.sendPhoto(chat_id, f)
                # response = self.sender.sendPhoto(f)
                yield from self.sender.sendMessage("foto inviata")
                return;
                
            elif commands[0] == '/check' or commands[0] == 'check':
                return;         # cmd disabled
                filename = dirname + '/user/' + str(chat_id) + '/' + commands[1]
                mkdir_p(filename)                   # if not exist, create dir that contain file
                yield from self.sender.sendMessage(filename)
                if ChkFileExist(filename):
                    yield from self.sender.sendMessage('file exist')
                else:
                    yield from self.sender.sendMessage('FILE NOT EXIST !!!')
                return;
                
            elif commands[0] == '/pos' or commands[0] == 'pos':
                return;         # cmd disabled
                bot.telegram-location(chat_id, latitude, longitude)
                yield from self.sender.sendMessage(str(latitude) + str(longitude))
                return;
            
            elif commands[0] == '/getlang' or commands[0] == 'getlang':
                return;         # cmd disabled
                yield from self.sender.sendMessage('chat_id=[' + str(chat_id) + ']')
                yield from self.sender.sendMessage(self._lang)
                return;
                
            elif commands[0] == '/setlang' or commands[0] == 'setlang':
                return;         # cmd disabled
                self._lang = commands[1]
                yield from self.sender.sendMessage('current lang setting: %s' % self._lang )
                
            elif commands[0] == '/?' or commands[0] == '?':
                return;         # cmd disabled
                show_keyboard = lst_cmd
                yield from self.sender.sendMessage('Get help!', reply_markup=show_keyboard)
                return;
                
            elif commands[0] == '/hidekbd' or commands[0] == 'hidekbd':
                return;         # cmd disabled
                hide_keyboard = {'hide_keyboard': True}
                yield from self.sender.sendMessage('Hide helps', reply_markup=hide_keyboard)
                return;

            else :
                if flag_SetPos == False:
                    yield from self.sender.sendMessage('Command error!!! Use hlp command to see command list')
                    return;

                
            # ------------------------------------------------------
            # end of commands disabled: used to test new code
            # ------------------------------------------------------
                
# ===========================================================               
# main
# ===========================================================               

# BotRf bot token
TOKEN = '208996750:AAGtHWAMCL-n3JyF6AKLXFYSdQlm7wRXVdk'

bot = telepot.async.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(SplatBot, timeout=60)),
])
loop = asyncio.get_event_loop()

loop.create_task(bot.message_loop())
print('Listening ...')

loop.run_forever()
