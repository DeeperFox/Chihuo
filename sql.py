import pymysql

class DbMysql:
	# 参数用于连接数据库
    def __init__(self, host, port, user, passwd, database, charset):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.database = database
        self.charset = charset
        self.cur = None
        self.conn = None
#连接数据库
    def connect_db(self):
        self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd,
                               database=self.database, charset=self.charset)
        # 连接成功就获取游标
        if self.conn:
            self.cur = self.conn.cursor()
#关闭数据库
    def close_db(self):
        if self.conn:
            if self.cur:
                self.cur.close()
            self.conn.close()
#查询操作
    def find(self, sql, *args):
        datas = None
        try:
        	# 连接数据库
            self.connect_db()
            # 执行查询操作
            self.cur.execute(sql, args)
            # 获取查询结果
            datas = self.cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            self.close_db()
        return datas
#插入操作
    def insert(self, table_name, *args):
    	# 对输入的参数进行处理，使SQL合法化，否则无法进行插入操作。
    	# 数值类型需要转换为字符串，字符串类型需要在外层加引号，NULL类型需要去掉外层引号。
        data = ",".join([x if x != '"NULL"' else eval(x) for x in [str(ele) if isinstance(ele, int) else '"%s"' % ele for ele in args]])
        sql = "insert into %s values(%s)" % (table_name, data)
        print(sql)
        try:
        	# 连接数据库
            self.connect_db()
            # 执行插入语句
            self.cur.execute(sql)
            # 提交
            self.conn.commit()
        except Exception as e:
            print(e)
        finally:
        	# 关闭数据库连接
            self.close_db()
#删除操作
    def delete(self, sql, *args):
        self.__execute_sql(sql, *args)
#更新操作
    def update(self, sql, *args):
        self.__execute_sql(sql, *args)

	# 更新和删除操作类似，定义私有方法执行
    def __execute_sql(self, sql, *args):
        try:
        	# 连接数据库
            self.connect_db()
            # 执行SQL语句
            self.cur.execute(sql, args)
            # 提交
            self.conn.commit()
        except Exception as e:
            print(e)
            # 出现异常，不提交而是回滚
            self.conn.rollback()
        finally:
        	# 关闭数据库连接
            self.close_db()
#
# -- from utils import DbMysql
# --
# -- if __name__ == '__main__':
# --     db = DbMysql(host="127.0.0.1", port=3306, user="root", passwd="123456", database="testdb", charset="utf8")
# --
# --     datas = db.find("select * from EMP where ENAME= %s", ["SMITH",])
# --     print(datas)
# --
# --     db.insert("EMP", 7759, "LUCY1", "clerk", 7882, "1994-11-10", 2000, "NULL", 30)
# --
# --     db.delete("delete from EMP where ENAME=%s", ["LUCY"])
# --
# --     db.update("update EMP set SAL=100 WHERE ENAME=%s", ["nick"])
