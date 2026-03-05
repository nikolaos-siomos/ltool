#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 21:31:10 2020

@author: nick
"""
import os
import numpy as np 

import matplotlib
matplotlib.use("Agg")

from matplotlib import pyplot as plt

def plot_layers(dir_out, fname, ms_id, layers, height, 
                sig, sig_err, wct, wct_err, wct_mc,
                max_height, max_sig, max_abs_wct, snr_factor, prod_label,
                prod_id, wavelength, show, dpi_val, units, height_units,
                scale_factor, save_plots = True, subfolder = 'plots'):
           
    height = np.round(height, decimals=2)
    
    sig = scale_factor * sig
    sig_err = scale_factor * sig_err
    
    wct = scale_factor * wct
    wct_err = scale_factor * wct_err
    wct_mc = scale_factor * wct_mc
    
    if height_units in ['km', 'km_asl', 'km_agl']:
        height = 1E-3 * height 
    
    if not max_abs_wct:
        max_abs_wct = 1.25 * np.nanmax(np.abs(wct))
    
    if not max_sig:
        max_sig = 1.25 * np.nanmax(sig[height <= max_height])

    if layers is not None:     
        if height_units in ['km', 'km_asl', 'km_agl']:
            bases = 1E-3 * layers.sel(features = 'base').values
            tops = 1E-3 * layers.sel(features = 'top').values
            coms = 1E-3 * layers.sel(features = 'center_of_mass').values
        else:
            bases = layers.sel(features = 'base').values
            tops = layers.sel(features = 'top').values
            coms = layers.sel(features = 'center_of_mass').values
    
    
    # Plots
    plt.figure(figsize=(5,5))
    if ms_id:
        plt.suptitle(f'Meas ID: {ms_id}')
        
    plt.subplot(122)
    if prod_id is not None and wavelength is not None:
        plt.title(f'Product: {prod_id} {wavelength}')
    else:
        plt.title('Product')
        
    xlims = [-0.05 * max_sig, max_sig]
    ylims = [0, max_height]
    if layers is not None:     
        for i in range(layers.shape[0]):
            if layers.sel(features='residual_layer_flag').values[i] == 1:
                clrs = ['gray', 'black', 'grey']
            if layers.sel(features='residual_layer_flag').values[i] == 0:
                clrs = ['purple', 'cyan', 'purple']
            plt.plot(xlims, [bases[i], bases[i]], color = clrs[0])
            plt.plot(xlims, [tops[i], tops[i]], color =  clrs[1])
            plt.plot(xlims, [coms[i], coms[i]], '--', color = 'goldenrod')
            plt.axhspan(bases[i], tops[i], facecolor = clrs[2], alpha = 0.2)
    plt.plot(sig, height, color = 'tab:blue')
    plt.fill_betweenx(height, sig - sig_err, 
                      sig + sig_err,
                      alpha = 0.3, color = 'tab:blue')
    plt.plot([0,0], ylims, '--', color = 'tab:brown')

    plt.axis(xlims + ylims)
    plt.xlabel(f'{prod_label} [{units}]')
    plt.ylabel(f'Height [{height_units}]')
    plt.grid()


    plt.subplot(121)
    plt.title('WCT')
    xlims = [-max_abs_wct, max_abs_wct]
    ylims = [0, max_height]
    if layers is not None:     
        for i in range(layers.shape[0]):
            if layers.sel(features='residual_layer_flag').values[i] == 1:
                clrs = ['gray', 'black', 'grey']
            if layers.sel(features='residual_layer_flag').values[i] == 0:
                clrs = ['purple', 'cyan', 'purple']
            plt.plot(xlims, [bases[i], bases[i]], color = clrs[0])
            plt.plot(xlims, [tops[i], tops[i]], color =  clrs[1])
            plt.plot(xlims, [coms[i], coms[i]], '--', color = 'goldenrod')
            plt.axhspan(bases[i], tops[i], facecolor = clrs[2], alpha = 0.2)
    if not np.isnan(wct).all():
        wct_min = np.min(wct_mc,axis = 0)
        wct_max = np.max(wct_mc,axis = 0)
        plt.fill_betweenx(height, wct_min - wct, 
                          wct_max - wct,
                          alpha = 0.3, color = 'tab:blue')
        plt.plot( wct, height, color='tab:blue')
            
    if not np.isnan(wct_err).all():
        plt.plot( snr_factor * wct_err, height, '--', color = 'darkgreen')
        plt.plot(-snr_factor * wct_err, height, '--', color = 'lightgreen')
    plt.axis(xlims + ylims)
    plt.xlabel(f'WCT [{units}]')
    plt.ylabel('Altitude [km]')
    plt.grid()
        
    if dir_out and save_plots:
        sdir_out = os.path.join(dir_out, subfolder)
        os.makedirs(sdir_out, exist_ok=True)
        plt.savefig(os.path.join(sdir_out, fname), dpi = dpi_val)
        
    if show:
        plt.show()
        
    plt.close('all') 
    
    return()
