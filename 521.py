# 定义一个函数，实现大小写转换
def swap_case(s):
    # 用字符串的 swapcase() 方法直接转换
    return s.swapcase()


# 获取用户输入的字符串
user_input = input("请输入一个字符串：")

# 调用函数并传参
result = swap_case(user_input)

# 输出结果
print("转换后的字符串是：", result)
