print("猜名人游戏")
print("一共五条信息")
print("点击enter开始游戏,输入esc退出游戏")

user_input = input()
if user_input == "":
    print("开始游戏")
    import time
    time.sleep(1)
elif user_input.lower() == "esc":
    print("退出游戏")
    exit()
xinxi = [
    "这位名人是一位黑人运动员",
    "这位名人不只是在自己的国家享有盛名，全球同样如此",
    "这位名人在比赛中非常喜欢使用某个动作用来对抗对手",
    "这位名人死亡于2020年，和自己的女儿一同遭遇不幸",
    "这位名人死亡于坠机"
]
daan = "科比"
for i in range(5):
    print("第", i+1, "条信息:", xinxi[i])
    guess = input("请输入您猜测的名人名字: ")
    if guess == daan:
        print("恭喜您，猜对了！你就是个天才！")
        break
    elif guess.lower() == "esc":
        print("游戏退出")
        break
    elif i == 4:
        print("很遗憾，五次机会用完了，正确答案是:", daan)
        break
    else:
        print("猜错了，继续加油！")
