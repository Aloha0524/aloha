# login.py
# 功能：登录分级（管理员/学生）+ 注册功能
# 原 book_manager.py 未做任何修改

import pymysql
from book_manager import BookManager
import time
from datetime import datetime


class LoginSystem:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                user="root",
                password="050524",
                database="book_db",
                charset="utf8mb4"
            )
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        except Exception as e:
            print(" 数据库连接失败", e)
            exit(1)

    def verify(self, username, password):
        sql = "SELECT * FROM user WHERE username=%s AND password=%s"
        self.cursor.execute(sql, (username, password))
        return self.cursor.fetchone()

    def register(self, username, password):
        """注册新用户，默认角色为 student"""
        # 检查用户名是否已存在
        self.cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
        if self.cursor.fetchone():
            return False, "用户名已存在"
        # 插入新用户
        sql = "INSERT INTO user (username, password, role) VALUES (%s, %s, 'student')"
        self.cursor.execute(sql, (username, password))
        self.conn.commit()
        return True, "注册成功"

    def close(self):
        self.cursor.close()
        self.conn.close()


def main():
    login_sys = LoginSystem()

    while True:
        print("\n========== 图书管理系统 ==========")
        print("1. 登录")
        print("2. 注册")
        print("0. 退出")
        print("================================")
        choice = input("请选择: ")

        if choice == "1":
            username = input("用户名: ")
            password = input("密码: ")
            user = login_sys.verify(username, password)
            if not user:
                print(" 用户名或密码错误")
                continue
            role = user['role']
            print(f" 登录成功！欢迎 {username}（{role}）")
            login_sys.close()
            # 进入图书管理系统（带权限控制）
            run_book_manager(username, role)
            break

        elif choice == "2":
            username = input("请输入用户名: ")
            password = input("请输入密码: ")
            success, msg = login_sys.register(username, password)
            print(f"✅ {msg}" if success else f"❌ {msg}")
            if success:
                print("请返回登录")
            continue

        elif choice == "0":
            login_sys.close()
            print("系统退出")
            break

        else:
            print("无效输入")


def run_book_manager(username, role):
    """根据角色运行带权限的图书管理系统"""
    bm = BookManager()
    # 添加用户信息以便日志记录
    bm.current_user = username
    bm.current_role = role

    # 重写日志方法，记录操作人
    original_write_log = bm.write_log

    def new_write_log(msg):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("book_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] [{username}({role})] {msg}\n")

    bm.write_log = new_write_log

    if role == 'admin':
        while True:
            print("\n======= 图书管理系统（管理员模式）=======")
            print("1. 添加图书")
            print("2. 查看所有图书")
            print("3. 按编号精准查询")
            print("4. 修改图书信息")
            print("5. 删除图书")
            print("6. 借阅图书")
            print("7. 归还图书")
            print("8. 按书名模糊查询")
            print("9. 按分类筛选图书")
            print("10. 分页查询")
            print("11. 查看所有借阅记录")
            print("0. 退出")
            print("========================================")
            choice = input("请选择: ")

            if choice == "1":
                bid = input("图书编号: ")
                title = input("书名: ")
                author = input("作者: ")
                publisher = input("出版社: ")
                year = input("出版年份: ")
                category = input("分类: ")
                bm.add_book(bid, title, author, publisher, year, category)
            elif choice == "2":
                bm.show_all_books()
            elif choice == "3":
                bid = input("图书编号: ")
                bm.search_by_id(bid)
            elif choice == "4":
                bid = input("图书编号: ")
                new_title = input("新书名(回车跳过): ") or None
                new_author = input("新作者(回车跳过): ") or None
                new_category = input("新分类(回车跳过): ") or None
                bm.update_book_info(bid, new_title, new_author, new_category)
            elif choice == "5":
                bid = input("图书编号: ")
                bm.delete_book(bid)
            elif choice == "6":
                bid = input("图书编号: ")
                name = input("借阅人姓名: ")
                uid = input("借阅人ID: ")
                bm.borrow_book(bid, name, uid)
            elif choice == "7":
                bid = input("图书编号: ")
                uid = input("借阅人ID: ")
                bm.return_book(bid, uid)
            elif choice == "8":
                keyword = input("书名关键字: ")
                bm.search_by_title(keyword)
            elif choice == "9":
                cat = input("分类名称: ")
                bm.filter_by_category(cat)
            elif choice == "10":
                try:
                    page = int(input("页码: "))
                    bm.page_query(page)
                except:
                    print("页码必须数字")
            elif choice == "11":
                bm.show_borrowing_records()
            elif choice == "0":
                bm.close()
                print("系统退出")
                break
            else:
                print("无效输入")

    else:  # student
        while True:
            print("\n======= 图书管理系统（学生模式）=======")
            print("1. 查看所有图书")
            print("2. 按编号查询图书")
            print("3. 按书名模糊查询")
            print("4. 按分类筛选图书")
            print("5. 分页查询")
            print("6. 借阅图书")
            print("7. 归还图书")
            print("8. 查看我的借阅记录")
            print("0. 退出")
            print("=====================================")
            choice = input("请选择: ")

            if choice == "1":
                bm.show_all_books()
            elif choice == "2":
                bid = input("图书编号: ")
                bm.search_by_id(bid)
            elif choice == "3":
                keyword = input("书名关键字: ")
                bm.search_by_title(keyword)
            elif choice == "4":
                cat = input("分类名称: ")
                bm.filter_by_category(cat)
            elif choice == "5":
                try:
                    page = int(input("页码: "))
                    bm.page_query(page)
                except:
                    print("页码必须数字")
            elif choice == "6":
                bid = input("图书编号: ")
                name = username
                uid = input("请输入你的学号/读者ID: ")
                bm.borrow_book(bid, name, uid)
            elif choice == "7":
                bid = input("图书编号: ")
                uid = input("请输入你的学号: ")
                bm.return_book(bid, uid)
            elif choice == "8":
                uid = input("请输入你的学号: ")
                sql = "SELECT * FROM borrowings WHERE borrower_id=%s ORDER BY borrow_time DESC"
                bm.cursor.execute(sql, (uid,))
                records = bm.cursor.fetchall()
                if not records:
                    print("暂无借阅记录")
                else:
                    print(f"\n====== {username} 的借阅记录 ======")
                    for r in records:
                        status_text = "已借出" if r['status'] == 'borrowed' else "已归还"
                        print(
                            f"《{r['book_title']}》 借阅日期: {r['borrow_time'].strftime('%Y-%m-%d')} 状态: {status_text}")
                        if r['return_time']:
                            print(f"   归还日期: {r['return_time'].strftime('%Y-%m-%d')}")
                bm.write_log(f"学生 {username} 查看自己的借阅记录")
            elif choice == "0":
                bm.close()
                print("系统退出")
                break
            else:
                print("无效输入")


if __name__ == "__main__":
    main()