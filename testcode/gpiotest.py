import pigpio
import time

# 서보모터를 연결할 GPIO 핀 설정
servo_pin = 13  # 예시로 17번 핀을 사용합니다. 실제 연결한 핀 번호로 변경하세요.

# pigpio 라이브러리 초기화
pi = pigpio.pi()

if not pi.connected:
    print("pigpio 데몬이 실행되지 않고 있습니다. 'sudo pigpiod' 명령어로 실행해주세요.")
    exit()

# 서보모터의 회전 방향 및 속도 설정
def move_servo(pulse_width):
    # 펄스 폭을 설정하여 서보모터 이동
    pi.set_servo_pulsewidth(servo_pin, pulse_width)
    print(f"펄스 폭: {pulse_width}us")
    time.sleep(1)  # 서보모터가 이동할 시간을 줍니다.

try:
    # 50Hz 주파수 설정
    pi.set_PWM_frequency(servo_pin, 50)  # 50Hz로 설정

    while True:
        # 시계방향 회전 (펄스 폭: 1ms)
        print("시계방향으로 회전")
        move_servo(1500)  # 1ms (1000us)
        time.sleep(3)  # 3초 대기

        # 정지 상태 (펄스 폭: 1.5ms)
        print("정지")
        move_servo(1800)  # 1.5ms (1500us)
        time.sleep(3)  # 3초 대기

        # 반시계방향 회전 (펄스 폭: 2ms)
        print("반시계방향으로 회전")
        move_servo(1500)  # 2ms (2000us)
        time.sleep(3)  # 3초 대기

except KeyboardInterrupt:
    print("프로그램이 종료되었습니다.")
finally:
    pi.stop()  # pigpio 종료
