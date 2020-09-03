from __future__ import division
from ScopeFoundry import Measurement
#from Hamamatsu_ScopeFoundry.CameraMeasurement import HamamatsuMeasurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
#from SyncreadoutTriggerMeasurement_dvp import SyncReadOutMeasurement
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import os
import time
from datetime import datetime
import h5py 
#from gevent.libev.corecext import self
#import pandas as pd


"""
lOGITECH F710 AND OTHERS COSTANTS:
"""
RESOLUTION = 0.0001
LH_ANALOG = 0 #LEFT HORIZONTAL
RH_ANALOG = 4 #RIGHT HORIZONTAL
T_ANALOG= 2 
A=0
X=2
B=1
Y=3
START=7


class SyncreadoutTriggerJoystickCounterMeasurement(Measurement):
    
    name = "SyncreadoutTriggerJoystickCounterMeasurement"
  
    
    def setup(self):
        
        "..." 

        self.ui_filename = sibling_path(__file__, "DualColor_pump.ui")

        self.ui = load_qt_ui_file(self.ui_filename)
        self.settings.New('save_h5', dtype=bool, initial=False, hardware_set_func=self.setSaveH5, hardware_read_func=self.getSaveH5)
        self.settings.New('refresh_period', dtype=float, unit='s', spinbox_decimals = 4, initial=0.02 , hardware_set_func=self.setRefresh, vmin = 0)
        self.settings.New('autoRange0', dtype=bool, initial=True)
        self.settings.New('autoLevels0', dtype=bool, initial=True)
        self.settings.New('level_min0', dtype=int, initial=60, hardware_read_func = self.getminLevel0)
        self.settings.New('level_max0', dtype=int, initial=150, hardware_read_func = self.getmaxLevel0)
        self.settings.New('autoRange1', dtype=bool, initial=True)
        self.settings.New('autoLevels1', dtype=bool, initial=True)
        self.settings.New('level_min1', dtype=int, initial=60, hardware_read_func = self.getminLevel1)
        self.settings.New('level_max1', dtype=int, initial=150, hardware_read_func = self.getmaxLevel1)
        self.settings.New('threshold', dtype=int, initial=500, hardware_set_func=self.setThreshold)
        
        self.camera = self.app.hardware['HamamatsuHardware']
        
        self.display_update_period = self.settings.refresh_period.val
        
        self.laser_1 = self.app.hardware['Laser_1']
        self.laser_2 = self.app.hardware['Laser_2']
        self.ni_co_1 = self.app.hardware['Counter_Output_1']
        self.ni_co_2 = self.app.hardware['Counter_Output_2']
        self.ni_do_1 = self.app.hardware['Digital_Output_1']
        """
        THIS CONNECTS THE JOYSTICK TO THE MEASUREMENT
        """
        self.joystick_hw = self.app.hardware['joystickHW']
        self.pump_hw = self.app.hardware['MFCSHardware']
        
        
        self.settings.New('Acq_freq', dtype=float, unit='Hz', initial=50)
        self.settings.New('xsampling', dtype=float, unit='um', initial=0.11)
        self.settings.New('ysampling', dtype=float, unit='um', initial=0.11)
        self.settings.New('zsampling', dtype=float, unit='um', initial=1.0)
        
        self.settings.New('counter_threshold', dtype=float, initial=5000, spinbox_step = 1000, spinbox_decimals = 0)
        self.settings.New('number_of_cells', dtype=float, initial=0, spinbox_step = 1, spinbox_decimals = 0, hardware_read_func = self.getNumberOfCells)
        self.settings.New('delta_t', dtype=float, initial=0, spinbox_step = .01, spinbox_decimals = 2, hardware_read_func = self.get_delta_t)
        self.settings.New('computed_channel', dtype=str, initial = '0', choices=['0','1'])
        self.settings.New('mean_image', dtype=float, initial=0, spinbox_step = 1, hardware_read_func = self.getMeanImage, spinbox_decimals = 0)
        
        
        # Create a setting names "sensitivity" that defines the sensitivity of joystick axes.
        self.settings.New('sensitivity', dtype=str, choices = ["low", "medium", "high"], initial="medium") 
        # Create a setting names "channel" that defines the channel to be controlled by the joystick
        self.settings.New('channel', dtype=str, choices = ["set_pressure_1", "set_pressure_2", "set_pressure_3","set_pressure_4"], initial="set_pressure_1") 
        
        self.app.settings.data_fname_format.val = '{timestamp:%y%m%d_%H%M%S}_{sample}_{measurement.name}.{ext}'
        self.app.settings.sample.val = 'sample'
        
         # Create a dictionary to associate numerical values to each sensitivity levels. This numerical value will be used in update_display
        self.sensitivity_dict = {"low":RESOLUTION*10, "medium":RESOLUTION*100, "high":RESOLUTION*10000}

        

        
    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
                
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        
        # connect ui widgets of live settings
        self.settings.autoLevels0.connect_to_widget(self.ui.autoLevels_checkBox0)
        self.settings.autoRange0.connect_to_widget(self.ui.autoRange_checkBox0)
        self.settings.level_min0.connect_to_widget(self.ui.min_doubleSpinBox0) #spinBox doesn't work nut it would be better
        self.settings.level_max0.connect_to_widget(self.ui.max_doubleSpinBox0) #spinBox doesn't work nut it would be better
        
        # connect ui widgets of live settings
        self.settings.autoLevels1.connect_to_widget(self.ui.autoLevels_checkBox1)
        self.settings.autoRange1.connect_to_widget(self.ui.autoRange_checkBox1)
        self.settings.level_min1.connect_to_widget(self.ui.min_doubleSpinBox1) #spinBox doesn't work nut it would be better
        self.settings.level_max1.connect_to_widget(self.ui.max_doubleSpinBox1) #spinBox doesn't work nut it would be better
        
        # connect ui widgets of pump control
        self.pump_hw.settings.set_pressure_1.connect_to_widget(self.ui.Ch1_val)
        self.pump_hw.settings.set_pressure_2.connect_to_widget(self.ui.Ch2_val)
        self.pump_hw.settings.set_pressure_3.connect_to_widget(self.ui.Ch3_val)
        self.pump_hw.settings.set_pressure_4.connect_to_widget(self.ui.Ch4_val)
        self.pump_hw.settings.read_pressure_1.connect_to_widget(self.ui.Ch1_read)
        self.pump_hw.settings.read_pressure_2.connect_to_widget(self.ui.Ch2_read)
        self.pump_hw.settings.read_pressure_3.connect_to_widget(self.ui.Ch3_read)
        self.pump_hw.settings.read_pressure_4.connect_to_widget(self.ui.Ch4_read)
        self.settings.channel.connect_to_widget(self.ui.comboBox_ch)
        self.settings.sensitivity.connect_to_widget(self.ui.comboBox_sensitivity)
        self.pump_hw.settings.save_pressure_1.connect_to_widget(self.ui.checkBox_save1)
        self.pump_hw.settings.save_pressure_2.connect_to_widget(self.ui.checkBox_save2)
        self.pump_hw.settings.save_pressure_3.connect_to_widget(self.ui.checkBox_save3)
        self.pump_hw.settings.save_pressure_4.connect_to_widget(self.ui.checkBox_save4)
        
        
        
        # Create 2 windows with the 2 image channels
        self.ui_filename_plots0 = sibling_path(__file__, "channel0.ui")
        self.ui_plots0 = load_qt_ui_file(self.ui_filename_plots0)
        self.ui_plots0.show()
        self.ui_plots0.activateWindow()

        self.ui_filename_plots1 = sibling_path(__file__, "channel1.ui")
        self.ui_plots1 = load_qt_ui_file(self.ui_filename_plots1)
        self.ui_plots1.show()
        self.ui_plots1.activateWindow()
     
        self.imv0 = pg.ImageView()
        self.imv1 = pg.ImageView()
        self.imv0.ui.histogram.hide()
        self.imv1.ui.histogram.hide()
        self.imv0.ui.roiBtn.hide()
        self.imv1.ui.roiBtn.hide()
        self.imv0.ui.menuBtn.hide()
        self.imv1.ui.menuBtn.hide()
         
        self.ui_plots0.channel0_groupBox.layout().addWidget(self.imv0)
        self.ui_plots1.channel1_groupBox.layout().addWidget(self.imv1)
        
        self.image0 = np.zeros((int(self.camera.subarrayv.val), int(self.camera.subarrayh.val)), dtype=np.uint16)
        self.image1 = np.zeros((int(self.camera.subarrayv.val), int(self.camera.subarrayh.val)), dtype=np.uint16)
        
    def run(self):
        
        self.Abutton_pressed_before = False
        self.Xbutton_pressed_before = False
        self.STARTbutton_pressed_before = False
        self.button_pressed_before = False
         
        
        self.N_frames = 1000000
        self.initH5CellCounter()
        self.eff_subarrayh = int(self.camera.subarrayh.val/self.camera.binning.val)
        self.eff_subarrayv = int(self.camera.subarrayv.val/self.camera.binning.val)
        
        
        self.image0 = np.zeros((self.eff_subarrayv,self.eff_subarrayh),dtype=np.uint16)
        self.image1 = np.zeros((self.eff_subarrayv,self.eff_subarrayh),dtype=np.uint16)
        
        self.image0[0,0] = 1
        self.image1[0,0] = 1
        
        try:
            
            self.camera.read_from_hardware()

            self.start_triggered_Acquisition(self.settings['Acq_freq'])
            
            index = 0
            
            if self.camera.acquisition_mode.val == "fixed_length":
            
                if self.settings['save_h5']:
                    self.initH5()
                    print("\n \n ******* \n \n Saving :D !\n \n *******")
                    
                while index < self.camera.hamamatsu.number_image_buffers:
        
                    # Get frames.
                    #The camera stops acquiring once the buffer is terminated (in snapshot mode)
                    [frames, dims] = self.camera.hamamatsu.getFrames()
                    
                    # Save frames.
                    for aframe in frames:
                        
                        self.np_data = aframe.getData()  
                        self.image = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh)) 
                        if self.settings['save_h5']:
                            self.image_h5[index,:,:] = self.image # saving to the h5 dataset
                            self.h5file.flush() # maybe is not necessary
                                            
                        if self.interrupt_measurement_called:
                            break
                        index+=1
                        print(index)
                    
                    if self.interrupt_measurement_called:
                        break    
                    #index = index + len(frames)
                    #np_data.tofile(bin_fp)
                    self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                    
            elif self.camera.acquisition_mode.val == "run_till_abort":
                
                self.counter=0
                self.detection=0
                self.cell_list=[]
                self.t0=time.time()
                self.delta_t=0
                self.frame_mean = 0
                self.h5_index_counter = -1
                
                while not self.interrupt_measurement_called:
            
                    [frame, dims] = self.camera.hamamatsu.getLastFrame()

                    if self.camera.hamamatsu.last_frame_number == 1:
                        frameA = frame
                        self.np_data0 = frameA.getData()
                        self.image0 = np.reshape(self.np_data0, (self.eff_subarrayv, self.eff_subarrayh))
                        
                    elif self.camera.hamamatsu.buffer_index%2 == 0:
                        frameA = frame
                        self.np_data0 = frameA.getData()
                        self.image0 = np.reshape(self.np_data0, (self.eff_subarrayv, self.eff_subarrayh))
                        
                        if self.camera.hamamatsu.backlog != 1:
                            if self.camera.hamamatsu.buffer_index != 0:
                                frameB = self.camera.hamamatsu.getRequiredFrame(self.camera.hamamatsu.buffer_index-1)[0]
                                self.np_data1 = frameB.getData()
                                self.image1 = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))
                            else:
                                frameB = self.camera.hamamatsu.getRequiredFrame(self.camera.hamamatsu.number_image_buffers-1)[0]
                                self.np_data1 = frameB.getData()
                                self.image1 = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))
                    else:
                        if self.camera.hamamatsu.backlog == 1:
                            frameB = frame
                            
                            self.np_data1 = frameB.getData()
                            self.image1 = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))
                        else:
                            frameB = frame
                            frameA = self.camera.hamamatsu.getRequiredFrame(self.camera.hamamatsu.buffer_index-1)[0]
                            
                            self.np_data0 = frameA.getData()
                            self.image0 = np.reshape(self.np_data0, (self.eff_subarrayv, self.eff_subarrayh))
                            self.np_data1 = frameB.getData()
                            self.image1 = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))                         
                    
                    self.h5_index_counter += 1
                    
                    if self.settings.computed_channel.val == '0':
                        self.update_cell_counter(self.np_data0,self.settings.counter_threshold.val)
                    elif self.settings.computed_channel.val == '1' and hasattr(self, 'np_data1'):
                        self.update_cell_counter(self.np_data1,self.settings.counter_threshold.val)
                                      
                    
                    self.settings.number_of_cells.read_from_hardware()
                    self.settings.mean_image.read_from_hardware()
                    self.settings.delta_t.read_from_hardware()
                    
                  
                    if self.settings['save_h5']:
                        self.camera.hamamatsu.stopAcquisitionNotReleasing()
                        self.initH5()
                        print("\n \n ******* \n \n Saving :D !\n \n *******")
                        
                        [frames, dims] = self.camera.hamamatsu.getLastTotFrames()
                        
                        sub_index_0 = 0
                        sub_index_1 = 0
                        buffer_index = self.camera.hamamatsu.buffer_index + 1
                        
                        for aframe in frames:                            
                        

                            self.np_data = aframe.getData()
                            self.image_on_the_run = np.reshape(self.np_data, (self.eff_subarrayv, self.eff_subarrayh))
                            if buffer_index%2 == 0:
                                self.image_h5_0[sub_index_0, :, :] = self.image_on_the_run  # saving to the h5 dataset
                                sub_index_0+=1
                            else:
                                self.image_h5_1[sub_index_1, :, :] = self.image_on_the_run  # saving to the h5 dataset
                                sub_index_1+=1
                            self.h5file.flush()  # maybe is not necessary
                            self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                            index+=1
                            buffer_index+=1

                        
                        self.h5file.close()
                        self.settings.save_h5.update_value(new_val = False)
                        index = 0
                        self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                        self.camera.hamamatsu.startAcquisitionWithoutAlloc()
        finally:
            
            self.stop_triggered_Acquisition()
            self.h5file_counter.close()
            
            if self.settings['save_h5']:
                self.h5file.close() # close h5 file  
                self.settings.save_h5.update_value(new_val = False)
            
                
    def update_display(self):
        """
        Displays the numpy array called self.image.
        This function runs repeatedly and automatically during the measurement run,
        its update frequency is defined by self.display_update_period.
        """
        # self.optimize_plot_line.setData(self.buffer)
        # self.imv.setImage(np.reshape(self.np_data,(self.camera.subarrayh.val, self.camera.subarrayv.val)).T)
        # self.imv.setImage(self.image, autoLevels=False, levels=(100,340))
        if self.settings.autoLevels0.val == False:
            self.imv0.setImage((self.image0).T, autoLevels=self.settings.autoLevels0.val,
                              autoRange=self.settings.autoRange0.val, levels=(self.settings.level_min0.val, self.settings.level_max0.val))    
        else:  # levels should not be sent when autoLevels is True, otherwise the image is displayed with them
            self.imv0.setImage((self.image0).T, autoLevels=self.settings.autoLevels0.val,
                              autoRange=self.settings.autoRange0.val)    
            self.settings.level_min0.read_from_hardware()
            self.settings.level_max0.read_from_hardware() 
         
        if self.settings.autoLevels1.val == False:    
            self.imv1.setImage((self.image1).T, autoLevels=self.settings.autoLevels1.val,
                              autoRange=self.settings.autoRange1.val, levels=(self.settings.level_min1.val, self.settings.level_max1.val))
        else:
            self.imv1.setImage((self.image1).T, autoLevels=self.settings.autoLevels1.val,
                              autoRange=self.settings.autoRange1.val)
            self.settings.level_min1.read_from_hardware()
            self.settings.level_max1.read_from_hardware() 
        
        """
        START JOYSTICK CONTROL
        """
        if hasattr(self.joystick_hw,'joystick_dev'):
            
            """
            This prevent out of range input
            """ 

            
            if self.pump_hw.settings[self.settings['channel']]>self.pump_hw.settings._logged_quantities[self.settings['channel']].vmax:#self.pump_hw.settings[self.settings['channel']].vmax:
                
                self.pump_hw.settings[self.settings['channel']]=self.pump_hw.settings._logged_quantities[self.settings['channel']].vmax #self.pump_hw.settings[self.settings['channel']].vmax:
            
            if self.pump_hw.settings[self.settings['channel']]<self.pump_hw.settings._logged_quantities[self.settings['channel']].vmin:#self.pump_hw.settings[self.settings['channel']].vmin:
                
                self.pump_hw.settings[self.settings['channel']]=self.pump_hw.settings._logged_quantities[self.settings['channel']].vmin #self.pump_hw.settings[self.settings['channel']].vmin:
                                                                                       
            if self.button_pressed_before and not (self.joystick_hw.joystick_dev.get_hat_values(1) or self.joystick_hw.joystick_dev.get_hat_values(0)):
            
                self.button_pressed_before = False
            
             
            """
            This reads the joystick axis and hats values to set the pressure at the current channel (self.settings['channel'])
            """
            if (self.joystick_hw.joystick_dev.get_hat_values(1) or self.joystick_hw.joystick_dev.get_hat_values(0)) and not self.button_pressed_before:
                
                self.button_pressed_before = True
                self.pump_hw.settings[self.settings['channel']] = self.pump_hw.settings[self.settings['channel']] \
                                                                + 10**4*RESOLUTION*self.joystick_hw.joystick_dev.get_hat_values(1) + 10**3*RESOLUTION*self.joystick_hw.joystick_dev.get_hat_values(0)
            if abs(self.joystick_hw.joystick_dev.get_axis_values(T_ANALOG)) > 10**(-4):            #this is a threshold to filter out the joystick noise (-3.0517578125e-05)-better to find a more general implementation-       
                self.pump_hw.settings[self.settings['channel']] = self.pump_hw.settings[self.settings['channel']] \
                                                      - self.sensitivity_dict[self.settings['sensitivity']]*(self.joystick_hw.joystick_dev.get_axis_values(T_ANALOG))                                          
            # read all pressures from hardware
            self.pump_hw.read_pressure_1.read_from_hardware()
            self.pump_hw.read_pressure_2.read_from_hardware()
            self.pump_hw.read_pressure_3.read_from_hardware()
            self.pump_hw.read_pressure_4.read_from_hardware()

            
            """
            This reads the joystick B button value and save the pressure of channeL 1
            """
            if self.settings['channel'] == "set_pressure_1" :
                self.pump_hw.settings['save_pressure_1']=self.joystick_hw.joystick_dev.get_button_values(B)
            elif self.settings['channel'] ==  "set_pressure_2":
                self.pump_hw.settings['save_pressure_2']=self.joystick_hw.joystick_dev.get_button_values(B)
            elif self.settings['channel'] ==  "set_pressure_3":
                self.pump_hw.settings['save_pressure_3']=self.joystick_hw.joystick_dev.get_button_values(B)
            elif self.settings['channel'] ==  "set_pressure_4":   
                self.pump_hw.settings['save_pressure_4']=self.joystick_hw.joystick_dev.get_button_values(B)
            """
            This reads the joystick Y button value and set the saved pressures at each channel
            """
            self.pump_hw.settings['set_saved_pressure']=self.joystick_hw.joystick_dev.get_button_values(Y)
            
            """
            This reads the joystick X button and change the value of save_h5
            """
            if self.Xbutton_pressed_before and not self.joystick_hw.joystick_dev.get_button_values(X):
                self.Xbutton_pressed_before = False
                
            if self.joystick_hw.joystick_dev.get_button_values(X) and not self.Xbutton_pressed_before :
                self.Xbutton_pressed_before = True
                self.settings['save_h5'] = not self.settings['save_h5']
        
            """
            This reads the joystick A button and change the value of sensitivity (still have to find an alternative to elif...)
            """
            if self.Abutton_pressed_before and not self.joystick_hw.joystick_dev.get_button_values(A):
                self.Abutton_pressed_before = False
            
            if self.joystick_hw.joystick_dev.get_button_values(A) and not self.Abutton_pressed_before:
                
                self.Abutton_pressed_before = True
                
                if self.settings['sensitivity'] == "low":
                    self.settings['sensitivity'] = "medium"
                
                elif self.settings['sensitivity'] == "medium":
                    self.settings['sensitivity'] = "high"
                    
                elif self.settings['sensitivity'] == "high":
                    self.settings['sensitivity'] = "low"
                    
            """
            This reads the joystick START button and change the channel (still have to find an alternative to elif...)
            """
            if self.STARTbutton_pressed_before and not self.joystick_hw.joystick_dev.get_button_values(START):
                self.STARTbutton_pressed_before = False
            
            if self.joystick_hw.joystick_dev.get_button_values(START) and not self.STARTbutton_pressed_before:
                
                self.STARTbutton_pressed_before = True
                
                if self.settings['channel'] == "set_pressure_1" :
                    self.settings['channel'] =  "set_pressure_2"
                    
                
                elif self.settings['channel'] ==  "set_pressure_2":
                    self.settings['channel'] = "set_pressure_3"
                    
                    
                elif self.settings['channel'] =="set_pressure_3":
                    self.settings['channel'] = "set_pressure_4"
                    
                            
                elif self.settings['channel'] == "set_pressure_4":
                    self.settings['channel'] = "set_pressure_1"
 
                
        """
        END JOYSTICK CONTROL
        """                    
    def setRefresh(self, refresh_period):  
        self.display_update_period = refresh_period
            
    def setThreshold(self, threshold):
        self.threshold = threshold
    
    def setSaveH5(self, save_h5):
        self.settings.save_h5.val = save_h5
        
    def getSaveH5(self):
        if self.settings['record']:
            self.settings.save_h5.val = False
        return self.settings.save_h5.val 
    

    
    def updateIndex(self, last_frame_index):
        """
        Update the index of the image to fetch from buffer. 
        If we reach the end of the buffer, we reset the index.
        """
        last_frame_index+=1
        
        if last_frame_index > self.camera.hamamatsu.number_image_buffers - 1: #if we reach the end of the buffer
            last_frame_index = 0 #reset
        
        return last_frame_index
    
    
           
    def start_laser(self, laserHW):
        ''' Laser is prepared for digital modulation at the power specified. Laser is turned OFF before'''   
        if laserHW.laser_status.val=='ON':
            self.stop_laser(laserHW)
        if laserHW.connected.val: # do this only if the laser was connected by the user!
            if laserHW.operating_mode.val!='DIGITAL':
                laserHW.operating_mode.val='DIGITAL'
                laserHW.operating_mode.write_to_hardware()
            
            laserHW.laser_status.val='ON'
            laserHW.laser_status.write_to_hardware()
            laserHW.read_from_hardware()
        
    def stop_laser(self, laserHW):
        ''' Laser is turned off '''
        
        if laserHW.connected.val: # do this only if the laser was connected by the user!
            laserHW.laser_status.val='OFF' 
            laserHW.laser_status.write_to_hardware()
        
    def start_digital_rising_edge(self, digitalHW):
        '''The digital output of the DAQ start a rising edge procedure at the channel set by the user '''
        
        digitalHW.value.val=0
        digitalHW.write_value()
        
        digitalHW.value.val=1
        digitalHW.write_value() # Trigger
        digitalHW.read_from_hardware()     
    
    def start_triggered_counter_task(self, counterHW, initial_delay, freq, duty_cycle):
        ''' DAQ Counter set to be at 5V and 0V with a frequency of half the exposure time of the camera (1 frame OFF and 1 frame ON).
        It will be triggered by the digital output of the DAQ at the channel set by the user (please check that is equal to the one used for the ni_do_HW)'''
        
        if counterHW.connected.val: # do this only if the counter was connected by the user!
            counterHW.freq.val=freq
            counterHW.freq.write_to_hardware()
            # if exposure time is less 1/fps then the laser should not be ON
            # for all the period but only when the camera is exposing pixels
            
            #===================================================================
            # if self.camera.exposure_time.val < 1/self.camera.internal_frame_rate.val:
            #     counterHW.duty_cycle.val=self.camera.exposure_time.val*counterHW.freq.val
            #     print(counterHW.duty_cycle.val)
            #     counterHW.duty_cycle.write_to_hardware()
            #===================================================================
            counterHW.duty_cycle.val=duty_cycle
            counterHW.duty_cycle.write_to_hardware()
            counterHW.trigger.val=True
            counterHW.trigger.write_to_hardware()
            counterHW.initial_delay.val=initial_delay # probably in start trigger mode there is no delay so counter 1 should have an initial delay = 0
            #counterHW.initial_delay.val=0.00003896
            #counterHW.initial_delay.val=0.0000877 # initial delay to be synchronized with the camera( check camera documentation at start trigger mode...)
            counterHW.initial_delay.write_to_hardware()
            counterHW.start()
            counterHW.read_from_hardware()
            
    def stop_counter_task(self, counterHW):
        ''' Stop counter output task '''
        
        if counterHW.connected.val: # do this only if the counter was connected by the user!
            counterHW.stop()
    
    def start_triggered_Acquisition(self,freq1):
        ''' The camera is operated with external start trigger mode and will be triggered by the digital output of the DAQ '''
        
        self.camera.trsource.val='external'
        self.camera.trsource.write_to_hardware()
        self.camera.trmode.val='normal'
        self.camera.trmode.write_to_hardware()
        self.camera.tractive.val='syncreadout'
        self.camera.tractive.write_to_hardware()        
        self.camera.read_from_hardware()
        self.camera.hamamatsu.startAcquisition() 

        self.start_laser(self.laser_1)
        self.start_laser(self.laser_2)
        
        #dutycycle for advanced laser switch hardware
        
        t_readout = self.camera.hamamatsu.getPropertyValue("internal_line_interval")[0]
        camera_dutycycle = freq1*t_readout*self.camera.subarrayv.val
        
        #dutycycle for simple laser switch hardware
        
        camera_dutycycle=0.5 
        self.start_triggered_counter_task(self.ni_co_1, initial_delay=0.0000, freq=freq1, duty_cycle=camera_dutycycle)
        #CounterOutput2 used to control 2 lasers via 1 signal and a duplication port with a buffer and a NOT. 
        self.start_triggered_counter_task(self.ni_co_2, initial_delay=0.00003896, freq=freq1/2, duty_cycle=0.5)
        
        self.start_digital_rising_edge(self.ni_do_1)
        
    def stop_triggered_Acquisition(self):
        ''' Acquisition is terminated, laser and counters turned off '''        
         
        self.camera.hamamatsu.stopAcquisition() 
        self.stop_laser(self.laser_1)
        self.stop_laser(self.laser_2)
        self.stop_counter_task(self.ni_co_1)
        self.stop_counter_task(self.ni_co_2)
        self.camera.trsource.val='internal'
        
    
    def initH5(self):
        """
        Initialization operations for the h5 file.
        """
        t0 = time.time()
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(t0),
            sample =self.app.settings["sample"],
            ext='h5')
        
        fname = os.path.join(self.app.settings['save_dir'], f)
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image0.shape #both image1 and image2 are valid, since they have the same shape
        length=self.camera.hamamatsu.number_image_buffers/2 #divided by two since we have the two channels
        self.image_h5_0 = self.h5_group.create_dataset( name  = 't0/channel0/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image0.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      ) #both image1 and image2 are valid, since they have the same shape
        self.image_h5_1 = self.h5_group.create_dataset( name  = 't0/channel1/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image0.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      ) #both image1 and image2 are valid, since they have the same shape
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5_0.dims[0].label = "z"
        self.image_h5_0.dims[1].label = "y"
        self.image_h5_0.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5_0.attrs['element_size_um'] =  [1,1,1]
        
        self.image_h5_1.dims[0].label = "z"
        self.image_h5_1.dims[1].label = "y"
        self.image_h5_1.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5_1.attrs['element_size_um'] =  [1,1,1]
        
    def initH5_temp(self):
        """
        Initialization operations for the h5 file.
        """
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image.shape
        length=self.camera.hamamatsu.number_image_buffers
        self.image_h5 = self.h5_group.create_dataset( name  = 't0/c0/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5.dims[0].label = "z"
        self.image_h5.dims[1].label = "y"
        self.image_h5.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5.attrs['element_size_um'] =  [1,1,1]
        
                
    def initH5_temp2(self):
        """
        Initialization operations for the h5 file.
        """
        t0 = time.time()
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(t0),
            sample=self.app.settings["sample"],
            ext='h5')
        fname = os.path.join(self.app.settings['save_dir'], f)
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image.shape
        length=self.camera.hamamatsu.number_image_buffers
        self.image_h5 = self.h5_group.create_dataset( name  = 't0/c0/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5.dims[0].label = "z"
        self.image_h5.dims[1].label = "y"
        self.image_h5.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5.attrs['element_size_um'] =  [1,1,1]
    
    def getminLevel0(self):
        return self.imv0.levelMin
        
    def getmaxLevel0(self):
        return self.imv0.levelMax

    def getminLevel1(self):
        return self.imv1.levelMin
        
    def getmaxLevel1(self):
        return self.imv1.levelMax 

    def initH5CellCounter(self):
        
        """
        Initialization operations for the h5 file.
        """
        t0 = time.time()
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(t0),
            sample = self.app.settings["sample"] + "_cell_counter",
            ext='h5')
        
        fname = os.path.join(self.app.settings['save_dir'], f)
        
        self.h5file_counter = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)

        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file_counter )
        
        self.h5_mean = self.h5_group.create_dataset( name  = 't0/c0/mean',
                                                      shape = (self.N_frames,1 ,1),
                                                      dtype = "int16", chunks = (1, 1 ,1)
                                                      )
        self.h5_dt = self.h5_group.create_dataset( name  = 't0/c0/dt',
                                                      shape = (self.N_frames,1,1),
                                                      dtype = "float", chunks = (1, 1,1)
                                                      )
        
        self.h5_t1 = self.h5_group.create_dataset( name  = 't0/c0/t1',
                                                      shape = (self.N_frames,1,1),
                                                      dtype = "float", chunks = (1,1,1)
                                                      )
        
    def update_cell_counter(self,frame,th): #th potrebbe essere un valore da inserire
        
        self.frame_mean = frame_mean = np.mean(frame)
        t1 = time.time()
        delta_t = t1-self.t0
        self.cell_list.append([t1, delta_t, frame_mean])
        
        if self.h5_index_counter < self.N_frames:
            self.h5_mean[self.h5_index_counter, 0, 0] = frame_mean
            self.h5_dt[self.h5_index_counter, 0, 0] = delta_t
            self.h5_t1[self.h5_index_counter, 0, 0] = t1
        
        if self.h5_index_counter >= self.N_frames:
            self.h5file_counter.close()
             
        if frame_mean > th and not self.detection :
            self.counter+=1
            self.detection=1
            self.delta_t = delta_t    
            self.t0 = t1
            
        elif frame_mean < th and self.detection :
            self.detection=0        
    
    def getNumberOfCells(self):
        
        return self.counter
    
    def get_delta_t(self):
        
        return self.delta_t
    
    def getMeanImage(self):
        
        return self.frame_mean
