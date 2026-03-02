#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 21:31:10 2020

@author: nick
"""
import os, sys, datetime
import numpy as np
import unicodedata

REPLACEMENTS = {
    "ß": "ss",
    "ẞ": "SS",
}

def export_nc(layers, alpha, wavelength, snr_factor, wct_peak_margin, version, 
              fname, save_netcdf = True, dir_out = None, metadata = None,
              subfolder = 'netcdf'):
        
    geom_dts = layers.to_dataset('features')
    geom_dts = geom_dts.drop_vars('layers')
    
    encoding = {}
    for v in geom_dts.data_vars:
        if np.issubdtype(geom_dts[v].dtype, np.floating):
            encoding[v] = {"_FillValue": None}   # or np.nan if you prefer
    
    time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    if metadata:
        geom_dts.attrs = metadata
        
        argv = sys.argv
        argv[-1] = os.path.basename(argv[-1])
        args = ' '.join(argv[1:])
        geom_dts.attrs['history'] = f"{geom_dts.attrs['history']}; {time}: ltool {args}" 

        ssc_vd = geom_dts.attrs['scc_version_description']
        parts = ssc_vd.split(')')
        ssc_vd = f'{parts[0]}, LTOOL vers. {version}){parts[-1]}'
        geom_dts.attrs['scc_version_description'] = ssc_vd
        
    geom_dts.attrs['processor_name'] = 'ltool'
    geom_dts.attrs['processor_version'] = version

    geom_dts.attrs['layer_method'] = 'Wavelet Correlation Transform'
    
    geom_dts.attrs['__file_format_version'] = '1.0'
    
    geom_dts['snr_factor'] = snr_factor
    geom_dts.snr_factor.attrs['long_name'] = 'WCT to noise ratio threshold applied for identifiying the potential layer features. It is used to discern between noise and actual layers.'
    geom_dts.snr_factor.attrs['units'] = ''
    
    geom_dts['wct_peak_margin'] = wct_peak_margin
    geom_dts.wct_peak_margin.attrs['long_name'] = 'Optimization threhold applied on the WCT to decide which features will be selected as layer base and top within a coarser layer region. Instead of just selecting the most pronounce feature as base/top based only on the WCT value, an acceptance interval of up to wct_peak_margin times the maximum WCT is provided favoring higher tops and lower bases. Features with WCT values less than this threshold times the maximum WCT are rejected. '
    geom_dts.wct_peak_margin.attrs['units'] = ''

    geom_dts['dilation'] = alpha
    geom_dts.dilation.attrs['long_name'] = 'The dilation value (window) used for the WCT calculations.'
    geom_dts.dilation.attrs['units'] = 'm'
   
    geom_dts['wavelength'] = float(wavelength)
    geom_dts.wavelength.attrs['long_name'] = 'The wavelength of the ELDA product used to obtain the geometrical properties'
    geom_dts.wavelength.attrs['units'] = 'nm'

    geom_dts['residual_layer_flag'] = geom_dts['residual_layer_flag'].astype('int32')
    geom_dts.residual_layer_flag.attrs['values'] = '0 for normal layers, 1 for the residual layer'
    geom_dts.residual_layer_flag.attrs['long_name'] = 'Flag for the first layer.It is 1 when its true base is not identified. In this case, the first range bin is used as the base instead and the layer is marked as a potential candidate for the residual layer'
    geom_dts.residual_layer_flag.attrs['units'] = ''

    geom_dts.base.attrs['long_name'] = 'The layer base (ASL)'
    geom_dts.base.attrs['units'] = 'm'
    
    geom_dts.center_of_mass.attrs['long_name'] = 'The layer center of mass. It is the average altitude weighted by the product values (ASL)'
    geom_dts.center_of_mass.attrs['units'] = 'm'
    
    geom_dts.top.attrs['long_name'] = 'The layer top (ASL)'
    geom_dts.top.attrs['units'] = 'm'
    
    geom_dts.peak.attrs['long_name'] = 'The height of the backscatter maximum within the layer (ASL)'
    geom_dts.peak.attrs['units'] = 'm'
    
    geom_dts.thickness.attrs['long_name'] = 'The layer thickness (top - base)'
    geom_dts.thickness.attrs['units'] = 'm'
    
    geom_dts.base_sig.attrs['long_name'] = 'The backscatter value at the base of the layer'
    geom_dts.base_sig.attrs['units'] = 'm-1 sr-1'
    
    geom_dts.top_sig.attrs['long_name'] = 'The backscatter value at the top of the layer'
    geom_dts.top_sig.attrs['units'] = 'm-1 sr-1'
    
    geom_dts.peak_sig.attrs['long_name'] = 'The backscatter value at the peak of the layer'
    geom_dts.peak_sig.attrs['units'] = 'm-1 sr-1'
    
    geom_dts.depth.attrs['long_name'] = 'Integrated backscatter within the layer'
    geom_dts.depth.attrs['units'] = 'sr-1'

    geom_dts.sharpness.attrs['long_name'] = 'Minimum absolute difference between the backscatter value at the peak and the product value at the base or top'        
    geom_dts.sharpness.attrs['units'] = 'm-1 sr-1'
    
    geom_dts.trend.attrs['long_name'] = 'Difference between the backscatter value at the top and the backscatter value at the base'        
    geom_dts.trend.attrs['units'] = 'm-1 sr-1'

    geom_dts.weight.attrs['long_name'] = 'Fraction of the integrated backscatter within the layer to the whole columnar integral'
    geom_dts.weight.attrs['units'] = ''
    
    if dir_out and save_netcdf:
        if subfolder in [None, '']:
            sdir_out = dir_out
        else:
            sdir_out = os.path.join(dir_out, subfolder)
        
        os.makedirs(sdir_out, exist_ok=True)

        out_path = os.path.join(sdir_out, fname)
        geom_dts.to_netcdf(out_path, engine="scipy",
                           mode = 'w', encoding = encoding)
        
    return(geom_dts)

def nc_name(ver, st_id, prod_type_id, wavelength, prod_id, 
            start_time, stop_time, ms_id):
    
    fname = None
        
    if st_id:
        fname = '_'.join(filter(None, [fname, str(st_id)]))

    if prod_type_id:
        fname = '_'.join(filter(None, [fname, str(prod_type_id)]))

    if wavelength:
        fname = '_'.join(filter(None, [fname, str(wavelength)]))
        
    if prod_id:
        fname = '_'.join(filter(None, [fname, str(prod_id)]))
    
    if start_time:
        fname = '_'.join(filter(None, [fname, str(start_time)]))
    
    if start_time and stop_time:
        fname = '_'.join(filter(None, [fname, str(stop_time)]))

    if ms_id:
        fname = '_'.join(filter(None, [fname, str(ms_id)]))
        
    fname = '_'.join(filter(None, [fname, 'ltool', f'v{str(ver)}'])) + '.nc'

    return(fname)

def ascii_safe(s):
    if not isinstance(s, str):
        s = str(s)
    
    for k, v in REPLACEMENTS.items():
        s = s.replace(k, v)
    
    return (
        unicodedata.normalize("NFKD", s)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
