from DAQ_Laser_Camera.SyncreadoutTriggerMeasurement import SyncreadoutTriggerMeasurement
import time
from datetime import datetime
import os
import numpy as np
from ScopeFoundry import h5_io

RESOLUTION = 0.0001
AXIS_L2 = 5
AXIS_R2 = 4
BUTTON_PS = 12
X=1
O=2
Q=3

class SyncreadoutTriggerJoystickMeasurement(SyncreadoutTriggerMeasurement):
    
    name = "SyncreadoutTriggerJoystickMeasurement"
    
    def setup(self):
        
        super().setup()
        
        # Create a setting names "sensitivity" that defines the sensitivity of joystick axes.
        self.settings.New('sensitivity', dtype=str, choices = ["low", "medium", "high"], initial="medium") 
        
        # Create a dictionary to associate numerical values to each sensitivity levels. This numerical value will be used in update_display
        self.sensitivity_dict = {"low":0.0001, "medium":0.001, "high":0.1}
        #self.sensitivity_dict["low"]
        """
        THIS CONNECTS THE JOYSTICK TO THE MEASUREMENT
        """
        self.joystick_hw = self.app.hardware['joystickHW']
        self.pump_hw = self.app.hardware['MFCSHardware']

    def run(self):
        
        self.button_pressed_before = False
        self.xbutton_pressed_before = False
        
        self.eff_subarrayh = int(self.camera.subarrayh.val/self.camera.binning.val)
        self.eff_subarrayv = int(self.camera.subarrayv.val/self.camera.binning.val)
        
        self.image = np.zeros((self.eff_subarrayv,self.eff_subarrayh),dtype=np.uint16)
        self.image1 = np.zeros((self.eff_subarrayv,self.eff_subarrayh),dtype=np.uint16)
        self.image2 = np.zeros((self.eff_subarrayv,self.eff_subarrayh),dtype=np.uint16)
        
        self.image[0,0] = 1 #Otherwise we get the "all zero pixels" error (we should modify pyqtgraph...)
        self.image1[0,0] = 1
        self.image2[0,0] = 1
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
                
                #save = True
                
                while not self.interrupt_measurement_called:
            
                    [frame, dims] = self.camera.hamamatsu.getLastFrame()

                    if self.camera.hamamatsu.last_frame_number == 1: #if it is the first image taken (buffer index 0)(initialization condition)
                        frame1 = frame
                        self.np_data1 = frame1.getData()
                        self.image1 = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))
                        
                    elif self.camera.hamamatsu.buffer_index%2 == 0: #if the index of the buffer is even
                        frame1 = frame
                        self.np_data1 = frame1.getData()
                        self.image1 = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))
                        
                        if self.camera.hamamatsu.backlog != 1:
                            if self.camera.hamamatsu.buffer_index != 0:
                                frame2 = self.camera.hamamatsu.getRequiredFrame(self.camera.hamamatsu.buffer_index-1)[0]
                                self.np_data2 = frame2.getData()
                                self.image2 = np.reshape(self.np_data2, (self.eff_subarrayv, self.eff_subarrayh))
                            else:
                                frame2 = self.camera.hamamatsu.getRequiredFrame(self.camera.hamamatsu.number_image_buffers-1)[0]
                                self.np_data2 = frame2.getData()
                                self.image2 = np.reshape(self.np_data2, (self.eff_subarrayv, self.eff_subarrayh))
                    else:
                        if self.camera.hamamatsu.backlog == 1:
                            frame2 = frame
                            
                            self.np_data2 = frame2.getData()
                            self.image2 = np.reshape(self.np_data2, (self.eff_subarrayv, self.eff_subarrayh))
                        else:
                            frame2 = frame
                            frame1 = self.camera.hamamatsu.getRequiredFrame(self.camera.hamamatsu.buffer_index-1)[0]
                            
                            self.np_data1 = frame1.getData()
                            self.image1 = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))
                            self.np_data2 = frame2.getData()
                            self.image2 = np.reshape(self.np_data2, (self.eff_subarrayv, self.eff_subarrayh))

                    #===========================================================
                    # record isn't supported
                    # if self.settings['record']:
                    #     self.camera.hamamatsu.stopAcquisition()
                    #     self.camera.hamamatsu.startRecording()
                    #     self.camera.hamamatsu.stopRecording()
                    #     self.interrupt()    
                    #===========================================================
                    
                    if self.settings['save_h5']:
                        self.camera.hamamatsu.stopAcquisitionNotReleasing()
                        self.initH5()
                        print("\n \n ******* \n \n Saving :D !\n \n *******")
                        [frames1, dims1] = self.camera.hamamatsu.getLastEvenFrames()
                        [frames2, dims2] = self.camera.hamamatsu.getLastOddFrames()
                        for aframe1 in frames1:
                            self.np_data1 = aframe1.getData()
                            self.image_on_the_run = np.reshape(self.np_data1, (self.eff_subarrayv, self.eff_subarrayh))
                            self.image_h5_1[index, :, :] = self.image_on_the_run  # saving to the h5 dataset
                            self.h5file.flush()  # maybe is not necessary
                            self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                            index+=1
                            
                        for aframe2 in frames2:
                            self.np_data2 = aframe2.getData()
                            self.image_on_the_run = np.reshape(self.np_data2, (self.eff_subarrayv, self.eff_subarrayh))
                            self.image_h5_2[index, :, :] = self.image_on_the_run  # saving to the h5 dataset
                            self.h5file.flush()  # maybe is not necessary
                            self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                            index+=1
                            
                        self.h5file.close()
                        self.settings.save_h5.update_value(new_val = False)
                        index = 0
                        self.settings['progress'] = index*100./self.camera.hamamatsu.number_image_buffers
                        self.camera.hamamatsu.startAcquisitionWithoutAlloc()
        finally:
            
            self.stop_triggered_Acquisition()

            if self.settings['save_h5']:
                self.h5file.close() # close h5 file  
                self.settings.save_h5.update_value(new_val = False)
                
        
    def update_display(self):
        
        super().update_display()
        
        if hasattr(self.joystick_hw,'joystick_dev'):
            """
            THIS READS THE JOYSTICK AXIS VALUE AND SET THE PRESSURE AT CH1
            """
            self.pump_hw.settings['set_pressure_1'] = self.pump_hw.settings['set_pressure_1'] \
                                                  + RESOLUTION*self.joystick_hw.joystick_dev.get_hat_values(1) + 10**2*RESOLUTION*self.joystick_hw.joystick_dev.get_hat_values(0) \
                                                  - self.sensitivity_dict[self.settings['sensitivity']]*(1 + self.joystick_hw.joystick_dev.get_axis_values(AXIS_L2)) \
                                                  + self.sensitivity_dict[self.settings['sensitivity']]*(1 + self.joystick_hw.joystick_dev.get_axis_values(AXIS_R2)) \
            
            self.pump_hw.read_pressure_1.read_from_hardware()
            
            """
            THIS READS THE JOYSTICK BUTTON VALUE AND SET THE SAVED PRESSURE
            """
            self.pump_hw.settings['save_pressure']=self.joystick_hw.joystick_dev.get_button_valuess(O)
            self.pump_hw.settings['apply_saved_pressure']=self.joystick_hw.joystick_dev.get_button_valuess(Q)
            """
            THIS READS THE JOYSTICK X BUTTON AND CHANGE THE VALUE OF SAVE_H5
            """
            if self.xbutton_pressed_before and not self.joystick_hw.joystick_dev.get_button_values(X):
                self.xbutton_pressed_before = False
                
            if self.joystick_hw.joystick_dev.get_button_values(X) and not self.xbutton_pressed_before :
                self.xbutton_pressed_before = True
                self.settings['save_h5'] = not self.settings['save_h5']
        
            """
            THIS READS THE JOYSTICK PS BUTTON AND CHANGE THE VALUE OF SENSITIVITY (STILL HAVE TO FIND AN ALTERNATIVE TO ELIF...)
            """
            if self.button_pressed_before and not self.joystick_hw.joystick_dev.get_button_values(BUTTON_PS):
                self.button_pressed_before = False
            
            if self.joystick_hw.joystick_dev.get_button_values(BUTTON_PS) and not self.button_pressed_before:
                
                self.button_pressed_before = True
                
                if self.settings['sensitivity'] == "low":
                    self.settings['sensitivity'] = "medium"
                
                elif self.settings['sensitivity'] == "medium":
                    self.settings['sensitivity'] = "high"
                    
                elif self.settings['sensitivity'] == "high":
                    self.settings['sensitivity'] = "low"
                    
    def initH5(self):
        """
        Initialization operations for the h5 file.
        """
