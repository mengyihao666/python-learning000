# car_dual_line_follower.py
# 功能：使用比例控制实现更平滑的双车道线循迹

# ------------------------- 1, 2, 3 部分与之前完全相同 -------------------------
import RPi.GPIO as GPIO
import time
import cv2
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


def stop():
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)

# ------------------------- 4. 核心功能函数 (全新/重写) -------------------------


def get_lane_center(binary_img, scan_height_percent, scan_width_percent):
    """
    在一张二值化图像的指定高度，通过左右扫描找到车道中心。
    :param binary_img: 输入的二值化图像 (车道线为白色)
    :param scan_height_percent: 从上到下扫描线所在的高度百分比 (0-1)
    :param scan_width_percent: 从中心向两侧扫描的最大宽度百分比 (0-1)
    :return: (车道中心X坐标, 左边界点X坐标, 右边界点X坐标) 或 (None, None, None)
    """
    img_height, img_width = binary_img.shape
    scan_line_y = int(img_height * scan_height_percent)
    center_x = img_width // 2
    scan_width = int(img_width * scan_width_percent)

    # 从中心向左扫描
    left_point = 0
    for x in range(center_x, center_x - scan_width, -1):
        if binary_img[scan_line_y, x] == 255:  # 找到白色像素
            left_point = x
            break

    # 从中心向右扫描
    right_point = img_width
    for x in range(center_x, center_x + scan_width):
        if binary_img[scan_line_y, x] == 255:  # 找到白色像素
            right_point = x
            break

    # --- 决策逻辑 ---
    if left_point != 0 and right_point != img_width:
        # 状况1: 左右两边都找到了线 -> 正常
        lane_center = (left_point + right_point) // 2
        return lane_center, left_point, right_point
    elif left_point == 0 and right_point != img_width:
        # 状况2: 只找到右边的线 -> 可能是左转弯，根据右线估算中心
        # 假设标准车道宽度为图像宽度的70%
        lane_center = right_point - int(img_width * 0.35)
        return lane_center, None, right_point
    elif left_point != 0 and right_point == img_width:
        # 状况3: 只找到左边的线 -> 可能是右转弯，根据左线估算中心
        lane_center = left_point + int(img_width * 0.35)
        return lane_center, left_point, None
    else:
        # 状况4: 一条线都没找到
        return None, None, None


def dual_line_follower_mode(move_speed, Kp, binary_threshold):
    """进入双线循迹模式"""
    print("已进入双线循迹模式... 按下 'q' 键退出。")

    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    image_center = 320 // 2
    time.sleep(1)

    last_deviation = 0  # 记录上一次的有效偏移量

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        crop_img = frame[120:240, :]
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(
            blur, binary_threshold, 255, cv2.THRESH_BINARY_INV)

        # 获取车道中心
        lane_center, lp, rp = get_lane_center(
            thresh, scan_height_percent=0.5, scan_width_percent=0.45)

        deviation = 0
        if lane_center is not None:
            deviation = lane_center - image_center
            last_deviation = deviation  # 更新最后一次有效偏移
        else:
            # 如果一条线都没看到，使用上一次的偏移量来做“惯性”维持
            deviation = last_deviation

        # --- 运动控制 (与之前的P控制完全相同！) ---
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
        # 在裁剪后的图像上画出扫描线和检测点
        scan_y = int(crop_img.shape[0] * 0.5)
        cv2.line(crop_img, (0, scan_y), (320, scan_y), (255, 0, 0), 1)  # 蓝色扫描线
        if lp:
            cv2.circle(crop_img, (lp, scan_y), 5, (0, 255, 0), -1)   # 绿色左点
        if rp:
            cv2.circle(crop_img, (rp, scan_y), 5, (0, 255, 0), -1)   # 绿色右点
        if lane_center:
            cv2.circle(crop_img, (lane_center, scan_y),
                       5, (0, 0, 255), -1)  # 红色中心点

        cv2.imshow('Debug View', crop_img)
        # cv2.imshow('Threshold View', thresh)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 5. 主程序入口 -------------------------
try:
    # 校准参数与之前类似，但Kp可能需要重新微调
    MOVE_SPEED = 30
    Kp = 0.7  # 双线的Kp可能与单线不同
    BINARY_THRESHOLD = 80  # 保持为黑线白地校准好的值

    dual_line_follower_mode(MOVE_SPEED, Kp, BINARY_THRESHOLD)

except KeyboardInterrupt:
    print("\n程序已被用户中断")
finally:
    print("清理GPIO资源...")
    stop()
    GPIO.cleanup()
