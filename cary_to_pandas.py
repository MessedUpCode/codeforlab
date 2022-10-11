# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 15:04:37 2021
Only for series keeping the same wavelength interval
and resolution for all spectra!
@author: Carlo

16/09/22: tried to add option to load data with different
wavelengths. Partially works
(use load(file, same_wavelengths=False))

How to use:
- load data from a cary csv file (not "3d csv"!)
  and convert to pandas.DataFrame:
  * if all spectra share the same wavelengths
    or other x axis data (e.g. time in a single wavelength kinteic)
    (both range and number of points must match):
        df = cary_to_pandas.load(file)
    df.index will contain the wavelengths
    df.columns will contain the titles
  * if different spectra have different wavelengths/
    x axis data do not match:
        df = cary_to_pandas.load(file, same_wavelengths=False)
    may generate NaN values where the wavelengths do not match,
    if you need to plot the data as line it may result in "missing"
    segments.
- create a (titration/kinetic/other) profile:
  * using the DataFrame columns for the new index:
        p = cary_to_pandas.profile(data_frame, wavelength)
    returns a Pandas.Series object
    "wavelength" is not necessarily a wavelength, any number in the
    df.index (x axis) will work.
    the code will select the index that is closest to the 
    "wavelength" value.
    The code assumes that df.index is sorted (as happens with the
    recorded spectra). If you manually created data from the cary software
    using adl commands make sure the sequence is sorted or edit the function.
  * using different x (index) data for the profile:
        p = cary_to_pandas.profile(data_frame, wl, new_x=iterable)
    Lists, Numpy arrays or any kind of iterable can be used.
- load collection times (1 second time resolution):
  (this requires a csv file containing log data,
  make sure the appropriate option is enabled in the
  cary software before saving your data)
  * using data from a single file:
        s = cary_to_pandas.load_time(file)
    will return a pd.Series object with
    s.index = titles
    and times in second relative to the 1st spectrum
    (meaning the 1st recorded spectrum is always 0)
  * combining multiple files or using absolute times:
        for file in file_list:
            ...
            s = cary_to_pandas.load_time(file, absolute=True)
            ...
    later the Series can be combined and the lowest time 
    can be subtracted from all of the values.
- replace titles with times:
    as far as I have seen the spectra and log data
    are written in the same order, make sure your
    software version does the same.
        df = cary_to_pandas.load(file)
        time = cary_to_pandas.load_time(file)
        df.columns = time.to_list()
    if they do not match you can still write a few 
    lines of code to sort the times to match with
    your df.columns sequence
    
"""
import pandas as pd
from time import mktime, strptime

def load(path_and_file, same_wavelengths=True):
    # prescan
    with open(path_and_file) as f:
        fl = f.readline()
        titles = fl.split(',,')[:-1]
        f.readline()
        n = 0
        while True:
            if len(f.readline()) <= 1:
                break
            n += 1
    # load
    if same_wavelengths:
        d = pd.read_csv(path_and_file, header=0, skiprows=1,
                        nrows = n, index_col=0)
        c2 = []
        for c in range(0, len(d.columns), 2):
            c2.append(d.columns[c])
        d = d[c2]
        d.columns = titles
    else:
        d = pd.read_csv(path_and_file,header=None,skiprows=2,
                        nrows=n)
        l = len(d.columns)
        d2 = []
        for i in range(0,l-1,2):
            x = d[d.columns[i]].to_numpy()
            y = d[d.columns[i+1]].to_numpy()
            d2.append(pd.Series(data=y, index=x,
                                name = titles[i//2]
                                ).dropna())
        d = pd.concat(d2,axis=1, sort=True)
        del d2
    
    return d

def profile(data, wl, new_x=None):
    err = float('inf')
    for i in range(len(data.index)):
        e = abs(data.index[i] - wl)
        if e < err:
            err = e
            best = i
        else:
            break
    pr = data.iloc[best]
    try:
        pr.index = new_x
    except (TypeError, ValueError):
        pass
    return pr
    
def load_time(path_and_file, absolute=False):
    _defaulttimeformat = '%d/%m/%Y %H.%M.%S'
    _timestring = 'Collection Time: '
    _tsl = len(_timestring)
    with open(path_and_file) as f:
        l = ''
        while l != '\n':
            l = f.readline()
        # read collection time
        titles, times = [], []
        while l != '':
            # normal structure is: '\n', 'title,\n', 'original title\n',
            # 'Collection Time: %d/%m/%Y %H.%M.%S\n'
            while l != '\n' and l != '':
                l = f.readline()
            while l[-2:] != ',\n': # "title,\n"
                l = f.readline()
                if len(l) <= 1:
                    break
            title = l[:-2]
            while len(l) >= 1:
                l = f.readline()
                if l[:_tsl] == _timestring:
                    time = int(mktime(strptime(l[_tsl:-1], _defaulttimeformat)))
                    break
            titles.append(title)
            times.append(time)
        s = pd.Series(times[:-1], index=titles[:-1], name = 'Time (seconds)')
        if absolute:
            return s
        else:
            return s - min(s)
