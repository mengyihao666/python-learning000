# car_autonomous_smoothed.py
# 功能：通过“滑动平均滤波器”平滑运动趋势，实现更稳健的自主决策循迹。

# ------------------------- 1 & 2. 硬件初始化 (与之前完全相同) -------------------------
import RPi.GPIO as GPIO
import time
import cv2
import Adafruit_PCA9685
import numpy as np
from collections import deque  # --- 新增：导入双端队列，用于实现高效的滑动窗口 ---

# (此处省略所有硬件初始化代码，与上一版完全一致)
# ...
AIN1, AIN2, PWMA, BIN1, BIN2, PWMB, L_Motor, R_Motor, pwm, tilt_angle = (
    None,) * 10


def setup_hardware():
    global AIN1, AIN2, PWMA, BIN1, BIN2, PWMB, L_Motor, R_Motor, pwm, tilt_angle
    AIN1, AIN2, PWMA = 22, 27, 18
    BIN1, BIN2, PWMB = 25, 24, 23
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [AIN1, AIN2, BIN1, BIN2, PWMA, PWMB]:
        GPIO.setup(pin, GPIO.OUT)
    L_Motor = GPIO.PWM(PWMA, 100)
    R_Motor = GPIO.PWM(PWMB, 100)
    L_Motor.start(0)
    R_Motor.start(0)
    try:
        pwm = Adafruit_PCA9685.PCA9685()
        pwm.set_pwm_freq(50)
        global SERVO_TILT_CHANNEL
        SERVO_TILT_CHANNEL = 4
        tilt_angle = 90
        set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)
        print("舵机驱动板初始化成功！")
    except:
        pwm = None


setup_hardware()


def set_servo_angle(channel, angle):
    pulse = 4096 * ((angle * 11) + 500) / 20000 + 0.5
    pwm.set_pwm(channel, 0, int(pulse))


def stop(): L_Motor.ChangeDutyCycle(0); R_Motor.ChangeDutyCycle(0)
# --------------------------------------------------------------------------


# --- 定义状态常量 (与之前相同) ---
TURN_RIGHT = "RIGHT_TURN"
TURN_LEFT = "LEFT_TURN"
STRAIGHT = "STRAIGHT"

# ------------------------- 3. 主功能函数 (核心逻辑升级) -------------------------


def autonomous_follower_mode():
    global tilt_angle

    # --- 初始化 ---
    current_turn_state = STRAIGHT
    last_cx = 160

    # --- ★★★ 新增：初始化滑动平均滤波器 ★★★ ---
    # 定义滑动窗口的大小 N (存储最近5帧的历史)
    DELTA_WINDOW_SIZE = 5
    # 使用双端队列 (deque) 创建一个固定长度的“记忆缓冲区”
    delta_history = deque(maxlen=DELTA_WINDOW_SIZE)
    # -----------------------------------------------

    print("已进入带平滑决策的循迹模式...")
    # ... (摄像头和Numpy核的初始化)
    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    time.sleep(1)
    dilation_kernel = np.ones((3, 3), np.uint8)
    last_deviation = 0

    while True:
        # ... (图像处理部分与之前完全相同)
        ret, frame = cap.read()
        if not ret:
            break
        crop_img = frame[120:240, :]
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 80, 255, cv2.THRESH_BINARY_INV)
        thresh_processed = cv2.dilate(thresh, dilation_kernel, iterations=2)
        _, contours, _ = cv2.findContours(
            thresh_processed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        current_cx = None
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] != 0:
                current_cx = int(M["m10"] / M["m00"])

        # --- ★★★ 核心决策逻辑：基于平滑后的趋势 ★★★ ---
        if current_cx is not None:
            delta_cx = current_cx - last_cx
            # 1. 更新历史记录
            delta_history.append(delta_cx)
            last_cx = current_cx

            # 2. 计算平均趋势 (只有当缓冲区填满时才开始决策，避免初期误判)
            if len(delta_history) == DELTA_WINDOW_SIZE:
                avg_delta_cx = sum(delta_history) / DELTA_WINDOW_SIZE

                # 3. 基于平滑后的平均值来更新状态
                if avg_delta_cx > 2.0:  # 阈值比之前稍小，因为平均值会更平滑
                    current_turn_state = TURN_RIGHT
                elif avg_delta_cx < -2.0:
                    current_turn_state = TURN_LEFT
                else:
                    current_turn_state = STRAIGHT
        # -----------------------------------------------

        # --- (动态参数加载与运动控制部分，与之前完全相同) ---
        if current_turn_state == TURN_RIGHT:
            move_speed = 50
            Kp = 0.7
            target_position = 240
        elif current_turn_state == TURN_LEFT:
            move_speed = 40
            Kp = 0.5
            target_position = 100
        else:  # STRAIGHT
            move_speed = 55
            Kp = 0.6
            target_position = 180

        deviation = last_deviation
        if current_cx is not None:
            deviation = current_cx - target_position
            last_deviation = deviation

        correction = Kp * deviation
        left_speed = move_speed + correction
        right_speed = move_speed - correction
        left_speed = max(min(left_speed, 100), 0)
        right_speed = max(min(right_speed, 100), 0)
        L_Motor.ChangeDutyCycle(left_speed)
        R_Motor.ChangeDutyCycle(right_speed)
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
        GPIO.output(BIN1, GPIO.HIGH)
        GPIO.output(BIN2, GPIO.LOW)

        # --- (可视化与键盘处理部分)
        cv2.putText(crop_img, f"STATE: {current_turn_state}",
                    (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if len(delta_history) > 0:
            cv2.putText(crop_img, f"AVG_D: {sum(delta_history)/len(delta_history):.1f}",
                        (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow('Autonomous Smoothed Follower', crop_img)

        key = cv2.waitKey(1) & 0xFF
        # (键盘处理部分与之前相同)
        # ...

    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 4. 主程序入口 -------------------------
try:
    autonomous_follower_mode()
except KeyboardInterrupt:
    pass
finally:
    print("清理GPIO资源...")
    stop()
    if pwm:
        set_servo_angle(SERVO_TILT_CHANNEL, 90)
        time.sleep(0.5)
    GPIO.cleanup()
