m = int(input("请输入你购物的总金额:"))
a = input("你是否关注了本店铺？输入y或n:")
if m < 100:
    m = m+10
elif m >= 100 and m < 300:
    m = m-20
elif m >= 300 and m < 500:
    m = m-50
elif m >= 500:
    m = m-100
if a == "y":
    print("最终支付金额：", m-10)
else:
    print("最终支付金额：", m)
