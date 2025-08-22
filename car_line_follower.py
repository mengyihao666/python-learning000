# car_line_follower.py
# 功能：实现小车基于OpenCV的视觉循迹运动

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO      # 用于控制树莓派的GPIO引脚
import time                  # 用于延时等时间相关功能
import cv2                   # 导入OpenCV库，用于计算机视觉处理

# ------------------------- 2. 定义硬件引脚 -------------------------
# 根据电机驱动板与树莓派的实际接线定义
# --- 左电机引脚 ---
AIN1, AIN2, PWMA = 22, 27, 18
# --- 右电机引脚 ---
BIN1, BIN2, PWMB = 25, 24, 23

# ------------------------- 3. GPIO与PWM初始化 -------------------------
GPIO.setmode(GPIO.BCM)       # 使用BCM引脚编号模式
GPIO.setwarnings(False)      # 忽略GPIO警告

# 将所有电机控制引脚设置为输出模式
for pin in [AIN1, AIN2, BIN1, BIN2, PWMA, PWMB]:
    GPIO.setup(pin, GPIO.OUT)

# 创建PWM实例，用于控制电机速度，频率设置为100Hz
L_Motor = GPIO.PWM(PWMA, 100)
R_Motor = GPIO.PWM(PWMB, 100)

# 启动PWM，初始占空比为0，即电机静止
L_Motor.start(0)
R_Motor.start(0)

# ------------------------- 4. 小车基础动作函数 -------------------------
# 在循迹模式中，动作函数被设计为"非阻塞式"，即不包含time.sleep()
# 这样主循环才能快速、连续地进行判断和调整，而不是执行一个动作后"盲走"


def forward(speed):
    """小车前进（非阻塞）"""
    L_Motor.ChangeDutyCycle(speed)  # 设置左轮速度
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)  # 左轮正转
    R_Motor.ChangeDutyCycle(speed)  # 设置右轮速度
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)  # 右轮正转


