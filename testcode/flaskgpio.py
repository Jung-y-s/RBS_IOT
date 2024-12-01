from flask import Flask   

import RPi.GPIO as GPIO
import time           

app = Flask(__name__)                    

@app.route('/start')                                      
def start():
    pin = 18 # PWM pin num 18 
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)

    p = GPIO.PWM(pin, 50)
    p.start(0)
    cnt = 0
    
    p.ChangeDutyCycle(5) #0도
    print ("angle : 1")
    time.sleep(1)
    p.ChangeDutyCycle(7.5) #90도
    print ("angle : 5")
    time.sleep(1)
    p.ChangeDutyCycle(10) #180도
    print ("angle : 10")
    time.sleep(1)

    GPIO.cleanup()
    
    return 0
    
@app.route('/stop')                                      
def stop():
    pin = 18 # PWM pin num 18 
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)

    p = GPIO.PWM(pin, 50)
    p.start(0)
    cnt = 0
    
    p.ChangeDutyCycle(5) #0도
    print ("angle : 1")
    time.sleep(1)

    GPIO.cleanup()
    
    return 0

if __name__ == '__main__':          
    app.run(debug=True, port=80, host='0.0.0.0') 