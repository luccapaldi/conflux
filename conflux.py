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

import tifffile
import datetime
import pickle
import json
import numpy


def logscript(name, **kwargs):
    """
    Record a log when analysis script exports important variables.

    Keyword arguements:
    name -- name of the file to be exported
    **kwargs -- can be populated with variables used in script
    """

    # Open a new file
    log = open(name + ".yaml", "a")
    # Iterate through the parameters and record in the log
    for key, value in kwargs.items():
        log.write("{} : {}\n".format(key, value))
    log.close()


def pickledata(dataobject, filename):
    """
    Pickle (serialize) python data object.

    Keyword arguments:
    dataobject -- python object to be serialized
    filename -- name of pickle file to save serialized data
    """
    with open(filename, "wb") as fileobject:
        pickle.dump(dataobject, fileobject, pickle.HIGHEST_PROTOCOL)


def unpickledata(filename):
    """Unpickle (import serialized) data."""
    with open(filename, "rb") as fileobject:
        dataobject = pickle.load(fileobject)
    return dataobject


def importtiff(filename):
    """Import a tiff image or image stack as a numpy array."""
    imgarray = tifffile.imread(filename)
    return imgarray


# TODO def splitchannels(tiffarray):
# split channels in a tiffarray

# TODO check the output if it is in correct YAML format
def extractmetadata(filename):
    """
    Extract acquisition metadata from text file produced by ImageJ MicroManager
    with an Andor camera.

    Keyword arguments:
    filename -- name of textfile containing metadata
    """
    metafile = open(filename, "r")
    metadata = metafile.read()  # read metadata as string
    jsonf = json.loads(metadata)  # parse metadata string as json
    framekeys = list(jsonf.keys())[1:]  # create list of FrameKeys in metadata
    # Record acquisition metadata from the first frame recorded.
    readoutmode = jsonf[framekeys[0]]["Andor-ReadoutMode"]["PropVal"]
    interval = jsonf[framekeys[0]]["Andor-ActualInterval-ms"]["PropVal"]
    roi = jsonf[framekeys[0]]["ROI"]
    pixeltype = jsonf[framekeys[0]]["Andor-PixelType"]["PropVal"]
    outputamplifier = jsonf[framekeys[0]]["Andor-Output_Amplifier"]["PropVal"]
    exposure = jsonf[framekeys[0]]["Exposure-ms"]
    preampgain = jsonf[framekeys[0]]["Andor-Pre-Amp-Gain"]["PropVal"]
    adconvertor = jsonf[framekeys[0]]["Andor-AD_Converter"]["PropVal"]
    camspecs = jsonf[framekeys[0]]["Andor-Camera"]["PropVal"].split()
    gain = jsonf[framekeys[0]]["Andor-Gain"]["PropVal"]
    binning = jsonf[framekeys[0]]["Binning"]
    exposure = jsonf[framekeys[0]]["Andor-Exposure"]["PropVal"]
    temperature = jsonf[framekeys[0]]["Andor-CCDTemperature"]["PropVal"]
    # Split camera specifications into  individual variables.
    camtype = camspecs[1]
    cammodel = camspecs[3]
    camserial = camspecs[5]
    # Initialize lists to store the two channel time values.
    channel0, channel1 = [], []
    starttime = jsonf[framekeys[0]]["ElapsedTime-ms"]
    # Add normalized times to each channel list.
    for frame in framekeys:
        if jsonf[frame]["ChannelIndex"] == 0:
            channel0.append(jsonf[frame]["ElapsedTime-ms"] - starttime)
        else:
            channel1.append(jsonf[frame]["ElapsedTime-ms"] - starttime)
    # Export parameters into log file
    logscript(
        "acquisition-parameters",
        cameratype=camtype,
        cameramodel=cammodel,
        cameraserialnumber=camserial,
        exposure=exposure,
        estimatedframeinterval=interval,
        preamplifiergain=preampgain,
        gain=gain,
        outputamplifier=outputamplifier,
        binning=binning,
        roi=roi,
        temperature=temperature,
        pixeltype=pixeltype,
        readoutmode=readoutmode,
        adconvertor=adconvertor,
    )

    # Pickle time series data for each channel.
    if len(channel0) > 0:
        pickledata(channel0, "channel-0_time-series.pickle")
    if len(channel1) > 0:
        pickledata(channel1, "channel-1_time-series.pickle")


