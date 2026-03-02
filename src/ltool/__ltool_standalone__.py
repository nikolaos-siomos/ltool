#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:20:01 2026

@author: Nikolaos Siomos
"""

import sys
import numpy as np
from .readers.generic_reader import list_input_netcdf_files, \
    read_product_file, check_arrays
from .__ltool__ import get_layers 
from .readers.parse_options import collect_ltool_settings

def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]
            
    # Collect argument options
    ltool_settings = collect_ltool_settings(argv)
    
    files = list_input_netcdf_files(
        input_path=ltool_settings["input_path"],
        wavelength=ltool_settings["wavelength"],
        include_globs=ltool_settings.get("include_glob", []),
        exclude_globs=ltool_settings.get("exclude_glob", []),
        name_regex=ltool_settings.get("name_regex", None),
        allowed_exts=ltool_settings.get("netcdf_ext", [".nc"]),
    )
    
    list_geom = []
    list_obj = []
    
    # Geometrical retrievals
    for file in files:
    
        if ltool_settings["debug"]:
            print("------------------------------------------")
            print(f"A) Reading file: {file}")
            print("------------------------------------------")
            
        metadata, profiles = read_product_file(file)
        
        bad_profile = check_arrays(profiles)    
        
        if not bad_profile:
            # Layer calculations
            layer_obj = get_layers(
                height = np.copy(profiles['height']), 
                sig = np.copy(profiles['product']), 
                sig_err = np.copy(profiles['product_error']), 
                alpha = ltool_settings['alpha'], 
                snr_factor = ltool_settings['snr_factor'], 
                wct_peak_margin = ltool_settings['wct_peak_margin'],
                method = ltool_settings['method'],
                debug = ltool_settings["debug"],
                )
        
            plot_fname = layer_obj.visualize(
                dir_out = ltool_settings["output_folder"],
                max_height = ltool_settings["plot_max_height"],
                height_units = ltool_settings["plot_height_units"],
                dpi_val = ltool_settings["dpi"],
                prod_id = ltool_settings["plot_product_type"],
                show = ltool_settings["show_plots"],
                save_plots = ltool_settings["save_plots"],
                debug = ltool_settings["debug"],
                **metadata
                )
       
            geom_dts, netcdf_fname = layer_obj.export_to_netcdf(
                dir_out = ltool_settings["output_folder"],
                save_netcdf = ltool_settings["save_netcdf"],
                debug = ltool_settings["debug"],
                **metadata
                )
            
            list_geom.append(geom_dts)
            list_obj.append(layer_obj)
    
    list_geom = list_geom[0] if len(list_geom) == 1 else list_geom
    list_obj = list_obj[0] if len(list_obj) == 1 else list_obj
        
    return list_geom, list_obj

if __name__ == "__main__":
    
    list_geom = main()
    