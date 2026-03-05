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

def persistent_peaks_tolerant(
    wct_mc,
    *,
    k=1,
    fraction=1.0,
    **find_peaks_kwargs,
):
    """
    Find height indices where a peak is present in a given fraction of MC runs.

    Parameters
    ----------
    wct_mc : ndarray, shape (n_iter, n_height)
        Monte Carlo realizations.
    k : int
        Tolerance in index bins (±k).
    fraction : float in (0, 1]
        Required fraction of iterations containing a peak.
        1.0 = 100%, 0.95 = 95%, etc.
    **find_peaks_kwargs :
        Passed directly to scipy.signal.find_peaks.

    Returns
    -------
    persistent_idx : ndarray
        Indices that satisfy the persistence criterion.
    counts : ndarray
        Number of iterations contributing to each index.
    """

    if not (0 < fraction <= 1):
        raise ValueError("fraction must be in (0, 1]")

    n_iter, n_h = wct_mc.shape
    peak_mask = np.zeros((n_iter, n_h), dtype=bool)

    # Detect peaks per iteration
    for i in range(n_iter):
        p, _ = find_peaks(wct_mc[i], **find_peaks_kwargs)
        peak_mask[i, p] = True

    # Allow ±k-bin tolerance
    peak_mask_tol = peak_mask.copy()
    for shift in range(1, k + 1):
        peak_mask_tol[:, shift:] |= peak_mask[:, :-shift]
        peak_mask_tol[:, :-shift] |= peak_mask[:, shift:]

    # Count persistence
    counts = peak_mask_tol.sum(axis=0)
    min_count = int(np.ceil(fraction * n_iter))

    persistent_idx = np.where(counts >= min_count)[0]

    return persistent_idx, counts

def get_layer_features(height, sig, sig_err, 
                       wct, wct_err, wct_mc, snr_factor):
    
    # Make the error positive to be on the safe side....
    sig_err = np.abs(sig_err)
    sig_err[sig_err == 0.] = 1e-8

    wct_err = np.abs(wct_err)
    wct_err[wct_err == 0.] = 1e-8
    
    prm = np.abs(wct) - snr_factor * wct_err
    
    # Index of potential features
    b_index = find_peaks(wct)[0]
    t_index = find_peaks(-wct)[0]
    
    # b_index, _ = \
    #     persistent_peaks_tolerant(wct_mc, k=5, fraction = 0.95)
    # t_index,  _ = \
    #     persistent_peaks_tolerant(-wct_mc, k=5, fraction = 0.95)
    
    # Add indexes of end points
    valid_ind = np.where(wct == wct)[0]

    if len(valid_ind) > 1:
        s_ind = np.where(wct == wct)[0][0]
        e_ind = np.where(wct == wct)[0][-1]
        
        if np.abs(wct[s_ind]) > np.abs(wct[s_ind+1]):
            if wct[s_ind] > 0: 
                b_index = np.r_[s_ind, b_index]
            else:
                t_index = np.r_[s_ind, t_index]
                
        if np.abs(wct[e_ind]) > np.abs(wct[e_ind-1]):
            if wct[s_ind] > 0: 
                b_index = np.r_[b_index, e_ind]
            else:
                t_index = np.r_[t_index, e_ind]
                     
    # Calculate base/top snr
    b_snr = wct[b_index] / wct_err[b_index]
    t_snr = wct[t_index] / wct_err[t_index]  
    
    # Filter out features with normalized wct values below the thershold
    b_index = b_index[b_snr >  snr_factor]
    t_index = t_index[t_snr < -snr_factor]

    b_snr = b_snr[b_snr >  snr_factor]
    t_snr = t_snr[t_snr < -snr_factor]
    
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
                            prm[b_index],
                            b_snr,
                            b_flag)).T
    
    tops_data  = np.vstack((t_index,
                            height[t_index],
                            sig[t_index], 
                            sig_err[t_index], 
                            wct[t_index],
                            wct_err[t_index],
                            prm[t_index],
                            t_snr,
                            t_flag)).T

    features = ['array_index', 'height', 'sig', 'sig_err', 'wct', 'wct_err', 
                'prm', 'snr', 'flag']
    
    bases = xr.DataArray(bases_data,
                         dims = ('height','features'),
                         coords = (height[b_index], features))
   
    tops  = xr.DataArray(tops_data,
                         dims = ('height','features'),
                         coords = (height[t_index], features))
    
   
    return(bases, tops)

