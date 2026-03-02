#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 14:20:01 2026

@author: Nikolaos Siomos
"""

from ltool.__ltool_standalone__ import main as ltool

if __name__ == "__main__":
    # # Example using EARLINET DB backscatter files
    # argv = [
    #     "--input_path",
    #     "/home/nikos/Big_Data/EARLINET_testing/raw_all_sorted/test/SCC/",
    #     "--include-glob",
    #     # "*_b*",
    #     "*_003_*_elda_*",
    #     "--method",
    #     "optimized_prm",
    #     # "--show_plot",
    #     "--save_plots",
    #     "--save_netcdf",

    # ]
   
    argv = [
    # Example using SCC backscatter files
        "--input_path",
        "/home/nikos/Big_Data/EARLINET_testing/raw_all_sorted/test/EARL/",
        "--include-glob",
        "*_b*",
        "--method",
        "optimized_prm",
        "--show_plot",
        "--save_plots",
        "--save_netcdf",
        ]
    geom, obj = ltool(argv)