#         t0 = time.time()
#         f = self.app.settings['data_fname_format'].format(
#             app=self.app,
#             measurement=self,
#             timestamp=datetime.fromtimestamp(t0),
#             ext='h5')
        
#         f = self.app.settings['data_fname_format'].format(
#             app=self.app,
#             measurement=self,
#             timestamp=datetime.fromtimestamp(t0),
#             sample=self.app.settings["sample"],
#             ext='h5')
#         fname = os.path.join(self.app.settings['save_dir'], f)
        
#        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)

        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image.shape
        length=self.camera.hamamatsu.number_image_buffers
        self.image_h5_1 = self.h5_group.create_dataset( name  = 't0/c0/image', 
                                                      shape = ( length/2, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        self.image_h5_2 = self.h5_group.create_dataset( name  = 't0/c1/image', 
                                                      shape = ( length/2, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5_1.dims[0].label = "z"
        self.image_h5_1.dims[1].label = "y"
        self.image_h5_1.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5_1.attrs['element_size_um'] =  [1,1,1]
        
        self.image_h5_2.dims[0].label = "z"
        self.image_h5_2.dims[1].label = "y"
        self.image_h5_2.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5_2.attrs['element_size_um'] =  [1,1,1]
        
    def initH5_original(self):
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
        
                