from DAQ_Laser_Camera.Laser_DAQ_Camera_App import Laser_DAQ_Camera_App

class ProChipJoystickApp(Laser_DAQ_Camera_App):
    
    name = 'ProChipJoystickApp'
    
    def setup(self):
        
        from joystick_hardware.joystick_hd import JoyStick_HW
        from FluigentHardwareUpdated.PumpHardware import MFCSHardware
        
        self.add_hardware(JoyStick_HW(self))
        self.add_hardware(MFCSHardware(self))
        

        super().setup()
        from Microscopes.ProChipMicroscopeJoystick.SyncreadoutTriggerJoystickMeasurement import SyncreadoutTriggerJoystickMeasurement
        from Microscopes.ProChipMicroscopeJoystick.CameraJoystickMeasurement import CameraJoystickMeasurement
        self.add_measurement(SyncreadoutTriggerJoystickMeasurement(self))
        self.add_measurement(CameraJoystickMeasurement(self))
        
if __name__ == '__main__':
            
    import sys
    app = ProChipJoystickApp(sys.argv)
    sys.exit(app.exec_())
        