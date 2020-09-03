from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time

RESOLUTION = 0.0001
AXIS_L2 = 5
AXIS_R2 = 4
BUTTON_PS = 12
X=1

class SineWaveJoyStickMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "sine_wave_joystick"
    
    
    def setup(self):
        """
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "sine_plot.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        
        # Create a setting names "sensitivity" that defines the sensitivity of joystick axes.
        self.settings.New('sensitivity', dtype=str, choices = ["low", "medium", "high"], initial="medium") 
        
        # Create a dictionary to associate numerical values to each sensitivity levels. This numerical value will be used in update_display
        self.sensitivity_dict = {"low":0.0001, "medium":0.001, "high":0.1}
        #self.sensitivity_dict["low"]
        
        # Create empty numpy array to serve as a buffer for the acquired data
        self.buffer = np.zeros(120, dtype=float)
        
        # Define how often to update display during a run
        self.display_update_period = 0.1 
        
        # Convenient reference to the hardware used in the measurement
        self.func_gen = self.app.hardware['virtual_function_gen']
        """
        THIS CONNECTS THE JOYSTICK TO THE MEASUREMENT
        """
        self.joystick = self.app.hardware['joystickHW']


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
        self.func_gen.settings.amplitude.connect_to_widget(self.ui.amp_doubleSpinBox)
        
        # Set up pyqtgraph graph_layout in the UI
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # Create PlotItem object (a set of axes)  
        self.plot = self.graph_layout.addPlot(title="Sine Wave Readout Plot")
        # Create PlotDataItem object ( a scatter plot on the axes )
        self.optimize_plot_line = self.plot.plot([0])        

    
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        self.optimize_plot_line.setData(self.buffer) 
        
        """
        THIS READS THE JOYSTICK AXIS VALUE AND SET THE AMPLITUDE OF THE FUNCTION GENERATOR 
        """

        if hasattr(self.joystick,'joystick_dev'):
            """
            THIS READS THE JOYSTICK AXIS VALUE AND SET THE AMPLITUDE OF THE FUNCTION GENERATOR 
            """
            self.func_gen.settings['amplitude'] = self.func_gen.settings['amplitude'] \
                                                  + RESOLUTION*self.joystick.joystick_dev.get_hat_values(1) + 10**2*RESOLUTION*self.joystick.joystick_dev.get_hat_values(0) \
                                                  - self.sensitivity_dict[self.settings['sensitivity']]*(1 + self.joystick.joystick_dev.get_axis_values(AXIS_L2)) \
                                                  + self.sensitivity_dict[self.settings['sensitivity']]*(1 + self.joystick.joystick_dev.get_axis_values(AXIS_R2)) \
            
            """
            THIS READS THE JOYSTICK X BUTTON AND CHANGE THE VALUE OF SAVE_H5
            """
            if self.xbutton_pressed_before and not self.joystick.joystick_dev.get_button_values(X):
                self.xbutton_pressed_before = False
                
            if self.joystick.joystick_dev.get_button_values(X) and not self.xbutton_pressed_before :
                self.xbutton_pressed_before = True
                self.settings['save_h5'] = not self.settings['save_h5']
        
            """
            THIS READS THE JOYSTICK PS BUTTON AND CHANGE THE VALUE OF SENSITIVITY (STILL HAVE TO FIND AN ALTERNATIVE TO ELIF...)
            """
            if self.button_pressed_before and not self.joystick.joystick_dev.get_button_values(BUTTON_PS):
                self.button_pressed_before = False
            
            if self.joystick.joystick_dev.get_button_values(BUTTON_PS) and not self.button_pressed_before:
                
                self.button_pressed_before = True
                
                if self.settings['sensitivity'] == "low":
                    self.settings['sensitivity'] = "medium"
                
                elif self.settings['sensitivity'] == "medium":
                    self.settings['sensitivity'] = "high"
                    
                elif self.settings['sensitivity'] == "high":
                    self.settings['sensitivity'] = "low"
            
            
    def run(self):
        
        self.button_pressed_before = False
        self.xbutton_pressed_before = False
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        # first, create a data file
        if self.settings['save_h5']:
            # if enabled will create an HDF5 file with the plotted data
            # first we create an H5 file (by default autosaved to app.settings['save_dir']
            # This stores all the hardware and app meta-data in the H5 file
            self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
            
            # create a measurement H5 group (folder) within self.h5file
            # This stores all the measurement meta-data in this group
            self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
            
            # create an h5 dataset to store the data
            self.buffer_h5 = self.h5_group.create_dataset(name  = 'buffer', 
                                                          shape = self.buffer.shape,
                                                          dtype = self.buffer.dtype)
        
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        try:
            i = 0
            
            
            
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
            
                
                
                
                
                
                i %= len(self.buffer)
                
                # Set progress bar percentage complete
                self.settings['progress'] = i * 100./len(self.buffer)
                
                # Fills the buffer with sine wave readings from func_gen Hardware
                self.buffer[i] = self.func_gen.settings.sine_data.read_from_hardware()
                
                if self.settings['save_h5']:
                    # if we are saving data to disk, copy data to H5 dataset
                    self.buffer_h5[i] = self.buffer[i]
                    # flush H5
                    self.h5file.flush()
                
                # wait between readings.
                # We will use our sampling_period settings to define time
                time.sleep(self.settings['sampling_period'])
                
                i += 1

                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    break

        finally:            
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
