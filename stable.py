# car_dual_line_follower_final.py
# 功能：实现双线循迹，实时调节摄像头角度，并通过形态学膨胀优化细线检测。

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO
import time
import cv2
import Adafruit_PCA9685
import numpy as np  # --- 新增：导入Numpy库，用于创建膨胀核 ---

# ------------------------- 2. 硬件引脚定义与初始化 (与之前相同) -------------------------
# --- 电机引脚 ---
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

# --- 舵机驱动板与舵机初始化 (与之前相同) ---
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

# ------------------------- 4. 核心功能函数 (与之前相同) -------------------------


def get_lane_center(binary_img, scan_height_percent, scan_width_percent):
    """在一张二值化图像的指定高度，通过左右扫描找到车道中心。"""
    # (此函数无需修改)
    img_height, img_width = binary_img.shape
    scan_line_y = int(img_height * scan_height_percent)
    center_x = img_width // 2
    scan_width = int(img_width * scan_width_percent)
    left_point = 0
    for x in range(center_x, center_x - scan_width, -1):
        if binary_img[scan_line_y, x] == 255:
            left_point = x
            break
    right_point = img_width
    for x in range(center_x, center_x + scan_width):
        if binary_img[scan_line_y, x] == 255:
            right_point = x
            break
    if left_point != 0 and right_point != img_width:
        lane_center = (left_point + right_point) // 2
        return lane_center, left_point, right_point
    elif left_point == 0 and right_point != img_width:
        lane_center = right_point - int(img_width * 0.35)
        return lane_center, None, right_point
    elif left_point != 0 and right_point == img_width:
        lane_center = left_point + int(img_width * 0.35)
        return lane_center, left_point, None
    else:
        return None, None, None


def dual_line_follower_mode(move_speed, Kp, binary_threshold):
    """进入带膨胀优化的双线循迹模式"""
    global tilt_angle

    print("已进入双线循迹模式...")
    print("--- 操作指南 ---")
    print(" W: 摄像头向上 | S: 摄像头向下 | Q: 退出程序")

    cap = cv2.VideoCapture(0)
    # --- ★★★ 您取消了裁剪，所以我们不再裁剪 ★★★ ---
    # 我们直接使用完整的320x240分辨率进行处理
    cap.set(3, 320)
    cap.set(4, 240)
    image_center = 320 // 2
    time.sleep(1)
    last_deviation = 0

    # --- 新增：为形态学膨胀创建一个“核” ---
    # (3,3)表示膨胀操作的范围是3x3的像素矩阵
    dilation_kernel = np.ones((3, 3), np.uint8)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- ★ 图像处理流程修改 ★ ---
        # 1. 灰度化 (直接在完整帧上操作)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2. 高斯模糊
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. 二值化
        _, thresh = cv2.threshold(
            blur, binary_threshold, 255, cv2.THRESH_BINARY_INV)

        # 4. ★★★ 核心优化：形态学膨胀 ★★★
        # 对二值化图像进行膨胀，让细线“长胖”，并连接断点
        # iterations=2 表示执行两次膨胀操作，您可以根据实际效果调整这个数字
        thresh_processed = cv2.dilate(thresh, dilation_kernel, iterations=2)
        # --- End of 修改 ---

        # 5. 获取车道中心 (注意：输入的是膨胀处理后的图像)
        # 因为不再裁剪，我们需要在一个更靠下的位置扫描，比如80%高度处
        lane_center, lp, rp = get_lane_center(
            thresh_processed, scan_height_percent=0.8, scan_width_percent=0.45)

        # --- (运动控制部分与之前完全相同) ---
        deviation = last_deviation  # 默认使用上一次的偏移
        if lane_center is not None:
            deviation = lane_center - image_center
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

        # --- 可视化调试 ---
        # 我们在原始的彩色帧上画出调试信息，而不是在裁剪后的图上
        scan_y = int(frame.shape[0] * 0.8)  # 确保扫描线画在正确的高度
        cv2.line(frame, (0, scan_y), (320, scan_y), (255, 0, 0), 1)
        if lp:
            cv2.circle(frame, (lp, scan_y), 5, (0, 255, 0), -1)
        if rp:
            cv2.circle(frame, (rp, scan_y), 5, (0, 255, 0), -1)
        if lane_center:
            cv2.circle(frame, (lane_center, scan_y), 5, (0, 0, 255), -1)

        cv2.imshow('Debug View (Full Frame)', frame)
        # 强烈建议打开这个窗口来观察膨胀效果
        cv2.imshow('Processed Threshold View', thresh_processed)

        # --- (键盘处理与之前相同) ---
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

    # --- (退出清理部分与之前相同) ---
    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 5. 主程序入口 -------------------------
try:
    MOVE_SPEED = 30
    Kp = 0.7
    BINARY_THRESHOLD = 80

    dual_line_follower_mode(MOVE_SPEED, Kp, BINARY_THRESHOLD)

except KeyboardInterrupt:
    print("\n程序已被用户中断")
finally:
    print("清理GPIO资源...")
    stop()
    if pwm:
        set_servo_angle(SERVO_TILT_CHANNEL, 90)
        time.sleep(0.5)
    GPIO.cleanup()
