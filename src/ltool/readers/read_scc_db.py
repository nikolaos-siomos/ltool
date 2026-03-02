# -*- coding: utf-8 -*-
"""
Created on Sat Aug 27 10:45:43 2016

@author: nick

"""
import numpy as np
import os
import logging
from dateutil.parser import parse 
from datetime import datetime
from netCDF4 import Dataset
from ..export_layers import export_nc

logger = logging.getLogger(__name__)

def read_scc_db(path):

    base = os.path.basename(path)
    
    logger.info(f"       Reading file: {base} ")
    
    fh = Dataset(path, mode='r')
    metadata = fh.__dict__
    
    # Remove special characters (transliteration)
    for key, value in metadata.items():
        if key.startswith("hoi"):
            continue
        if value is None:
            continue
        if isinstance(value, str):
            metadata[key] = export_nc.ascii_safe(value)
    
    
    metadata['title'] = 'Geometrical properties of aerosol layers'
    metadata['input_file'] = base
    
    # Dates
    start_m = parse(fh.measurement_start_datetime)
    dt_start = datetime(start_m.year, start_m.month, start_m.day, 
                        start_m.hour, start_m.minute, start_m.second)
    
    # Profiles
    alt = np.round(fh.variables['altitude'][:].data/1000., decimals = 5)
    prod = fh.variables['backscatter'][0, 0, :].data
    rh = (fh.variables['backscatter_calibration_range'][0,1] + fh.variables['backscatter_calibration_range'][0,0])/2.
    prod_err = fh.variables['error_backscatter'][0, 0, :].data
    
    # Wavelength
    wave = str(int(fh.variables['wavelength'][0].data))

    return(dt_start, alt, prod, prod_err, metadata, wave, rh)

def check_arrays(alt, prod, prod_err):
    
    if (len(prod[prod == prod]) <= 10) or (len(alt[prod > 0.]) <= 10) \
        or (len(alt[prod_err > 0.]) <= 10):
        
        raise Exception()
    
    return()

def trim_arrays(alt, prod, prod_err, rh):

    step = np.round(np.nanmin(alt[1:] - alt[:-1]), decimals = 5)
        
    # Nans above the reference height and where prod =  9.96920997e+36              
    mask = (alt < rh) & (prod >= 0.) & (prod < 1)
    
    prod = prod[mask]
    prod_err = prod_err[mask]
    alt = alt[mask]  

    alt_b = alt[0]

    return(alt, prod, prod_err, alt_b, step)

def interp_arrays(alt, prod, prod_err, step, end_fill):
                  
    # Interpolate intermediate nans and also keep nan above half wavelet step above end
    alt_n = np.round(np.arange(alt[0] - end_fill, alt[-1] + end_fill, step), decimals = 5)
    prod_n = np.interp(alt_n, np.hstack((alt[0] - end_fill, alt, alt[-1] + end_fill)),
                       np.hstack((prod[0], prod, prod[-1])))
    prod_err_n = np.interp(alt_n, np.hstack((alt[0] - end_fill, alt, alt[-1] + end_fill)),
                           np.hstack((prod_err[0], prod_err, prod_err[-1])))  
        
    return(alt_n, prod_n, prod_err_n)
        
