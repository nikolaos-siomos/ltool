#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun May 28 12:54:41 2017

@author: nick
"""
import numpy as np
from scipy.signal import find_peaks
import xarray as xr
import warnings
from .._compat import trapezoid

warnings.filterwarnings("ignore")
    
def get_geometrical_properties(rl_flag, bases, tops, height, sig):

    geom = None
    # Calculate layer thickness, center of mass, peak, and weight of the layer (ratio to the total integrated product)
    if len(bases) > 0:
        tck = np.round(tops - bases, decimals = 5)
        com = np.nan*np.zeros(bases.shape)
        dpth = np.nan*np.zeros(bases.shape)
        peak = np.nan*np.zeros(bases.shape) 
        bsig = np.nan*np.zeros(bases.shape) 
        tsig = np.nan*np.zeros(bases.shape) 
        psig = np.nan*np.zeros(bases.shape) 
        msig = np.nan*np.zeros(bases.shape) 
        shrp = np.nan*np.zeros(bases.shape) 
        trnd = np.nan*np.zeros(bases.shape) 
        wgh = np.nan*np.zeros(bases.shape)
        
        # Mask out nans 
        mask = (sig == sig)
        
        sig = sig[mask]
        height = height[mask]
        
        for i in range(bases.shape[0]):
            
            sig_l = sig[(height >= bases[i]) & (height <= tops[i])]
            height_l = height[(height >= bases[i]) & (height <= tops[i])]
            
            bases[i] = np.round(bases[i], decimals = 5) 
            tops[i] = np.round(tops[i], decimals = 5) 

            com[i] = np.round(trapezoid(sig_l*height_l, x = height_l)/
                              trapezoid(sig_l, x = height_l), decimals = 5)
            
            dpth[i] = np.round(trapezoid(sig_l, x = height_l)/
                               (tck[i]), decimals = 9)         
            
            wgh[i] = np.round(trapezoid(sig_l, x = height_l)/
                              (trapezoid(sig, x = height)), decimals = 5)         
            
            mask_max = (sig_l == np.nanmax(sig_l))

            peak[i] = np.round(height_l[mask_max][-1], decimals = 5)
            psig[i] = np.round(sig_l[mask_max][-1], decimals = 9)
            bsig[i] = np.round(sig_l[0], decimals = 9)
            tsig[i] = np.round(sig_l[-1], decimals = 9)
            msig[i] = np.round(np.min([bsig[i], tsig[i]]), decimals = 9)
            shrp[i] = np.round((psig[i] - np.max([bsig[i], tsig[i]])), 
                               decimals = 9)
            trnd[i] = np.round((tsig[i] - bsig[i]), decimals = 9)


        # Export to xarray Data Array, ensure there are layers left after removing the insignificant ones
        if len(bases) > 0:
            features = ['residual_layer_flag', 'base', 'center_of_mass', 'top', 
                        'peak', 'thickness', 'base_sig', 'top_sig', 'peak_sig', 
                        'depth', 'sharpness', 'trend', 'weight']
            layers = np.arange(1, bases.shape[0]+1, 1)
            layer_data = np.vstack((rl_flag.astype(object), 
                                    bases.astype(object), 
                                    com.astype(object), 
                                    tops.astype(object), 
                                    peak.astype(object), 
                                    tck.astype(object), 
                                    bsig.astype(object), 
                                    tsig.astype(object), 
                                    psig.astype(object), 
                                    dpth.astype(object),
                                    shrp.astype(object),
                                    trnd.astype(object),
                                    wgh.astype(object))).T
            layer_data = layer_data
            geom = xr.DataArray(data = layer_data, 
                                coords = [layers, features], 
                                dims = ['layers','features'],
                                name = 'geometrical_properties')
        
    return(geom)


def get_layer_features(height, sig, sig_err, wct, wct_err, snr_factor):
    
    # Make the error positive to be on the safe side....
    sig_err = np.abs(sig_err)
    sig_err[sig_err == 0.] = 1e-8

    wct_err = np.abs(wct_err)
    wct_err[wct_err == 0.] = 1e-8
    
    # Index of potential features
    b_index = find_peaks(wct)[0]
    t_index = find_peaks(-wct)[0]
    
    # Calculate base/top snr
    b_snr = np.abs(wct[b_index] / wct_err[b_index]) 
    t_snr = np.abs(wct[t_index] / wct_err[t_index])  
    
    # Filter out features with normalized wct values below the thershold
    b_index = b_index[b_snr > snr_factor]
    t_index = t_index[t_snr > snr_factor]

    b_snr = b_snr[b_snr > snr_factor]
    t_snr = t_snr[t_snr > snr_factor]
    
    # Set the flag to one (normal layer) for all bases/tops
    b_flag = np.zeros_like(b_index)
    t_flag = np.ones_like(t_index)
    
    # Setting dataframes of potential features     
    bases_data = np.vstack((b_index,
                            height[b_index],
                            sig[b_index], 
                            sig_err[b_index], 
                            wct[b_index],
                            wct_err[b_index],
                            b_snr,
                            b_flag)).T
    
    tops_data  = np.vstack((t_index,
                            height[t_index],
                            sig[t_index], 
                            sig_err[t_index], 
                            wct[t_index],
                            wct_err[t_index],
                            t_snr,
                            t_flag)).T

    features = ['array_index', 'height', 'sig', 'sig_err', 'wct', 'wct_err', 
                'snr', 'flag']
    
    bases_dtf = xr.DataArray(bases_data,
                             dims = ('height','features'),
                             coords = (height[b_index], features))
   
    tops_dtf  = xr.DataArray(tops_data,
                            dims = ('height','features'),
                            coords = (height[t_index], features))
    
   
    return(bases_dtf, tops_dtf)

def concatenate_layer_features(bases, tops):
    
    # Combine bases and tops in merged and sort by height    
    merged = xr.concat([bases.copy(), tops.copy()], dim = 'height').sortby('height')
    
    # Indexes of bases below the last top
    last_base_index = np.where(bases.loc[:,'height'] <= tops.loc[:,'height'].max())[0]

    # Ensure that the last feature is a top
    if len(last_base_index) > 0:
        last_base_height = bases.height[last_base_index[-1]].values
        merged = merged.copy().loc[:last_base_height,:]

    return(merged)

def identify_coarse_layer_regions(flag, height, ground_elevation):
    
    # Find a top-base pattern that marks the certain change of layer
    pattern_index = np.where(flag[:-1] - flag[1:] == 1)[0]
    
    # Find the coarse layer regions - as long as merged is not empty, there is always a layer because the last feature is always a top
    layer_region_bases = np.nan * np.zeros(len(pattern_index) + 1)
    layer_region_tops = np.nan * np.zeros(len(pattern_index) + 1)
    
    if len(pattern_index) > 0:
        layer_region_bases[1:] = height[pattern_index]
        layer_region_tops[:-1] = height[pattern_index]
            
    # The first coarse region base is always the ground elevation (0 if agl units are used)
    layer_region_bases[0] = ground_elevation

    # The last coarse region top is always the last top 
    layer_region_tops[-1] = height[-1]
    
    return(layer_region_bases, layer_region_tops)
    
def get_feature_index(flag, height, wct, snr, wct_peak_margin,
                      layer_region_base, layer_region_top, method):
    
    mask_region = (height >= layer_region_base) and (height <= layer_region_top) 
    
    mask_bases = (flag == 0) and (mask_region == True)
    mask_tops = (flag == 1) and (mask_region == True)
    
    potential_base_height = height[mask_bases]
    potential_top_height = height[mask_tops]
    
    potential_base_wct = np.abs(wct[mask_bases])
    potential_top_wct = np.abs(wct[mask_tops])

    potential_base_nrm_max = potential_base_wct / np.max(potential_base_wct)
    potential_top_nrm_max = potential_top_wct / np.max(potential_top_wct)
    
    potential_base_snr = snr[mask_bases]
    potential_top_snr = snr[mask_tops]
    
    if method == 'height_based':
        layer_top_index = np.argmax(potential_top_height)
    
    if method == 'wct_based':
        layer_top_index = np.argmax(potential_top_wct)
        
    if method == 'snr_based':
        layer_top_index = np.argmax(potential_top_snr)
    
    if method == 'optimized':
        layer_top_index = np.argmax(potential_top_height[potential_top_nrm_max >= wct_peak_margin])            
    
    if mask_tops.any() == True:
        residual_layer_flag = 0
        
        if method == 'height_based':
            layer_base_index = np.argmin(potential_base_height)
        
        if method == 'wct_based':
            layer_base_index = np.argmax(potential_base_wct)
        
        if method == 'snr_based':
            layer_base_index = np.argmin(potential_base_snr)
            
        if method == 'optimized':
            layer_base_index = np.argmin(potential_base_height[potential_base_nrm_max >= wct_peak_margin])

    else:
        residual_layer_flag = 1

        layer_base_index = np.nan
        
    return(layer_base_index, layer_top_index, residual_layer_flag)
    
def determine_layer_boundaries(bases, tops, snr_factor, wct_peak_margin, 
                               ground_elevation, method = 'optimized'):
    
    # Check if the provided method is correct
    check_method(method)
    
    # Combine bases and tops dataframes in a signle dataframe sorted by ascending index
    merged = concatenate_features(bases = bases, tops = tops)

    # Unpack the xarray into numpy arrays
    flag = merged.loc[:,'flag'].copy().values
    height = merged.loc[:,'height'].copy().values
    wct = merged.loc[:,'wct'].copy().values
    snr = merged.loc[:,'snr'].copy().values
            
    # Layer bases and tops will appended in lists
    layer_bases = []
    layer_tops = []
    residual_layer_flags = []
    
    if len(merged) > 0:
        
        # First the coarser layer region is marked by finding a top succeded by a base pattern
        layer_region_bases, layer_region_tops = \
            identify_coarse_layer_regions(flag = flag, 
                                          height = height, 
                                          ground_elevation = ground_elevation)

        # Iterate over the coarse layer regions and detect the actual layer boundaries
        for i in range(len(layer_region_bases)):
            
            layer_base_index, layer_top_index, residual_layer_flag = \
                get_feature_index(
                flag = flag, 
                height = height, 
                wct = wct, 
                snr = snr, 
                wct_peak_margin = wct_peak_margin,
                layer_region_base = layer_region_bases[i], 
                layer_region_top = layer_region_tops[i], 
                method = method
                )
            
            # Append bases, tops, and the residual layer flag in lists
            if residual_layer_flag == 0:
                base_height = height[layer_base_index]
            else:
                base_height = ground_elevation
                
            top_height = height[layer_top_index]
            
            layer_bases.append(base_height)
            layer_tops.append(top_height)
            residual_layer_flags.append(residual_layer_flag)
        
        
    # Convert to numpy arrays 
    layer_bases = np.array(layer_bases)
    layer_tops = np.array(layer_tops)
    residual_layer_flags = np.array(residual_layer_flags)
    
    return(layer_bases, layer_tops, residual_layer_flags)

def check_method(method):
    
    allowed_methods = ['height_based', 'wct_based', 'snr_based', 'optimized']
    
    if method not in allowed_methods:
        raise Exception(f"The selected method ({method}) is not supporte. Please select one of: {allowed_methods}")
    
    return
