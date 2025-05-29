import random
num = random.randint(1, 10)
print(num)
guess_num = int(input("请输入你猜的数字: "))
if guess_num == num:
    print("恭喜你第一次猜对了")
elif guess_num > num:
    print("你猜的数字太大了")
else:
    print("你猜的数字太小了")

    guess_num = int(input("请输入你猜的数字: "))
    if guess_num == num:
        print("恭喜你第二次猜对了")
    elif guess_num > num:
        print("你猜的数字太大了")
    else:
        print("你猜的数字太小了")

        guess_num = int(input("请输入你猜的数字: "))
        if guess_num == num:
            print("恭喜你第三次猜对了")
        elif guess_num != num:
            print("抱歉你的三次机会用完了")
