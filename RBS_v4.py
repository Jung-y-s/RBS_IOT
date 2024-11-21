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
        temp = 0
        humi = 0
        flame_val = 1
        weight_val= 0
        percentage = 0
        
        #화염센서
        if GPIO.input(flame) == 0:
            flame_val = 1
        else:
            flame_val = 0
        
        time.sleep(1)
        
        #온습도
        temp = dhtDevice.temperature
        humi = dhtDevice.humidity
        
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
        
        if weight_val >= 1:
            weight_val = 10
        elif weight_val >= 5:
            weight_val = 20
        
        time.sleep(1)
        
    except RuntimeError as error:
        print(error.args[0])
        
    finally:
        pass
    
    return int(temp), int(humi), int(flame_val), int(weight_val), int(percentage)


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
   
    return 'ok'

#투입구 닫기   
@app.route('/inclose')                           
def inclose():
    move_servo(inservo, 1500)  
    time.sleep(0.5)  
    move_servo(inservo, 1800) 
    time.sleep(0.5) 
    move_servo(inservo, 1500)
    
    tempVal, humiVal, flameVal, weightVal, percentageVal= tempsen()
    
    data = {
        "fire": 0,
        "humidity": humiVal,
        "id": 1,
        "sparkStatus": flameVal,
        "temperature": tempVal,
        "weight": weightVal,
        "weightNow": percentageVal
    }
   
    return jsonify(data)

#배출구 열기
@app.route('/outopen')                                
def outopen():
    move_servo(outservo, 1500)  
    time.sleep(0.5)  
    move_servo(outservo, 1200) 
    time.sleep(0.5) 
    move_servo(outservo, 1500)
    
    return "ok"

#배출구 닫기
@app.route('/outclose')                                
def outclose():
    move_servo(outservo, 1500)  
    time.sleep(0.6)  
    move_servo(outservo, 1800) 
    time.sleep(0.6) 
    move_servo(outservo, 1500)
    
    tempVal, humiVal, flameVal, weightVal, percentageVal= tempsen()
    
    data = {
        "fire": 0,
        "humidity": humiVal,
        "id": 1,
        "sparkStatus": flameVal,
        "temperature": tempVal,
        "weight": weightVal,
        "weightNow": percentageVal
    }
    
    print(data)

    return jsonify(data)

@app.route('/apisend')
def apisend():
    tempVal, humiVal, flameVal, weightVal, percentageVal, fbtVal= tempsen()
    
    print(tempVal)
    
    # 1. 로그인 요청
    login_url = "http://192.168.0.20:8080/login"
    login_data = {
        "userId": "user01",
        "userPw": 1234
    }

    try:
        # 로그인 요청
        login_response = requests.post(login_url, data=login_data)

        # 응답 상태 확인
        if login_response.status_code == 200:
            # 응답 헤더에서 Authorization 토큰 추출
            auth_token = login_response.headers.get("Authorization")
            if auth_token:
                print("토큰 획득:", auth_token)

                # 2. GET 요청에 토큰 포함
                fire_url = (
                    f"http://192.168.0.20:8080/msp/fire"
                    f"?temperature={tempVal}&humidity={humiVal}&fire=1&sparkStatus=1&weight=10&weightNow={percentageVal}&id=1")
                headers = {"Authorization": auth_token}

                print(fire_url)
                
                # GET 요청 보내기
                fire_response = requests.get(fire_url, headers=headers)

                # 응답 처리
                if fire_response.status_code == 200:
                    print("Fire 요청 성공:", fire_response.json())
                    return jsonify({
                        "status": "success",
                        "message": "Fire 요청 성공",
                        "data": fire_response.json()
                    })
                else:
                    print(f"Fire 요청 실패: 상태 코드 {fire_response.status_code}, 응답 내용: {fire_response.text}")
                    return jsonify({
                        "status": "error",
                        "message": f"Fire 요청 실패: 상태 코드 {fire_response.status_code}",
                        "details": fire_response.text
                    }), fire_response.status_code
            else:
                print("Authorization 토큰이 응답 헤더에 없습니다.")
                return jsonify({
                    "status": "error",
                    "message": "Authorization 토큰이 응답 헤더에 없습니다."
                }), 401  # Unauthorized 상태 코드 반환
        else:
            print(f"로그인 실패: 상태 코드 {login_response.status_code}, 응답 내용: {login_response.text}")
            return jsonify({
                "status": "error",
                "message": f"로그인 실패: 상태 코드 {login_response.status_code}",
                "details": login_response.text
            }), login_response.status_code  # 로그인 실패 상태 코드 반환
    except requests.exceptions.RequestException as e:
        print("요청 중 오류 발생:", e)
        return jsonify({
            "status": "error",
            "message": "요청 중 오류 발생",
            "details": str(e)
        }), 500  # 서버 오류 상태 코드 반환
    
   
    
