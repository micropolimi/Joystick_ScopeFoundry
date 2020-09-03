from ScopeFoundry import BaseMicroscopeApp
#from JoystickPump import JoystickPump

class FancyMicroscopeApp(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'fancy_microscope'
    
    # You must define a setup function that adds all the 
    #capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        
        #Add hardware components
        print("Adding Hardware Components")
        
        from ScopeFoundryHW.virtual_function_gen.vfunc_gen_hw import VirtualFunctionGenHW
        from ScopeFoundryHW.joystick_hardware.joystick_hd import JoyStick_HW
        self.add_hardware(VirtualFunctionGenHW(self))
        self.add_hardware(JoyStick_HW(self))
        
        #Add measurement components
        print("Create Measurement objects")
        
        from Microscopes.VirtualMicroscopeJoyStick.SineGenJoyStick_measure import SineWaveJoyStickMeasure
        self.add_measurement(SineWaveJoyStickMeasure(self))
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()
        
        #self.joystick = JoystickPump(self)
        #self.thread = Thread(target=self.joystick.joystickRun)
        #self.thread.start()
        
if __name__ == '__main__':
    
    import sys
    app = FancyMicroscopeApp(sys.argv)
    sys.exit(app.exec_())