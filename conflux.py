#                    __ _          
#    ___ ___  _ __  / _| |_   ___  __
# __/ __/ _ \| '_ \| |_| | | | \ \/ /
# __ (_| (_) | | | |  _| | |_| |>  < 
#   \___\___/|_| |_|_| |_|\__,_/_/\_\
#
# expecting the following file structure for raw data
# 20190116 ((date))
# - run-name
# -- raw-data
# -- metadata
# -- comment
# - run-name-post-initial-processing
# - run-name
# -- raw-data
# -- metadata
# -- comment
# ++ raw-data-channel-split-and-pickled
# ++ log.yaml-file-containing-all-processing-performed-along-with-comments
# ++ subfolder-if-you-want-to-branch-your-processing

import tifffile 
import datetime
import pickle
import json

def logscript(scriptname, logdescription, **kwargs):
    """
    Record the details of analysis script run on data set.

    Keyword arguments:
    scriptname -- name of script run on data set
    logdescription -- brief description of the script run
    **kwargs -- can be populated with variables used in script
    """
    timestamp = datetime.datetime.now()
    # Open current log file or write a new one if it does not exist.
    log = open('log.yaml','a') 
    log.write('- "' + scriptname + '"\n') 
    log.write('    description : "' + logdescription + '"\n')
    log.write('    date : "'
              + str(timestamp.year) + '-'
              + str(timestamp.month) + '-'
              + str(timestamp.day) + '"\n')
    log.write('    time : "'
              + str(timestamp.hour) + ':'
              + str(timestamp.minute) + ':'
              + str(timestamp.second) + '"\n')
    # Iterate through the parameters and record in the log.
    log.write('    parameters : \n')
    for key,value in kwargs.items():
        log.write('    - {} : {}\n'.format(key,value))
    log.close()

def pickledata(dataobject,filename):
    """
    Pickle (serialize) python data object.

    Keyword arguments:
    dataobject -- python object to be serialized
    filename -- name of pickle file to save serialized data
    """
    with open(filename, 'wb') as fileobject:
        pickle.dump(dataobject, fileobject, pickle.HIGHEST_PROTOCOL)
    logscript('pickledata','Pickle (serialize) data.',outputfile = filename)

def unpickledata(filename):
    """Unpickle (import serialized) data."""
    with open(filename, 'rb') as fileobject: 
        dataobject = pickle.load(fileobject) 
    logscript('unpickledata','Unpickle (import serialized) data.',
              inputfile = filename)
    return(dataobject)

def importtiff(filename): 
    """Import a tiff image or image stack as a numpy array."""
    imgarray = tifffile.imread(filename) 
    #log = open('log.yaml','a') # assume opening a new log 
    #log.write(str(filename) + '\n') 
    #log.close() 
    logscript('importtiff','Import tiff into numpy array.',inputfile = filename) 
    return(imgarray)

# def splitchannels(tiffarray):
    # split channels in a tiffarray

def extractmetadata(filename):
    """
    Extract acquisition metadata from text file produced by ImageJ MicroManager
    with an Andor camera.

    Keyword arguments:
    filename -- name of textfile containing metadata
    """
    # Need to add comments import.
    metafile = open(filename,'r')
    metadata = metafile.read() # read metadata as string
    json = json.loads(metadata) # parse metadata string as json
    framekeys = list(json.keys())[1:] # create list of FrameKeys in metadata
    # Record acquisition metadata from the first frame recorded.
    readoutmode = json[framekeys[0]]['Andor-ReadoutMode']['PropVal']
    interval = json[framekeys[0]]['Andor-ActualInterval-ms']['PropVal']
    roi = json[framekeys[0]]['ROI']
    pixeltype = json[framekeys[0]]['Andor-PixelType']['PropVal']
    outputamplifier = json[framekeys[0]]['Andor-Output_Amplifier']['PropVal']
    exposure = json[framekeys[0]]['Exposure-ms']
    preampgain = json[framekeys[0]]['Andor-Pre-Amp-Gain']['PropVal']
    adconvertor = json[framekeys[0]]['Andor-AD_Converter']['PropVal']
    camspecs = json[framekeys[0]]['Andor-Camera']['PropVal'].split()
    gain = json[framekeys[0]]['Andor-Gain']['PropVal']
    binning = json[framekeys[0]]['Binning']
    exposure = json[framekeys[0]]['Andor-Exposure']['PropVal']
    temperature = json[framekeys[0]]['Andor-CCDTemperature']['PropVal']
    # Split camera specifications into  individual variables.
    camtype = camspecs[1]
    cammodel = camspecs[3]
    camserial = camspecs[5]
    # Initialize lists to store the two channel time values.
    channel0, channel1  = [], []
    starttime = json[framekeys[0]]['ElapsedTime-ms']
    # Add normalized times to each channel list.
    for frame in framekeys:
        if json[frame]['ChannelIndex'] == 0:
            channel0.append(json[frame]['ElapsedTime-ms'] - starttime)
        else:
            channel1.append(json[frame]['ElapsedTime-ms'] - starttime)
    # Add metadata to logscript.
    logscript('extractmetadata', 'Extract metadata and frame capture times from
              metadata file produced by MicroManager with an Andor camera.',
              cameratype = camtype,
              cameramodel = cammodel,
              cameraserialnumber = camserial,
              exposure = exposure,
              estimatedframeinterval = interval,
              preamplifiergain = preampgain,
              gain = gain,
              outputamplifier = outputamplifier,
              binning = binning,
              roi = roi,
              temperature = temperature,
              pixeltype = pixeltype,
              readoutmode = readoutmode,
              adconvertor = adconvertor
    # Pickle time series data for each channel.
    if len(channel0) > 0:
        pickledata(channel0,'channel-0_time-series.pickle')
    if len(channel1) > 0:
        pickledata(channel1,'channel-1_time-series.pickle')

# def importdata(datafile,metafile,commentfile):
