#                    __ _          
#    ___ ___  _ __  / _| |_   ___  __
# __/ __/ _ \| '_ \| |_| | | | \ \/ /
# __ (_| (_) | | | |  _| | |_| |>  < 
#   \___\___/|_| |_|_| |_|\__,_/_/\_\
#

import tifffile 
import datetime
import pickle

def logscript(scriptname, logdescription, **kwargs):
    timestamp = datetime.datetime.now() # get current date and time
    log = open('log.yaml','a') # open current log file or write a new one
    log.write('- "' + scriptname + '"\n') # filename of script calling
    log.write('    description : "' + logdescription + '"\n')
    log.write('    date : "'
              + str(timestamp.year) + '-'
              + str(timestamp.month) + '-'
              + str(timestamp.day) + '"\n')
    log.write('    time : "'
              + str(timestamp.hour) + ':'
              + str(timestamp.minute) + ':'
              + str(timestamp.second) + '"\n')
    log.write('    parameters : \n') # iterate through parameters and record
    for key,value in kwargs.items():
        log.write('    - {} : {}\n'.format(key,value))
    log.close()

# Maybe is is better to use the filename with the extension already
def pickledata(dataobject,filename):
    with open(filename + '.pickle', 'wb') as fileobject:
        pickle.dump(dataobject, fileobject, pickle.HIGHEST_PROTOCOL)
    logscript.logscript('pickledata.py','Pickle (serialize) data')

def unpickledata(filename):
    with open(filename, 'rb') as fileobject: 
        dataobject = pickle.load(fileobject) 
    logscript.logscript('unpickledata.py','Unpickle (import serialized) data')
    return(dataobject)

def importtiff(filename): 
    imgarray = tifffile.imread(filename) 
    log = open('log.yaml','a') # assume opening a new log 
    log.write(str(filename) + '\n') 
    log.close() 
    logscript.logscript('importtiff.py','Import tiff into numpy array') 
    return(imgarray)
