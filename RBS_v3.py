from flask import Flask, jsonify   
import adafruit_dht
import board
import requests
import RPi.GPIO as GPIO
import time          
import pigpio 
import threading
from hx711 import HX711


#핀 배열
GPIO.setmode(GPIO.BCM)
inservo = 18
outservo = 12
fireservo = 13
bt = 25
flame = 27
weight = 22
TRIGER = 23
ECHO = 24
hx = HX711(5, 6)


#gpio 데몬
pi = pigpio.pi()
if not pi.connected:
    print("pigpio 데몬이 실행되지 않고 있습니다. 'sudo pigpiod' 명령어로 실행해주세요.")
    exit()
    
    
#온습도 센서 핀 지정
dhtDevice = adafruit_dht.DHT22(board.D17, use_pulseio=False)


#무게센서 설정
hx.set_reading_format("MSB", "MSB")
referenceUnit = 114
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()


# 서보모터의 회전 방향 및 속도 설정
def move_servo(servo, pulse_width):
    # 펄스 폭을 설정하여 서보모터 이동
    pi.set_servo_pulsewidth(servo, pulse_width)
    print(f"펄스 폭: {pulse_width}us")

#펄스 주파수 지정
pi.set_PWM_frequency(outservo, 50)
pi.set_PWM_frequency(fireservo, 50)