#화재 감지하는 쓰레드 함수    
def fire(): 
    while True:
        try:
            tempVal, humiVal, flameVal, weightVal, percentageVal, = tempsen()
            
            #if 버튼 푸쉬
            if tempVal == 70 or flameVal == 1 or GPIO.input(bt) == GPIO.HIGH:
                move_servo(fireservo, 1500)  
                time.sleep(0.5)  
                move_servo(fireservo, 1200) 
                time.sleep(0.5) 
                move_servo(fireservo, 1500)
                time.sleep(0.5) 
                move_servo(fireservo, 1800) 
                time.sleep(0.5) 
                move_servo(fireservo, 1500)
                
                print("비상!비상! 화재 감지 삐용삐용!!")

                #로그인 요청
                login_url = "http://192.168.0.20:8080/login"
                login_data = {
                    "userId": "user01",
                    "userPw": 1234
                }

                try:
                    #로그인 요청
                    login_response = requests.post(login_url, data=login_data)

                    #응답 상태 확인
                    if login_response.status_code == 200:
                        #응답 헤더에서 Authorization 토큰 추출
                        auth_token = login_response.headers.get("Authorization")
                        
                        if auth_token:
                            print("토큰 획득:", auth_token)

                            #GET 요청에 토큰 포함
                            fire_url = (
                                f"http://192.168.0.20:8080/msp/fire"
                                f"?temperature={tempVal}&humidity={humiVal}&fire=1&sparkStatus={flameVal}&weight={weightVal}&weightNow={percentageVal}&id=1")
                            headers = {"Authorization": auth_token}

                            print(fire_url)
                            
                            #GET 요청 보내기
                            fire_response = requests.get(fire_url, headers=headers)

                            #응답 처리
                            if fire_response.status_code == 200:
                                print("Fire 요청 성공:", fire_response.json())
                                return jsonify({
                                    "status": "success",
                                    "message": "Fire 요청 성공",
                                    "data": fire_response.json()
                                })
                                
                            else:
                                print(f"Fire 요청 실패: 상태 코드 {fire_response.status_code}, 응답 내용: {fire_response.text}")
                                return jsonify({
                                    "status": "error",
                                    "message": f"Fire 요청 실패: 상태 코드 {fire_response.status_code}",
                                    "details": fire_response.text
                                }), fire_response.status_code
                                
                        else:
                            print("Authorization 토큰이 응답 헤더에 없습니다.")
                            
                            return jsonify({
                                "status": "error",
                                "message": "Authorization 토큰이 응답 헤더에 없습니다."
                            }), 401
                            
                    else:
                        print(f"로그인 실패: 상태 코드 {login_response.status_code}, 응답 내용: {login_response.text}")
                        
                        return jsonify({
                            "status": "error",
                            "message": f"로그인 실패: 상태 코드 {login_response.status_code}",
                            "details": login_response.text
                        }), login_response.status_code 
                        
                except requests.exceptions.RequestException as e:
                    print("요청 중 오류 발생:", e)
                    
                    return jsonify({
                        "status": "error",
                        "message": "요청 중 오류 발생",
                        "details": str(e)
                    }), 500
                        
        except RuntimeError as error:
            print(error.args[0])
            
        finally:
            pass

#DB에 데이터 넣는 쓰레드 함수
def db():
    tempVal, humiVal, flameVal, weightVal, percentageVal= tempsen()
    
    print(tempVal)
    
    # 1. 로그인 요청
    login_url = "http://192.168.0.20:8080/login"
    login_data = {
        "userId": "user01",
        "userPw": 1234
    }

    try:
        #로그인 요청
        login_response = requests.post(login_url, data=login_data)

        #응답 상태 확인
        if login_response.status_code == 200:
            #응답 헤더에서 Authorization 토큰 추출
            auth_token = login_response.headers.get("Authorization")
            if auth_token:
                print("토큰 획득:", auth_token)

                #GET 요청에 토큰 포함
                fire_url = (
                    f"http://192.168.0.20:8080/msp/fire"
                    f"?temperature={tempVal}&humidity={humiVal}&fire=0&sparkStatus={flameVal}&weight={weightVal}&weightNow={percentageVal}&id=1")
                headers = {"Authorization": auth_token}

                print(fire_url)
                
                #GET 요청 보내기
                fire_response = requests.get(fire_url, headers=headers)

                #응답 처리
                if fire_response.status_code == 200:
                    print("Fire 요청 성공:", fire_response.json())
                    return jsonify({
                        "status": "success",
                        "message": "Fire 요청 성공",
                        "data": fire_response.json()
                    })
                else:
                    print(f"Fire 요청 실패: 상태 코드 {fire_response.status_code}, 응답 내용: {fire_response.text}")
                    return jsonify({
                        "status": "error",
                        "message": f"Fire 요청 실패: 상태 코드 {fire_response.status_code}",
                        "details": fire_response.text
                    }), fire_response.status_code
            else:
                print("Authorization 토큰이 응답 헤더에 없습니다.")
                return jsonify({
                    "status": "error",
                    "message": "Authorization 토큰이 응답 헤더에 없습니다."
                }), 401
        else:
            print(f"로그인 실패: 상태 코드 {login_response.status_code}, 응답 내용: {login_response.text}")
            return jsonify({
                "status": "error",
                "message": f"로그인 실패: 상태 코드 {login_response.status_code}",
                "details": login_response.text
            }), login_response.status_code
    except requests.exceptions.RequestException as e:
        print("요청 중 오류 발생:", e)
        return jsonify({
            "status": "error",
            "message": "요청 중 오류 발생",
            "details": str(e)
        }), 500
    
    
# thread_1 = threading.Thread(target=db)
thread_2 = threading.Thread(target=fire)

# thread_1.start()
thread_2.start()


if __name__ == '__main__':          
    app.run(debug=True, port=82, host='0.0.0.0',  threaded=True) 