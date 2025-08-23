# car_dual_line_follower_calibrated.py
# 功能：实现双线循迹，并加入中心偏移校准参数，以修正摄像头物理安装偏差。

# ------------------------- 1, 2, 3 部分 (硬件初始化) (与之前相同) -------------------------
import RPi.GPIO as GPIO
import time
import cv2
import Adafruit_PCA_9685
import numpy as np

# --- 引脚定义 ---
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


# 新增center_offset参数
def dual_line_follower_mode(move_speed, Kp, binary_threshold, center_offset):
    """进入带中心偏移校准的双线循迹模式"""
    global tilt_angle

    print("已进入双线循迹模式...")
    print("--- 操作指南 ---")
    print(" W: 摄像头向上 | S: 摄像头向下 | Q: 退出程序")

    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    image_center = 320 // 2
    time.sleep(1)
    last_deviation = 0

    dilation_kernel = np.ones((3, 3), np.uint8)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(
            blur, binary_threshold, 255, cv2.THRESH_BINARY_INV)
        thresh_processed = cv2.dilate(thresh, dilation_kernel, iterations=2)

        lane_center, lp, rp = get_lane_center(
            thresh_processed, scan_height_percent=0.8, scan_width_percent=0.5)

        deviation = last_deviation
        if lane_center is not None:
            # --- ★★★ 核心修改：修正deviation的计算公式 ★★★ ---
            # 真正的偏离 = 检测到的中心 - (理论中心 + 补偿值)
            # 这相当于我们把巡航的目标点从160，动态调整到了 (160 + center_offset)
            ideal_center = image_center + center_offset
            deviation = lane_center - ideal_center
            last_deviation = deviation

        # --- (P比例控制逻辑完全不需要修改，因为它只关心最终的deviation值) ---
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

        # --- (可视化调试与键盘处理部分与之前相同) ---
        scan_y = int(frame.shape[0] * 0.8)
        cv2.line(frame, (0, scan_y), (320, scan_y), (255, 0, 0), 1)
        if lp:
            cv2.circle(frame, (lp, scan_y), 5, (0, 255, 0), -1)
        if rp:
            cv2.circle(frame, (rp, scan_y), 5, (0, 255, 0), -1)
        if lane_center:
            cv2.circle(frame, (lane_center, scan_y), 5, (0, 0, 255), -1)
        cv2.imshow('Debug View (Full Frame)', frame)
        cv2.imshow('Processed Threshold View', thresh_processed)

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


# ------------------------- 5. 主程序入口 -------------------------
try:
    # ============ 参数校准区 ============
    MOVE_SPEED = 30
    Kp = 0.7
    BINARY_THRESHOLD = 80

    # --- ★★★ 新增：中心偏移校准参数 ★★★ ---
    # 这个值用来补偿摄像头物理安装的偏差。
    # - 如果小车总往【左】偏（压左线），说明deviation持续为负，我们需要一个【正数】来补偿，把它拉回0。
    # - 如果小车总往【右】偏（压右线），说明deviation持续为正，我们需要一个【负数】来补偿。
    # 【请从0开始，通过实验慢慢调整这个值，比如 5, 10, 15, -5, -10...】
    CENTER_OFFSET = 0  # 初始值为0，请根据您的实际情况进行校准
    # ==================================

    # 将新参数传递给主函数
    dual_line_follower_mode(MOVE_SPEED, Kp, BINARY_THRESHOLD, CENTER_OFFSET)

except KeyboardInterrupt:
    print("\n程序已被用户中断")
finally:
    print("清理GPIO资源...")
    stop()
    if pwm:
        set_servo_angle(SERVO_TILT_CHANNEL, 90)
        time.sleep(0.5)
    GPIO.cleanup()