#핀 타입 설정
GPIO.setup(inservo, GPIO.OUT)
GPIO.setup(flame, GPIO.IN)
GPIO.setup(weight, GPIO.IN)
GPIO.setup(bt, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(TRIGER, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)


#시간 변수 설정
startTime = time.time()  


#온습도 측정 
def tempsen():
    try:
        #온습도
        temp = dhtDevice.temperature
        humi = dhtDevice.humidity
        flame_val = 'off'
        weight_val = 0
        percentage = 0
        #화염센서
        if GPIO.input(flame) == 0:
            flame_val = "on"
        
        #초음파 센서
        GPIO.output(TRIGER, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(TRIGER, GPIO.HIGH)
        time.sleep(0.00002)
        GPIO.output(TRIGER, GPIO.LOW)
        
        while GPIO.input(ECHO) == GPIO.LOW:
            startTime = time.time()
 
        while GPIO.input(ECHO) == GPIO.HIGH:
            endTime = time.time()
            
        period = endTime - startTime
        dist1 = round(period * 1000000 / 58, 2)
        dist2 = round(period * 17241, 2)
        distance = (dist1 + dist2) / 2
        
        #퍼센트 변환
        percentage = ((25 - distance) / (25 - 6)) * 100
        
        
        #무게 측정
        weight_val = 0
        for i in range(5):
            weight_val += hx.get_weight(5)
        weight_val = weight_val/5
        
        time.sleep(1)
        
        #화재 버튼
        fbt = GPIO.input(bt)
        
    except RuntimeError as error:
        print(error.args[0])
        
    finally:
        pass
    
    return temp, humi, flame_val, weight_val, percentage, fbt


#플라스크 메인
app = Flask(__name__)                    


#투입구 열기
@app.route('/inopen')
def inopen():
    move_servo(inservo, 1500)  
    time.sleep(0.5)  
    move_servo(inservo, 1200) 
    time.sleep(0.5) 
    move_servo(inservo, 1500)
    
    tempVal, humiVal, flameVal, weightVal, percentageVal, fbtVal= tempsen()
    
    data = {
        'ID' : 1,
        'stats' : 'inopen',
        'temp' : tempVal,
        'humi' : humiVal,
        'flame' : flameVal,
        'weight' : weightVal,
        'full' : percentageVal, 
        'bt' : fbtVal
        }
    
    print(data)
   
    return jsonify(data)

#투입구 닫기   
@app.route('/inclose')                           
def inclose():
    move_servo(inservo, 1500)  
    time.sleep(0.5)  
    move_servo(inservo, 1800) 
    time.sleep(0.5) 
    move_servo(inservo, 1500)
    
    tempVal, humiVal, flameVal, weightVal, percentageVal, fbtVal= tempsen()
    
    data = {
        'ID' : 1,
        'stats' : 'inclose',
        'temp' : tempVal,
        'humi' : humiVal,
        'flame' : flameVal,
        'weight' : weightVal,
        'full' : percentageVal, 
        'bt' : fbtVal
        }
    
    print(data)
   
    return jsonify(data)

#배출구 열기
@app.route('/outopen')                                
def outopen():
    move_servo(outservo, 1500)  
    time.sleep(0.5)  
    move_servo(outservo, 1200) 
    time.sleep(0.5) 
    move_servo(outservo, 1500)
    
    tempVal, humiVal, flameVal, weightVal, percentageVal, fbtVal= tempsen()
    
    data = {
        'ID' : 1,
        'stats' : 'outopen',
        'temp' : tempVal,
        'humi' : humiVal,
        'flame' : flameVal,
        'weight' : weightVal,
        'full' : percentageVal, 
        'bt' : fbtVal
        }
    
    print(data)
    
    return jsonify(data)

#배출구 닫기
@app.route('/outclose')                                
def outclose():
    move_servo(outservo, 1500)  
    time.sleep(0.5)  
    move_servo(outservo, 1800) 
    time.sleep(0.5) 
    move_servo(outservo, 1500)
    
    tempVal, humiVal, flameVal, weightVal, percentageVal, fbtVal= tempsen()
    
    data = {
        'ID' : 1,
        'stats' : 'inclose',
        'temp' : tempVal,
        'humi' : humiVal,
        'flame' : flameVal,
        'weight' : weightVal,
        'full' : percentageVal, 
        'bt' : fbtVal
        }
    
    print(data)

    return jsonify(data)

@app.route('/apisend', methods=['POST'])
def apisend():
    # 외부 API의 URL
    api_url = 'https://192.168.0.20/msp/info'
    
    # 클라이언트에서 받은 데이터 (JSON 형식)
    data = request.get_json()

    # 기본 데이터 (디폴트로 사용할 값)
    if data is None:
        data = {'temperature': 25, 'humidity': 60}
    
    # 헤더 정의 (예: Authorization 헤더, Content-Type 헤더)
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJ1c2VyMDEiLCJyb2xlIjoiUk9MRV9BRE1JTiIsImlhdCI6MTczMTU2NzQ3MCwiZXhwIjoxNzMxNTY3NTA2fQ._ha5rGBP51Q0bkh44bxBPROvVNh9c8hRNF8A8QRWqX0',  # Bearer Token 방식의 인증
        'Content-Type': 'application/json'  # 요청 본문 데이터가 JSON 형식임을 명시
    }
    
    # POST 요청 보내기 (데이터를 JSON 형식으로 포함)
    response = requests.post(api_url, json=data, headers=headers)
    
    # 응답이 성공적이면 JSON 데이터를 반환
    if response.status_code == 200:
        return jsonify(response.json())  # 외부 API의 JSON 응답을 그대로 반환
    else:
        return jsonify({'error': 'Failed to fetch data'}), 500
    
    
#화재 감지하는 쓰레드 함수    
def fire(): 
    while True:
        try:
            move_servo(inservo, 1500)  
            time.sleep(0.5)  
            move_servo(inservo, 1200) 
            time.sleep(0.5) 
            move_servo(inservo, 1500)
            time.sleep(0.5) 
            move_servo(inservo, 1800) 
            time.sleep(0.5) 
            move_servo(inservo, 1500)

            tempVal, humiVal, flameVal, weightVal, percentageVal, fbtVal= tempsen()
            
            #if 버튼 푸쉬
            if tempVal == 70 or flameVal == "on" or GPIO.input(bt) == GPIO.HIGH:
                move_servo(fireservo, 1500)  
                time.sleep(0.5)  
                move_servo(fireservo, 1200) 
                time.sleep(0.5) 
                move_servo(fireservo, 1500)
                time.sleep(0.5) 
                move_servo(fireservo, 1800) 
                time.sleep(0.5) 
                move_servo(fireservo, 1500)
            
                data = {
                    'ID' : 1,
                    'stats' : 'fire',
                    'temp' : tempVal,
                    'humi' : humiVal,
                    'flame' : flameVal,
                    'weight' : weightVal,
                    'full' : percentageVal, 
                    'bt' : fbtVal
                }
                
                print("비상!비상! 화재 감지 삐용삐용!!")
                print(data)
            
            # API로 백에 전송 (창진이랑 상의 필요)
            
        except RuntimeError as error:
            print(error.args[0])
            
        finally:
            pass

def db(): #DB에 데이터 넣는 쓰레드 함수
    # 외부 API의 URL
    api_url = 'https://192.168.0.20/msp/info'

    # 헤더 정의 (예: Authorization 헤더, Content-Type 헤더)
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJ1c2VyMDEiLCJyb2xlIjoiUk9MRV9BRE1JTiIsImlhdCI6MTczMTU2NzQ3MCwiZXhwIjoxNzMxNTY3NTA2fQ._ha5rGBP51Q0bkh44bxBPROvVNh9c8hRNF8A8QRWqX0',
        'Content-Type': 'application/json',  # JSON 형식으로 데이터를 보낼 때 Content-Type 지정
    }

    # 보내려는 데이터 (JSON 형식)
    data = {
        'temperature': 25,
        'humidity': 60
    }

    # POST 요청 보내기 (데이터를 JSON 형식으로 포함)
    response = requests.post(api_url, json=data, headers=headers)

    # 응답이 성공적이면 JSON 데이터를 반환
    if response.status_code == 200:
        return jsonify(response.json())  # 외부 API의 JSON 응답을 그대로 반환
    else:
        return jsonify({'error': 'Failed to fetch data'}), 500
    
    
# thread_1 = threading.Thread(target=db)
thread_2 = threading.Thread(target=fire)

# thread_1.start()
thread_2.start()


if __name__ == '__main__':          
    app.run(debug=True, port=82, host='0.0.0.0',  threaded=True) 