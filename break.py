import random
m = 10000
for i in range(1, 21):
    if random.randint(1, 10) > 5 and m >= 1000:
        m -= 1000
        print(f"员工{i}获得1000元奖金")
    elif m < 1000:
        print(f"工资发完了")
        break
    elif i == 20 and m >= 1000:
        print(f"工资发完了")
