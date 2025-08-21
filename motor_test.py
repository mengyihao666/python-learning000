# motor_test.py
import RPi.GPIO as GPIO
import time

# 引脚定义
AIN1, AIN2 = 22, 27   # 左电机方向
BIN1, BIN2 = 25, 24   # 右电机方向

# 初始化
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [AIN1, AIN2, BIN1, BIN2]:
    GPIO.setup(pin, GPIO.OUT)


def left_forward(t):
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    time.sleep(t)


def left_backward(t):
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    time.sleep(t)


def right_forward(t):
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    time.sleep(t)


def right_backward(t):
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    time.sleep(t)


try:
    print("左轮正转 2 秒")
    left_forward(2)
    print("左轮反转 2 秒")
    left_backward(2)

    print("右轮正转 2 秒")
    right_forward(2)
    print("右轮反转 2 秒")
    right_backward(2)

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
