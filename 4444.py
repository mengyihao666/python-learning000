for i in range(1, 100):
    if i % 2 == 0:
        print(i)
i = 1
num = 0
while i < 100:
    num = num+i
    i = i+1
print(num)
n = 6666
guess = 0
print("请输入你猜测的价格：")
while guess != n:
    guess = int(input())
    if guess < n:
        print("你猜的价格太低了")
    elif guess > n:
        print("你猜的价格太高了")
print("恭喜你，你猜对了！")
z = "3406412713"
m = "MHmq1122"
while True:
    if input("请输入用户名：") == z and input("请输入密码：") == m:
        print("登录成功！")
        break
    else:
        print("用户名或密码错误！请重新输入！")
