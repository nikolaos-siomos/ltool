#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 11:15:48 2016

@author: lidar2
"""
import warnings, datetime
from .layering_functions.geometrical_calculations import get_layer_features, \
    calculate_geometrical_properties, determine_layer_boundaries
# from .layering_functions.checks import height_checks
from .layering_functions.wavelet import wct_calculation, get_first_valid_height
from .export_layers.export_nc import export_nc
from .export_layers.plot import plot_layers
from .version import __version__
from xarray import DataArray

#Ignores all warnings --> they are not printed in terminal
warnings.filterwarnings('ignore')  
    
class get_layers():
    
    """
    This class identifies the layer boundaries from lidar product and/or 
    signal profiles based on the wavelet covariance transform (WCT) method 
    taking into account the uncertainty of the lidar profile. 
    
    Input:
        
    height : 1D array float
        An array containing the height values of the lidar profile in 
        Expected units: m_asl

    sig : 1D array float
        An array containing the lidar profile (product or signal) 
        values of the lidar profile
    
    sig_err : 1D array float
        An array containing the lidar profile uncertainty (product or signal) 
        values of the lidar profile
        
    alpha : float
        The WCT dilation in the same units as height
    
    snr_factor : float
        Signal-to-noise ratio scaling factor used to validate boundary features
        
    wct_peak_margin : float
        Peak selection threshold used to reject weak adjacent WCT features and pick a single base/top.
        
    method: str
        Layer boundary selection method.
        
    debug : bool
        If set to True messages will be printed indicating the processing status
        Defaults to: False
    
    Calling the class get_layers creates an object with the following 
    information stored in addition to all input parameters:
        
    version : str
        The ltool code version
        
    wct : 1D array float
        An array containing the WCT profile (product or signal) 
        values of the lidar profile
    
    wct_err : 1D array float
        An array containing the WCT profile uncertainty (product or signal) 
        values of the lidar profile

    layers : 2D array float
        A 2D array containg the retrieved geometrical parameters for each layer
                
    start_time : datetime object
        A datetime object containing the starting time of the processing
    
    stop_time : datetime object
        A datetime object containing the rnding time of the processing
        
    duration : datetime object
        A datetime object containing the difference between start and stop time
            
    The class includes 2 functions that can be called by typing:
        <class_object>.export_to_netcdf(<args>)
        <class_object>.visualize(<args>)
        
    export_to_netcdf:
        This function generates a netcdf file with the retrieved
        geometrical property information and also some of the provided metadata
    
    visualize:
        This function generates a figure (.png file) with the layers ploted 
        against the lidar profile and the WCT profile

    """
    def __init__(self, height, sig, sig_err, alpha = 600., snr_factor = 3.291, 
                 wct_peak_margin = 0.7,  debug = False, method = 'optimized_prm'):

        if type(height) == type(DataArray()):
            height = height.copy().values

        if type(sig) == type(DataArray()):
            sig = sig.copy().values

        if type(sig_err) == type(DataArray()):
            sig_err = sig_err.copy().values
            
        # if type(ground_elevation) == type(DataArray()):
        #     ground_elevation = ground_elevation.copy().values
            
        # height, ground_elevation = \
        #     height_checks(height, height_units, ground_elevation, alpha) 
        
        self.version = __version__
        # self.height_units = height_units
        self.alpha = alpha
        self.snr_factor = snr_factor
        self.wct_peak_margin = wct_peak_margin
        # self.ground_elevation = ground_elevation
        self.debug = debug
        
        self.height = height
        self.sig = sig
        self.sig_err = sig_err
        
        start_time = datetime.datetime.now()
        self.start_time = start_time
        
    # 1) Identify layers and each base and top
        if self.debug:
            print("------------------------------------------")
            print("B) Identifying layer boundaries")
            
        # First valid index and height
        first_valid_idx, first_valid_height = \
            get_first_valid_height(height, sig)

        # Wavelet covariance transform
        if self.debug:
            print("-- Applying Wavelet Covariance Transform")
        wct, wct_err, wct_mc = wct_calculation(
            height = height, 
            product = sig, 
            product_error = sig_err, 
            alpha = alpha
            )
    
        self.wct = wct
        self.wct_err = wct_err
        self.wct_mc = wct_mc
        self.first_valid_idx = first_valid_idx
        self.first_valid_height = height[first_valid_idx]

        # Identify all valid bases and tops
        if self.debug:
            print("-- Identifying valid boundaries ")
        bases, tops = get_layer_features(
            height = height, 
            sig = sig, 
            sig_err = sig_err, 
            wct = wct, 
            wct_err = wct_err,
            wct_mc = wct_mc,
            snr_factor = snr_factor
            )

        self.all_bases = bases
        self.all_tops = tops
        
        # Create base-top pairs out of all potential features
        if self.debug:
            print("-- Pairing bases and tops ")
        layer_features = \
            determine_layer_boundaries(
                bases = bases,
                tops = tops,
                snr_factor = snr_factor, 
                wct_peak_margin = wct_peak_margin,
                first_valid_height = first_valid_height,
                method = method,
                debug = debug
                )
        self.layer_features = layer_features        

    # 2) Use base and top to the profile to extract additional geometrical properties
        if self.debug:
            print("------------------------------------------")
            print("C) Calculating layer properties")
            print("------------------------------------------")
        layers = calculate_geometrical_properties(
            layer_features = layer_features,
            height = height, 
            sig = sig
            )
        
        stop_time = datetime.datetime.now()
        duration = stop_time - start_time
        
        self.stop_time = stop_time
        self.duration = duration
        self.layers = layers
    
    ###############################################################################
    # C) Exporting
    ###############################################################################
    def export_to_netcdf(self, dir_out = None, metadata = None,
                         prod_type_id = None, 
                         prod_id = None, debug = True,
                         save_netcdf = True, subfolder = 'netcdf',
                         *, station_ID:str = None,  
                         wavelength:str = None, 
                         start_time:str = None, stop_time:str = None, 
                         measurement_ID:str = None,
                         **_extras):
    
        """
        This function generates a figure (.png file) with the layers ploted 
        against the lidar profile and the WCT profile
        
        Input (optional):
                
        dir_out : str
            Path to the directory where the netcdf file will be created. 
        
        metadata : dicttionary
            A dictionary containing all additional metadata to be stored in the
            netcdf file
            
        st_id : str
            The lidar station identifier
        
        prod_type_id : int
            The SCC product type ID. Applied for the implementation to the SCC 
            
        wavelength : float
            The corresponding wavelength of the lidar signal/product 
            in nanometers

        prod_id : int
            The SCC product ID. Applied for the implementation to the SCC 
            
        start_time : str
            A string containing the starting date/time of the lidar profile
        
        stop_time : str
            A datetime object containing the ending date/time of the lidar profile
            
        ms_id : str
            A string scalar containing the measurement ID
            
        debug : bool
            If set to True messages will be printed indicating the processing status
            
        save_netcdf : bool
            If set to False netcdf files will not be saved 
            
        subfolder : str
            Name of the subfolder inside which the saved netcdf files are placed
            Provide '' to place files in the dir_out folder
            
        """
                    
        # 1) Netcdf filename
        if debug:
            print("---- Creating netcdf filename ")
        
        # fname = nc_name(ver = self.version, 
        #                 st_id = st_id, 
        #                 prod_type_id = prod_type_id, 
        #                 wavelength = wavelength, 
        #                 prod_id = prod_id,
        #                 start_time = start_time, 
        #                 stop_time = stop_time, 
        #                 ms_id = ms_id)
        
        unpacked = {
            'measurement_ID':measurement_ID,
            'station_ID':station_ID,
            'wavelength':float(wavelength)
            }
        
        fname = output_name(ver = self.version, 
                            st_id = station_ID, 
                            prod_type_id = prod_type_id, 
                            wavelength = wavelength, 
                            prod_id = prod_id,
                            start_time = start_time, 
                            stop_time = stop_time, 
                            ms_id = measurement_ID,
                            extension = 'nc')
                
        # 2) Netcdf file 
        if self.layers is not None:     
            if debug:
                print("---- Exporting to netcdf ")
            
            metadata = unpacked.copy()
            metadata.update(_extras)

            geom_dts = \
                export_nc(layers = self.layers, 
                          metadata = metadata, 
                          alpha = self.alpha, 
                          wavelength = wavelength, 
                          snr_factor = self.snr_factor, 
                          wct_peak_margin = self.wct_peak_margin, 
                          version = self.version, 
                          fname = fname, 
                          dir_out = dir_out,
                          save_netcdf = save_netcdf,
                          subfolder = subfolder)
    
        else: 
            geom_dts = None
            if debug:
                print("---- Exporting to netcdf FAILED: No layers were identified for this measurement! ")

        return(geom_dts, fname)

    def visualize(
            self, dir_out:str = None, max_height:float = 10., 
            max_sig:float = None, max_abs_wct:float = None, 
            dpi_val:int = 100, show:bool = False, debug:bool = True, 
            units:str = r'$Mm^{-1} sr^{-1}$', scale_factor:float = 1E6,
            prod_label:str = r'$β_\mathrm{p}$', prod_id:str = None,
            prod_type_id:str = None, save_plots = True,
            height_units:str = 'km_asl', subfolder = 'plots',
            *, station_ID:str = None,  
            wavelength:str = None, 
            start_time:str = None, stop_time:str = None, 
            measurement_ID:str = None,
            **_extras
            ):
        
        """
        This function generates a netcdf file with the retrieved geometrical 
        property information and also some of the provided metadata
        
        Input (optional):
                
        dir_out : str
            Path to the directory where the plot file will be created. 
            Defaults to the current working directory
            
        max_height : float
            Uppermost limit for the height axis. Defaults to: 10. km

        max_sig : float
            Uppermost limit for the signal/product axis
                        
        station_ID : str
            The lidar station identifier
        
        prod_type_id : float
            The SCC product type ID. Applied for the implementation to the SCC 
            
        wavelength : float
            The corresponding wavelength of the lidar signal/product 
            in nanometers
        
        prod_id : int
            The SCC product ID. Applied for the implementation to the SCC 

        start_time : str
            A string containing the starting date/time of the lidar profile
        
        stop_time : str
            A datetime object containing the ending date/time of the lidar profile
            
        measurement_ID : str
            A string scalar containing the measurement ID

        show : bool
            If set to True the plot will be displayed as if plt.show() is called 
            
        save_plots : bool
            If set to False the plots will not be saved (they will still be plotted if show_plot is True)
            
        debug : bool
            If set to True messages will be printed indicating the processing status
            
        units : str
            Units used for the xaxis label for product and WCT
            Defaults to: r'$Mm^{-1} sr^{-1}$'

        height_units : str
            Units used for the yaxis label for height
                        
        scale_factor : float
            A scaling factor used to bring the product, WCT, and related errors
            to the desired units
            
        prod_label : str
            A description of the product used for the xaxis label
            
        subfolder : str
            Name of the subfolder inside which the saved netcdf files are placed
            Provide '' to place files in the dir_out folder
            
        """
        
        # 1) Plot filename
        if debug:
            print("---- Creating plot filename ")
           
        fname = output_name(ver = self.version, 
                            st_id = station_ID, 
                            prod_type_id = prod_type_id, 
                            wavelength = wavelength, 
                            prod_id = prod_id,
                            start_time = start_time, 
                            stop_time = stop_time, 
                            ms_id = measurement_ID,
                            extension = 'png')

        # 2) Generate Plot
        if debug:
            print("---- Generating plots ")
            
        plot_layers(dir_out = dir_out, 
                    fname = fname,
                    ms_id = measurement_ID,
                    layers = self.layers, 
                    height = self.height, 
                    sig = self.sig, 
                    sig_err = self.sig_err, 
                    wct = self.wct, 
                    wct_err = self.wct_err, 
                    wct_mc = self.wct_mc, 
                    max_height = max_height,
                    max_sig = max_sig,
                    max_abs_wct = max_abs_wct,
                    snr_factor = self.snr_factor,
                    prod_id = prod_id,
                    wavelength = wavelength,
                    units = units,
                    height_units = height_units,
                    scale_factor = scale_factor,
                    prod_label = prod_label,
                    dpi_val = dpi_val,
                    show = show,
                    save_plots = save_plots,
                    subfolder = subfolder)
        
        return fname

def output_name(ver, st_id, prod_type_id, wavelength, prod_id, 
                start_time, stop_time, ms_id, extension):
    
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
        
    fname = '_'.join(filter(None, [fname, 'ltool', f'v{str(ver)}'])) + f'.{extension}'

    return(fname)

def select_units(plot_product_type):
    
    unit_map = {
        "BSC": r'$Mm^{-1} sr^{-1}$',
        "EXT": r'$Mm^{-1}$',
        "PLDR": "",
        "SIG": "AU"
        }
    
    return unit_map[plot_product_type]

def select_symbol(plot_product_type):
    
    symbol_map = {
        "BSC": r'$β_\mathrm{p}$',
        "EXT": r'$α_\mathrm{p}$',
        "PLDR": r'$δ_\mathrm{p}$',
        "SIG": r'$S_\mathrm{RC}$'
        }
    
    return symbol_map[plot_product_type]

    
