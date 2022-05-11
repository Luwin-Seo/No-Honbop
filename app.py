from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'HONBOP'

import certifi

ca = certifi.where()
client = MongoClient('mongodb+srv://test:sparta@cluster0.wyhls.mongodb.net/cluster0?retryWrites=true&w=majority')
db = client.dbsparta


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        user_info = db.users.find_one({"id": payload["id"]})
        posts = list(db.posts.find({}))
        return render_template('index.html', user_info=user_info, posts=posts)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/postpop')
def postin():
    return render_template('posting_card.html')

@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        user_info = db.users.find_one({"id": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/detail/<post_id>')
def detail(post_id):
    # 게시글 상세 정보를 볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        post = db.posts.find_one({"post_id": int(post_id)})
        comments = list(db.comments.find({'post_id': post_id}))
        likes = db.likes.count_documents({"post_id": post_id})
        party = db.party.count_documents({"post_id": post_id})

        return render_template('detail.html', 
            likes=likes, post=post, comments=comments, post_id=post_id, party=party)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
    
# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': username_receive, 'pw': pw_hash})
    # db에 저장 될 때 키 값 db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'manner': 0}) 그래서 찾을 때 id,pw도 찾음

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    # 회원가입
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.users.insert_one({'id': id_receive, 'pw': pw_hash})

    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"id": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 프로필 업데이트
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        writer_info = db.users.find_one({'id': payload['id']}, {'_id': 0})
        # 포스팅하기
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        title_receive = request.form['title_give']
        place_receive = request.form['place_give']
        address_receive = request.form['address_give']
        desc_receive = request.form['desc_give']
        tag_receive = request.form['tag_give']
        url_receive = request.form['url_give']
        payment_receive = request.form['payment_give']
        datenow_receive = request.form['datenow_give']
        date_receive = request.form['date_give']
        time_receive = request.form['time_give']
        maxcount_receice = request.form['maxcount_give']
        all_posts = list(db.posts.find({}, {'_id': False}))
        count = len(all_posts) + 1

        doc = {
            'post_id': count,
            'title': title_receive,
            'place': place_receive,
            'desc': desc_receive,
            'tag': tag_receive,
            'url': url_receive,
            'address': address_receive,
            'payment': payment_receive,
            'user_id': payload['id'],
            'datenow': datenow_receive,
            'date': date_receive,
            'time': time_receive,
            'maxcount': maxcount_receice,
            'user_count': 0,
            'like': 0
        }

        db.posts.insert_one(doc)

        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/get_posts", methods=['GET'])
def get_posts():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        #포스팅 목록 받아오기
        posts = list(db.posts.find({})).sort("date", -1)
        for post in posts:
            post["_id"] = str(post["_id"])

        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts":posts })
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/detail/like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 좋아요 수 변경
        user_id = db.users.find_one({"id": payload["id"]})["id"]
        post_id = request.form["post_id"]
        
        doc = {
            "post_id": post_id,
            "user_id": user_id
        }
        
        if db.likes.find_one(doc):
            db.likes.delete_one(doc)
        else:
            db.likes.insert_one(doc)
        
        return redirect(post_id)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/detail/parti', methods=['POST'])
def participate():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 포스팅하기
        user_id = db.users.find_one({"id": payload["id"]})["id"]
        post_id = request.form["post_id"]
        
        doc = {
            "post_id": post_id,
            "user_id": user_id
        }
        
        if db.party.find_one(doc):
            db.party.delete_one(doc)
        else:
            db.party.insert_one(doc)
        
        return redirect(post_id)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/detail/write', methods=['POST'])
def write_comment():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        comment = request.form['comment']
        post_id = request.form['post_id']
        index = db.counts.find_one_and_update({ 'name': 'comment' }, { '$inc': { 'count': 1 } })
        
        db.comments.insert_one({
          'index': index['count'] + 1,
          'post_id': post_id,
          'user_id': payload["id"],
          'comment': comment
        })
        
        return redirect(post_id)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))

@app.route('/detail/delete', methods=['POST'])
def delete_comment():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        post_id = request.form['post_id']
        
        db.comments.delete_many({
          'index' : int(request.form['index']),
          'user_id': payload['id']
        })
        
        return redirect(post_id)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
