import RPi.GPIO as GPIO
import time

# 서보모터를 연결할 GPIO 핀 설정
servo_pin = 13  # 예시로 17번 핀을 사용합니다. 실제 연결한 핀 번호로 변경하세요.

# GPIO 설정
GPIO.setmode(GPIO.BCM)  # BCM 핀 번호 방식을 사용
GPIO.setup(servo_pin, GPIO.OUT)

# PWM 객체 생성, 50Hz (서보모터의 일반적인 주파수)
pwm = GPIO.PWM(servo_pin, 50)

# PWM 시작 (초기 듀티 사이클 0)
pwm.start(0)

def move_servo(angle):
    # 각도를 PWM 듀티 사이클로 변환 (서보모터가 0도에서 180도까지 회전한다고 가정)
    duty = angle / 18 + 2  # 듀티 사이클 계산
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)  # 서보모터가 위치를 변경할 수 있도록 대기
    pwm.ChangeDutyCycle(0)  # PWM 신호 종료

try:
    while True:
        # 시계방향 (0도 -> 180도)
        print("시계방향으로 회전")
        move_servo(0)  # 0도
        time.sleep(3)  # 3초 대기
        
        # 반시계방향 (180도 -> 0도)
        print("반시계방향으로 회전")
        move_servo(180)  # 180도
        time.sleep(3)  # 3초 대기

except KeyboardInterrupt:
    print("프로그램이 종료되었습니다.")
finally:
    pwm.stop()  # PWM 중지
    GPIO.cleanup()  # GPIO 정리