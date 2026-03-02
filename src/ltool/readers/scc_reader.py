# -*- coding: utf-8 -*-
"""
Created on Sat Aug 27 10:45:43 2016

@author: nick

"""
import numpy as np
import os
# import logging
from dateutil.parser import parse 
from datetime import datetime
from netCDF4 import Dataset

# logger = logging.getLogger(__name__)

def read_scc_product_file(file_path):

    fh = Dataset(file_path, mode='r')

    # Metadata
    metadata = fh.__dict__
    metadata['title'] = 'Geometrical properties of aerosol layers'
    metadata['input_file'] = os.path.basename(file_path)    
    metadata['wavelength'] = str(int(fh.variables['wavelength'][0].data))
    metadata['backscatter_calibration_height'] = (fh.variables['backscatter_calibration_range'][0,1] + fh.variables['backscatter_calibration_range'][0,0])/2.    
    metadata['height_units'] = 'm_asl'
    
    metadata['latitude'] = np.round(np.ma.filled(fh.variables['latitude'][:], fill_value=np.nan).item(), decimals = 4)
    metadata['longitude'] = np.round(np.ma.filled(fh.variables['longitude'][:], fill_value=np.nan).item(), decimals = 4)
    metadata['station_altitude'] = np.round(np.ma.filled(fh.variables['station_altitude'][:]).item(), decimals = 5)
    
    # Dates
    start_m = parse(fh.measurement_start_datetime)
    dt_start = datetime(start_m.year, start_m.month, start_m.day, 
                        start_m.hour, start_m.minute, start_m.second)
    metadata['start_datetime'] = dt_start
    metadata['start_time'] = datetime.strptime(metadata['measurement_start_datetime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M')
    metadata['stop_time'] = datetime.strptime(metadata['measurement_stop_datetime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d%H%M')
    
    # Profiles
    profiles = {}

    alt = np.round(np.ma.filled(fh.variables['altitude'][:], fill_value=np.nan), decimals = 5)
    prod = np.ma.filled(fh.variables['backscatter'][0, 0, :], fill_value=np.nan) 
    prod_err = np.ma.filled(fh.variables['error_backscatter'][0, 0, :], fill_value=np.nan) 

    # Extra precaution - fill too big values with nans (some EARLINET DB files have this issue)
    mask_goodvals = (alt <= 5E5) & (prod < 1.) & (prod_err < 1.) 
    
    prod[~mask_goodvals] = np.nan
    prod_err[~mask_goodvals] = np.nan

    profiles['height'] = alt
    profiles['product'] = prod
    profiles['product_error'] = prod_err
    
    return(metadata, profiles)

def check_arrays(profiles):
    
    alt = profiles['height']
    prod = profiles['product']
    prod_err = profiles['product_error']
    
    bad_profile = False
    
    if (len(prod[prod == prod]) <= 10) or (len(alt[prod > 0.]) <= 10) \
        or (len(alt[prod_err > 0.]) <= 10):
        
        bad_profile = True
    
    return(bad_profile)

def trim_arrays(profiles, backscatter_calibration_height):
    
    height = profiles['height']
    prod = profiles['product']
    prod_err = profiles['product_error']

    # step = np.round(np.nanmin(alt[1:] - alt[:-1]), decimals = 5)
        
    # Nans above the reference height and where prod =  9.96920997e+36              
    mask = (height < backscatter_calibration_height)
    
    prod[~mask] = np.nan
    prod_err[~mask] = np.nan
    
    prod = interpolate_and_trim_nans(x = height, y =  prod)
    prod_err = interpolate_and_trim_nans(x = height, y = prod_err)
    
    profiles['height'] = height
    profiles['product'] = prod
    profiles['product_error'] = prod_err
        
    return(profiles)

def interpolate_and_trim_nans(x, y):
    """
    Removes leading/trailing NaNs from 'product' and interpolates internal NaNs using 'height'.
    
    Parameters:
        y (np.ndarray): 1D array of measured values (may contain NaNs).
        x (np.ndarray): 1D array of same shape, represents height levels.

    Returns:
        (clean_product, clean_height): tuple of arrays with NaNs removed/interpolated.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)

    if y.shape != x.shape:
        raise ValueError("y and x must have the same shape")

    # Find indices where product is NOT NaN
    valid_indices = np.where(~np.isnan(y))[0]

    if valid_indices.size == 0:
        raise ValueError("Cannot interpolate: all product values are NaN.")

    # Determine the range to keep (first to last valid)
    start = valid_indices[0]
    end = valid_indices[-1] + 1

    # Trim arrays to remove leading/trailing NaNs
    trimmed_x = np.full(len(x), np.nan)
    trimmed_y = np.full(len(y), np.nan)
    trimmed_x[start:end] = x[start:end]
    trimmed_y[start:end] = y[start:end]
    
    # Interpolate internal NaNs
    isnan = np.isnan(trimmed_y)
    not_nan = ~isnan
    interpolated = np.interp(trimmed_x, trimmed_x[not_nan], trimmed_y[not_nan])

    return interpolated
        
