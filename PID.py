# car_line_follower_smooth.py
# 功能：使用比例控制（P控制）实现更平滑的视觉循迹

# ------------------------- 1. 导入库, 2. 定义引脚, 3. 初始化 (与之前完全相同) -------------------------
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

# ------------------------- 4. 小车基础动作函数 (简化，因为P控制直接操作PWM) -------------------------


def stop():
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)

# ------------------------- 5. 循迹主功能函数 (核心修改部分) -------------------------


def line_follower_smooth_mode(move_speed, Kp, binary_threshold):
    """
    进入平滑视觉循迹模式 (比例控制)
    :param move_speed: 小车的基础前进速度
    :param Kp: 比例控制系数，【需要仔细校准的关键参数】
    :param binary_threshold: 图像二值化的阈值
    """
    print("已进入平滑循迹模式... 按下 'q' 键退出。")

    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    center_line = 320 / 2
    time.sleep(1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        crop_img = frame[120:240, :]
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(
            blur, binary_threshold, 255, cv2.THRESH_BINARY_INV)

        _, contours, _ = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)

            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])

                # ============ 运动决策修改核心区 ============
                deviation = cx - center_line

                # --- 1. 计算一个“校正量” (Proportional Control) ---
                # 它是偏离量 deviation 与比例常数 Kp 的乘积。
                # 偏离得越远 (deviation越大)，校正量就越大，转弯就越“狠”。
                correction = Kp * deviation

                # --- 2. 动态调整左右轮速度 ---
                # 通过在一个轮子速度上增加校正量，另一个减去校正量，来实现平滑的差速转向。
                left_speed = move_speed + correction
                right_speed = move_speed - correction

                # --- 3. 速度限制 ---
                # 确保计算出的速度值不会超出PWM能接受的0-100范围
                left_speed = max(min(left_speed, 100), 0)
                right_speed = max(min(right_speed, 100), 0)

                # --- 4. 应用速度到电机 ---
                # 两个电机都保持前进方向，仅改变速度
                L_Motor.ChangeDutyCycle(left_speed)
                R_Motor.ChangeDutyCycle(right_speed)
                GPIO.output(AIN1, GPIO.HIGH)
                GPIO.output(AIN2, GPIO.LOW)
                GPIO.output(BIN1, GPIO.HIGH)
                GPIO.output(BIN2, GPIO.LOW)

                print(
                    f"偏离: {deviation: <4.0f} | 校正: {correction: <6.1f} | 左轮速: {left_speed: <5.1f} | 右轮速: {right_speed: <5.1f}")
                # ==========================================
            else:
                stop()
        else:
            stop()

        # cv2.imshow('Debug View', crop_img) # 可选的调试窗口
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 6. 主程序入口 -------------------------
try:
    # ============ 参数校准区 (现在更重要了!) ============
    MOVE_SPEED = 30  # 建议从更低的速度开始校准Kp

    # ！！【最关键的校准参数】！！：比例系数 Kp
    # 它定义了小车反应的“灵敏度”。
    # - Kp太小: 小车转弯不及时，容易冲出赛道。
    # - Kp太大: 小车反应过于激烈，会产生剧烈的高频抖动。
    # - 合适的Kp: 小车能平滑地修正路线，转弯流畅。
    # 【建议从一个较小的值如 0.4 开始，然后逐渐增大来寻找最佳点】
    Kp = 0.6

    BINARY_THRESHOLD = 80  # 保持之前为黑线白地校准好的值
    # ==================================

    line_follower_smooth_mode(MOVE_SPEED, Kp, BINARY_THRESHOLD)

except KeyboardInterrupt:
    print("\n程序已被用户中断")
finally:
    print("清理GPIO资源...")
    stop()
    GPIO.cleanup()
