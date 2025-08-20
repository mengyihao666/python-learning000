print("我们将通过比较两个品牌的价格、口碑、销量，帮您选出更符合要求的商品。\n")
print("请输入品牌1的价格、口碑、销量的分数 (范围1-100，用空格隔开):")
price1, reputation1, sales1 = map(int, input().split())
print("\n请输入品牌2的价格、口碑、销量的分数 (范围1-100，用空格隔开):")
price2, reputation2, sales2 = map(int, input().split())
print("\n如果 1 代表价格, 2 代表口碑, 3 代表销量，")
print("请输入您的优先级顺序 (例如: 如果最看重口碑，其次是价格，最后是销量，请输入 2 1 3):")
p1, p2, p3 = input().split()
p = [p1, p2, p3]
winner = None
for i in p:
    if i == '1':
        print(f"正在比较: [价格]")
        if price1 > price2:
            winner = "品牌1"
            print(f"品牌1在价格上胜出 ({price1}分 > {price2}分)。")
            break
        elif price2 > price1:
            winner = "品牌2"
            print(f"品牌2在价格上胜出 ({price2}分 > {price1}分)。")
            break
        else:
            print(f"价格分数相同 ({price1}分)，进入下一轮比较...")

    elif i == '2':
        print(f"正在比较: [口碑]")
        if reputation1 > reputation2:
            winner = "品牌1"
            print(f"品牌1在口碑上胜出 ({reputation1}分 > {reputation2}分)。")
            break
        elif reputation2 > reputation1:
            winner = "品牌2"
            print(f"品牌2在口碑上胜出 ({reputation2}分 > {reputation1}分)。")
            break
        else:
            print(f"口碑分数相同 ({reputation1}分)，进入下一轮比较...")

    elif i == '3':
        print(f"正在比较: [销量]")
        if sales1 > sales2:
            winner = "品牌1"
            print(f"品牌1在销量上胜出 ({sales1}分 > {sales2}分)。")
            break
        elif sales2 > sales1:
            winner = "品牌2"
            print(f"品牌2在销量上胜出 ({sales2}分 > {sales1}分)。")
            break
        else:
            print("销量分数也相同。")

if winner:
    print(f"\n最终推荐您选择: 【{winner}】")
else:
    print("\n所有指标的得分都完全一样，这两个品牌对您来说没有差别，可以随意选择！")
