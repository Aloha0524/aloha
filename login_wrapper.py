# login_wrapper.py
# 功能：数据库登录验证，成功后调用原学生管理系统（原代码完全不动）

import pymysql
import subprocess
import sys
import os

class LoginChecker:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                user="root",
                password="050524",   # 改成你自己的密码
                database="student_db",
                charset="utf8mb4"
            )
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        except Exception as e:
            print(f"❌ 数据库连接失败：{e}")
            sys.exit(1)

    def verify(self, username, password):
        sql = "SELECT * FROM user WHERE username=%s AND password=%s"
        self.cursor.execute(sql, (username, password))
        return self.cursor.fetchone() is not None

    def close(self):
        self.cursor.close()
        self.conn.close()


def main():
    print("========== 学生信息管理系统登录 ==========")
    username = input("请输入用户名: ")
    password = input("请输入密码: ")

    checker = LoginChecker()
    if checker.verify(username, password):
        print("✅ 登录成功！正在启动系统...\n")
        checker.close()

        # 调用原学生管理系统（不修改原文件）
        script_path = os.path.join(os.path.dirname(__file__), "studentmanagement.py")
        if not os.path.exists(script_path):
            print("❌ 找不到 studentmanagement.py，请确认文件存在")
            sys.exit(1)
        subprocess.run([sys.executable, script_path])
    else:
        print("❌ 用户名或密码错误，登录失败！")
        checker.close()
        sys.exit(1)


if __name__ == "__main__":
    main()