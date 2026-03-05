#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:20:01 2026

@author: Nikolaos Siomos
"""

from ltool.__ltool_standalone__ import main as ltool

if __name__ == "__main__":
    # Example using EARLINET DB backscatter files
    argv = [
        "--input_path",
        "<absolute_path_to_input>",
        "--include-glob",
        # "*_b*",
        "*_003_*_elda_*",
        "--method",
        "optimized_prm",
        "--show_plot",
        "--save_plots",
        "--save_netcdf",
        "--enable_output_timestamp",
        "--output_folder",
        "<path_to_output>",

    ]
   
    geom, obj = ltool(argv)

    argv = [
    # Example using SCC backscatter files
        "--input_path",
        "<absolute_path_to_input>",
        "--include-glob",
        "*_b*",
        "--method",
        "optimized_prm",
        "--show_plot",
        "--save_plots",
        "--save_netcdf",
        "--enable_output_timestamp",
        "--output_folder",
        "<path_to_output>",
        ]
    geom, obj = ltool(argv)
