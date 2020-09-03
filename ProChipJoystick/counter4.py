"""Written by Andrea Bassi (Politecnico di Milano) 10 August 2018
to find the location of datasets in a h5 file.
"""

import h5py
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from statistics import mean

def find_dataset(item):
        """Returns the DataSet within the HDF5 file and its shape. Found gives the number of dataset found"""
        [name,shape,found]= get_hdf5_item_structure(item, name=[], shape=[], found = 0)
        return (name,shape,found)
    
def get_hdf5_item_structure(g, name, shape, found) :
        """Extracts the dataset location (and its shape) and it is operated recursively in the h5 file subgroups  """
                
        if   isinstance(g,h5py.File) :
            found=found #this and others are unnecessary, but left for future modifications
               
        elif isinstance(g,h5py.Dataset) :
           
            found=found+1
            name.append(g.name)
            shape.append(g.shape)
               
        elif isinstance(g,h5py.Group) :
            found=found
            
        else :
            found=found
            print ('WARNING: UNKNOWN ITEM IN HDF5 FILE', g.name)
            #sys.exit ( "EXECUTION IS TERMINATED" )
     
        if isinstance(g, h5py.File) or isinstance(g, h5py.Group) :
           
            for key,val in dict(g).items() :
                subg = val
                
                [name,shape,found]=get_hdf5_item_structure(subg,name,shape,found)
                 
        return (name,shape,found)
      
def plot_transit_data (item, n_cell_mean) : # n_cell_mean numero di cellule su cui fare la media
    """plot of the frame mean, delta time and cells transit frequency over time"""
    
        [name,shape,found]= get_hdf5_item_structure(item, name=[], shape=[], found = 0)
        
        #data in the file
        deltat = file[dataname[0]]
        intensity = file[dataname[1]]
        time = file[dataname[2]]

        
        #conversion to np.array
        np_time = np.squeeze(np.array( time, dtype = float))
        np_data = np.squeeze(np.array( intensity, dtype = int))
        np_deltat = np.squeeze(np.array(deltat, dtype = float))
        
        #create the vector with non null values
        t = (np_time[0:175000]-np_time[0])/60 #time in minutes
        m = np_data[0:175000]
        dt = np_deltat[0:175000]
        
        # positional array of peaks that correspond to cells
        m_peaks, _=find_peaks(m, prominence=10, width=2)
        
        #delta time of 2 consecutive cells
        t_peaks=t[m_peaks] #time corresponding to peaks
        Dt=t_peaks[1:]-t_peaks[:len(t_peaks)-1]
        
        # average of Dt based on n_cell_mean
        Dt_average=[] 
        for i in range(0, len(m_peaks)-n_cell_mean, n_cell_mean):
            for j in range(m_peaks[i], m_peaks[i+n_cell_mean]):
                Dt_average.append(mean(Dt[i:i+n_cell_mean]))
        
        #frequency cells/time      
        freq=1/np.array(Dt_average)
        
        #PLOTS
        plt.figure()
        
        #plot mean vs time
        plt.subplot(221)
        plt.plot(t, m)
        plt.xlabel('time [minutes]')
        plt.ylabel('medium frame intensity')
        
        #plot mean peaks vs time
        plt.subplot(223)
        plt.plot(t, m)
        plt.plot(t[m_peaks], m[m_peaks], "x")
        plt.xlabel('time [minutes]')
        plt.ylabel('medium frame intensity')
        plt.text(10,400,'total peaks corresponding to cells:%d' %len(m_peaks))
        
        #plot of Dt vs time
        plt.subplot(222)
        plt.plot(t[m_peaks[0]:m_peaks[len(m_peaks)-1]], Dt_average)
        plt.xlabel('time [minutes]')
        plt.ylabel('delta time [minutes]')
        
        #plot of frequency vs time
        plt.subplot(224)
        plt.plot(t[m_peaks[0]:m_peaks[len(m_peaks)-1]], freq)
        plt.xlabel('time (minutes)')
        plt.ylabel('frequency [cells/minute]')
        
        plt.suptitle('Acquired data')
        plt.show()


            
"""The following is only to test the functions.
It will find a dataset and display it
"""     
if __name__ == "__main__" :
    
        import sys
        import pyqtgraph as pg
        import qtpy.QtCore
        from qtpy.QtWidgets import QApplication
        import numpy as np
        
        # this h5 file must contain a dataset composed by an array or an image
        file_name=r'C:\Users\Matteo\eclipse-workspace\video_treshold\13.02\200213_164621_SyncreadoutTriggerCounterMeasurement.h5'
        
        file = h5py.File(file_name, 'r') # open read-only
        [dataname,datashape,datafound] = find_dataset(file)    
        
        plot_cells_frequency (file, 6) 
        
                          
        file.close()
        sys.exit ( "End of test")