from machine import PWM, Pin, I2C
from neopixel import NeoPixel
from time import sleep, ticks_ms, ticks_diff
from hcsr04 import HCSR04
#######################################################################################################################
import network
import espnow
import time
#######################################################################################################################
##### N E T W O R K #########
# Stats tracking
last_stats_time = time.time()
stats_interval = 10  # Print stats every 10 seconds

# Initialize Wi-Fi in station mode
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.config(channel=1)  # Set channel explicitly if packets are not received
sta.disconnect()

# Initialize ESP-NOW
e = espnow.ESPNow()
try:
    e.active(True)
except OSError as err:
    print("Failed to initialize ESP-NOW:", err)
    raise

# Sender's MAC address
sender_mac = b'\x68\x25\xdd\xf0\xcb\x18'  # Sender MAC

# Add peer (sender) for unicast reliability
# You don't need to add peer for broadcast
#try:
#    e.add_peer(sender_mac)
#except OSError as err:
#    print("Failed to add peer:", err)
#    raise

def print_stats():
    stats = e.stats()
    print("\nESP-NOW Statistics:")
    print(f"  Packets Sent: {stats[0]}")
    print(f"  Packets Delivered: {stats[1]}")
    print(f"  Packets Dropped (TX): {stats[2]}")
    print(f"  Packets Received: {stats[3]}")
    print(f"  Packets Dropped (RX): {stats[4]}")

print("Listening for ESP-NOW messages...")


#########################################################################################################
#Engine settings and vallues

# Motor A
IN1 = PWM(Pin(33), freq=1000)
IN2 = PWM(Pin(25), freq=1000)

# Motor B
IN3 = PWM(Pin(26), freq=1000)
IN4 = PWM(Pin(27), freq=1000)

# ESP32 PWM range: 0–1023 # 10 bit resolution scale 2^10
MAX_DUTY = 65535

def set_motor(pin_forward, pin_reverse, speed):
    speed = max(min(speed, 100), -100) # Defining speed range oom motors 0-100% both ways

    duty = int(abs(speed) * MAX_DUTY / 100) #Absolute duty cycle (0-65535) for the speed (technially 0-100)

    if speed > 0:
        pin_forward.duty_u16(duty)
        pin_reverse.duty_u16(0)

    elif speed < 0:
        pin_forward.duty_u16(0)
        pin_reverse.duty_u16(duty)

    else:
        pin_forward.duty_u16(0)
        pin_reverse.duty_u16(0)

def motorA(speed):
    set_motor(IN1, IN2, speed)

def motorB(speed):
    set_motor(IN3, IN4, speed)
       
       
###################### P I D #################################        
       
       
#Pid stats
#setpoint # What we want
#Ut  Control output
#Kp  Proportional gain (P) (Larger Kp increases responsiveness but risks oscillations)
#Ki  Intigral gain (I) (Addresses cumulative errors over time, eliminates steady state errors
#Kd  Derivative gain (D) (Predicts future errors based on error rate of change, reduces overshoot and stabalizes)
#Et  Error signal, defined as distance between
#setpoint r(t) and process variable y(t) (Error at time t)
#process_variable = #Distance reading from HCSR04

# E(t) = r(t) - y(t)
class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0

############### P I D Setup ###################################
    def compute (self, process_variable, dt):
        # Calculate error via diffrence of where we want to be and where we are
        error = process_variable - self.setpoint
   
        # Proportional term (Kp given value multiplies with error value)
        P_out = self.Kp * error
   
        # Integral term (Ki given value
        self.integral += error * dt #dt is delta time remember to add dt to true loop and not allow it to go to zero (we dont want to devide by zero)
        I_out = self.Ki * self.integral
   
        # Derivative term
        derivative = (error - self.previous_error) /dt
        D_out = self.Kd * derivative
   
        #compute total output
        output = P_out + I_out + D_out
   
        #Update previouse error (Ut = output)
        self.previous_error = error
   
        return output
# Initialize PID
setpoint = 60.0  # where we want to stop (60cm) ## Target distance
### initializing timer for dt
last_time = ticks_ms()


pid = PIDController (1.0, 0, 0.1, setpoint) #PID gains set

#########################################################################################################

#servopin = 25
#buzz = PWM(Pin(13, Pin.OUT))

#def sirene():
#    while True:
#        frekvens = 650
#        buzz.freq(frekvens)
#        sleep(0.3)
#        frekvens += 200r
#        sleep(0.8)
#        if frekvens >= 1050:
#            frekvens = 650

np = NeoPixel(Pin(14,Pin.OUT),24)

servo = PWM(Pin(32, Pin.OUT))

servofin = PWM(Pin(18, Pin.OUT))

ultralyd = HCSR04(15,16)

def set_color(r,g,b):
    for i in range(24):
        np[i] = (r,g,b)        
    np.write()

set_color(255,255,255)
set_color(0,0,0)

servofin.freq(50)
servo.freq(50)

dutti = 26

findutti = 77
servofin.duty(findutti)

#sirene()

while True:
    #####################################################################################################################################
    try:
        # Receive message (host MAC, message, timeout of 10 seconds)
        host, msg = e.recv(10000)
        if msg:
            print(f"Received from {host.hex()}: {msg.decode()}")
            break
        # Print stats every 10 seconds
    except KeyboardInterrupt:
        print("Stopping receiver...")
        e.active(False)
        sta.active(False)

        break
    #####################################################################################################################################
while True:  
    distance = ultralyd.distance_cm()
    print(distance, "cm")
    sleep(0.05)
    servo.duty(dutti)
    sleep(0.05)
    dutti += 10
    grad = 1.764705882 * (dutti-10) + -45.882352896
    print(round(grad),"grader")
    if dutti >= 128:
        dutti = 26
    ###########################################################
    if distance >= 0 and distance < 60:
        servofin.duty(77)#servo fin returnerer til neutral position
        set_color(255,255,255)
        #motor stopper
    if distance > 60:
        set_color(255,0,0)
        findutti = -1 * (dutti-10) + 154 #servo er modsat relativ til grad på radar -10 da dutti får 10+ efter rettelse
        servofin.duty(dutti)
        sleep(3)
        #tænd motor og kør
 ##########################################################################      
    current_time = ticks_ms()
    dt = ticks_diff(current_time, last_time) / 1000
    last_time = current_time

    if dt <= 0:
        dt = 0.01

    process_variable = ultralyd.distance_cm()

    motor_speed = pid.compute(process_variable, dt)

    motor_speed = max(min(motor_speed, 100), -100)

    motorA(motor_speed)
    motorB(motor_speed)
    print("speed:", motor_speed)
    time.sleep(0.05)