import random

num = random.randint(1, 10000)
print("欢迎进入猜数字游戏！")
guess_count = 0  # 初始化猜测次数计数器

while True:  # 使用无限循环，直到猜对数字
    guess = int(input("请输入你猜测的数字："))
    guess_count += 1  # 每次猜测后增加计数器
    if guess == num:
        print("恭喜你猜对了！")
        print(f"你总共猜了{guess_count}次")
        break
    elif guess < num:
        print("你猜的数字小了")
    else:
        print("你猜的数字大了")