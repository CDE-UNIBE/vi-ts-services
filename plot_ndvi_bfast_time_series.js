/**
 * Author : Adrian Weber
 *
 * Copyright 2014 Centre for Development and Environment, University of Bern. All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */


/*
 * Example request:
 * http://localhost/cgi-bin/zoo_loader.cgi?ServiceProvider=&metapath=&Service=WPS&Request=Execute&Version=1.0.0&Identifier=NDVIBfast&DataInputs=lon=-11.1676025390625;lat=6.980954426458497;epsg=4326;width=800;height=300&RawDataOutput=plot@mimeType=application/json
 */
function PlotNdviBfastTimeSeries(conf, inputs, outputs){

    var outputMimeType = outputs.plot.mimeType;

    // Get the input coordinates:
    var lon = parseFloat(inputs.lon.value);
    var lat = parseFloat(inputs.lat.value);
    var epsg = parseInt(inputs.epsg.value);
    if(epsg != 4326){
        return {
            result: ZOO.SERVICE_FAILED,
            outputs: {
                message: "Request CRS is not supported."
            }
        };
    }

    // Get the image width and height from the request or set the defaults
    var width = 1024;
    if(inputs.width){
        width = parseFloat(inputs.width.value);
    }
    var height = 512;
    if(inputs.height){
        height = parseFloat(inputs.height.value);
    }
    
    // Create a WPS Format to parse the results from the subprocesses
    var wpsFormat = new ZOO.Format.WPS();

    // Set up the extract time series process
    var extractProcess = new ZOO.Process('http://localhost/cgi-bin/zoo_loader.cgi', 'ExtractTimeSeries');
    var extractInputs = {
        lon: {
            type: "literal",
            value: lon
        },
        lat: {
            type: "literal",
            value: lat
        },
        epsg: {
            type: "literal",
            value: epsg
        },
        band: {
            type: "literal",
            value: "NDVI"
        }
    };
    
    // Get the result
    var extractExecuteResult= extractProcess.Execute(extractInputs);
    var extractResult = wpsFormat.read(extractExecuteResult);

    // Set up the plotting time series process
    var bfastProcess = new ZOO.Process("http://localhost/cgi-bin/zoo_loader.cgi", "PlotBfast");
    var bfastInputs = {
        timeseries: {
            type: "complex",
            value: extractResult.value,
            mimeType: "application/json"
        },
        width: {
            type: "literal",
            value: width
        },
        height: {
            type: "literal",
            value: height
        }
    };
    
    var bfastExecuteResult = bfastProcess.Execute(bfastInputs);
    var bfastResult = wpsFormat.read(bfastExecuteResult);
    
    return {
        "result": ZOO.SERVICE_SUCCEEDED,
        "outputs": [{
            "name": "plot",
            "value": bfastResult.value,
            "mimeType": outputMimeType
        }]
    };
}