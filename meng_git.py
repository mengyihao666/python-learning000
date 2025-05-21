def check_string_in_list():
    # 获取用户输入的字符串
    user_input = input("请输入一个字符串：")

    # 定义一个示例列表
    sample_list = ["apple", "banana", "cherry", "date"]

    # 判断用户输入的字符串是否在列表中
    result = user_input in sample_list

    # 输出判断结果
    print(result)


# 调用函数
check_string_in_list()
