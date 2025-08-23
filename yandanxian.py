# car_single_line_edgerunner.py
# 功能：使用比例控制，让小车沿着单条线的边缘平滑行驶。
# 这是一个更稳定、更鲁棒的方案，用于替代复杂的双线循迹。

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO
import time
import cv2
import Adafruit_PCA9685
import numpy as np

# ------------------------- 2. 硬件引脚定义与初始化 -------------------------
# --- 电机引脚 ---
AIN1, AIN2, PWMA = 22, 27, 18
BIN1, BIN2, PWMB = 25, 24, 23

# --- GPIO 初始化 ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [AIN1, AIN2, BIN1, BIN2, PWMA, PWMB]:
    GPIO.setup(pin, GPIO.OUT)
L_Motor = GPIO.PWM(PWMA, 100)
R_Motor = GPIO.PWM(PWMB, 100)
L_Motor.start(0)
R_Motor.start(0)

# --- 舵机驱动板与舵机初始化 ---
try:
    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(50)
    SERVO_TILT_CHANNEL = 4

    def set_servo_angle(channel, angle):
        pulse = 4096 * ((angle * 11) + 500) / 20000 + 0.5
        pwm.set_pwm(channel, 0, int(pulse))

    tilt_angle = 90
    set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)
    print("舵机驱动板初始化成功！")
except Exception as e:
    print(f"警告：无法初始化舵机驱动板！将以无舵机控制模式运行。错误: {e}")
    pwm = None


def stop():
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)

# ------------------------- 3. 主功能函数 (核心逻辑) -------------------------


def single_line_edge_mode(move_speed, Kp, binary_threshold, target_position):
    """
    进入贴边单线循迹模式
    :param move_speed: 基础前进速度
    :param Kp: 比例系数
    :param binary_threshold: 二值化阈值
    :param target_position: 我们希望线条稳定在图像的哪个X坐标位置【核心参数】
    """
    global tilt_angle
    print("已进入贴边单线循迹模式...")
    print("--- 操作指南 ---")
    print(" W: 摄像头向上 | S: 摄像头向下 | Q: 退出程序")

    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    time.sleep(1)

    # 为形态学膨胀创建“核”
    dilation_kernel = np.ones((3, 3), np.uint8)

    last_deviation = 0  # 用于在丢失目标时维持状态

    # 主循环 (基于您优化后的无stop()版本)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 图像处理 (使用裁剪，因为我们只需要看清一条线)
        crop_img = frame[120:240, :]
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(
            blur, binary_threshold, 255, cv2.THRESH_BINARY_INV)
        thresh_processed = cv2.dilate(thresh, dilation_kernel, iterations=2)

        # 运动决策 (基于稳定的单线逻辑)
        # 兼容OpenCV 3.x 版本
        _, contours, _ = cv2.findContours(
            thresh_processed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        deviation = last_deviation  # 默认使用上一次的有效偏移

        if len(contours) > 0:
            # 找到最大轮廓
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])

                # --- ★★★ 核心逻辑：计算偏离“目标线”的距离 ★★★ ---
                # 偏离量 = 线的当前位置 - 我们期望它在的位置 (target_position)
                deviation = cx - target_position
                last_deviation = deviation  # 更新记忆

        # --- (后续P比例控制逻辑完全不变) ---
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

        # --- 可视化调试 (在裁剪图上画出红色的目标线) ---
        cv2.line(crop_img, (target_position, 0),
                 (target_position, 120), (0, 0, 255), 2)
        # 画出检测到的线条中心点
        if len(contours) > 0 and M["m00"] != 0:
            cv2.circle(crop_img, (cx, 60), 5, (0, 255, 0), -1)  # 绿色检测点
        cv2.imshow('Edge Runner Debug View', crop_img)
        cv2.imshow('Processed Threshold View', thresh_processed)

        # --- (键盘处理部分) ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif pwm and key == ord('w'):
            tilt_angle = max(0, tilt_angle - 5)
            set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)
            print(f"摄像头向上 -> 俯仰角度: {tilt_angle}")
        elif pwm and key == ord('s'):
            tilt_angle = min(180, tilt_angle + 5)
            set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)
            print(f"摄像头向下 -> 俯仰角度: {tilt_angle}")

    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 4. 主程序入口 -------------------------
try:
    # ============ 参数校准区 ============
    MOVE_SPEED = 50
    Kp = 0.5  # 可能需要为新策略重新微调Kp，建议从0.4左右开始
    BINARY_THRESHOLD = 80  # 保持为黑线白地校准好的值

    # --- ★★★ 核心校准参数：目标线位置 ★★★ ---
    # 定义我们希望线稳定在哪个X坐标上。图像宽度320，裁剪后宽度不变。
    #
    # 如果您调整摄像头看到【右侧】的线，并想贴着它内侧(左侧)跑，
    # 请设置一个大于图像中心(160)的值，比如 240。
    #
    # 如果您调整摄像头看到【左侧】的线，并想贴着它内侧(右侧)跑，
    # 请设置一个小于图像中心(160)的值，比如 80。
    TARGET_POSITION = 240
    # ==================================

    single_line_edge_mode(MOVE_SPEED, Kp, BINARY_THRESHOLD, TARGET_POSITION)

except KeyboardInterrupt:
    print("\n程序已被用户中断")
    pass
finally:
    print("清理GPIO资源...")
    stop()
    if pwm:
        set_servo_angle(SERVO_TILT_CHANNEL, 90)
        time.sleep(0.5)
    GPIO.cleanup()
