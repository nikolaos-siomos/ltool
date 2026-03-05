#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:20:01 2026

@author: Nikolaos Siomos
"""

from ltool.__ltool_standalone__ import main as ltool
from pathlib import Path
import os 

script_dir = Path(__file__).resolve().parent

if __name__ == "__main__":

    # Test_methods on EARLINET file
    argv = [
        "--input_path",
        os.path.join(script_dir,"sample_files","EARL","EARLINET_AerRemSen_arr_Lev02_b0355_202006220525_202006220626_v02_qc03.nc"),
        "--method",
        "",
        "--save_plots",
        "--save_netcdf",
        "--output_folder",
        "",
        # "--show_plot",
    ]
   
    methods = ["height_based", "wct_based", "snr_based", "prm_based",
               "optimized_wct", "optimized_snr", "optimized_prm"]
    
    for method in methods:
        argv[3] = method
        argv[7] = os.path.join(script_dir,"output_single",method)
        geom, obj = ltool(argv)
    
    # Example using EARLINET DB backscatter files - no output folder
    argv = [
        "--input_path",
        os.path.join(script_dir,"sample_files","SCC"),
        "--include-glob",
        # "*_b*",
        "*_003_*_elda_*",
        "--method",
        "optimized_prm",
        # "--show_plot",
        "--save_plots",
        "--save_netcdf",

    ]
   
    geom, obj = ltool(argv)

    argv = [
    # Example using SCC backscatter files - absolute output folder
        "--input_path",
        os.path.join(script_dir,"sample_files","EARL"),
        "--include-glob",
        "*_b*",
        "--method",
        "optimized_prm",
        # "--show_plot",
        "--save_plots",
        "--save_netcdf",
        "--output_folder",
        os.path.join(script_dir,"output"),
        ]
    
    geom, obj = ltool(argv)
