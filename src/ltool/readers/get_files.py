#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 23 13:03:44 2020

@author: nick
"""
import mysql.connector
import numpy as np
import os

def database(meas_id, cfg):
    
    mydb = mysql.connector.connect(
      host=cfg.dtb['host'],
      user=cfg.dtb['user'],
      passwd=cfg.dtb['password'],
      port=cfg.dtb['port'],
      db=cfg.dtb['scc-db-name']
    )
    
    cur = mydb.cursor()
    
    cur.execute("SELECT products.ID, products._prod_type_ID, " +\
                "ltool_product_options.dilation, ltool_product_options.snr_factor, " +\
                "ltool_product_options.wct_peak_margin, elda_products.filename  "  +\
                "FROM measurements INNER JOIN system_product INNER JOIN products " +\
                "INNER JOIN ltool_product_options INNER JOIN elda_products " +\
                "ON measurements._hoi_system_ID=system_product._system_ID " +\
                "AND system_product._Product_ID=products.ID " +\
                "AND ltool_product_options._product_ID=products.ID " +\
                "AND ltool_product_options._input_product_ID=elda_products._product_ID " +\
                "AND elda_products.__measurements__ID=measurements.ID " +\
                "WHERE products._prod_type_ID IN (10,11) AND " +\
                "measurements.ID='"+meas_id+"';")

    query = cur.fetchall()
    
    files = np.array([os.path.join(cfg.scc['input-dir'], x[5]) for x in query])
    
    rpath = np.array([os.path.split(x[5])[0] for x in query])

    alphas = np.array([x[2] for x in query])

    alphas[alphas == None] = 400.

    snr_factor = np.array([x[3] for x in query])
    
    snr_factor[snr_factor == None] = 3.291
        
    wct_peak_margin = np.array([x[4] for x in query])

    wct_peak_margin[wct_peak_margin == None] = 1.
    
    ids = np.array([x[0] for x in query], dtype = str)
    typ = np.array([x[1] for x in query], dtype = str)
    
    mydb.close()
            
    return(files, rpath, alphas, snr_factor, wct_peak_margin, typ, ids)
