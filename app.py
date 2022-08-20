from wsgiref.simple_server import make_server
from flask import *
import pymysql
from werkzeug.utils import secure_filename
from gevent import pywsgi
from error import *
from sql import DbMysql
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import flask_mail
import random
from decorators import *
from upload_picture import *
import os
import time


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'kawa!fdtp'
# SMTP服务器地址，例如QQ邮箱的smtp.qq.com
app.config['MAIL_SERVER'] = 'smtp.qq.com'
# SMTP服务器端口，SSL为465
app.config['MAIL_PORT'] = 465
# 是否启用SSL加密（反正很牛逼的东西）
app.config['MAIL_USE_SSL'] = True
# 是否启用TLS加密（反正很牛逼的东西）
app.config['MAIL_USE_TLS'] = False
# 登入的邮箱，例如2731510961@qq.com，不能使用无法其他服务的邮箱，例如snbckcode@gmail.com不能使用smtp.qq.com
app.config['MAIL_USERNAME'] = '1110923@qq.com'
# 授权码，在设置smtp的时候有
app.config['MAIL_PASSWORD'] = 'vyuhjgsswycobjfd'
# 初始化对象
mail = flask_mail.Mail(app)


# 发送邮件
@app.route('/send_email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        email_code = random.randint(100000, 999999)
        email_account = request.form.get('mail_account')
        if email_account:
            msg = flask_mail.Message(subject="吃货旅人app验证邮件",
                                     sender="1110923@qq.com", )
            msg.body = "您的验证码为：" + str(email_code)
            msg.recipients = [email_account]
            session['email_code'] = email_code
            session['email'] = email_account
            with app.app_context():
                mail.send(msg)

            return jsonify({
                "data": {"email": session['email']},
                "message": "success",
                "code": 200
            })
        else:
            return bad_request("missing param")


# 验证码比对
@app.route('/verify_code', methods=['POST'])
def verify_code():
    if request.method == 'POST':
        email_code = request.form.get('email_code')
        email_code2 = session['email_code']
        if email_code == email_code2:
            return jsonify({
                "data": {"email": session['email_account']},
                "message": "success",
                "code": 200
            })
        else:
            return bad_request("code error")


# 注册
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user_nick = request.form.get('user_nick')
        if not all([user_name, user_nick, password1, password2]):
            return bad_request("missing param")
        if password1 != password2:
            return bad_request("the two passwords are different")
        try:
            db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
            str1 = db.find("select * from user where user_name= %s", user_name)
            if str1:
                return bad_request("username repeated")
            else:
                password = generate_password_hash(password1, method="pbkdf2:sha256", salt_length=8)
                uid = uuid.uuid1()
                db.insert("user", uid, user_name, password, user_nick, "NULL", "customer")

                response = jsonify({
                    "data": {"user_name": user_name, "user_nick": user_nick},
                    "message": "OK",
                    "code": 200
                })
                return response
        except Exception:
            return servererror("Internal server error")


# 登录
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        if not all([user_name, password]):
            return bad_request("missing param")
        try:
            db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
            str1 = db.find("select * from user where user_name= %s", user_name)
            print(str1)
            if str1 is None:
                return bad_request("this user is not exist")
            if check_password_hash(str1[0][2], password):
                if str1[0][5] == "customer":
                    response = jsonify({"data": {
                        "user_name": user_name,
                        "user_nick": str1[0][3],
                        "token": str(generate_token(user_name,"customer"), 'utf-8')
                    }, "message": 'OK', "code": 200}
                    )
                    response.status_code = 200
                    return response
                elif str1[0][5] == "admin":
                    response = jsonify({"data": {
                        "user_name": user_name,
                        "user_nick": str1[0][3],
                        "token": str(generate_token(user_name,"admin"), 'utf-8')
                    }, "message": 'OK', "code": 200}
                    )
                    response.status_code = 200
                    return response
            else:
                return bad_request("password error")
        except Exception:
            raise Exception


# 修改密码
@app.route('/<email>/change_password', methods=['POST'])
@login_limit
def change_password(email):
    if request.method == 'POST':
        new_password1 = request.form.get('new_password1')
        new_password2 = request.form.get('new_password2')
        if not all([new_password1, new_password2]):
            return bad_request("missing param")
        if new_password1 != new_password2:
            return bad_request("the two passwords are different")
        else:
            new_password3 = generate_password_hash(new_password1, method="pbkdf2:sha256", salt_length=8)
            db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
            db.update("update user set password=%s WHERE user_name=%s", [new_password3, email])
            return jsonify({
                "data": {"user_name": "", "user_nick": ""},
                "message": "success",
                "code": 200
            })


# 修改昵称
@app.route('/<email>/change_nick', methods=['POST'])
@login_limit
def change_nick(email):
    if request.method == 'POST':
        new_nick = request.form.get('new_nick')
        if new_nick:
            db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
            db.update("update user set user_nick=%s WHERE user_name=%s", [new_nick], [email])
            return jsonify({
                "data": {"user_name": "", "user_nick": ""},
                "message": "success",
                "code": 200
            })
        else:
            return bad_request("missing param")


# 关注or取关
@app.route('/<email1>/follow/<email2>')
@login_limit
def follow(email1, email2):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    uid = db.find("select id from user where user_name= %s and my_follow= %s", [email1], [email2])
    if id:
        db.delete("delete from follow where id=%s", [uid])
        a = db.find("select my_fans from fans_count where user_name=%s", [email2])
        db.update("update fans_count set my_fans=%s where user_name=%s", [a[0][0]-1], [email2])
        b = db.find("select my_follow from fans_count where user_name=%s", [email1])
        db.update("update fans_count set my_follow=%s where user_name=%s", [b[0][0] - 1], [email1])
        return jsonify({
            "data": {"user_name": "", "user_nick": ""},
            "message": "cancel follow",
            "code": 200
        })
    else:
        id1 = uuid.uuid1()
        db.insert("follow", id1, email1, email2)
        a = db.find("select my_fans from fans_count where user_name=%s", [email2])
        db.update("update fans_count set my_fans=%s where user_name=%s", [a[0][0] + 1], [email2])
        b = db.find("select my_follow from fans_count where user_name=%s", [email1])
        db.update("update fans_count set my_follow=%s where user_name=%s", [b[0][0] + 1], [email1])
        return jsonify({
            "data": {"user_name": "", "user_nick": ""},
            "message": "follow success",
            "code": 200
        })


# 关注数and粉丝数
@app.route('/<email>/fans_count')
@login_limit
def fans_count(email):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    a = db.find("select my_follow,my_fans from user where user_name= %s ", [email])
    if a:
        return jsonify({
            "data": {"my_follow": a[0][0], "my_fans": a[0][1]},
            "message": "success",
            "code": 200
        })
    else:
        return jsonify({
            "data": {"my_follow": 0, "my_fans": 0},
            "message": "success",
            "code": 200
        })


# 我的收藏（美食）
@app.route('/<email>/food_collect')
@login_limit
def food_collect(email):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find(
        "select collect.time,collect.picture,food.name from collect inner join food where collect.user_name=%s and collect.type=1 and food.id=collect.target",
        [email])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 我的收藏（店家）
@app.route('/<email>/store_collect')
@login_limit
def store_collect(email):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find(
        "select collect.time,collect.picture,store.name from collect inner join store where collect.user_name=%s and collect.type=0 and store.id=collect.target",
        [email])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 上传头像
@app.route('/<email>/change_head', methods=['POST'])
def change_head(email):
    if request.method == 'POST':
        file = request.files['file']
        if file:
            basepath = os.path.dirname(__file__)
            basepath = basepath.replace('\\', '/')
            print(basepath)
            path = basepath + '/static/' + secure_filename(file.filename)
            print(path)
            file.save(path)
            url = upload_picture(path)
            db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
            db.update("update user set head=%s WHERE user_name=%s", [email])
            return jsonify({
                "data": {"url": url},
                "message": "success",
                "code": 200
            })
        else:
            return bad_request("missing param")


# 我的帖子
@app.route('/<email>/my_post')
@login_limit
def my_post(email):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select title,picture,time,grade,collect from posts where user_name=%s", [email])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 查看社区全部帖子
@app.route('/community/all_post')
def all_post():
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find(
        "select user.user_nick,posts.title,posts.picture,posts.time,posts.grade,posts.collect,posts.id from user inner join posts where user.user_name=posts.user_name")
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 查看关注的帖子
@app.route('/<email>/community/follow_post')
@login_limit
def follow_post(email):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    follower = db.find("select my_follow from follow where user_name=%s", [email])
    list1 = []
    for i in follower:
        a = db.find("select user.user_nick,posts.title,posts.picture,posts.time,posts.grade,posts.collect,posts.id from posts inner join user where posts.user_name=%s and user.user_name=%s", [i[0]], [i[0]])
        for j in a:
            b = list(j)
            list1.append(b)
    return jsonify({
        "data": list1,
        "message": "success",
        "code": 200
    })


# 查看帖子详情
@app.route('/post_detail/<uid>')
@login_limit
def post_detail(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find(
        "select user.user_nick,post.user_name,posts.title,posts.time,posts.grade,posts.collect,posts.detail from user inner join posts where user.user_name=posts.user_name and posts.id=%s",
        [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 查看帖子图片
@app.route('/picture/<uid>')
@login_limit
def picture(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select url from picture where target=%s", [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 发布新帖
@app.route('/<email>/up_post', methods=['POST'])
@login_limit
def up_post(email):
    global picture2
    j = 1
    title = request.form.get('title')
    detail = request.form.get('detail')
    pictures = request.files.getlist('file')
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    id1 = db.find("select id from user where user_name=%s", [email])
    for picture in pictures:
        basepath = os.path.dirname(__file__)
        basepath = basepath.replace('\\', '/')
        print(basepath)
        path = basepath + '/static/' + secure_filename(picture.filename)
        print(path)
        picture.save(path)
        url = upload_picture(path)
        uid = uuid.uuid1()
        db.insert("picture", uid, 3, id1[0][0], url)
        if j == 1:
            picture2 = picture
        j += 1
    uid1 = uuid.uuid1()
    time1 = time.time()
    db.insert("posts", uid1, email, title, detail, 0, 0, time1, picture2)
    return jsonify({
            "data": {"user_name": "", "user_nick": ""},
            "message": "success",
            "code": 200
        })


# 相关景点陈列
@app.route('/food/<uid>/related_sites')
@login_limit
def related_sites(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select name,mainPicture from attraction where target=%s", [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 相关店铺陈列
@app.route('/food/<uid>/related_stores')
@login_limit
def related_stores(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select name,main_picture from store where target=%s", [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


#  美食详情、历史
@app.route('/food/<uid>/detail')
@login_limit
def food_detail(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select detail,history from food where id=%s", [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 美食做法
@app.route('/food/<uid>/practice')
@login_limit
def food_practice(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select practice,ingredients from food where id=%s", [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 美食列表
@app.route('/<address>/food')
@login_limit
def food_list(address):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select name,main_picture,grade from food where address=%s", [address])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 店铺详情
@app.route('/store/<uid>')
@login_limit
def store_detail(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select name,detail,connect,adress,grade,work_time from store where id=%s", [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 特色菜接口
@app.route('/store/<uid>/food')
@login_limit
def store_food(uid):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select name,url,price from store_food where target=%s", [uid])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 查看小瓶子
@app.route('/<email>/check_bottle')
@login_limit
def check_bottle(email):
    db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
    tuple1 = db.find("select type,degree from bottle where user_name=%s", [email])
    collect = list(tuple1)
    j = 0
    for i in collect:
        collect[j] = list(i)
        j += 1
    return jsonify({
        "data": collect,
        "message": "success",
        "code": 200
    })


# 设置小瓶子
@app.route('/<email>/set_bottle', methods=['POST'])
@login_limit
def set_bottle(email):
    if request.method == 'POST':
        db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
        list1 = request.files.getlist('bottle')
        for i in list1:
            db.insert("bottle", i["type"], i["degree"], email)
        return jsonify({
            "data": {"user_name": "", "user_nick": ""},
            "message": "success",
            "code": 200
        })


if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 8888), app)
    server.serve_forever()
