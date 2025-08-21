# car_trajectory_motion.py
# 功能：实现小车的基本动作以及固定轨迹运动（矩形、三角形、圆形）

# ------------------------- 1. 导入必要的库 -------------------------
import RPi.GPIO as GPIO  # 导入用于控制树莓派GPIO引脚的库
import time              # 导入用于延时功能的库，例如 time.sleep()

# ------------------------- 2. 定义硬件引脚 -------------------------
# 根据你的电机驱动板和树莓派的接线来定义引脚编号

# --- 左侧电机引脚定义 ---
AIN1 = 22  # 左电机方向控制引脚1
AIN2 = 27  # 左电机方向控制引脚2
PWMA = 18  # 左电机速度控制引脚 (必须是支持PWM的引脚)

# --- 右侧电机引脚定义 ---
BIN1 = 25  # 右电机方向控制引脚1
BIN2 = 24  # 右电机方向控制引脚2
PWMB = 23  # 右电机速度控制引脚 (必须是支持PWM的引脚)

# ------------------------- 3. GPIO初始化 -------------------------
GPIO.setmode(GPIO.BCM)       # 设置引脚编号模式为 BCM。这意味着我们使用 "GPIOxx" 的编号，而不是物理引脚的顺序。
GPIO.setwarnings(False)      # 忽略GPIO引脚被重复设置时的警告信息。

# 使用一个循环将所有定义的电机控制引脚设置为输出模式
# "输出"模式意味着树莓派可以从这些引脚发送信号（高/低电平）出去，来控制电机驱动板。
for pin in [AIN1, AIN2, BIN1, BIN2, PWMA, PWMB]:
    GPIO.setup(pin, GPIO.OUT)

# ------------------------- 4. PWM初始化 -------------------------
# PWM (Pulse Width Modulation, 脉冲宽度调制) 是一种通过快速开关电流来控制电机速度的技术。
# 占空比 (Duty Cycle) 越高 (0-100)，电机获得的平均电压越高，转速越快。

# 为左电机创建一个PWM实例，关联到PWMA引脚，频率设置为100Hz。100Hz对于电机控制是一个常用的频率。
L_Motor = GPIO.PWM(PWMA, 100)
# 为右电机创建PWM实例
R_Motor = GPIO.PWM(PWMB, 100)

# 启动PWM功能，但初始占空比设置为0。
# 这是一个非常好的安全习惯，可以确保程序开始运行时电机不会突然转动。
L_Motor.start(0)
R_Motor.start(0)

# ------------------------- 5. 小车基础动作函数 -------------------------
# 将每个动作封装成一个函数，可以让代码更清晰、更易于复用。


def forward(speed, t):
    """
    函数功能：控制小车前进
    :param speed: 前进的速度 (0-100的占空比)
    :param t: 前进的持续时间 (秒)
    """
    # --- 控制左轮 ---
    L_Motor.ChangeDutyCycle(speed)  # 设置左轮速度
    GPIO.output(AIN1, GPIO.HIGH)    # AIN1=高电平
    GPIO.output(AIN2, GPIO.LOW)     # AIN2=低电平，组合起来使左轮正转

    # --- 控制右轮 ---
    R_Motor.ChangeDutyCycle(speed)  # 设置右轮速度
    GPIO.output(BIN1, GPIO.HIGH)    # BIN1=高电平
    GPIO.output(BIN2, GPIO.LOW)     # BIN2=低电平，组合起来使右轮正转

    # --- 持续运行 ---
    time.sleep(t)  # 保持当前状态，持续t秒钟


def backward(speed, t):
    """
    函数功能：控制小车后退
    :param speed: 后退的速度 (0-100)
    :param t: 后退的持续时间 (秒)
    """
    # --- 控制左轮 ---
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)     # AIN1=低电平
    GPIO.output(AIN2, GPIO.HIGH)    # AIN2=高电平，组合起来使左轮反转

    # --- 控制右轮 ---
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)     # BIN1=低电平
    GPIO.output(BIN2, GPIO.HIGH)    # BIN2=高电平，组合起来使右轮反转

    time.sleep(t)


def left(speed, t):
    """
    函数功能：控制小车原地向左转
    :param speed: 转向的速度 (0-100)
    :param t: 转向的持续时间 (秒)
    """
    # --- 控制左轮 (反转) ---
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)

    # --- 控制右轮 (正转) ---
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    # 左右轮方向相反，实现原地旋转

    time.sleep(t)


def right(speed, t):
    """
    函数功能：控制小车原地向右转
    :param speed: 转向的速度 (0-100)
    :param t: 转向的持续时间 (秒)
    """
    # --- 控制左轮 (正转) ---
    L_Motor.ChangeDutyCycle(speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    # --- 控制右轮 (反转) ---
    R_Motor.ChangeDutyCycle(speed)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)

    time.sleep(t)


def stop(t=0):
    """
    函数功能：停止小车
    :param t: 停止后保持静止的时间 (秒)，默认为0
    """
    # 将两个电机的占空比都设为0，即切断动力。
    L_Motor.ChangeDutyCycle(0)
    R_Motor.ChangeDutyCycle(0)
    time.sleep(t)