def extractcomments(filename):
    """
    Extract comments recording during acquition using the ImageJ MicroManager
    with an Andor camera.

    Keyword arguments:
    filename -- name of textfile containing metadata
    """

    commentfile = open(filename, "r")
    comments = commentfile.read()  # read comments as string
    cleancomments = comments[4:]  # remove non-json compliant header
    jsonfile = json.loads(cleancomments)  # parse metadata string as json


def boundarysubtract(imagestack):
    """
    Find mean of boundary pixel intensities in each frame of image stack and 
    subtract that mean from each pixel. Also find the standard deviation of 
    the boundary pixel intensities and output them as an array.

    Keyword arguments:
    imagearray -- array of images which should exist as an array of numpy
    arrays (imported by tifffile)
    """

    # empty array to store values
    stdevs = numpy.zeros(imagestack.shape[0])

    for slice in range(imagestack.shape[0]):
        # sum together boundary pixels
        boundaries = [imagestack[slice][:,0],
                      imagestack[slice][:,imagestack.shape[2]-1],
                      imagestack[slice][0,:]
                      imagestack[slice][imagestack.shape[1]-1]]
        boundarypixels = numpy.concatenate(boundaries)
        boundarymean = numpy.mean(boundarypixels)
        # calculate the sample standard deviation of the boundary pixels
        stdevs[slice] = numpy.std(boundarypixels, ddof=1)
        # remove mean of boundary pixels from slice
        imagestack[slice] = imagestack[slice] - boundarymean

    # change negative pixel values to zero
    imagestack = imagestack.clip(min=0)
    return (imagestack, stdevs)

def check3x3neighbors(slice, pixelcoord):
    """
    Find mean of neighboring pixels surrounding single pixel of interest.

    0 0 0 0 0 0 0
    0 0 0 0 0 0 0
    0 0 X X X 0 0
    0 0 X P X 0 0
    0 0 X X X 0 0
    0 0 0 0 0 0 0
    0 0 0 0 0 0 0

    Keyword arguments:
    slice -- single tiff image (imported as numpy array) which we can reference
    neighbors within.
    pixelcoord -- coordinate (as an array [row, column]) of pixel of interest
    """
    [y,x] = pixelcoord
    neighbormean = numpy.mean([slice[y - 1][x - 1],
                               slice[y - 1][x],
                               slice[y - 1][x + 1],
                               slice[y][x - 1],
                               slice[y][x + 1],
                               slice[y + 1][x - 1],
                               slice[y + 1][x],
                               slice[y + 1][x + 1]])
    return neighbormean
    
def check5x5neighbors(slice, pixel):
    """
    Find mean of pixels surrounding a single pixel of interest but at a distance of one
    pixel from it.

    0 0 0 0 0 0 0
    0 X X X X X 0
    0 X 0 0 0 X 0
    0 X 0 P 0 X 0
    0 X 0 0 0 X 0
    0 X X X X X 0
    0 0 0 0 0 0 0

    Keyword arguments:
    slice -- single tiff image (imported as numpy array) which we can reference
    neighbors within.
    pixelcoord -- coordinate (as an array [row, column]) of pixel of interest
    """
    [y,x] = pixelcoord
    neighbormean = numpy.mean([slice[y - 2][x - 2],
                               slice[y - 2][x - 1],
                               slice[y - 2][x]
                               slice[y - 2][x + 1],
                               slice[y - 2][x + 2],
                               slice[y - 1][x - 2],
                               slice[y - 1][x + 2],
                               slice[y][x - 2],
                               slice[y][x + 2],
                               slice[y + 1][x - 2],
                               slice[y + 1][x + 2],
                               slice[y + 2][x - 2],
                               slice[y + 2][x - 1],
                               slice[y + 2][x],
                               slice[y + 2][x + 1],
                               slice[y + 2][x + 2]])
    return neighbormean

