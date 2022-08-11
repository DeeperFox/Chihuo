from functools import wraps
from flask import request,jsonify,current_app
from error import forbidden,unauthorized
from authlib.jose import jwt, JoseError
from sql import DbMysql


def generate_token(user, role):
    """生成用于邮箱验证的JWT（json web token）"""
    # 签名算法
    header = {'alg': 'HS256'}
    # 用于签名的密钥
    key = current_app.config['SECRET_KEY']
    # 待签名的数据负载
    data = {'user': user, 'role': role}

    return jwt.encode(header=header, payload=data, key=key)


def validate_token(token):
    """用于验证用户注册和用户修改密码或邮箱的token, 并完成相应的确认操作"""
    key = current_app.config['SECRET_KEY']

    try:
        data = jwt.decode(token, key)
    except JoseError:
        return {}
    ... # 其他字段确认
    return data


# 登录限制的装饰器
def login_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 在请求头上拿到token
            token = request.headers["Authorization"]
        except Exception:
            return unauthorized("没有附带请求头")
        try:
            t = validate_token(token.encode("utf-8"))
        except Exception:
            return forbidden("未登录或者登录已过期")
        if t:
            db = DbMysql(host="localhost", port=3306, user="root", passwd="123456", database="fdtp", charset="utf8")
            str1 = db.find("select * from user where user_name= %s", t['user'])
            if str1:
                return func(*args, **kwargs)
            else: return forbidden("未找到对应账号")
        return unauthorized("没有附带请求头")

    return wrapper