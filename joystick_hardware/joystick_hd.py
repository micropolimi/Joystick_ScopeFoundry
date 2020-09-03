from ScopeFoundry import HardwareComponent
from joystick_hardware.joystick_device import JoyStickDevice

class JoyStick_HW(HardwareComponent):
    
    ## Define name of this hardware plug-in
    name = 'joystickHW'
    
    def setup(self):
        # Define your hardware settings here.
        # These settings will be displayed in the GUI and auto-saved with data files
        self.settings.New(name='index', initial=0, dtype = int, ro=False)
        self.settings.New(name='axis', initial=0.0, dtype=float, ro=True)
        self.settings.New(name='button', initial=False, dtype= bool, ro=True)
        self.settings.New(name='hat', initial=0, dtype= int, ro=True)
         # Create a setting names "sensitivity" that defines the sensitivity of joystick axes.
        self.settings.New('sensitivity', dtype=str, choices = ["low", "medium", "high"], initial="medium") 
        # Create a dictionary to associate numerical values to each sensitivity levels. This numerical value will be used in update_display
        self.sensitivity_dict = {"low":0.0001, "medium":0.001, "high":0.1}
        #self.sensitivity_dict["low"]

    def connect(self):
       
        INDEX = 0
        
        # Open connection to the device:
        self.joystick_dev = JoyStickDevice()
        
        self.joystick_dev.index = self.settings.index.val
        
        # Connect settings to hardware:
        self.settings.index.connect_to_hardware(
            write_func  = self.joystick_dev.set_index
            )
              
        self.settings.axis.connect_to_hardware(
            read_func  = self.joystick_dev.get_axis_values
            )
        
        self.settings.button.connect_to_hardware(
            read_func  = self.joystick_dev.get_button_values
            )
        
        self.settings.hat.connect_to_hardware(
             read_func  = self.joystick_dev.get_hat_values
            )
        self.settings.sensitivity.connect_to_hardware(
            read_func  = self.joystick_dev.get_button_values
            )
#                 
        #Take an initial sample of the data.
        self.read_from_hardware()
        
    def disconnect(self):
        # remove all hardware connections to settings
        self.settings.disconnect_all_from_hardware()
        
        # Don't just stare at it, clean up your objects when you're done!
        if hasattr(self, 'joystick_dev'):
            del self.joystick_dev