def determine_layer_boundaries(bases, tops, snr_factor, wct_peak_margin, 
                               first_valid_height, method, debug = True):
    
    # At least one top must be identified for ltool togenerate layers
    if len(tops) > 0:
        
        # Combine bases and tops dataframes in a signle dataframe sorted by ascending index
        merged = concatenate_layer_features(bases = bases, 
                                            tops = tops)

        # Unpack the xarray into numpy arrays
        flag = merged.loc[:,'flag'].copy().values
        height = merged.loc[:,'height'].copy().values
        wct = merged.loc[:,'wct'].copy().values
        snr = merged.loc[:,'snr'].copy().values
        prm = merged.loc[:,'prm'].copy().values
                
        # Layer bases and tops will appended in lists
        layer_bases = []
        layer_tops = []
        residual_layer_flags = []
        
        if len(merged) > 0:
            
            # First the coarser layer region is marked by finding a top succeeded by a base pattern
            layer_regions = \
                identify_coarse_layer_regions(
                    flag = flag, 
                    height = height, 
                    first_valid_height = first_valid_height
                    )

            # Iterate over the coarse layer regions and detect the actual layer boundaries
            if layer_regions.region.size > 0:
                for reg_id in layer_regions.region.values:
                    
                    layer_region_base = layer_regions.loc['base',reg_id].values
                    layer_region_top = layer_regions.loc['top',reg_id].values
                    
                    layer_base_index, layer_top_index, base_flag, top_flag = \
                        get_feature_index(
                        flag = flag, 
                        height = height, 
                        wct = wct, 
                        snr = snr, 
                        prm = prm,
                        wct_peak_margin = wct_peak_margin,
                        region_base = layer_region_base, 
                        region_top = layer_region_top, 
                        method = method
                        )  
    
                    # Append bases, tops, and the residual layer flag in lists
                    if base_flag == 0:
                        base_height = height[layer_base_index]
                    elif base_flag == 1:
                        base_height = first_valid_height
                    else:
                        raise Exception(f"Base flag {base_flag} not recognised. Allowed values: 0 or 1")
    
                    if top_flag == 0:                     
                        top_height = height[layer_top_index]
                        
                        layer_bases.append(base_height)
                        layer_tops.append(top_height)
                        residual_layer_flags.append(base_flag)
                        
                    elif top_flag == 1:
                        pass
                    
                    else:
                        raise Exception(f"Top flag {base_flag} not recognised. Allowed values: 0 or 1")
            
        # Convert to numpy arrays 
        layer_bases = np.array(layer_bases)
        layer_tops = np.array(layer_tops)
        residual_layer_flags = np.array(residual_layer_flags)
        
        layer_features = xr.DataArray(
            [layer_bases, layer_tops, residual_layer_flags], 
            dims = ['features', 'layers'],
            coords = [['base','top','flag'], range(len(layer_bases))])
        
    else:
        if debug:
            print("    -- Warning: No top identified --> No layers detected")
        layer_features = xr.DataArray(
            dims = ['features', 'layers'],
            coords = [['base','top','flag'], range(0)])
        
    return layer_features

