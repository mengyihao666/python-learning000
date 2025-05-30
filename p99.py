i = 1
while i < 10:
    j = 1
    while j <= i:
        print(i, "*", j, "=", i * j, end="\t")
        j += 1
    print()  # 换行
    i += 1
