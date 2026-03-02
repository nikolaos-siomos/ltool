#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 14:42:40 2020

@author: nick
"""
import logging
import os
import getpass

def scc_logger(logger):
    
    # Get the logger with the appropriate level
    format_string = '%(asctime)s %(user)s %(name)s [%(process)d] -- %(levelname)s -- %(funcName)s(): %(message)s'
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Add a filter to provide username in log messages
    user_filter = UsernameFilter()

    stream_handler = logging.StreamHandler()
    add_handler(logger, stream_handler, formatter, user_filter)

    return(logger)

class UsernameFilter(logging.Filter):
    """
    This is a filter which injects the user name into the log.
    """

    def filter(self, record):
        record.user = getpass.getuser()
        return True
    
def add_handler(logger, handler, formatter, user_filter):
    
    handler.setFormatter(formatter)
    handler.addFilter(user_filter)
    logger.addHandler(handler)
    
    return()

def add_filepath(cfg, meas_id, logger):
    
    # Get the logger with the appropriate level
    format_string = '%(asctime)s %(user)s %(name)s [%(process)d] -- %(levelname)s -- %(funcName)s(): %(message)s'
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Add a filter to provide username in log messages
    user_filter = UsernameFilter()
    
    if 'log-dir' in cfg.scc.keys():
        log_dir = cfg.scc['log-dir']
        # Setup logfile
        if meas_id:
            log_filename = '{0}.log'.format(meas_id)
        else:
            log_filename = 'all.log'
    
        log_filepath = os.path.join(log_dir, log_filename)
        
        logfile_handler = logging.FileHandler(filename = log_filepath, mode = 'a')
        add_handler(logger, logfile_handler, formatter, user_filter)
        
    return()