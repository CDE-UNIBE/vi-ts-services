import sys
import time

from ConfigParser import ConfigParser
from ModisExtent import ModisExtent
from ModisExtent import ModisAvailableCountry
from gdalconst import GA_ReadOnly
from geoalchemy import WKTSpatialElement
from geoalchemy import functions as spfunc
import logging
import logging.config
import osgeo.gdal as gdal
import osgeo.osr as osr
from pyspatialite import dbapi2 as spatialite
import rpy2.rinterface as rinterface
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
try:
    import simplejson as json
except ImportError:
    import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import or_
from tempfile import NamedTemporaryFile

logging.config.fileConfig('logging.ini')
log = logging.getLogger(__name__)

# ZOO Constants
# See also http://zoo-project.org/docs/workshop/2012/first_service.html
SERVICE_FAILED = 4
SERVICE_SUCCEEDED = 3

def ModisTimeSeries(conf, inputs, outputs):

    mimeType = outputs['timeseries']['mimeType']

    lon = float(inputs['lon']['value'])
    lat = float(inputs['lat']['value'])
    epsg = int(inputs['epsg']['value'])
    imageWidth = int(inputs['width']['value'])
    imageHeight = int(inputs['height']['value'])

    handler = ModisTimeSeriesHandler(conf, inputs, outputs)
    result = handler.get_time_series((lon, lat), epsg, mimeType, imageWidth, imageHeight)

    return result

class ModisTimeSeriesHandler(object):

    def __init__(self, conf, inputs, outputs):
        self.conf = conf
        self.inputs = inputs
        self.outputs = outputs

        # Create a config parser
        self.config = ConfigParser()
        self.config.read('ModisTimeSeries.ini')

    def get_time_series(self, input_coords, epsg, mimeType, width=512, height=512):

        # Reproject the input coordinates to the MODIS sinusoidal projection
        coords = self._reproject_coordinates(input_coords, epsg)

        # Get the path to the MODIS tile
        modis_file = self._get_tile(coords)

        if modis_file is not None:

            array_int_values = self._get_value_from_gdal(coords, modis_file)

            if mimeType == 'image/png':
                self.outputs['timeseries']['value'] = self._create_plot(array_int_values, width, height)
            else:
                self.outputs['timeseries']['value'] = json.dumps({'data': array_int_values})

            return SERVICE_SUCCEEDED

        else:
            self.conf["lenv"]["message"] = "No imagery available for requested coordinates."
            return SERVICE_FAILED

    def _get_tile(self, coords):
        """
        Get the directory path to the requested MODIS subtile using a spatially
        enabled database.
        """

        # Get the SQLAlchemy URL from the configuration
        sqlalchemy_url = self.config.get('main', 'sqlalchemy.url')
        # the MODIS data directory
        modis_datadir = self.config.get('main', 'modis.datadir')
        # and the custom CRS for the MODIS sinusoidal projection.
        custom_crs = self.config.getint('main', 'custom.crs')

        # Engine, which the Session will use for connection resources
        engine = create_engine(sqlalchemy_url, module=spatialite)
        # Create a configured "Session" class
        Session = sessionmaker(bind=engine)
        # Create a Session
        session = Session()

        # Create a point from the requested coordinates
        p = WKTSpatialElement('POINT(%s %s)' % coords, custom_crs)

        countryConditions = []
        for country in session.query(ModisAvailableCountry).filter(ModisAvailableCountry.available == True):
            countryConditions.append(spfunc.within(p, country.geometry))

        tile = session.query(ModisExtent.name)\
            .filter(ModisExtent.available == True)\
            .filter(spfunc.within(p, ModisExtent.geometry))\
            .filter(or_(*countryConditions))\
            .first()
        if tile is not None:
            modis_file = "/%s/%s/NDVI.tif" % (modis_datadir, tile.name)
            return modis_file

        else:
            # Return None if there is no MODIS tile available for the requested
            # coordinates.
            return None
	
    def _get_value_from_gdal(self, coords, datadir):

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
        log.debug("Accessing file: %s" % datadir)
        ds = gdal.Open(str(datadir), GA_ReadOnly)
        if ds is None:
            log.warn('Could not open image: %s' % str(datadir))
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

    def _reproject_coordinates(self, coords, epsg_code):
        """
        Reproject the requested coordinates to MODIS sinusoidal projection. EPSG
        code of input CRS must be known to GDAL.
        """

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(int(epsg_code))

        sinusoidalSrs = osr.SpatialReference()
        # From spatialreference.org: http://spatialreference.org/ref/sr-org/6842/
        sinusoidalSrs.ImportFromProj4("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")

        ct = osr.CoordinateTransformation(srs, sinusoidalSrs)

        (x, y, z) = ct.TransformPoint(float(coords[0]), float(coords[1]))

        return (x, y)

    def _create_plot(self, data_array, width, height):
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
        grdevices.png(file=file.name, width=width, height=height)
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
