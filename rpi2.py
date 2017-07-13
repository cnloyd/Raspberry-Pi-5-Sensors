#!/usr/bin/python 

# uses the curses library to make a terminal screen that allows
# the user to communicate with Atlas Scientific boards

import curses, curses.ascii # needed to allow seperate terminal displays
import serial # required for communication with boards
import RPi.GPIO as GPIO
from time import strftime, sleep # used for timestamps, delays

def main(stdscr):
    #screen parameters
    pos_text = 0 # the position of the cursor in the user input area
    stdscr.nodelay(1) # stops the terminal from waiting for user input
    height,width = stdscr.getmaxyx() # gets the height and width of the terminal window
    max_pad_length = 100 # the maximum length of the received text buffer
    pad = curses.newpad(max_pad_length, width) # creates a text area buffer that holds max_pad_length lines
    inputpad = stdscr.subpad(1, width, height-1, 0) # creates the area to input text on the bottom
    
    #USB parameters
    usbport = '/dev/ttyAMA0'
    ser = serial.Serial(usbport, 9600, timeout = 0) # sets the serial port to the specified port, with a 9600 baud rate
    # Timeout = 0 tells the serial port to not wait for input if there is non 
    
    # declare and initialize the data buffers
    line = "" 
    user_input = ""

    def set_channel(channel):
        # sets the multiplexer to the specified channel
        # channel name is a string, not an int
        if channel == '0':
            GPIO.output(S0_pin, False)
            GPIO.output(S1_pin, False)

        elif channel == '1':
            GPIO.output(S0_pin, True)
            GPIO.output(S1_pin, False)
            GPIO.output(S2_pin, False)
            
        elif channel == '2':
            GPIO.output(S0_pin, False)
            GPIO.output(S1_pin, True)
            GPIO.output(S2_pin, False)

        elif channel == '3':
            GPIO.output(S0_pin, True)
            GPIO.output(S1_pin, True)
            GPIO.output(S2_pin, False)

        elif channel == '4':
            GPIO.output(S0_pin, False)
            GPIO.output(S1_pin, False)
            GPIO.output(S2_pin, True)
        pad.addstr("> Channel %s\n" % channel)
        sleep(1)
        ser.flushInput() # clear the data received on the previous channel
              
    GPIO.setmode(GPIO.BCM)
    S0_pin = 18
    S1_pin = 23
    S2_pin = 24
    channel = '0' # intial channel
    GPIO.setup(S0_pin, GPIO.OUT) # S0 
    GPIO.setup(S1_pin, GPIO.OUT) # S1
    GPIO.setup(S2_pin, GPIO.OUT) # S2
    
    pad.addstr("Atlas Scientific Serial Port Expander Sample Code\n")
    pad.addstr("  x:[command] switches to channel x and sends a command over it\n")
    pad.addstr("    ex. 1:L,? switches the mux to channel 1, then sends the L,? command\n")
    pad.addstr("  A command with no channel prefix is sent on the last used channel\n")
    set_channel(channel)
    
    #main loop
    try:
        while True:
            y,x = pad.getyx() # gets the position of the cursor in the main screen
            if(y >= max_pad_length-3): # clear screen when at the end of buffer
                pad.erase()
                pad.move(0,0)
            pad.refresh(y-(height-3),0, 0,0, height-2,width) # refresh the main screen and scroll to the cursor
            inputpad.refresh() # refresh the input area every loop
            sleep(.1)
            
            # sensor receive
            data = ser.read() # get serial data
            if(data == "\r"): # if its terminated by a newline
                pad.addstr("> " + strftime("%Y-%m-%d %H:%M:%S") + 
                " Channel %s: %s\n" % (channel, line)) #print the timestamp and received data to the main screen
                line = "" # clears the input
                
            else:
                line  = line + data # if the line isn't complete, add the new characters to it
            
            # user receive
            c= stdscr.getch()
            if c != -1:
                if(c == curses.KEY_BACKSPACE):
                    # if the backspace character is pressed, clear the current user input
                    pos_text = 0
                    inputpad.clear()
                    user_input = ""
                    
                elif(c == ord('\n') or c == ord('\r')):
                    # if the enter key is pressed, send the input to the board and clear the user input
                    try:
                        split_input = user_input.split(":")
                        send_line = split_input[1]
                        channel = split_input[0] # the first letter of the user input
                        set_channel(channel)
                        
                    except IndexError:
                        send_line = user_input # else send to current channel
                    
                    if(len(send_line) > 0): # only send if there is a command
                        pad.addstr("> Sent to board %s: %s\n" % (channel, send_line))
                        ser.write(send_line + '\r')
                    pos_text = 0
                    inputpad.clear()
                    user_input = ""
                    
                elif(curses.ascii.isprint(c)):
                    # if the character is a printable character, put it into the input area and send buffer
                    user_input = user_input + chr(c)
                    inputpad.addstr(0, pos_text, chr(c))
                    inputpad.move(0, pos_text)
                    pos_text = (pos_text + 1) % (width -1) # increments the cursors position in the input area, returns it to the beginning if it runs past the screen size
                else:
                    #if the character entered doesnt meet any conditions, ignore it
                    pass
    except KeyboardInterrupt: GPIO.cleanup() # frees GPIO driver from usage
                    
if __name__ == '__main__':
    curses.wrapper(main) # wraps the curses window to undo the changes it makes to the terminal on exits and exceptions

