
from BaseMicroscopeModified_ScopeFoundry.BaseMicroscopeAppModified import BaseMicroscopeAppModified
class ProChipJoystickApp(BaseMicroscopeAppModified):
    
    name = 'Laser_DAQ_Camera_App'
    
    def setup(self):
        

        from Hamamatsu_ScopeFoundry.CameraHardware import HamamatsuHardware
        from laser.laser_hardware import LaserHW
        from nidaqmx_test.ni_do_hardware import NI_DO_hw
        from nidaqmx_test.ni_co_hardware import NI_CO_hw
        from joystick_hardware.joystick_hd import JoyStick_HW
        from FluigentHardwareUpdated.PumpHardware import MFCSHardware

        self.add_hardware(HamamatsuHardware(self))
        self.add_hardware(LaserHW(self, name='Laser_1'))
        self.add_hardware(LaserHW(self, name='Laser_2'))
        self.add_hardware(NI_CO_hw(self, name='Counter_Output_1'))
        self.add_hardware(NI_CO_hw(self, name='Counter_Output_2'))
        self.add_hardware(NI_DO_hw(self, name='Digital_Output_1'))
        self.add_hardware(JoyStick_HW(self))
        self.add_hardware(MFCSHardware(self))
        print("Adding Hardware Components")
        
        #from StartTriggerMeasurement import StartTriggerMeasurement
        #self.add_measurement(StartTriggerMeasurement(self))
        
        from ProChipJoystick.SyncreadoutTriggerJoystickCounterMeasurement import SyncreadoutTriggerJoystickCounterMeasurement
        self.add_measurement(SyncreadoutTriggerJoystickCounterMeasurement(self))
        
        #from DAQ_Laser_Camera.temp import temp
        #self.add_measurement(temp(self))
                
        #from DAQ_Laser_Camera.SyncreadoutTriggerMeasurement import SyncreadoutTriggerMeasurement
        #self.add_measurement(SyncreadoutTriggerMeasurement(self))
        
        from Hamamatsu_ScopeFoundry.CameraMeasurement import HamamatsuMeasurement
        self.add_measurement(HamamatsuMeasurement(self))
        
#         from temp_measurement import TempMeasurement
#         self.add_measurement(TempMeasurement(self))
#         
        print("Adding measurement components")
        
        self.ui.show()
        self.ui.activateWindow()
        

if __name__ == '__main__':
            
    import sys
    app = ProChipJoystickApp(sys.argv)
    sys.exit(app.exec_())
        
        