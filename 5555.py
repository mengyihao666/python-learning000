import random
a = random.randint(0, 9)
b = random.randint(0, 9)
n = int(f"{a}{b}")
print(n)
i = 10
while i > 0:
    guess = int(input("请输入你猜测的数字："))
    if guess == n:
        print("恭喜你，猜对了！")
        i = i+10
    else:
        i = i-2
        if i == 0:
            print("很遗憾，你没有猜对，正确答案是：", n)
            break
