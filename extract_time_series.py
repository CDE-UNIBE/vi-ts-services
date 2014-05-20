import sys
import time

from ConfigParser import ConfigParser
from ModisExtent import ModisAvailableCountry
from ModisExtent import ModisExtent
import cgi
from gdalconst import GA_ReadOnly
from geoalchemy import WKTSpatialElement
from geoalchemy import functions as spfunc
import logging
import logging.config
import os
import osgeo.gdal as gdal
import osgeo.osr as osr
from pyspatialite import dbapi2 as spatialite
try:
    import simplejson as json
except ImportError:
    import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import or_
from tempfile import NamedTemporaryFile
try:
    from cStringIO import StringIO
except ImportError:
    import StringIO
from random import random

logging.config.fileConfig('logging.ini')
# Get the root logger from the config file
log = logging.getLogger(__name__)
# Get also the spatial logger, which logs the requested to a separate csv file
spatiallog = logging.getLogger("spatial.logger")

# ZOO Constants
# See also http://zoo-project.org/docs/workshop/2012/first_service.html
SERVICE_FAILED = 4
SERVICE_SUCCEEDED = 3

# Send all output especially the R output to the dump
#f = open(os.devnull, 'w')
#sys.stdout = f

def ExtractTimeSeries(conf, inputs, outputs):

    try:
        lon = float(inputs['lon']['value'])
        lat = float(inputs['lat']['value'])
    except ValueError:
        conf["lenv"]["message"] = "Parameter \"lon\" or \"lat\" is not valid."
        return SERVICE_FAILED

    try:
        epsg = int(inputs['epsg']['value'])
    except ValueError:
        epsg = 4326
    if epsg not in [4326]:
        conf["lenv"]["message"] = "Requested CRS is not supported."
        return SERVICE_FAILED
    
    band = str(inputs['band']['value'])
    if band.lower() not in ['ndvi', 'qual']:
        conf["lenv"]["message"] = "Requested band is not available."
        return SERVICE_FAILED

    handler = ExtractTimeSeriesHandler(conf, inputs, outputs)
    result = handler.extract_values((lon, lat), epsg, band)

    return result

class ExtractTimeSeriesHandler(object):

    def __init__(self, conf, inputs, outputs):
        self.conf = conf
        self.inputs = inputs
        self.outputs = outputs

        # Create a config parser
        self.config = ConfigParser()
        self.config.read('ModisTimeSeries.ini')

    def extract_values(self, input_coords, epsg, band):
        
        log.debug("Extract values with coords %s and band %s" % (input_coords, band))

        # Reproject the input coordinates to the MODIS sinusoidal projection
        coords = self._reproject_coordinates(input_coords, epsg)

        # Get the path to the MODIS tile
        modis_file = self._get_tile(coords, band)

        # Log this request to the spatial file logger
        # Get the IP
        ip = cgi.escape(os.environ["REMOTE_ADDR"])
        # Log the cordinates
        spatiallog.info("%s,%s,\"%s\",%s" % (input_coords[0], input_coords[1], ip, modis_file != None))

        if modis_file is not None:

            array_int_values = self._get_value_from_gdal(coords, modis_file)
            #array_int_values = self._get_random_values()

            self.outputs['timeseries']['value'] = json.dumps({"success": True, "data": array_int_values})
            self.outputs['timeseries']['mimeType'] = "application/json"
            return SERVICE_SUCCEEDED

        else:

            self.outputs['timeseries']['value'] = json.dumps({"success": False, "data": None})
            return SERVICE_FAILED


    def _get_tile(self, coords, band):
        """
        Get the directory path to the requested MODIS subtile using a spatially
        enabled database.
        """

        # Get the SQLAlchemy URL from the configuration
        sqlalchemy_url = self.config.get('main', 'sqlalchemy.url')
        log.debug("sqlalchemy_url is set to %s" % sqlalchemy_url)
        # the MODIS data directory
        modis_datadir = self.config.get('main', 'modis.datadir')
        log.debug("MODIS data directory is set to %s" % modis_datadir)
        # and the custom CRS for the MODIS sinusoidal projection.
        custom_crs = self.config.getint('main', 'custom.crs')
        log.debug("Custom CRS is set to %s" % custom_crs)

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
            modis_file = "%s/%s/%s/%s.tif" % (modis_datadir, band, tile.name, band)
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
            value = float(data[0, 0])
            result.append(value / 10000.0)

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

    def _get_random_values(self):
        """
        A method only used during the development to replace the method
        _get_value_from_gdal
        """

        return [random() for i in range(322)]
