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
from ..export_layers import export_nc
from datetime import datetime, timedelta
from typing import Optional, Iterable, List, Union

# logger = logging.getLogger(__name__)

def parse_utc_datetime(value):
    """Parse ISO-like UTC timestamps used in input NetCDF metadata.

    Accepted examples:
        2020-03-12T17:00:15Z
        2020-03-12T17:00:15
        2020-03-12T17:00:15.123Z
        2020-03-12T17:00:15.123

    Also repairs the known malformed form:
        2020-04-09T08:47:01T

    A timestamp without a trailing ``Z`` is treated as UTC, matching the
    existing metadata convention. Leap-second values ending in ``:60`` or
    ``:60Z`` are normalized to the first instant of the following minute.
    """
    if isinstance(value, bytes):
        value = value.decode("utf-8")

    if not isinstance(value, str):
        raise TypeError(
            f"Datetime metadata must be str or bytes, "
            f"got {type(value).__name__}"
        )

    value = value.strip()

    if not value:
        raise ValueError("Datetime metadata is empty")

    # Repair a known metadata defect: an extra trailing "T" after the seconds.
    # Example: "2020-04-09T08:47:01T"
    if value.endswith("T") and value.count("T") == 2:
        print(
            f"-- Warning: removing unexpected trailing 'T' "
            f"from datetime metadata {value!r}"
        )
        value = value[:-1]

    formats = (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    # Python datetime does not accept second=60.
    # Parse second=59, then add one second.
    has_z = value.endswith("Z")
    core = value[:-1] if has_z else value

    if core.endswith(":60"):
        normalized = core[:-3] + ":59"

        if has_z:
            normalized += "Z"
            fmt = "%Y-%m-%dT%H:%M:%SZ"
        else:
            fmt = "%Y-%m-%dT%H:%M:%S"

        return (
            datetime.strptime(normalized, fmt)
            + timedelta(seconds=1)
        )

    raise ValueError(
        f"Unsupported datetime format: {value!r}. Expected "
        "YYYY-MM-DDTHH:MM:SS with optional fractional seconds "
        "and optional Z."
    )
        
        
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

    # File checks
    missing_vars = check_missing_variables(fh)
    missing_metas = check_missing_metadata(fh)
    
    if missing_vars or missing_metas:
        fh.close()
        return None, None, True

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
    # metadata['height_units'] = 'm_asl'
    
    # metadata['latitude'] = np.round(np.ma.filled(fh.variables['latitude'][:], fill_value=np.nan).item(), decimals = 4)
    # metadata['longitude'] = np.round(np.ma.filled(fh.variables['longitude'][:], fill_value=np.nan).item(), decimals = 4)
    # metadata['station_altitude'] = np.round(np.ma.filled(fh.variables['station_altitude'][:]).item(), decimals = 5)
    
    # Dates
    metadata['start_time'] = parse_utc_datetime(
        metadata['measurement_start_datetime']
        ).strftime('%Y%m%d%H%M')

    metadata['stop_time'] = parse_utc_datetime(
        metadata['measurement_stop_datetime']
        ).strftime('%Y%m%d%H%M')

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

    # Store arrays in dictionary
    profiles['height'] = alt
    profiles['product'] = prod
    profiles['product_error'] = prod_err
    
    # Check if the arrays are too short
    bad_profile = check_arrays(profiles)
    
    # Close the netcdf
    fh.close()
    
    return metadata, profiles, bad_profile

# def check_arrays(profiles):
    
#     alt = profiles['height']
#     prod = profiles['product']
#     prod_err = profiles['product_error']
    
#     bad_profile = False
    
#     if (len(prod[prod == prod]) <= 10) or (len(alt[prod > 0.]) <= 10) \
#         or (len(alt[prod_err > 0.]) <= 10):
        
#         bad_profile = True
    
#     return(bad_profile)

def check_missing_variables(fh):
    required_keys = [
        'altitude', 
        'backscatter', 
        'error_backscatter',
        'wavelength',
        # 'measurement_start_datetime',
        # 'measurement_stop_datetime'
        ]

    # Check if any variables are missing in the netcdf files
    missing = [key for key in required_keys if key not in fh.variables]

    if missing:
        print(f"Missing variables: {missing}")
        return True
    else:
        print("All variables are present")
        return False

def check_missing_metadata(fh):
    required_keys = [
        'measurement_start_datetime',
        'measurement_stop_datetime'
        ]

    # Check if any variables are missing in the netcdf files
    missing = [key for key in required_keys if key not in fh.__dict__]

    if missing:
        print(f"Missing metadata: {missing}")
        return True
    else:
        print("All metadata are present")
        return False
    
    
    
def check_arrays(profiles):
    
    alt = profiles['height']
    prod = profiles['product']
    prod_err = profiles['product_error']
    
    bad_profile = False
    
    # Check array length
    if (len(prod[~np.isnan(prod)]) <= 10) or \
       (len(alt[prod > 0.]) <= 10) or \
       (len(alt[prod_err > 0.]) <= 10):
        
        bad_profile = True
        print("-- Warning: Arrays too short! Skipping file")
        
    # Check negative values
    if (alt < 0.).any():
        
        bad_profile = True
        
        print("-- Warning: Negative altitude values detected! Skipping file")

    if (prod_err <= 0.).any():
        
        bad_profile = True
        
        print("-- Warning: Negative error values detected! Skipping file")

    if np.any(~np.isfinite(alt)):

        bad_profile = True
        
        print("-- Warning: Height contains non-finite values! Skipping file")

    if np.any(np.diff(alt) <= 0):

        bad_profile = True
        
        print("-- Warning: Height should be strictly increasing! Skipping file")

    # # ✅ New: check for constant height step
    # if len(alt) > 1:
    #     steps = np.diff(alt)
    #     first_step = steps[0]
        
    #     if not np.allclose(steps, first_step, atol=1e-5):
    #         print("-- Warning: Irregular height grid detected")
    #         bad_profile = True

    return bad_profile

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
        