def calculate_geometrical_properties(layer_features, height, sig):

    geom = None
    
    # Calculate layer thickness, center of mass, peak, and weight of the layer (ratio to the total integrated product)
    if layer_features.size > 0:
        
        bases = layer_features.loc['base',:].values
        tops = layer_features.loc['top',:].values
        residual_layer_flags = layer_features.loc['flag',:].values

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
            layer_data = np.vstack((residual_layer_flags.astype(object), 
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

def concatenate_layer_features(bases, tops):
    
    # Indexes of bases below the last top
    last_base_index = np.where(bases.loc[:,'height'] <= tops.loc[:,'height'].max())[0]

    # Remove bases that are above the last top and ensure that the last feature is a top
    if len(last_base_index) > 0:
        last_base_height = bases.height[last_base_index[-1]].values
        bases = bases.copy().loc[:last_base_height,:]
        
    # Combine bases and tops in merged and sort by height    
    merged = xr.concat([bases.copy(), tops.copy()], dim = 'height').sortby('height')

    return(merged)

def identify_coarse_layer_regions(flag, height, first_valid_height):
    
    # Find a top-base pattern that marks the certain change of layer
    pattern_index = np.where(flag[:-1] - flag[1:] == 1)[0]
    
    # Find the coarse layer regions - as long as merged is not empty, there is always a layer because the last feature is always a top
    layer_region_bases = np.nan * np.zeros(len(pattern_index) + 1)
    layer_region_tops = np.nan * np.zeros(len(pattern_index) + 1)
    
    if len(pattern_index) > 0:
        layer_region_bases[1:] = height[pattern_index]
        layer_region_tops[:-1] = height[pattern_index]
            
    # # The first coarse region base is always the first_valid_height
    layer_region_bases[0] = first_valid_height

    # The last coarse region top is always the last top 
    layer_region_tops[-1] = height[-1]
    
    # Save to Data Array
    regions = np.vstack(([layer_region_bases, layer_region_tops]))
    layer_regions = xr.DataArray(
        regions,
        dims = ['boundaries', 'region'],
        coords = [['base', 'top'], range(len(layer_region_bases)) ]
        )
    
    return(layer_regions)
    
def optimize_feature_selection(param, height, param_peak_margin, mode):
    
    abs_param = np.abs(param)
    abs_param_nrm = abs_param / np.nanmax(abs_param)
    
    mask_valid = (abs_param_nrm >= param_peak_margin) & \
        (abs_param_nrm == abs_param_nrm)
        
    valid_heights = height[mask_valid]
    
    if mode == 'base':
        best_feature_height = np.nanmin(valid_heights)
    elif mode == 'top':
        best_feature_height = np.nanmax(valid_heights)
    else:
        raise Exception(f"Provided mode {mode} not recognised. Allowed values: base, top")
    
    layer_feature_index = np.where(height == best_feature_height)[0][0]

    return layer_feature_index
    
def get_feature_index(flag, height, wct, snr, prm, wct_peak_margin,
                      region_base, region_top, method):

    mask_region = (height > region_base) & (height <= region_top) 
    
    mask_bases = (flag == 0) & (mask_region == True)
    mask_tops = (flag == 1) & (mask_region == True)

    if mask_tops.any():
        
        top_ind = np.where(mask_tops)[0]

        top_height = height[top_ind]
        top_wct = wct[top_ind]
        top_snr = snr[top_ind]
        top_prm = prm[top_ind]
        
        if method == 'height_based':
            region_top_index = np.nanargmax(top_height)
        
        if method == 'wct_based':
            region_top_index = np.nanargmax(np.abs(top_wct))
            
        if method == 'snr_based':
            region_top_index = np.nanargmax(np.abs(top_snr))

        if method == 'prm_based':
            region_top_index = np.nanargmax(np.abs(top_prm))
                
        if method == 'optimized_wct':
            region_top_index = optimize_feature_selection(
                param = top_wct,
                height = top_height,
                param_peak_margin = wct_peak_margin,
                mode = 'top'
                )
            
        if method == 'optimized_snr':
            region_top_index = optimize_feature_selection(
                param = top_snr,
                height = top_height,
                param_peak_margin = wct_peak_margin,
                mode = 'top'
                )
            
        if method == 'optimized_prm':
            region_top_index = optimize_feature_selection(
                param = top_prm,
                height = top_height,
                param_peak_margin = wct_peak_margin,
                mode = 'top'
                )
    
        layer_top_index = top_ind[region_top_index]

        top_flag = 0
        
    else:
        layer_top_index = -1
        
        top_flag = 1

    if mask_bases.any():

        base_ind = np.where(mask_bases)[0]

        base_height = height[base_ind]
        base_wct = wct[base_ind]
        base_snr = snr[base_ind]
        base_prm = prm[base_ind]
    
        if method == 'height_based':
            region_base_index = np.nanargmin(base_height)
        
        if method == 'wct_based':
            region_base_index = np.nanargmax(np.abs(base_wct))
        
        if method == 'snr_based':
            region_base_index = np.nanargmax(np.abs(base_snr))
            
        if method == 'prm_based':
            region_base_index = np.nanargmax(np.abs(base_prm))
            
        if method == 'optimized_wct':
            region_base_index = optimize_feature_selection(
                param = base_wct,
                height = base_height,
                param_peak_margin = wct_peak_margin,
                mode = 'base'
                )
            
        if method == 'optimized_snr':
            region_base_index = optimize_feature_selection(
                param = base_snr,
                height = base_height,
                param_peak_margin = wct_peak_margin,
                mode = 'base'
                )
            
        if method == 'optimized_prm':
            region_base_index = optimize_feature_selection(
                param = base_prm,
                height = base_height,
                param_peak_margin = wct_peak_margin,
                mode = 'base'
                )
            
        layer_base_index = base_ind[region_base_index]

        base_flag = 0

    else:
        layer_base_index = 0

        base_flag = 1


    return(layer_base_index, layer_top_index, base_flag, top_flag)

# def check_method(method):
    
#     allowed_methods = ['height_based', 'wct_based', 'snr_based', 'optimized']
    
#     if method not in allowed_methods:
#         raise Exception(f"The selected method ({method}) is not supporte. Please select one of: {allowed_methods}")
    
#     return
