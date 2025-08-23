# camera_servo_test.py
# 功能：调用摄像头显示画面，并允许通过键盘控制舵机，实现摄像头上下左右转动。

# 1. 导入必要的库
import cv2
import Adafruit_PCA9685  # --- 新增：导入舵机控制库 ---

# --- 新增部分：舵机初始化与设置 ---

print("正在初始化PCA9685舵机驱动板...")
try:
    # 2. 创建PCA9685驱动板的实例
    pwm = Adafruit_PCA9685.PCA9685()

    # 3. 设置PWM频率为50Hz，这是舵机的标准工作频率
    pwm.set_pwm_freq(50)
    print("舵机驱动板初始化成功！")

    # 4. 定义舵机连接的通道 (根据实训任务书)
    SERVO_TILT_CHANNEL = 4  # 顶部舵机(上下/俯仰)在通道4
    SERVO_PAN_CHANNEL = 5   # 底座舵机(左右/平移)在通道5

    # 5. 定义一个辅助函数，将0-180度的角度值转换为舵机需要的PWM脉冲值
    # 这个函数直接来自于任务书的逻辑，确保兼容性
    def set_servo_angle(channel, angle):
        """
        设置舵机角度
        :param channel: 舵机连接的通道 (0-15)
        :param angle: 要设置的角度 (0-180)
        """
        # 这个复杂的公式是将0-180度的角度映射到PCA9685的4096个脉冲计数值中的特定范围
        pulse = 4096 * ((angle * 11) + 500) / 20000 + 0.5
        pwm.set_pwm(channel, 0, int(pulse))

except Exception as e:
    print(f"错误：无法初始化舵机驱动板！请检查：")
    print(f"1. PCA9685库是否已通过 'pip3 install adafruit-pca9685' 安装。")
    print(f"2. I2C接口是否已在 'sudo raspi-config' 中启用。")
    print(f"具体错误: {e}")
    exit()

# ----------------------------------------

print("正在尝试启动摄像头...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("错误：无法打开摄像头！")
    exit()

print("摄像头与舵机准备就绪！")
print("--- 操作指南 ---")
print(" W: 摄像头向上")
print(" S: 摄像头向下")
print(" A: 摄像头向左")
print(" D: 摄像头向右")
print(" Q: 退出程序")
print("----------------")
print("请先用鼠标点击一下 'Camera View' 窗口再按键。")


# --- 新增部分：用于存储舵机当前角度的变量 ---
# 将舵机初始位置设置在中间 (90度)
pan_angle = 90  # 左右平移角度
tilt_angle = 90  # 上下俯仰角度
set_servo_angle(SERVO_PAN_CHANNEL, pan_angle)
set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)


# --- 主循环：读取画面并处理按键 ---
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("错误：无法读取画面帧。")
            break

        cv2.imshow('Camera View', frame)

        # 等待按键，现在我们需要它的返回值来判断是哪个键
        key = cv2.waitKey(1) & 0xFF

        # --- 新增部分：处理键盘输入以控制舵机 ---
        if key == ord('w'):
            tilt_angle += 5  # 角度增加5度
            if tilt_angle > 180:
                tilt_angle = 180  # 限制最大角度
            set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)
            print(f"向上 -> 俯仰角度: {tilt_angle}")

        elif key == ord('s'):
            tilt_angle -= 5
            if tilt_angle < 0:
                tilt_angle = 0  # 限制最小角度
            set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)
            print(f"向下 -> 俯仰角度: {tilt_angle}")

        elif key == ord('a'):
            pan_angle += 5
            if pan_angle > 180:
                pan_angle = 180
            set_servo_angle(SERVO_PAN_CHANNEL, pan_angle)
            print(f"向左 -> 平移角度: {pan_angle}")

        elif key == ord('d'):
            pan_angle -= 5
            if pan_angle < 0:
                pan_angle = 0
            set_servo_angle(SERVO_PAN_CHANNEL, pan_angle)
            print(f"向右 -> 平移角度: {pan_angle}")

        elif key == ord('q'):
            print("接收到退出指令...")
            break
finally:
    # --- 退出前的清理工作 ---
    print("正在释放资源并将舵机归中...")
    # 在退出程序时，将摄像头恢复到中间位置
    set_servo_angle(SERVO_PAN_CHANNEL, 90)
    set_servo_angle(SERVO_TILT_CHANNEL, 90)
    time.sleep(0.5)  # 给舵机一点时间回到原位

    cap.release()
    cv2.destroyAllWindows()
    GPIO.cleanup()  # 虽然没直接用，但加上是个好习惯
    print("程序已安全退出。")
