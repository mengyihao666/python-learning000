import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import Adafruit_PCA9685

# =================================================================
# 1. 配置参数
# =================================================================

# ---------- GPIO引脚定义 ----------
PIN_LEFT_PWMA, PIN_LEFT_AIN2, PIN_LEFT_AIN1 = 18, 27, 22
PIN_RIGHT_PWMB, PIN_RIGHT_BIN2, PIN_RIGHT_BIN1 = 23, 24, 25

# --- 舵机控制参数 ---
SERVO_CHANNEL = 0
SERVO_ANGLE_STRAIGHT, SERVO_ANGLE_TURN = 90, 125
TURN_THRESHOLD = 20

# --- 摄像头与图像处理参数 ---
CAM_WIDTH, CAM_HEIGHT = 320, 240
BINARY_THRESHOLD = 60
MORPH_KERNEL_SIZE = (5, 5)
SCAN_AREA_Y_START, SCAN_AREA_HEIGHT = 180, 20

# --- ★★★ NEW: 摄像头物理偏移校准参数 ★★★ ---
# 按照上面的校准指南来确定此值!
# 如果摄像头在物理中心的左边，此值为正; 在右边，此值为负。
CAMERA_OFFSET_PIXELS = 25  # <--- 这是您需要校准的关键值!

# ---------- PID控制器参数 ----------
Kp, Ki, Kd = 0.45, 0.0, 0.3

# ---------- 小车运行参数 ----------
BASE_SPEED = 30
SHOW_IMAGE = True

# =================================================================
# 2. 舵机和电机控制 (无变化)
# =================================================================


def angle_to_pulse(angle):
    pulse = int((angle / 180.0) * (2500 - 500) + 500)
    return int(pulse / 20000.0 * 4096)


class Motor:
    # ... (此处省略与之前版本完全相同的 Motor 类代码)
    def __init__(self, pin_pwm, pin_in1, pin_in2):
        self.pin_pwm, self.pin_in1, self.pin_in2 = pin_pwm, pin_in1, pin_in2
        GPIO.setup(self.pin_pwm, GPIO.OUT)
        GPIO.setup(self.pin_in1, GPIO.OUT)
        GPIO.setup(self.pin_in2, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin_pwm, 100)
        self.pwm.start(0)

    def move(self, speed):
        if speed > 100:
            speed = 100
        elif speed < -100:
            speed = -100
        if speed > 0:
            GPIO.output(self.pin_in1, GPIO.HIGH)
            GPIO.output(self.pin_in2, GPIO.LOW)
            self.pwm.ChangeDutyCycle(speed)
        elif speed < 0:
            GPIO.output(self.pin_in1, GPIO.LOW)
            GPIO.output(self.pin_in2, GPIO.HIGH)
            self.pwm.ChangeDutyCycle(abs(speed))
        else:
            GPIO.output(self.pin_in1, GPIO.LOW)
            GPIO.output(self.pin_in2, GPIO.LOW)
            self.pwm.ChangeDutyCycle(0)

    def stop(self): self.move(0)

# =================================================================
# 3. 核心循迹算法 (无变化)
# =================================================================


def find_track_center_robust(morphed_img):
    # ... (此处省略与之前版本完全相同的 find_track_center_robust 函数代码)
    height, width = morphed_img.shape
    center_x = width // 2
    scan_area = morphed_img[SCAN_AREA_Y_START: SCAN_AREA_Y_START +
                            SCAN_AREA_HEIGHT, :]
    left_half, right_half = scan_area[:, 0:center_x], scan_area[:, center_x:]
    M_left, M_right = cv2.moments(left_half), cv2.moments(right_half)
    left_line_x, right_line_x = None, None
    if M_left['m00'] > 0:
        left_line_x = int(M_left['m10'] / M_left['m00'])
    if M_right['m00'] > 0:
        right_line_x = int(M_right['m10'] / M_right['m00']) + center_x
    if left_line_x is not None and right_line_x is not None:
        track_center = (left_line_x + right_line_x) // 2
        return track_center, left_line_x, right_line_x
    # 对于单边情况，我们直接返回单边位置，让主循环决定误差
    elif left_line_x is not None:
        return left_line_x, left_line_x, None
    elif right_line_x is not None:
        return right_line_x, None, right_line_x
    else:
        return None, None, None

# =================================================================
# 4. 主程序 (集成偏移校准)
# =================================================================


def main():
    # --- 初始化 ---
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    left_motor = Motor(PIN_LEFT_PWMA, PIN_LEFT_AIN1, PIN_LEFT_AIN2)
    right_motor = Motor(PIN_RIGHT_PWMB, PIN_RIGHT_BIN1, PIN_RIGHT_BIN2)
    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(50)
    pwm.set_pwm(SERVO_CHANNEL, 0, angle_to_pulse(SERVO_ANGLE_STRAIGHT))
    camera_state = 'straight'
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    time.sleep(2)

    previous_error, integral = 0, 0
    kernel = np.ones(MORPH_KERNEL_SIZE, np.uint8)

    # --- 计算出我们的真正目标中心线 ---
    image_center = CAM_WIDTH // 2
    target_center = image_center + CAMERA_OFFSET_PIXELS

    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                break

            # --- 图像处理 ---
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, binary = cv2.threshold(
                blur, BINARY_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
            morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            track_center, l_line, r_line = find_track_center_robust(morphed)

            if track_center is not None:
                # --- ★★★ MODIFIED: 使用校准后的目标中心计算误差 ★★★ ---
                error = track_center - target_center

                # --- PID 控制器 ---
                integral += error
                derivative = error - previous_error
                turn = (Kp * error) + (Ki * integral) + (Kd * derivative)
                previous_error = error

                left_speed = BASE_SPEED + turn
                right_speed = BASE_SPEED - turn
                left_motor.move(left_speed)
                right_motor.move(right_speed)

                # --- 动态视野控制 ---
                if abs(turn) > TURN_THRESHOLD and camera_state != 'turn':
                    pwm.set_pwm(SERVO_CHANNEL, 0,
                                angle_to_pulse(SERVO_ANGLE_TURN))
                    camera_state = 'turn'
                elif abs(turn) <= TURN_THRESHOLD and camera_state != 'straight':
                    pwm.set_pwm(SERVO_CHANNEL, 0, angle_to_pulse(
                        SERVO_ANGLE_STRAIGHT))
                    camera_state = 'straight'
            else:
                left_motor.stop()
                right_motor.stop()
                previous_error, integral = 0, 0

            # --- 调试画面 ---
            if SHOW_IMAGE:
                y_start = SCAN_AREA_Y_START
                y_end = y_start + SCAN_AREA_HEIGHT
                cv2.rectangle(frame, (0, y_start),
                              (CAM_WIDTH, y_end), (0, 255, 0), 2)

                # 画出物理图像中心 (方便校准)
                cv2.line(frame, (image_center, 0),
                         (image_center, CAM_HEIGHT), (255, 0, 255), 1)
                # ★ NEW: 画出我们校准后的虚拟中心线 ★
                cv2.line(frame, (target_center, 0),
                         (target_center, CAM_HEIGHT), (0, 255, 255), 2)

                if track_center:
                    cv2.circle(frame, (track_center, y_start +
                               SCAN_AREA_HEIGHT//2), 7, (0, 0, 255), -1)

                cv2.imshow('Morphed', morphed)
                cv2.imshow('Frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    finally:
        print("清理...")
        left_motor.stop()
        right_motor.stop()
        pwm.set_pwm(SERVO_CHANNEL, 0, angle_to_pulse(90))
        GPIO.cleanup()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
