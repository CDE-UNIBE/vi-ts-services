import sys
import time

from gdalconst import GA_ReadOnly
import logging
import osgeo.gdal as gdal
import osgeo.osr as osr
import rpy2.rinterface as rinterface
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
import simplejson as json
from tempfile import NamedTemporaryFile

log = logging.getLogger(__name__)

def ModisTimeSeries(conf, inputs, outputs):

    mimeType = outputs['timeseries']['mimeType']

    lon = float(inputs['lon']['value'])
    lat = float(inputs['lat']['value'])
    epsg = int(inputs['epsg']['value'])

    datadir = conf['main']['dataPath']

    coords = _reproject_coordinates((lon, lat), epsg)

    modis_file = "%s/MODIS_NDVI/h21v08/tif15/out.tif" % datadir

    try:
        array_int_values = _get_value_from_gdal(coords, modis_file)

        if mimeType == 'image/png':
            outputs['timeseries']['value'] = _create_plot(array_int_values)
        else:
            outputs['timeseries']['value'] = json.dumps({'data': array_int_values})
    except:
        outputs['timeseries']['value'] = "[]"

    

    return 3
	
def _get_value_from_gdal(coords, datadir):

    # start timing
    startTime = time.time()
    # coordinates to get pixel values for
    x = coords[0]
    y = coords[1]
    # Register GeoTIFF driver
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()

    result = []

    # open the image
    ds = gdal.Open(datadir, GA_ReadOnly)
    if ds is None:
        log.debug('Could not open image')
        sys.exit(1)

    # get image size
    #rows = ds.RasterYSize
    #cols = ds.RasterXSize
    bands = ds.RasterCount
    # get georeference info
    transform = ds.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    # compute pixel offset
    xOffset = int((x - xOrigin) / pixelWidth)
    yOffset = int((y - yOrigin) / pixelHeight)
    # create a string to print out
    # loop through the bands
    for j in range(bands):
        band = ds.GetRasterBand(j + 1) # 1-based index

        # read data and add the value to the string
        data = band.ReadAsArray(xOffset, yOffset, 1, 1)
        value = data[0, 0]
        result.append(int(value))

    endTime = time.time()
    # figure out how long the script took to run
    log.debug('It took ' + str(endTime - startTime) + ' seconds to read the input raster file.')

    return result

def _reproject_coordinates(coords, epsg_code):

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(epsg_code))

    sinusoidalSrs = osr.SpatialReference()
    # From spatialreference.org: http://spatialreference.org/ref/sr-org/6842/
    sinusoidalSrs.ImportFromProj4("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")

    ct = osr.CoordinateTransformation(srs, sinusoidalSrs)

    (x, y, z) = ct.TransformPoint(float(coords[0]), float(coords[1]))

    return (x, y)

def _create_plot(data_array):
    """
    Create a plot with R
    """

    # Start R timing
    startTime = time.time()

    rinterface.initr()

    r = robjects.r
    grdevices = importr('grDevices')

    vector = robjects.FloatVector(data_array)

    file = NamedTemporaryFile()
    grdevices.png(file=file.name, width=512, height=512)
    # Plotting code here
    r.par(col="black")
    r.plot(vector, xlab="Image Nr", ylab="Values", main="", type="l")
    # Close the device
    grdevices.dev_off()

    # End R timing and log it
    endTime = time.time()
    log.debug('It took ' + str(endTime - startTime) + ' seconds to initalize R and draw a plot.')

    # Return the file content
    return file.read()

    file.close()