# car_avoidance.py
# 功能：实现小车红外避障运动

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO
import time

# ------------------------- 2. 定义硬件引脚 -------------------------
# --- 左侧电机引脚定义 ---
AIN1, AIN2, PWMA = 22, 27, 18
# --- 右侧电机引脚定义 ---
BIN1, BIN2, PWMB = 25, 24, 23
# --- 红外传感器引脚定义 (新增) ---
IR_LEFT = 17   # 左侧红外传感器连接到 GPIO 17
IR_RIGHT = 21  # 右侧红外传感器连接到 GPIO 21

# ------------------------- 3. GPIO初始化 -------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# --- 电机引脚初始化为输出 ---
for pin in [AIN1, AIN2, BIN1, BIN2, PWMA, PWMB]:
    GPIO.setup(pin, GPIO.OUT)

# --- 红外传感器引脚初始化为输入 (新增) ---
# "输入"模式意味着树莓派要从这些引脚读取信号(高/低电平)。
# PUD_UP表示启用内部上拉电阻，可以使信号更稳定，防止误判。
GPIO.setup(IR_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IR_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ------------------------- 4. PWM初始化 -------------------------
L_Motor = GPIO.PWM(PWMA, 100)
R_Motor = GPIO.PWM(PWMB, 100)
L_Motor.start(0)
R_Motor.start(0)

# ------------------------- 5. 小车基础动作函数 (与之前相同) -------------------------


def forward(speed, t=0):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    if t != 0:
        time.sleep(t)


def backward(speed, t):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    time.sleep(t)


def left(speed, t):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    time.sleep(t)


def right(speed, t):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    time.sleep(t)


def stop(t=0):
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)
    time.sleep(t)

# ------------------------- 6. 红外避障功能函数 (核心新增功能) -------------------------


def obstacle_avoidance_mode(speed, turn_speed, turn_time):
    """
    函数功能：进入红外避障模式
    :param speed: 正常前进的速度
    :param turn_speed: 转向时的速度
    :param turn_time: 转向的持续时间
    """
    print("已进入红外避障模式... 按下 Ctrl+C 退出。")

    # 这是一个无限循环，程序会一直在这个模式下运行，直到被中断
    while True:
        # 读取左右两个红外传感器的值
        # 注意：有障碍物时，值为 0 (False)；无障碍物时，值为 1 (True)
        left_val = GPIO.input(IR_LEFT)
        right_val = GPIO.input(IR_RIGHT)

        # --- 判断逻辑 ---
        if left_val == True and right_val == True:
            # 状态1：两边都无障碍物，前进
            print("路径清晰，前进...")
            forward(speed)

        elif left_val == True and right_val == False:
            # 状态2：右边有障碍物，向左转
            print("右侧检测到障碍物，向左转！")
            stop(0.1)  # 短暂停顿
            left(turn_speed, turn_time)

        elif left_val == False and right_val == True:
            # 状态3：左边有障碍物，向右转
            print("左侧检测到障碍物，向右转！")
            stop(0.1)
            right(turn_speed, turn_time)

        elif left_val == False and right_val == False:
            # 状态4：两边都有障碍物（可能正前方是墙），先退后，再转向
            print("正前方检测到障碍物，后退并转向！")
            stop(0.1)
            backward(speed, 0.5)  # 先后退0.5秒
            right(turn_speed, turn_time)  # 然后右转

        time.sleep(0.02)  # 短暂延时，降低CPU占用率


# ------------------------- 7. 主程序入口 -------------------------
try:
    # 设置避障模式的参数
    MOVE_SPEED = 50       # 正常前进速度
    TURN_SPEED = 60       # 转向时的速度
    TURN_DURATION = 0.35  # 每次转向的持续时间(秒)，可根据实际效果调整

    # 直接调用避障模式函数
    obstacle_avoidance_mode(MOVE_SPEED, TURN_SPEED, TURN_DURATION)


except KeyboardInterrupt:
    print("\n程序已被用户中断")
    pass

finally:
    print("清理GPIO资源...")
    GPIO.cleanup()
