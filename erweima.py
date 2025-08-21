# car_qrcode_control.py
# 功能：识别二维码并根据其内容执行相应指令

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO
import time
import cv2
from pyzbar import pyzbar  # 导入pyzbar库

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

# ------------------------- 4. 二维码识别与控制主函数 -------------------------


def qr_code_mode(move_speed, turn_speed):
    """进入二维码指令识别模式"""
    print("已进入二维码识别模式... 将二维码放入摄像头视野。按 'q' 退出。")

    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    time.sleep(1)

    # 存储上一个有效指令，避免频繁停止/启动
    last_command = None

    while True:
        # 1. 捕获图像
        ret, frame = cap.read()
        if not ret:
            break

        # 2. 检测并解码二维码
        # pyzbar.decode会返回一个包含所有二维码信息的列表
        barcodes = pyzbar.decode(frame)

        # 默认指令为停止
        current_command = "Stop"

        for barcode in barcodes:
            # 3. 提取信息并进行可视化
            # 将二维码数据从字节(bytes)解码为字符串(string)
            command = barcode.data.decode('utf-8')
            current_command = command  # 获取检测到的指令

            # 提取二维码的位置，并在图像上画出边框
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 在边框上方显示二维码的内容
            cv2.putText(frame, command, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 2)

        # 4. 指令解析与执行
        # 只有当指令发生变化时才打印，避免刷屏
        if current_command != last_command:
            print(f"接收到指令: {current_command}")
            last_command = current_command

        if current_command == "Run":
            forward(move_speed)
        elif current_command == "Back":
            backward(move_speed)
        elif current_command == "Left":
            left(turn_speed)
        elif current_command == "Right":
            right(turn_speed)
        else:  # 包括 "Stop" 指令或者没有检测到任何指令
            stop()

        # 显示调试窗口
        cv2.imshow("QR Code Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------------- 5. 主程序入口 -------------------------
try:
    MOVE_SPEED = 50
    TURN_SPEED = 60

    qr_code_mode(MOVE_SPEED, TURN_SPEED)

except KeyboardInterrupt:
    print("\n程序已被用户中断")
finally:
    print("清理GPIO资源...")
    stop()
    GPIO.cleanup()
