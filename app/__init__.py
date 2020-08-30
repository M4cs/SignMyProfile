from flask import Flask, request, jsonify, make_response, Response, redirect, render_template
from flask_mongoengine import MongoEngine
import requests
import json
from datetime import datetime
import pytz
import time
from flask_restful import reqparse

SCOPES = 'read:user'


mongo = MongoEngine()

def create_app():
    app = Flask(__name__)
    with open('config.json', 'r+') as f:
        config = json.load(f)
        app.config['MONGODB_SETTINGS'] = {'db': 'smp_db', 'host': config['MONGO_URI'], 'connect': False}
        app.config['PROPOGATE_EXCEPTIONS'] = True
        app.config['GH_CLIENT_ID'] = config['GH_CLIENT_ID']
        app.config['GH_SECRET_KEY'] = config['GH_SECRET_KEY']
        # TODO: CHANGE THIS!!!!!!!!!!!!!!!!!!!!
        app.config['SECRET_KEY'] = 'FILLER_FOR_PRE_PRODUCTION'
    mongo.init_app(app)
    return app

app = create_app()

def callback_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('code')
    return parser

TEMPLATE = '''\
            <div class="box">
                <article class="media">
                    <div class="media-left">
                        <figure class="image is-64x64">
                            <img src="{user_image}" alt="Image">
                        </figure>
                    </div>
                    <div class="media-content">
                        <div class="content">
                            <p>
                                <strong>{display_name}</strong><br><small>@{username}</small><br><small>{time}</small>
                            </p>
                        </div>
                    </div>
                </article>
            </div>
'''

@app.route('/card/<target>')
def card(target):
    from app.models import User
    api = 'https://img.shields.io/badge/Sign%20My%20Profile-{amt}%20People%20Have-red'
    u = User.objects(gh_id=target).first()
    if u:
        if u.signature_count == 1:
            api = api.replace('%20Person%20Has', '%20People%20Have')
        return redirect(api.format(amt=u.signature_count), 302)
    else:
        return 404

@app.route('/callback')
def callback():
    from app.models import User, Signatures
    parser = callback_parser()
    args = parser.parse_args()
    res = requests.post('https://github.com/login/oauth/access_token', data={
        'client_id': app.config['GH_CLIENT_ID'],
        'client_secret': app.config['GH_SECRET_KEY'],
        'code': args['code']
    })
    res_obj = str(res.content)
    rspl = res_obj.split('&')
    rspl = rspl[0].split('=')
    at = rspl[1]
    res = requests.get('https://api.github.com/user', headers={'Authorization': 'Bearer ' + at, 'accept': 'application/vnd.github.v3+json'})
    user_obj = json.loads(res.content)
    gh_id = user_obj['id']
    user = User.objects(gh_id=gh_id).first()
    if not user:
        new_user_obj = {
            'gh_id': gh_id,
            'username': user_obj['login'],
            'display_name': user_obj['name'],
            'avatar_url': user_obj['avatar_url'],
            'github_oauth': at
        }
        new_user = User(**new_user_obj)
        if new_user.save():
            if request.cookies.get('loginandsigntarget'):
                res = make_response(redirect('http://localhost:5000/sign/' + request.cookies.get('loginandsigntarget'), 302))
                res.set_cookie('loginandsigntarget', '', 0)
                return res
            res = make_response(redirect('http://localhost:5000/'))
            res.set_cookie('auth_token', new_user.github_oauth)
            return res
    else:
        res = make_response(redirect('http://localhost:5000/'))
        res.set_cookie('auth_token', user.github_oauth, 3600)
        if request.cookies.get('loginandsigntarget'):
                res = make_response(redirect('http://localhost:5000/sign/' + request.cookies.get('loginandsigntarget'), 302))
                res.set_cookie('auth_token', user.github_oauth, 3600)
                res.set_cookie('loginandsigntarget', '', 0)
                return res
        return res

@app.route('/sign/<target>')
def sign(target):
    from app.models import Signatures, User
    if request.cookies.get('auth_token'):
        user = User.objects(github_oauth=request.cookies.get('auth_token')).first()
        if user:
            tar = User.objects(gh_id=target).first()
            if tar:
                sig = Signatures.objects(target=tar.id, signee=user.id).first()
                if not sig:
                    new_sig = {
                        'target': tar.id,
                        'signee': user.id,
                        'time': time.time()
                    }
                    sign = Signatures(**new_sig)
                    if sign.save():
                        user.signature_count += 1
                        user.save()
                        return redirect('https://github.com/' + tar.username, 302)
        return redirect('http://localhost:5000/')
    else:
        return redirect('http://localhost:5000/loginandsign/' + target, 302)

@app.route('/loginandsign/<target>')
def loginandsign(target):
    if request.cookies.get('loginandsigntarget'):
        res = make_response(redirect('http://localhost:5000/loginandsign/' + target, 302))
        res.set_cookie('loginandsigntarget', '', 0)
        return res
    res = make_response(redirect('https://github.com/login/oauth/authorize?scope=read:user&client_id=0ea3c43634a76b9a4b7f', 302))
    res.set_cookie('loginandsigntarget', target, 3600)
    return res


@app.route('/')
def index():
    from app.models import User, Signatures
    if request.cookies.get('auth_token'):
        user = User.objects(github_oauth=request.cookies.get('auth_token')).first()
        if user:
            res = requests.get('https://api.github.com/user', headers={'Authorization': 'Bearer ' + request.cookies.get('auth_token'), 'accept': 'application/vnd.github.v3+json'})
            if res.status_code != 200:
                resp = make_response(redirect('https://github.com/login/oauth/authorize?scope=read:user&client_id=0ea3c43634a76b9a4b7f', 301))
                resp.set_cookie('auth_token', '', 0)
                return resp, 200
            else:
                temp = ''
                user = User.objects(github_oauth=request.cookies.get('auth_token')).first()
                sigs = Signatures.objects(target=user.id).all()
                for sig in sigs:
                    st = datetime.fromtimestamp(sig.time).strftime("%Y-%m-%d %H:%M")
                    dt = datetime.strptime(st, "%Y-%m-%d %H:%M")
                    dt_utc = dt.replace(tzinfo=pytz.timezone('America/New_York'))
                    st = dt_utc.strftime("%Y-%m-%d %H:%M")
                    u = User.objects(id=sig.signee).first()
                    temp += TEMPLATE.format(username=u.username, display_name=u.display_name, user_image=u.avatar_url, time=st+" EST") + "<br>"
                badge = "https://img.shields.io/badge/Signed%20By-{amnt}%20People-red"
                if user.signature_count == 1:
                    badge = badge.replace('People', 'Person')
                print(temp)
                return render_template('index.html', username=user.username, badge=badge.format(amnt=user.signature_count), template=temp, gh_id=user.gh_id)
        else:
            res = make_response(redirect('http://localhost:5000/', 302))
            res.set_cookie('auth_token', '', 0)
            return res
    else:
        return redirect('https://github.com/login/oauth/authorize?scope=read:user&client_id=0ea3c43634a76b9a4b7f', 302)