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

def pickledata(dataobject,filename):
    with open(filename, 'wb') as fileobject:
        pickle.dump(dataobject, fileobject, pickle.HIGHEST_PROTOCOL)
    logscript('pickledata','Pickle (serialize) data.',outputfile = filename)

def unpickledata(filename):
    with open(filename, 'rb') as fileobject: 
        dataobject = pickle.load(fileobject) 
    logscript('unpickledata','Unpickle (import serialized) data.',
              inputfile = filename)
    return(dataobject)

def importtiff(filename): 
    imgarray = tifffile.imread(filename) 
    #log = open('log.yaml','a') # assume opening a new log 
    #log.write(str(filename) + '\n') 
    #log.close() 
    logscript('importtiff','Import tiff into numpy array.',inputfile = filename) 
    return(imgarray)

# def splitchannels(tiffarray):
    # split channels in a tiffarray

def extractmetadata(filename):
    # need to add comments import
    metafile = open('MMStack_Pos0_metadata.txt','r') # load metadata file
    metadata = metafile.read() # read metadata as string
    json = json.loads(metadata) # parse metadata string as json
    framekeys = list(json.keys())[1:] # create list of FrameKeys in metadata
    # record acquisition metadata from the first frame recorded
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
    # split camera specifications into  individual variables
    camtype = camspecs[1]
    cammodel = camspecs[3]
    camserial = camspecs[5]
    # record frame start times for channel 0 
    channel0, channel1  = [], [] # make empty lists to store time values
    starttime = json[framekeys[0]]['ElapsedTime-ms'] # time of first frame
    # add normalized times to each channel list
    for frame in framekeys:
        if json[frame]['ChannelIndex'] == 0:
            channel0.append(json[frame]['ElapsedTime-ms'] - starttime)
        else:
            channel1.append(json[frame]['ElapsedTime-ms'] - starttime)
    # add metadata to logscript
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
    # pickle time series data for each channel
    if len(channel0) > 0:
        pickledata(channel0,'channel-0_time-series.pickle')
    if len(channel1) > 0:
        pickledata(channel1,'channel-1_time-series.pickle')

# def importdata(datafile,metafile,commentfile):
