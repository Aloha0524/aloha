import pymysql
import time
from datetime import datetime

class BookManager:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                user="root",
                password="050524",
                database="book_db",
                charset="utf8mb4",
                autocommit=False
            )
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            print("数据库连接成功")
        except Exception as e:
            print("数据库连接失败：", e)

    def write_log(self, msg):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("book_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] {msg}\n")

    # 1. 添加图书
    def add_book(self, book_id, title, author, publisher, publish_year, category):
        try:
            sql = "INSERT INTO books(book_id, title, author, publisher, publish_year, category, status) VALUES(%s,%s,%s,%s,%s,%s,'可借阅')"
            self.cursor.execute(sql, (book_id, title, author, publisher, publish_year, category))
            self.conn.commit()
            print("图书添加成功")
            self.write_log(f"新增图书：编号{book_id} 书名《{title}》分类：{category}")
        except Exception as e:
            self.conn.rollback()
            print("添加失败！图书编号重复或数据格式错误", e)

    # 2. 查看所有图书
    def show_all_books(self):
        sql = "SELECT * FROM books ORDER BY book_id"
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        if not res:
            print("暂无图书数据！")
            return
        print("\n" + "="*100)
        print(f"{'编号':<8} {'书名':<20} {'作者':<12} {'分类':<10} {'状态':<8}")
        print("-"*100)
        for item in res:
            print(f"{item['book_id']:<8} {item['title']:<20} {item['author']:<12} {item['category']:<10} {item['status']:<8}")
        print("="*100)
        self.write_log("查看所有图书")

    # 3. 按编号精准查询
    def search_by_id(self, book_id):
        sql = "SELECT * FROM books WHERE book_id=%s"
        self.cursor.execute(sql, (book_id,))
        book = self.cursor.fetchone()
        if book:
            print(f"\n编号：{book['book_id']} | 书名：《{book['title']}》| 作者：{book['author']}")
            print(f"出版社：{book['publisher']} | 出版年份：{book['publish_year']}")
            print(f"分类：{book['category']} | 状态：{book['status']}")
            self.write_log(f"精准查询图书：编号{book_id}")
        else:
            print("未找到该图书")

    # 4. 修改图书信息（书名、作者、分类）
    def update_book_info(self, book_id, new_title=None, new_author=None, new_category=None):
        try:
            updates = []
            params = []
            if new_title:
                updates.append("title=%s")
                params.append(new_title)
            if new_author:
                updates.append("author=%s")
                params.append(new_author)
            if new_category:
                updates.append("category=%s")
                params.append(new_category)
            if not updates:
                print("没有提供任何修改内容")
                return
            params.append(book_id)
            sql = f"UPDATE books SET {', '.join(updates)} WHERE book_id=%s"
            self.cursor.execute(sql, params)
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print("图书信息修改成功")
                self.write_log(f"修改图书信息：编号{book_id}")
            else:
                print("未找到该图书")
        except Exception as e:
            self.conn.rollback()
            print("修改失败", e)

    # 5. 删除图书（二次确认）
    def delete_book(self, book_id):
        try:
            self.cursor.execute("SELECT status FROM books WHERE book_id=%s", (book_id,))
            book = self.cursor.fetchone()
            if not book:
                print("图书不存在")
                return
            self.cursor.execute("SELECT COUNT(*) as cnt FROM borrowings WHERE book_id=%s AND status='borrowed'", (book_id,))
            if self.cursor.fetchone()['cnt'] > 0:
                print("该图书有未归还的借阅记录，无法删除")
                return
            confirm = input(f"确认删除编号 {book_id} 的图书吗？(y/n): ")
            if confirm.lower() != 'y':
                print("删除已取消")
                return
            self.cursor.execute("DELETE FROM books WHERE book_id=%s", (book_id,))
            self.conn.commit()
            print("图书删除成功")
            self.write_log(f"删除图书：编号{book_id}")
        except Exception as e:
            self.conn.rollback()
            print("删除失败", e)

    # 6. 借阅图书（限借3本）
    def borrow_book(self, book_id, borrower_name, borrower_id):
        try:
            self.cursor.execute("SELECT status, title FROM books WHERE book_id=%s", (book_id,))
            book = self.cursor.fetchone()
            if not book:
                print("图书不存在")
                return
            if book['status'] == '已借出':
                print("该书已借出，暂不可借")
                return
            self.cursor.execute("SELECT COUNT(*) as cnt FROM borrowings WHERE borrower_id=%s AND status='borrowed'", (borrower_id,))
            if self.cursor.fetchone()['cnt'] >= 3:
                print("该读者已达到最大借阅数量（3本），无法继续借阅")
                return
            self.cursor.execute("UPDATE books SET status='已借出' WHERE book_id=%s", (book_id,))
            borrow_time = datetime.now()
            sql = "INSERT INTO borrowings(book_id, book_title, borrower_name, borrower_id, borrow_time, status) VALUES(%s,%s,%s,%s,%s,'borrowed')"
            self.cursor.execute(sql, (book_id, book['title'], borrower_name, borrower_id, borrow_time))
            self.conn.commit()
            print(f"《{book['title']}》借阅成功，借阅日期：{borrow_time.strftime('%Y-%m-%d')}")
            self.write_log(f"借阅图书：《{book['title']}》 借阅人：{borrower_name}({borrower_id})")
        except Exception as e:
            self.conn.rollback()
            print("借阅失败", e)

    # 7. 归还图书
    def return_book(self, book_id, borrower_id):
        try:
            sql = "SELECT * FROM borrowings WHERE book_id=%s AND borrower_id=%s AND status='borrowed' ORDER BY borrow_time DESC LIMIT 1"
            self.cursor.execute(sql, (book_id, borrower_id))
            borrowing = self.cursor.fetchone()
            if not borrowing:
                print("未找到有效的借阅记录")
                return
            self.cursor.execute("UPDATE books SET status='可借阅' WHERE book_id=%s", (book_id,))
            return_time = datetime.now()
            self.cursor.execute("UPDATE borrowings SET status='returned', return_time=%s WHERE id=%s", (return_time, borrowing['id']))
            self.conn.commit()
            print(f"✅ 《{borrowing['book_title']}》归还成功")
            self.write_log(f"归还图书：《{borrowing['book_title']}》 借阅人：{borrowing['borrower_name']}")
        except Exception as e:
            self.conn.rollback()
            print("归还失败", e)

    # 8. 按书名模糊查询
    def search_by_title(self, keyword):
        sql = "SELECT * FROM books WHERE title LIKE %s"
        self.cursor.execute(sql, (f"%{keyword}%",))
        books = self.cursor.fetchall()
        if not books:
            print("未找到相关图书")
            return
        print(f"\n====== 包含「{keyword}」的图书 ======")
        for b in books:
            print(f"{b['book_id']} | 《{b['title']}》 | {b['author']} | {b['category']} | {b['status']}")
        self.write_log(f"模糊查询书名：{keyword}")

    # 9. 按分类筛选
    def filter_by_category(self, category):
        sql = "SELECT * FROM books WHERE category=%s"
        self.cursor.execute(sql, (category,))
        books = self.cursor.fetchall()
        if not books:
            print(f"分类「{category}」下暂无图书")
            return
        print(f"\n====== 分类：{category} ======")
        for b in books:
            print(f"{b['book_id']} | 《{b['title']}》 | {b['author']} | {b['status']}")
        self.write_log(f"按分类筛选：{category}")

    # 10. 分页查询（每页5条）
    def page_query(self, page=1, page_size=5):
        offset = (page - 1) * page_size
        sql = "SELECT * FROM books LIMIT %s OFFSET %s"
        self.cursor.execute(sql, (page_size, offset))
        books = self.cursor.fetchall()
        if not books:
            print("没有更多数据")
            return
        print(f"\n====== 第 {page} 页（每页{page_size}条）======")
        for b in books:
            print(f"{b['book_id']} | 《{b['title']}》 | {b['author']} | {b['category']} | {b['status']}")
        self.write_log(f"分页查询第{page}页")

    # 11. 查看所有借阅记录
    def show_borrowing_records(self, status=None):
        if status:
            sql = "SELECT * FROM borrowings WHERE status=%s ORDER BY borrow_time DESC"
            self.cursor.execute(sql, (status,))
        else:
            sql = "SELECT * FROM borrowings ORDER BY borrow_time DESC"
            self.cursor.execute(sql)
        records = self.cursor.fetchall()
        if not records:
            print("暂无借阅记录")
            return
        print("\n========== 借阅记录 ==========")
        now = datetime.now()
        for r in records:
            borrow_date = r['borrow_time']
            overdue = False
            if r['status'] == 'borrowed' and (now - borrow_date).days > 30:
                overdue = True
            status_text = "已借出" if r['status'] == 'borrowed' else "已归还"
            overdue_flag = " 逾期！" if overdue else ""
            print(f"图书：《{r['book_title']}》| 借阅人：{r['borrower_name']}({r['borrower_id']})")
            print(f"借阅时间：{borrow_date.strftime('%Y-%m-%d')} | 状态：{status_text}{overdue_flag}")
            if r['return_time']:
                print(f"归还时间：{r['return_time'].strftime('%Y-%m-%d')}")
            print("-" * 80)

    def close(self):
        self.cursor.close()
        self.conn.close()
        print("数据库连接已关闭")

def main():
    bm = BookManager()
    while True:
        print("\n======= 图书管理系统 =======")
        print("1. 添加图书")
        print("2. 查看所有图书")
        print("3. 按编号查询")
        print("4. 修改图书信息")
        print("5. 删除图书")
        print("6. 借阅图书")
        print("7. 归还图书")
        print("8. 按书名模糊查询")
        print("9. 按分类筛选")
        print("10. 分页查询")
        print("11. 查看全部借阅记录")
        print("0. 退出")
        print("==========================")
        choice = input("请输入功能编号：")

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

if __name__ == "__main__":
    main()