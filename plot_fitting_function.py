import sys
import time

from ConfigParser import ConfigParser
import cairo
import logging
import logging.config
import os
import rpy2.rinterface as rinterface
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
try:
    import simplejson as json
except ImportError:
    import json
from tempfile import NamedTemporaryFile
try:
    from cStringIO import StringIO
except ImportError:
    import StringIO

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
f = open(os.devnull, 'w')
sys.stdout = f

def PlotFittingFunction(conf, inputs, outputs):
    
    try:
        timeseries = json.loads(str(inputs['timeseries']['value']).strip())
    except ValueError:
        conf["lenv"]["message"] = "Parameter \"timeseries\" is not valid or not supported."
        return SERVICE_FAILED

    try:
        imageWidth = int(inputs['width']['value'])
    except ValueError:
        imageWidth = 1024
    try:
        imageHeight = int(inputs['height']['value'])
    except ValueError:
        imageHeight = 512

    handler = FittingFunctionTimeSeriesHandler(conf, inputs, outputs)
    result = handler.plot(timeseries["data"], imageWidth, imageHeight)

    return result

class FittingFunctionTimeSeriesHandler():

    def __init__(self, conf, inputs, outputs):
        self.conf = conf
        self.inputs = inputs
        self.outputs = outputs

        # Create a config parser
        self.config = ConfigParser()
        self.config.read('ModisTimeSeries.ini')


    def plot(self, data_array, width, height):
        """
        Create a plot with R
        """

        # Start R timing
        startTime = time.time()

        rinterface.initr()

        r = robjects.r
        grdevices = importr('grDevices')
        
        # Import the bfast package
        log.debug(os.environ["R_SCRIPTS_USER"])
        r.source("%s/4253H_twice.R" % os.environ["R_SCRIPTS_USER"] )

        b = robjects.FloatVector(data_array)

        # Make a time series from the vector
        b_ts = r.ts(b, start=robjects.IntVector([2000, 4]), frequency=23)
        
        b_fitting = r.my4253Htwice(x=b_ts)

        temp_datadir = self.config.get('main', 'temp.datadir')
        temp_url = self.config.get('main', 'temp.url')
        file = NamedTemporaryFile(suffix=".png", dir=temp_datadir, delete=False)

        log.debug("Writing resulting diagram to file %s" % file.name)
        grdevices.png(file=file.name, width=width, height=height)
        # Plotting code here
        #r.par(col="black")
        r.plot(b_fitting, type="l", axes=False, ylab="Double logistic fitting", ylim=robjects.FloatVector([0.0, 1.0]))
        r.box()
        r.axis(2, labels=robjects.StrVector(['0.0', '0.2', '0.4', '0.6', '0.8', '1.0']), at=robjects.FloatVector([0.0, 0.2, 0.4, 0.6, 0.8, 1.0]))
        r.axis(1, labels=robjects.StrVector(['2000', '2002', '2004', '2006', '2008', '2010', '2012', '2014']), at=robjects.FloatVector([2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014]))
        r.abline(v=robjects.IntVector([2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014]), col="lightgrey", lty=2) # vertikale linien bei jedem jahr, lty ist line type
        r.abline(h=robjects.FloatVector([0, 0.2000, 0.4000, 0.6000, 0.8000, 1.0000]), col="lightgrey", lty=2)
        # Close the device
        grdevices.dev_off()

        # End R timing and log it
        endTime = time.time()
        log.debug('It took ' + str(endTime - startTime) + ' seconds to initalize R and draw a plot.')

        file.close()

        result = {"file": "%s/%s" % (temp_url, file.name.split("/")[-1])}

        self.outputs['plot']['value'] = json.dumps({"file": "%s/%s" % (temp_url, file.name.split("/")[-1])})
        return SERVICE_SUCCEEDED

    def _create_empty_image(self, image_width, image_height):

        # Check pycairo capabilities
        if not (cairo.HAS_IMAGE_SURFACE and cairo.HAS_PNG_FUNCTIONS):
            raise HTTPBadRequest('cairo was not compiled with ImageSurface and PNG support')

        # Create a new cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(image_width), int(image_height))

        ctx = cairo.Context(surface)

        text = "No imagery available for requested coordinates."

        x_bearing, y_bearing, width, height, x_advance, y_advance = ctx.text_extents (text)

        ctx.move_to((image_width / 2) - (width / 2), (image_height / 2) + (height / 2))
        ctx.set_source_rgba(0, 0, 0, 0.85)
        ctx.show_text(text)

        temp_datadir = self.config.get('main', 'temp.datadir')
        temp_url = self.config.get('main', 'temp.url')
        file = NamedTemporaryFile(suffix=".png", dir=temp_datadir, delete=False)
        surface.write_to_png(file)
        file.close()

        return {"file": "%s/%s" % (temp_url, file.name.split("/")[-1])}
