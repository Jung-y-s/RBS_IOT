import time
import RPi.GPIO as GPIO

# GPIO 핀 설정
GPIO.setmode(GPIO.BCM)
StepPins = [12, 16, 20, 21]

# 모든 핀을 출력으로 설정
for pin in StepPins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

# 스텝모터 제어 시퀀스
Seq = [
    [0, 0, 0, 1],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [1, 0, 0, 0]
]

# 모터의 스텝 각도 (0.08789도)
StepAngle = 0.08789  # 스텝모터가 한 스텝마다 회전하는 각도
StepCount = 4096  # 전체 한 바퀴 회전 시 필요한 스텝 수 (360도 / 0.08789도)
StepCounter = 0  # 현재 스텝 (전역 변수로 사용)

def rotate_motor(degrees, direction=1):
    """
    모터를 특정 각도만큼 회전시킵니다.
    degrees: 회전할 각도 (양수는 시계방향, 음수는 반시계방향)
    direction: 회전 방향 (1은 시계방향, -1은 반시계방향)
    """
    global StepCounter  # 전역 변수 StepCounter 사용

    steps_to_move = int(degrees / StepAngle)  # 회전할 스텝 수 계산
    step_direction = direction  # 회전 방향

    # 원하는 각도만큼 회전
    for _ in range(abs(steps_to_move)):
        for pin in range(4):
            xpin = StepPins[pin]
            if Seq[StepCounter][pin] != 0:
                GPIO.output(xpin, True)
            else:
                GPIO.output(xpin, False)

        # StepCounter 값을 0부터 3 사이로 순환 (반시계방향도 지원)
        StepCounter += step_direction  # 스텝 카운터 증가 또는 감소
        if StepCounter == len(Seq):  # StepCounter가 Seq 길이를 초과할 경우
            StepCounter = 0
        elif StepCounter < 0:  # StepCounter가 0보다 작으면 마지막 인덱스로 돌아가도록
            StepCounter = len(Seq) - 1

        time.sleep(0.01)  # 속도 조절 (필요에 따라 변경)

try:
    # 예시: 90도 회전 후 다시 90도 회전
    print("Rotating 90 degrees clockwise.")
    rotate_motor(90, direction=1)  # 시계방향 90도 회전
    time.sleep(1)

    print("Rotating 90 degrees counterclockwise.")
    rotate_motor(90, direction=-1)  # 반시계방향 90도 회전
    time.sleep(1)

except KeyboardInterrupt:
    print("Program interrupted.")
finally:
    GPIO.cleanup()  # GPIO 리소스 정리
