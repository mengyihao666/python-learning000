# car_color_tracker.py
# 功能：实现小车基于OpenCV的颜色球体追踪

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO
import time
import cv2
import numpy as np  # OpenCV经常使用numpy进行数组操作

# ------------------------- 2. 定义硬件引脚与初始化 -------------------------
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

# ------------------------- 3. 小车基础动作函数 (非阻塞) -------------------------


def forward(speed):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)


def backward(speed):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)


def left(speed):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)


def right(speed):
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)


def stop():
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)

# ------------------------- 4. 颜色追踪主功能函数 -------------------------


def color_tracker_mode(color_lower, color_upper, move_speed, turn_speed, target_radius, tolerance):
    """
    进入颜色追踪模式
    :param color_lower: 目标颜色的HSV下限 (例如: [0, 100, 100])
    :param color_upper: 目标颜色的HSV上限 (例如: [10, 255, 255])
    :param move_speed: 前进/后退速度
    :param turn_speed: 转向速度
    :param target_radius: 理想的追踪距离对应的物体半径 (像素)
    :param tolerance: 半径误差容忍范围 (像素)
    """
    print("已进入颜色追踪模式... 按下 'q' 键退出。")

    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    center_line = 320 / 2

    time.sleep(1)

    while True:
        # 1. 捕获图像并转换到HSV色彩空间
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 2. 创建颜色掩码 (Mask)
        #    根据预设的HSV范围，在hsv图像中寻找颜色，生成一张只有黑白两色的图像(掩码)
        mask = cv2.inRange(hsv, color_lower, color_upper)

        #    (可选) 对掩码进行形态学操作，去除噪点，使物体区域更平滑
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # 3. 在掩码中查找轮廓
        contours, _ = cv2.findContours(
            mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        center = None  # 球体中心
        radius = 0    # 球体半径

        if len(contours) > 0:
            # 找到最大的轮廓，认为是我们的目标球体
            c = max(contours, key=cv2.contourArea)
            # 计算能包围此轮廓的最小圆形
            ((x, y), radius) = cv2.minEnclosingCircle(c)

            # 计算轮廓的中心
            M = cv2.moments(c)
            if M["m00"] > 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                # 只有当检测到的半径大于一个最小值时，才认为是有效目标
                if radius > 10:
                    # 在原始画面中画出识别到的圆形和中心点
                    cv2.circle(frame, (int(x), int(y)),
                               int(radius), (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)

        # 4. 运动决策
        if center is not None and radius > 10:
            cx = center[0]
            deviation = cx - center_line

            # -- 策略1：优先调整方向，再调整距离 ---
            if abs(deviation) > 15:  # 如果偏离中心线较远，优先转向
                if deviation > 0:
                    print(
                        f"Object on the right, turning right. Radius: {radius:.1f}")
                    right(turn_speed)
                else:
                    print(
                        f"Object on the left, turning left. Radius: {radius:.1f}")
                    left(turn_speed)
            else:  # 如果方向已经对准
                if radius > target_radius + tolerance:
                    # 物体太大 -> 离得太近 -> 后退
                    print(f"Too close, moving backward. Radius: {radius:.1f}")
                    backward(move_speed)
                elif radius < target_radius - tolerance:
                    # 物体太小 -> 离得太远 -> 前进
                    print(f"Too far, moving forward. Radius: {radius:.1f}")
                    forward(move_speed)
                else:
                    # 距离和方向都完美 -> 停止
                    print(f"Target locked! Radius: {radius:.1f}")
                    stop()
        else:
            # 没有找到目标 -> 停止
            print("Target not found.")
            stop()

        # 显示调试窗口
        cv2.imshow("Tracking View", frame)
        # cv2.imshow("Mask View", mask) # 取消注释可查看颜色掩码效果

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 5. 主程序入口 -------------------------
try:
    # ============ 参数校准区 ============
    # 【请在这里通过实验，修改为你自己的小车最合适的值】

    # 任务：追踪一个红色的物体 (例如：一个红色的瓶盖)
    # 红色在HSV空间中比较特殊，它可能分布在0附近和179附近
    # 我们先定义一个常用的红色范围
    # H: 0-10 和 160-179, S: 100-255, V: 100-255
    # !! 这里我们只用0-10的范围做示例，如果效果不好，需要使用两个范围并合并掩码 !!
    COLOR_LOWER = np.array([0, 120, 120])  # HSV下限
    COLOR_UPPER = np.array([10, 255, 255])  # HSV上限

    MOVE_SPEED = 35         # 前进/后退速度
    TURN_SPEED = 50         # 转向速度
    TARGET_RADIUS = 45      # 目标追踪距离对应的物体半径（像素）
    RADIUS_TOLERANCE = 5    # 半径容忍误差（像素）
    # ==================================

    color_tracker_mode(COLOR_LOWER, COLOR_UPPER, MOVE_SPEED,
                       TURN_SPEED, TARGET_RADIUS, RADIUS_TOLERANCE)

except KeyboardInterrupt:
    print("\n程序已被用户中断")
finally:
    print("清理GPIO资源...")
    stop()
    GPIO.cleanup()
