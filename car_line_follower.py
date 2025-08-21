# car_line_follower.py
# 功能：实现小车基于OpenCV的视觉循迹运动

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO
import time
import cv2  # 导入OpenCV库

# ------------------------- 2. 定义硬件引脚 -------------------------
# --- 电机引脚定义 ---
AIN1, AIN2, PWMA = 22, 27, 18
BIN1, BIN2, PWMB = 25, 24, 23

# ------------------------- 3. GPIO与PWM初始化 -------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [AIN1, AIN2, BIN1, BIN2, PWMA, PWMB]:
    GPIO.setup(pin, GPIO.OUT)

L_Motor = GPIO.PWM(PWMA, 100)
R_Motor = GPIO.PWM(PWMB, 100)
L_Motor.start(0)
R_Motor.start(0)

# ------------------------- 4. 小车基础动作函数 -------------------------
# 注意：我们将forward函数修改为非阻塞式，即不包含time.sleep()
# 因为我们需要在主循环中持续判断，而不是让小车"盲走"一段时间


def forward(speed):
    """小车前进（非阻塞）"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)


def left(speed):
    """小车左转（非阻塞）"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)


def right(speed):
    """小车右转（非阻塞）"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)


def stop():
    """小车停止"""
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)

# ------------------------- 5. 循迹主功能函数 -------------------------


def line_follower_mode(move_speed, turn_speed, deviation_threshold, binary_threshold):
    """
    进入视觉循迹模式
    :param move_speed: 正常循迹速度
    :param turn_speed: 转向调整速度
    :param deviation_threshold: 路径中心偏移阈值，小于此值认为在正中
    :param binary_threshold: 图像二值化的阈值【需要校准】
    """
    print("已进入视觉循迹模式... 按下 'q' 键退出。")

    # --- 摄像头初始化 ---
    # 打开默认摄像头 (通常是 0)
    cap = cv2.VideoCapture(0)
    # 设置较低的分辨率以提高处理速度
    # 宽度设置为320, 高度设置为240
    cap.set(3, 320)
    cap.set(4, 240)

    # 图像中心线
    center_line = 320 / 2  # 图像宽度的一半

    time.sleep(1)  # 等待摄像头稳定

    # --- 主循环：不断处理视频帧 ---
    while True:
        # 1. 捕获图像
        ret, frame = cap.read()
        if not ret:
            print("摄像头图像捕获失败！")
            break

        # 2. 图像处理
        # -- 裁剪图像: 我们只关心靠近车头的地面部分
        #    这里我们取图像高度的后一半 frame[120:240, :]
        crop_img = frame[120:240, :]

        # -- 灰度化
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)

        # -- 高斯模糊: 去除噪点
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # -- 二值化: 将图像转为只有黑白两色。
        #    THRESH_BINARY_INV 表示反向二值化，适用于“白线黑地”
        #    如果你的场地是“黑线白地”，请使用 cv2.THRESH_BINARY
        _, thresh = cv2.threshold(
            blur, binary_threshold, 255, cv2.THRESH_BINARY_INV)

        # 3. 轮廓查找与分析
        # -- 查找所有轮廓
        contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            # -- 如果找到了轮廓
            #    找出面积最大的轮廓，我们认为它就是循迹线
            c = max(contours, key=cv2.contourArea)

            #    计算最大轮廓的几何矩
            M = cv2.moments(c)

            #    计算轮廓的中心点 (cx, cy)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # 在调试窗口中画出轮廓和中心点，方便观察
                cv2.drawContours(crop_img, [c], -1, (0, 255, 0), 2)  # 绿色轮廓
                cv2.circle(crop_img, (cx, cy), 5, (0, 0, 255), -1)   # 红色中心点

                # 4. 运动决策
                #    计算循迹线中心点与图像中心线的偏移量
                deviation = cx - center_line

                if abs(deviation) <= deviation_threshold:
                    # -- 偏移量很小，在正中 -> 前进
                    print(f"On Track! Deviation: {deviation:.2f}")
                    forward(move_speed)
                elif deviation > deviation_threshold:
                    # -- 循迹线在右侧 -> 小车需右转
                    print(f"Turn Right! Deviation: {deviation:.2f}")
                    right(turn_speed)
                else:  # deviation < -deviation_threshold
                    # -- 循迹线在左侧 -> 小车需左转
                    print(f"Turn Left! Deviation: {deviation:.2f}")
                    left(turn_speed)

            else:
                # m00为0，说明轮廓面积为0，当没看见处理
                print("Line detected, but area is zero.")
                stop()

        else:
            # -- 如果没有找到任何轮廓 -> 停止
            print("I don't see the line.")
            stop()

        # 显示用于调试的窗口
        cv2.imshow('Debug View', crop_img)
        # cv2.imshow('Threshold View', thresh) # 可以取消这行注释，单独查看二值化效果

        # 检测按键，如果按下 'q' 键，则退出循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- 循环结束后，释放资源 ---
    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 6. 主程序入口 -------------------------
try:
    # ============ 参数校准区 ============
    # 【请在这里通过实验，修改为你自己的小车最合适的值】

    MOVE_SPEED = 35         # 正常循迹速度 (建议不要太快，方便调整)
    TURN_SPEED = 50         # 转向调整速度
    DEVIATION_THRESHOLD = 20  # 中心偏移阈值(像素)，数值越小，循迹越灵敏但也可能更抖动

    # ！！！最重要的参数：二值化阈值 (0-255) ！！！
    # 这个值决定了程序如何区分“循迹线”和“地面”。
    # 你需要根据实际场地光线和颜色来调整。
    # 如何调整：运行程序，观察"Debug View"窗口，确保循迹线能被稳定地识别为绿色轮廓。
    # 如果循迹线无法识别，或者很多杂乱的背景也被识别，就需要调整这个值。
    BINARY_THRESHOLD = 150
    # ==================================

    # 调用循迹模式主函数
    line_follower_mode(MOVE_SPEED, TURN_SPEED,
                       DEVIATION_THRESHOLD, BINARY_THRESHOLD)


except KeyboardInterrupt:
    print("\n程序已被用户中断")
    pass

finally:
    print("清理GPIO资源...")
    stop()           # 确保电机停止
    GPIO.cleanup()   # 清理GPIO
