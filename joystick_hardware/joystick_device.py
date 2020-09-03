import pygame

class JoyStickDevice(object):

        
    def __init__(self):
        """
        Connects the joystick using pygame
        """
        
        pygame.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.running =True 
        self.axes = self.joystick.get_numaxes() 
        self.button = self.joystick.get_numbuttons() 
        self.hats = self.joystick.get_numhats()
        self.index = 0  
        
        
    def set_index(self,index):
        
        self.index = index    
    
    def get_axis_values(self, *argv):
        
        if len(argv) > 0:
            index=argv[0]
        else:
            index=self.index
        axis = []
        pygame.event.get()
        for i in range(self.axes):
            #print(self.joystick.get_axis(5))
            axis.append(self.joystick.get_axis(i))
        return axis[index]


    def get_button_values(self, *argv):
        
        if len(argv) > 0:
            index=argv[0]
        else:
            index=self.index
        
        buttons = []
        pygame.event.get()
        for i in range(self.button):
            #print(self.joystick.get_axis(5))
            buttons.append(self.joystick.get_button(i))
        return buttons[index]
#         
    def get_hat_values(self, *argv):
        
        if len(argv) > 0:
            index=argv[0]
        else:
            index=self.index
        
        hats = []
        pygame.event.get()
        for i in range(self.hats):
            #print(self.joystick.get_axis(5))
            hats.append(self.joystick.get_hat(i))
        return hats[0][index]
                    
                    
    def close(self):
        
        self.running = False
        pygame.joystick.quit()
        pygame.quit()
       
                    
if __name__ == '__main__':

    import time
    
    try:    
        ps4 =  JoyStickDevice()
        
        t0=time.time()
           
        while time.time()-t0 < 60:
           
            axis_values = ps4.get_axis_values()
            button_values = ps4.get_button_values()
            hat_values = ps4.get_hat_values(1)
            #print(axis_values)
            #print(button_values)
            print(hat_values)
            
    except Exception as err:
        print(err)
    finally:
        ps4.close()
                   
    