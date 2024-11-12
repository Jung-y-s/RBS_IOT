from flask import Flask, jsonify   
import adafruit_dht
import board

import RPi.GPIO as GPIO
import time          
import pigpio 

import threading


#핀 배열
GPIO.setmode(GPIO.BCM)
inservo = 18
outservo = 12
fireservo = 13
bt = 25
flame = 27
weight = 22

#gpio 데몬
pi = pigpio.pi()
if not pi.connected:
    print("pigpio 데몬이 실행되지 않고 있습니다. 'sudo pigpiod' 명령어로 실행해주세요.")
    exit()


# 서보모터의 회전 방향 및 속도 설정
def move_servo(servo, pulse_width):
    # 펄스 폭을 설정하여 서보모터 이동
    pi.set_servo_pulsewidth(servo, pulse_width)
    print(f"펄스 폭: {pulse_width}us")
    time.sleep(1)

#펄스 주파수 지정
pi.set_PWM_frequency(outservo, 50)
pi.set_PWM_frequency(fireservo, 50)


#핀 타입 설정
GPIO.setup(inservo, GPIO.OUT)
GPIO.setup(flame, GPIO.IN)
GPIO.setup(weight, GPIO.IN)
GPIO.setup(bt, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

#온습도 센서 핀 지정
dhtDevice = adafruit_dht.DHT22(board.D17)

  
#플라스크 메인
app = Flask(__name__)                    

#투입구 열기
@app.route('/inopen')
def inopen():
    
    print("투입구 열기")
    
    move_servo(inservo, 1500)  
    time.sleep(1)  
    move_servo(inservo, 1200) 
    time.sleep(1) 
    move_servo(inservo, 1500)
    
    data = {'stats' : '투입구 열기'}
   
    return jsonify(data)

#투입구 닫기   
@app.route('/inclose')                           
def inclose():
    
    print("투입구 닫기")
    
    move_servo(inservo, 1500)  
    time.sleep(1)  
    move_servo(inservo, 1800) 
    time.sleep(1) 
    move_servo(inservo, 1500)
    
    data = {'stats' : '투입구 닫기'}
   
    return jsonify(data)


#배출구 열기
@app.route('/outopen')                                
def outopen():
    
    print("배출구 열기")
    
    move_servo(outservo, 1500)  
    time.sleep(1)  
    move_servo(outservo, 1200) 
    time.sleep(1) 
    move_servo(outservo, 1500)
    
    data = {'stats' : '배출구 열기'}
   
    return jsonify(data)

#배출구 닫기
@app.route('/outclose')                                
def outclose():
    
    print("배출구 닫기")
    
    move_servo(outservo, 1500)  
    time.sleep(1)  
    move_servo(outservo, 1800) 
    time.sleep(1) 
    move_servo(outservo, 1500)
    
    data = {'stats' : '배출구 닫기'}
   
    return jsonify(data)


#센서 상태 확인하는 api 
@app.route('/state')
def state():
    
    try:
        humidity_data = dhtDevice.humidity
        temperature_data = dhtDevice.temperature
        flame_val = "off"
        
        if GPIO.input(flame) == 0:
            flame_val = "on"
        
        
        time.sleep(1)
        
        data = {"temp" : temperature_data,
                "humi" : humidity_data,
                "flame" : flame_val}
        
        print(humidity_data,temperature_data, flame_val)
        
        time.sleep(2)
        
    except RuntimeError as error:
        print(error.args[0])
        
    finally:
        pass

    return jsonify(data)


# def db(): #DB에 데이터 넣는 쓰레드 함수
#     return 0
    
#화재 감지하는 쓰레드 함수    
def fire(): 
    while True:
        try:
            humidity_data = dhtDevice.humidity
            temperature_data = dhtDevice.temperature
            
            #if 버튼 푸쉬
            
            if temperature_data == 70 or GPIO.input(flame) == 0 or GPIO.input(bt) == GPIO.HIGH:
                move_servo(fireservo, 1500)  
                time.sleep(1)
                move_servo(fireservo, 1800)  
                time.sleep(5)
                move_servo(fireservo, 1500) 
            
                data = {"temp" : temperature_data,
                        "humi" : humidity_data,
                        "flame" : "fire"}
                
                print("비상!비상! 화재 감지")
            
            # API로 백에 전송
            
        except RuntimeError as error:
            print(error.args[0])
            
        finally:
            pass


    
    
# thread_1 = threading.Thread(target=db)
thread_2 = threading.Thread(target=fire)

# thread_1.start()
thread_2.start()

if __name__ == '__main__':          
    app.run(debug=True, port=82, host='0.0.0.0',  threaded=True) 
    
    #무게 감지, db,