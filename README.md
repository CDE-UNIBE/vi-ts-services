A ZOO Web Processing Service to extract time series from MODIS imagery.

Prerequisites
-------------
* A running [ZOO WPS Platform](http://www.zoo-project.org/)
* [GDAL](http://www.gdal.org/) with Python bindings
  * tested with version 1.10dev, other versions may work
* [R](http://www.r-project.org/) and [rpy2](http://pypi.python.org/pypi/rpy2/2.3.1)
  * tested with version 2.3.1, other versions may work

Installation
------------
* Change the `CGI_DIR` in the Makefile according to your server installation
* `sudo make install`
* Check the installation:
  [http://localhost/cgi-bin/zoo_loader.cgi?ServiceProvider=&metapath=&Service=WPS&Request=DescribeProcess&Version=1.0.0&Identifier=ModisTimeSeries](http://localhost/cgi-bin/zoo_loader.cgi?ServiceProvider=&metapath=&Service=WPS&Request=DescribeProcess&Version=1.0.0&Identifier=ModisTimeSeries)