def arc(left_speed, right_speed, t):
    """
    函数功能：让小车走弧线（画圆的基础）
    通过设置两个轮子不同的前进速度，实现边走边转的效果。
    :param left_speed: 左轮的速度 (0-100)
    :param right_speed: 右轮的速度 (0-100)
    :param t: 走弧线的持续时间 (秒)
    """
    # 两个电机都设置为正转
    L_Motor.ChangeDutyCycle(left_speed)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    R_Motor.ChangeDutyCycle(right_speed)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)

    time.sleep(t)

# ------------------------- 6. 复杂轨迹函数 -------------------------
# 通过组合基础动作来实现更复杂的运动轨迹


def draw_rectangle(speed, side_time, turn_90_time):
    """
    函数功能：控制小车画一个矩形
    :param speed: 移动和转向的速度
    :param side_time: 走完一条直线边所需的时间
    :param turn_90_time: 原地转90度所需的时间【需要校准！】
    """
    print("开始画矩形...")
    # 矩形有4条边，所以循环4次
    for i in range(4):
        print(f"  > 走第 {i+1} 条边")
        forward(speed, side_time)  # 走一条直线
        print(f"  > 转第 {i+1} 个弯")
        left(speed, turn_90_time)  # 转一个90度的弯
        stop(0.5)  # 每次转弯后停顿一下，让动作更清晰


def draw_triangle(speed, side_time, turn_120_time):
    """
    函数功能：控制小车画一个等边三角形
    :param speed: 移动和转向的速度
    :param side_time: 走完一条直线边所需的时间
    :param turn_120_time: 原地转120度所需的时间【需要校准！】
    """
    print("开始画三角形...")
    # 三角形有3条边，所以循环3次
    for i in range(3):
        print(f"  > 走第 {i+1} 条边")
        forward(speed, side_time)  # 走一条直线
        print(f"  > 转第 {i+1} 个弯 (120度)")
        left(speed, turn_120_time)  # 等边三角形内角60度，外角转向120度
        stop(0.5)


def draw_circle(outer_speed, inner_speed, circle_360_time):
    """
    函数功能：控制小车画一个圆形
    :param outer_speed: 外侧轮速度
    :param inner_speed: 内侧轮速度
    :param circle_360_time: 跑完一整圈360度所需的时间【需要校准！】
    """
    print("开始画圆形...")
    # 调用arc函数，通过内外轮速差来画圆。
    # 这里我们用右轮做外侧轮（速度快），左轮做内侧轮（速度慢），实现向左转画圆
    arc(inner_speed, outer_speed, circle_360_time)
    stop()


# ------------------------- 7. 主程序入口 -------------------------
# try...except...finally 结构可以确保程序无论如何结束（即使是手动按Ctrl+C），
# GPIO资源都会被正确清理，这是一个非常好的习惯。
try:
    # ============ 参数校准区 ============
    # !!非常重要!!: 下面的时间值需要你根据自己的小车进行实验和调整。
    # 因为电池电压、地面摩擦力、电机性能都会影响实际效果。

    # 设定一个标准速度，方便校准，避免每次都用不同的速度测试。
    STD_SPEED = 60

    # 1. 校准原地左转90度所需的时间 (秒)
    #    运行程序，观察小车是否刚好转了90度。转多了就减小此值，转少了就增大此值。
    TURN_90_TIME = 0.55

    # 2. 校准原地左转120度所需的时间 (秒)
    #    理论上是90度时间的 120/90=1.33倍，可以此为初值进行微调。
    TURN_120_TIME = 0.75

    # 3. 校准画一整个圆所需的时间 (秒)
    #    观察小车是否刚好走完一圈回到起点。
    CIRCLE_360_TIME = 8.0
    # ==================================

    # --- 按顺序执行轨迹任务 ---

    # 任务1: 画一个矩形，每条边走1秒
    draw_rectangle(speed=STD_SPEED, side_time=1, turn_90_time=TURN_90_TIME)

    print("矩形完成，准备画三角形。休息3秒...")
    time.sleep(3)  # 在不同任务之间留出等待时间

    # 任务2: 画一个等边三角形，每条边走1秒
    draw_triangle(speed=STD_SPEED, side_time=1, turn_120_time=TURN_120_TIME)

    print("三角形完成，准备画圆形。休息3秒...")
    time.sleep(3)

    # 任务3: 画一个圆
    draw_circle(outer_speed=80, inner_speed=40,
                circle_360_time=CIRCLE_360_TIME)

    print("所有轨迹任务完成！")


except KeyboardInterrupt:
    # 如果用户按下 Ctrl+C，程序会跳转到这里执行。
    # pass 语句表示什么都不做，只是为了让程序平稳地继续向下执行 finally 块。
    print("\n程序已被用户中断")
    pass

finally:
    # 无论程序是正常结束还是被中断，finally 块中的代码都一定会被执行。
    print("清理GPIO资源...")
    GPIO.cleanup()  # 释放所有之前占用的GPIO引脚资源，将它们恢复到初始状态。
