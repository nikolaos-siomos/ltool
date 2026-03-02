#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 27 09:23:20 2025

@author: nikos
"""

import os
import argparse
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

PathLike = Union[str, Path]

def could_be_dir(path_str: str) -> bool:
    try:
        Path(path_str)
    except Exception:
        return False
    return True

def absolute_existing_file_or_dir(p: str) -> str:
    """
    Argparse 'type' validator: must be an absolute path to an existing file OR directory.
    Returns the original string (argparse convention), but validation happens here.
    """
    path = Path(p)

    if not path.exists():
        raise Exception(f"Path does not exist: {p}")

    if not (path.is_file() or path.is_dir()):
        raise Exception(f"Path must be a file or directory: {p}")

    if not path.is_absolute():
        raise Exception(f"Path must be absolute: {p}")

    return str(path)

def get_base_dir(input_path: PathLike) -> Path:
    p = Path(input_path)
    
    if not p.exists():
        raise Exception(
            f"Provided input_path does not exist: {input_path}"
        )
    
    return p if p.is_dir() else p.parent

def resolve_export_dir(
    input_path: PathLike,
    export_arg: Optional[str],
) -> Path:
    """
    Resolve an export directory.

    Rules:
    - If export_arg is None:
        -> default to <base_dir>/<default_leaf> (may not exist yet)
    - If export_arg is relative:
        -> resolve relative to base_dir
    - If export_arg is absolute:
        -> use as-is
    """
    base_dir = get_base_dir(input_path)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_leaf = f'output_{ts}'
    if export_arg is None:
        export_path = base_dir / '..' /default_leaf

    else:
        probably_dir = could_be_dir(export_arg)
        if not probably_dir:
            raise Exception(
                f"Provided output_folder cannot be an absolute or relative path: {export_path}"
            )
        export_path = Path(export_arg)

        
        if export_path.is_absolute():
            export_path = export_path / default_leaf
        else:
            export_path = base_dir / export_path / default_leaf
        
    return export_path.resolve()


def collect_ltool_settings(argv=None):

    parser = argparse.ArgumentParser(description="Collect ltool settings from command line arguments.")

    # NEW: file-or-dir absolute input
    parser.add_argument(
    '--input_path',
    type=absolute_existing_file_or_dir,
    required=True,
    help=(
        "Absolute path to an input directory or a single input file. "
        "This path defines the base_dir used to resolve output folders."
        )
    )


    parser.add_argument('--alpha', type=float, default=600., help='Dilation alpha value in meters (default: 600.)')
    
    parser.add_argument('--snr_factor', type=float, default=3.291, help='Signal to noise ratio threshold (default: 3.291)')
    
    parser.add_argument('--wct_peak_margin', type=float, default=0.7, help='Wavelet Covariance Transformation (WCT) peak margin (default: 0.7)')

    parser.add_argument('--wavelength', type=str, choices=['None', '355', '532', '1064'],
                        default='None', help="Wavelength (options: None, 355, 532, 1064; default: None)")

    parser.add_argument('--method', type=str, choices=['height_based', 'wct_based', 'snr_based', 'prm_based', 'optimized_wct', 'optimized_snr', 'optimized_prm'],
                        default='optimized_prm', help="Method applied for selecting layer boundaries...")

    parser.add_argument('--debug', action='store_true', default=False, help="Show text messages indicating the processing stage.Useful for debugging")

    parser.add_argument('--show_plots', action='store_true', default=False, help="Show plots")

    parser.add_argument('--save_plots', action='store_true', default=False, help="Enable to save the layer plots")

    parser.add_argument('--save_netcdf', action='store_true', default=False, help="Enable to save the layer boundaries and properties in SCC netcdf file format")

    parser.add_argument('--plot_max_height', type=float, default=15., help="Maximum height for the y axis in the layer plots. The units must be as given by plot_height_units (km_asl by default")

    parser.add_argument('--plot_height_units', type=str, default='km_asl', choices=['km','km_asl','km_agl','m','m_asl','m_agl'],
                        help="The y axis units for height. Defaults in km_asl")

    parser.add_argument('--plot_product_type', choices=['BSC', 'EXT', 'PLDR', 'SIG'], type=str, default="BSC", help="Product type used for the layer plots. It determines the x axis label and units.")

    parser.add_argument('--dpi', type=int, default=100, help="Plot resultion (dpi)")

    parser.add_argument(
        '--output_folder',
        type=str,
        default=None,
        help=(
            "Directory where the netcdf and plot folders will be saved.\n"
            "Resolution rules:\n"
            "  • If omitted: defaults to <base_dir>/../output_<timestamp>\n"
            "  • If relative: resolved relative to <base_dir>/output_<timestamp>\n"
            "  • If absolute: <base_dir>/output_<timestamp>\n"
            "\n"
            "base_dir is defined as:\n"
            "  • input_path, if input_path is a directory\n"
            "  • parent directory of input_path, if input_path is a file"
        )
    )
    
    parser.add_argument(
        "--include-glob",
        action="append",
        default=[],
        help=(
            "Filename glob pattern(s) to include (can be used multiple times). "
            "Matched against the filename only (not full path). "
            "Example: --include-glob '*_AerRemSen_*' --include-glob '*_elda_*'"
        ),
    )
    
    parser.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help=(
            "Filename glob pattern(s) to exclude (can be used multiple times). "
            "Matched against the filename only. Example: --exclude-glob '*quicklook*'"
        ),
    )
    
    parser.add_argument(
        "--name-regex",
        type=str,
        default=None,
        help=(
            "Optional regex applied to the filename (not full path). "
            "Example: --name-regex '.*_AerRemSen_.*_b(0355|0532).*'"
        ),
    )
    
    parser.add_argument(
        "--netcdf-ext",
        action="append",
        default=[".nc"],
        help=(
            "Allowed NetCDF file extension(s). Can be used multiple times. "
            "Default: .nc. Example: --netcdf-ext .nc --netcdf-ext .nc4"
        ),
    )
    
    args = parser.parse_args(argv)

    check_args(args, parser)

    args = modify_args(args)

    create_directories(args)

    ltool_settings = vars(args)

    return ltool_settings

def check_args(args, parser):
    # input_path is validated by argparse type=absolute_existing_file_or_dir
    # but you can keep this if you want a clearer error location:
    p = Path(args.input_path)
    if not p.is_absolute() or not p.exists() or not (p.is_file() or p.is_dir()):
        parser.error(f"Invalid input_path: {p}")


def modify_args(args):
    # Process wavelength
    args.wavelength = None if args.wavelength == 'None' else args.wavelength.zfill(4)

    # Resolve output directories
    args.output_folder = resolve_export_dir(
        args.input_path,
        args.output_folder,
    )


    return args

def create_directories(args):
    
    if args.save_plots or args.save_netcdf:
        os.makedirs(args.output_folder, exist_ok = True)
