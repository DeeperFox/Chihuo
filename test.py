from sql import DbMysql

db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
uid = db.find("select id from user where user_name= %s and my_follow= %s", ["123@qq.com"], ["456@qq.com"])