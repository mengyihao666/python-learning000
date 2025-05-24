# todo_list.py

tasks = []  # 用于存储任务，格式为列表，每个任务是一个字典 {"task": str, "completed": bool}


def show_menu():
    print("\n=== 待办事项清单 ===")
    print("1. 添加任务")
    print("2. 查看任务")
    print("3. 标记任务为已完成")
    print("4. 删除任务")
    print("5. 退出程序")


def add_task():
    task = input("请输入新的任务内容: ").strip()
    if task:
        tasks.append({"task": task, "completed": False})
        print(f"✅ 已添加任务: {task}")
    else:
        print("⚠️ 任务内容不能为空！")


def view_tasks():
    if not tasks:
        print("📭 当前没有任何任务！")
        return
    print("\n📋 当前任务清单:")
    for i, task in enumerate(tasks, 1):
        status = "[x]" if task["completed"] else "[ ]"
        print(f"{i}. {status} {task['task']}")


def complete_task():
    view_tasks()
    if not tasks:
        return
    try:
        index = int(input("请输入要标记为已完成的任务编号: "))
        if 1 <= index <= len(tasks):
            tasks[index - 1]["completed"] = True
            print(f"✅ 任务已标记为完成: {tasks[index - 1]['task']}")
        else:
            print("⚠️ 编号超出范围！")
    except ValueError:
        print("⚠️ 请输入有效的任务编号！")


def delete_task():
    view_tasks()
    if not tasks:
        return
    try:
        index = int(input("请输入要删除的任务编号: "))
        if 1 <= index <= len(tasks):
            removed = tasks.pop(index - 1)
            print(f"🗑️ 已删除任务: {removed['task']}")
        else:
            print("⚠️ 编号超出范围！")
    except ValueError:
        print("⚠️ 请输入有效的任务编号！")


def main():
    while True:
        show_menu()
        choice = input("请选择操作（1-5）: ").strip()
        if choice == "1":
            add_task()
        elif choice == "2":
            view_tasks()
        elif choice == "3":
            complete_task()
        elif choice == "4":
            delete_task()
        elif choice == "5":
            print("👋 感谢使用，再见！")
            break
        else:
            print("⚠️ 无效选项，请输入 1-5！")


if __name__ == "__main__":
    main()