def left(speed):
    """小车原地左转（非阻塞）"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)  # 左轮反转
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)  # 右轮正转


def right(speed):
    """小-车原地右转（非阻塞）"""
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)  # 左轮正转
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)  # 右轮反转


def stop():
    """小车停止"""
    # 将两个电机的占空比都设为0，切断动力
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)

# ------------------------- 5. 循迹主功能函数 (核心逻辑) -------------------------


def line_follower_mode(move_speed, turn_speed, deviation_threshold, binary_threshold):
    """
    进入视觉循迹模式
    :param move_speed: 正常循迹时的前进速度
    :param turn_speed: 转向调整时的速度
    :param deviation_threshold: 路径中心点的偏移容忍范围（像素），小于此值即认为在正中
    :param binary_threshold: 图像二值化的阈值 (0-255)【这是需要校准的最重要参数】
    """
    print("已进入视觉循迹模式... 在视频窗口激活时，按下 'q' 键退出。")

    # --- 步骤A: 初始化摄像头 ---
    cap = cv2.VideoCapture(0)  # 打开编号为0的摄像头（通常是默认摄像头）
    if not cap.isOpened():
        print("错误：无法打开摄像头！")
        return

    # 设置摄像头的分辨率。较低的分辨率可以大大提高处理速度。
    # 属性3是宽度，属性4是高度。
    cap.set(3, 320)
    cap.set(4, 240)

    # 定义图像的中心线X坐标，用于后续计算偏移量
    center_line = 320 / 2

    time.sleep(1)  # 短暂延时，等待摄像头完成初始化和稳定

    # --- 步骤B: 进入主循环，持续处理视频的每一帧 ---
    while True:
        # 1. 捕获图像帧
        ret, frame = cap.read()  # ret是布尔值，表示是否成功捕获；frame是捕获到的图像
        if not ret:
            print("图像捕获失败，退出循环。")
            break

        # 2. 核心图像处理流程
        # -- 2.1 裁剪 (Crop): 我们只关心地面上的循迹线，所以只取图像的下半部分
        #    图像数组的切片方式是 [y1:y2, x1:x2]。这里我们取高度从120到240的区域。
        crop_img = frame[120:240, :]

        # -- 2.2 灰度化 (Grayscale): 颜色信息对于循迹是干扰，转为灰度图简化计算
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)

        # -- 2.3 高斯模糊 (Blur): 平滑图像，去除微小的噪点，使线条更连贯
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # -- 2.4 二值化 (Thresholding): 将图像变成只有纯黑和纯白。这是提取循迹线的关键！
        #    cv2.threshold函数返回两个值，我们通常只需要第二个，即处理后的图像
        #    THRESH_BINARY_INV 是反向二值化，适用于亮色循迹线在深色背景上的情况。
        #    如果像素值 > binary_threshold，则变为0（黑）；否则变为255（白）。
        _, thresh = cv2.threshold(
            blur, binary_threshold, 255, cv2.THRESH_BINARY_INV)

        # 3. 轮廓分析，找到循迹线
        # -- 3.1 查找轮廓: 在二值化图像中找到所有白色区域的边界
        _, contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            # -- 3.2 如果找到了至少一个轮廓
            #    使用max函数配合cv2.contourArea，找出面积最大的那个轮廓，我们认为它就是循迹线
            c = max(contours, key=cv2.contourArea)

            # -- 3.3 计算最大轮廓的“几何矩”，这是一个包含多种几何属性（如面积、中心点等）的字典
            M = cv2.moments(c)

            # -- 3.4 计算中心点: 通过几何矩计算轮廓的质心 (cx, cy)
            #    为避免除以零的错误，先检查面积 'm00' 是否不为0
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])  # 中心的X坐标
                # cy = int(M["m01"] / M["m00"]) # 中心的Y坐标 (在循迹中通常不用)

                # --- （可选）可视化调试：在画面上画出轮廓和中心点，方便观察 ---
                cv2.drawContours(crop_img, [c], -1, (0, 255, 0), 2)  # 用绿色画出轮廓
                # 在固定高度画一个红点表示中心X位置
                cv2.circle(crop_img, (cx, 90), 5, (0, 0, 255), -1)

                # 4. 根据中心点位置进行运动决策
                #    计算循迹线中心点cx与图像中心线的偏移量
                deviation = cx - center_line

                if abs(deviation) <= deviation_threshold:
                    # -- 4.1 偏移量在容忍范围内 -> 保持前进
                    print(f"路径居中 | 偏移量: {deviation:.1f}")
                    forward(move_speed)
                elif deviation > deviation_threshold:
                    # -- 4.2 循迹线在图像右侧 -> 小车需向右转以对准
                    print(f"路径偏右 -> 右转 | 偏移量: {deviation:.1f}")
                    right(turn_speed)
                else:  # deviation < -deviation_threshold
                    # -- 4.3 循迹线在图像左侧 -> 小车需向左转以对准
                    print(f"路径偏左 -> 左转 | 偏移量: {deviation:.1f}")
                    left(turn_speed)
            else:
                # 轮廓面积为0，当没看见处理
                print("未找到有效循迹线 (面积为0)")
                stop()

        else:
            # -- 如果在二值化图像中没有找到任何白色区域 -> 停止
            print("视野中无循迹线")
            stop()

        # --- 步骤C: 显示用于调试的窗口 ---
        cv2.imshow('Debug View (Cropped & Marked)', crop_img)  # 显示处理后并标记的图像
        # cv2.imshow('Threshold View', thresh) # 可以取消这行注释，单独查看二值化效果，对校准阈值非常有帮助

        # --- 步骤D: 检测退出指令 ---
        # 等待1毫秒，并检查是否有按键。如果按下的是'q'键，则退出主循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- 步骤E: 循环结束后，释放所有资源 ---
    print("退出循迹模式。")
    cap.release()          # 释放摄像头
    cv2.destroyAllWindows()  # 关闭所有OpenCV创建的窗口


# ------------------------- 6. 主程序入口 -------------------------
try:
    # ============ 参数校准区 ============
    # !!非常重要!!: 下面的参数，特别是BINARY_THRESHOLD，需要您根据实际场地光线和循迹线颜色进行反复实验和微调。

    MOVE_SPEED = 35          # 正常循迹时的速度 (建议从一个较低的值开始)
    TURN_SPEED = 50          # 转向调整时的速度
    # 中心偏移容忍阈值(像素)。值越小，小车越敏感，但可能来回摆动；值越大，小车越迟钝，但行驶更平稳。
    DEVIATION_THRESHOLD = 20

    # !!【最关键的校准参数】!!: 图像二值化阈值 (0-255)
    # 这个值决定了程序如何区分“循迹线”和“地面”。
    # 如何校准：运行程序，打开'Threshold View'窗口，调整此值，直到窗口中只有循迹线是清晰的白色，且背景干扰最少。
    BINARY_THRESHOLD = 80
    # ==================================

    # 一切准备就绪，调用循迹模式主函数
    line_follower_mode(MOVE_SPEED, TURN_SPEED,
                       DEVIATION_THRESHOLD, BINARY_THRESHOLD)


except KeyboardInterrupt:  # 如果用户在终端按下 Ctrl+C
    print("\n程序已被用户手动中断")
    pass

finally:  # 无论程序如何退出（正常结束或被中断），此部分都将被执行
    print("执行最后的清理工作...")
    stop()           # 确保电机在程序退出前已停止
    GPIO.cleanup()   # 释放所有已占用的GPIO资源
