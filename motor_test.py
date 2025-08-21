# car_basic_motion.py
# 功能：实现小车的基本动作（前进、后退、左转、右转、停止）

import RPi.GPIO as GPIO
import time

# ---------------- 引脚定义 ----------------
# 左电机控制
AIN1, AIN2, PWMA = 22, 27, 18
# 右电机控制
BIN1, BIN2, PWMB = 25, 24, 23

# ---------------- GPIO初始化 ----------------
GPIO.setmode(GPIO.BCM)       # 使用BCM引脚编号
GPIO.setwarnings(False)      # 忽略重复警告

# 设置电机控制引脚为输出
for pin in [AIN1, AIN2, BIN1, BIN2, PWMA, PWMB]:
    GPIO.setup(pin, GPIO.OUT)

# 初始化PWM（频率100Hz）
L_Motor = GPIO.PWM(PWMA, 100)
R_Motor = GPIO.PWM(PWMB, 100)
L_Motor.start(0)  # 初始占空比0（不转）
R_Motor.start(0)

# ---------------- 小车动作函数 ----------------


def forward(speed, t):
    """小车前进"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)

    time.sleep(t)


def backward(speed, t):
    """小车后退"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)

    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)

    time.sleep(t)


def left(speed, t):
    """小车左转（原地左转）"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)

    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)

    time.sleep(t)


def right(speed, t):
    """小车右转（原地右转）"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)

    time.sleep(t)


def stop(t=0):
    """小车停止"""
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)
    time.sleep(t)


# ---------------- 主程序 ----------------
try:
    print("前进 2 秒")
    forward(50, 2)   # 50%速度前进2秒

    print("停止 1 秒")
    stop(1)

    print("左转 1 秒")
    left(60, 1)

    print("右转 1 秒")
    right(60, 1)

    print("后退 2 秒")
    backward(50, 2)

    print("停止")
    stop()

# 按 Ctrl+C 可以安全退出
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
