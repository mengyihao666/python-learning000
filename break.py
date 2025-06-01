import random
m = 10000
for i in range(1, 21):
    if m < 1000:
        print("工资发完了")
        break
    if random.randint(1, 10) > 5:
        m -= 1000
        print(f"员工{i}获得1000元奖金")
else:  # 循环正常结束（未被break中断）
    print("工资发完了")