def doylebackgroundsubtract(imgstack, sigmamod = 3.00, nearneighbor = True, farneighbor
                            = True):
    """
    Subtract background noise from tiff images or stacks using the method detailed in
    the supplementary information of the following paper:

    Revisiting the Conformation and Dynamics of DNA in Slitlike Confinement
    Jing Tang, Stephen L. Levy, Daniel W. Trahan, Jeremy J. Jones, Harold G. Craighead,
    and Patrick S. Doyle
    Macromolecules 2010 43 (17), 7368-7377
    DOI: 10.1021/ma101157x

    Keyword arguments:
    imgstack -- tiff image or stack as a numpy array
    sigmamod -- if the mean intensities of the near or far neighbors (depending on
    booleans below) are less than this value times the standard deviation of the
    boundary pixels, the pixel is taken to be noise and set to 0
    nearneighbor -- use the 3x3 near neighbors in evaluation of each pixel
    farneighbor -- use the 5x5 far neighbors in evaluation of each pixel
    """

    # initial subtraction and get standard deviation of boundaries
    [stack, stdevs] = boundarysubtract(imgstack)
    # create an empty array to store resulting modified image
    newstack = np.zeros(stack[:,2:-2].shape)
    # this new shape will have the outer two bounding rows of pixels removed
    newshape = newstack.shape

    for slice in range(newshape[0]):
        noisecondition = stdevs[slice] * sigmamod
        for row in range(newshape[1]):
            for column in range(newshape[2]):
                pixel = stack[slice][row + 2][column + 2]
                if nearneighbor == True:
                    nearmean = check3x3neighbors(stack[slice],pixel)
                    if nearmean >= noisecondition:
                        newstack[slice][row][column] = pixel
                if farneighbor == True:
                    farcheck = check5x5neighbors(stack[slice],stack[slice][row + 2][column + 2]) 
                    if farcheck >= noisecondition:
                        newstack[slice][row][column] = pixel
                    
    return(newstack)

# def importdata(datafile,metafile,commentfile):


def calculate_center_of_mass(imgarray):
    """
    Calculate center of mass for each slice of a 3D array.
    
    Keyword arguments:
    imgarray -- multidimensional array of tiff images
    """
    #  Sum x(column) and y(row) intensity values
    m_x = imgarray.sum(axis=1)
    m_y = imgarray.sum(axis=0)
    #  cm = sum(m*r)/sum(m), where r is the arbitrary distance from the origin
    cmx = numpy.sum(m_x * (numpy.arange(m_x.size))) / numpy.sum(m_x)
    cmy = numpy.sum(m_y * (numpy.arange(m_y.size))) / numpy.sum(m_y)
    return (cmx, cmy)


def display_cm_overlay(imgarray, cmx_rounded, cmy_rounded):
    """
    Convert grayscale tiff image stack to RGB and overlay center of mass.

    Keyword arguments:
    array_tiff -- multidimensional array of tiff images
    cmx_rounded -- list of rounded x coordinates for center of mass of 3D array
    cmy_rounded -- list of rounded y coordinates for center of mass of 3D array
    """
    list_rgb = []
    coord_count = 0
    #  Iterate through frames and convert grayscale images to RGB images.
    for image in range(len(imgarray)):
        #  Create index values for center of mass
        x_index = cmx_rounded[coord_count]
        y_index = cmy_rounded[coord_count]
        coord_count += 1
        #  Convert each frame to RGB
        rbg_channel = imgarray[image]
        image_rgb = numpy.stack((rbg_channel, rbg_channel, rbg_channel), axis=2)
        #  Add red pixel at center of mass cordinates
        #  To change color of cm pixel, change RGB intensity values below
        image_rgb[x_index, y_index, :] = [255, 0, 0]
        list_rgb.append(image_rgb)
    cm_overlay = numpy.asarray(list_rgb)
    return cm_overlay
