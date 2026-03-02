# -*- coding: utf-8 -*-
"""
Created on Sat Aug 27 10:45:43 2016

@author: nick

"""
import os
import re
import fnmatch
import numpy as np
# import logging
from pathlib import Path
from netCDF4 import Dataset
from datetime import datetime
from ..export_layers import export_nc
from typing import Optional, Iterable, List, Union

# logger = logging.getLogger(__name__)

def list_input_netcdf_files(
    input_path: Union[str, Path],
    wavelength: Optional[str],
    include_globs: Iterable[str],
    exclude_globs: Iterable[str],
    name_regex: Optional[str],
    allowed_exts: Iterable[str],
) -> List[Path]:
    """
    Returns a sorted list of NetCDF files to process.
    - If input_path is a file: validate extension + filters and return [file] or [].
    - If input_path is a dir: scan for allowed extensions and apply filters.
    Filtering is applied to the filename (Path.name).
    """
    input_path = Path(input_path)

    allowed_exts = {e if e.startswith(".") else f".{e}" for e in allowed_exts}
    regex = re.compile(name_regex) if name_regex else None

    def is_netcdf(p: Path) -> bool:
        return p.is_file() and p.suffix.lower() in {e.lower() for e in allowed_exts}

    def matches_filters(p: Path) -> bool:
        name = p.name

        # convenience: wavelength filter (if provided)
        # Adjust this if you prefer to match "b{wavelength}" strictly.
        if wavelength is not None and f"b{wavelength}" not in name:
            return False

        # include globs: if any are provided, must match at least one
        if include_globs:
            if not any(fnmatch.fnmatch(name, g) for g in include_globs):
                return False

        # exclude globs: if any match, reject
        if exclude_globs:
            if any(fnmatch.fnmatch(name, g) for g in exclude_globs):
                return False

        # optional regex: must match
        if regex and not regex.search(name):
            return False

        return True

    # Single file mode
    if input_path.is_file():
        if not is_netcdf(input_path):
            raise ValueError(f"Input file must be NetCDF with extension {sorted(allowed_exts)}: {input_path}")
        return [input_path] if matches_filters(input_path) else []

    # Directory mode
    if not input_path.is_dir():
        raise ValueError(f"input_path must be a file or directory: {input_path}")

    # Collect candidate NetCDF files
    candidates: List[Path] = []
    for ext in allowed_exts:
        candidates.extend(input_path.rglob(f"*{ext}"))

    files = [p for p in candidates if is_netcdf(p) and matches_filters(p)]
    return sorted(files)

def read_product_file(file_path):

    fh = Dataset(file_path, mode='r')

    # Metadata
    original_metadata = fh.__dict__
    
    # Remove special characters (transliteration)
    for key, value in original_metadata.items():
        if key.startswith("hoi"):
            continue
        if value is None:
            continue
        if isinstance(value, str):
            original_metadata[key] = export_nc.ascii_safe(value)
    
    metadata = {}
    for key in original_metadata.keys():
        metadata[key] = original_metadata[key]
        
    metadata['title'] = 'Geometrical properties of aerosol layers'
    metadata['input_file'] = os.path.basename(file_path)    
    metadata['wavelength'] = str(int(fh.variables['wavelength'][0].data))
    metadata['backscatter_calibration_height'] = (fh.variables['backscatter_calibration_range'][0,1] + fh.variables['backscatter_calibration_range'][0,0])/2.    
    # metadata['height_units'] = 'm_asl'
    
    metadata['latitude'] = np.round(np.ma.filled(fh.variables['latitude'][:], fill_value=np.nan).item(), decimals = 4)
    metadata['longitude'] = np.round(np.ma.filled(fh.variables['longitude'][:], fill_value=np.nan).item(), decimals = 4)
    metadata['station_altitude'] = np.round(np.ma.filled(fh.variables['station_altitude'][:]).item(), decimals = 5)
    
    # Dates
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

    # Kick out nan values on the height array
    mask_empty = (alt != alt)
    s_ind = np.where(~mask_empty)[0][0]
    e_ind = np.where(~mask_empty)[0][-1]
    alt = alt[s_ind:e_ind+1]
    prod = prod[s_ind:e_ind+1]
    prod_err = prod_err[s_ind:e_ind+1]
    
    # Interpolate to make sure 
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
    
    # prod = interpolate_and_trim_nans(x = height, y =  prod)
    # prod_err = interpolate_and_trim_nans(x = height, y = prod_err)
    
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
        
