from flask import Flask, request, jsonify, make_response, Response, redirect, render_template
from flask_mongoengine import MongoEngine
from jinja2 import Markup
import requests
import json
from datetime import datetime
import pytz
import time
from flask_restful import reqparse
import uuid

TEMPLATE = '''\
            <a href="https://github.com/{username}" target="_blank">
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
            </a>
'''

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

def badge_parser():
    parser = reqparse.RequestParser()
    parser.add_argument('target')
    return parser

@app.route('/')
def index():
    if request.cookies.get('auth_token'):
        return redirect('https://smp.maxbridgland.com/home')
    else:
        return render_template('main.html')

@app.route('/callback')
def callback():
    from app.models import User
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
    access_token = rspl[1]
    user_res = requests.get('https://api.github.com/user', headers={'Authorization': 'Bearer ' + access_token, 'accept': 'application/vnd.github.v3+json'}).json()
    gh_id = user_res['id']
    user = User.objects(gh_id=gh_id).first()
    if not user:
        new_user_obj = {
            'gh_id': gh_id,
            'username': Markup.escape(user_obj['login']),
            'display_name': Markup.escape(user_obj['name']),
            'avatar_url': user_obj['avatar_url'],
            'github_oauth': at
        }
        new_user = User(**new_user_obj)
        if request.cookies.get('loginandsign'):
            res = make_response(redirect('https://smp.maxbridgland.com/sign/' + request.cookies.get('loginandsigntarget')))
            res.set_cookie('loginandsigntarget', '', 0)
            return res
        else:
            res = make_response(redirect('https://smp.maxbridgland.com/home'))
            res.set_cookie('auth_token', new_user.github_oauth, 3600)
            return res
    else:
        user.github_oauth = access_token
        user.save()
        res = make_response(redirect('https://smp.maxbridgland.com/home'))
        res.set_cookie('auth_token', user.github_oauth, 3600)
        return res

@app.route('/home')
def home():
    from app.models import User, Signatures
    if request.cookies.get('auth_token'):
        user = User.objects(github_oauth=request.cookies.get('auth_token')).first()
        if user:
            r = requests.get('https://api.github.com/user', headers={'Authorization': 'Bearer ' + user.github_oauth, 'accept': 'application/vnd.github.v3+json'})
            if r.status_code != 200:
                resp = make_response(redirect('https://github.com/login/oauth/authorize?scope=read:user&client_id=0ea3c43634a76b9a4b7f'))
                resp.set_cookie('auth_token', '', 0)
                return resp
            temp = ''
            user = User.objects(github_oauth=request.cookies.get('auth_token')).first()
            sigs = Signatures.objects(target=user.id).all()
            for sig in sigs:
                st = datetime.fromtimestamp(sig.time).strftime("%Y-%m-%d %H:%M")
                dt = datetime.strptime(st, "%Y-%m-%d %H:%M")
                dt_utc = dt.replace(tzinfo=pytz.timezone('America/New_York'))
                st = dt_utc.strftime("%Y-%m-%d %H:%M")
                u = User.objects(id=sig.signee).first()
                temp += TEMPLATE.format(username=Markup(u.username), display_name=Markup(u.display_name), user_image=u.avatar_url, time=st+" EST") + "<br>"
            temp2 = ''
            sigs2 = Signatures.objects(signee=user.id).all()
            for sig in sigs2:
                st = datetime.fromtimestamp(sig.time).strftime("%Y-%m-%d %H:%M")
                dt = datetime.strptime(st, "%Y-%m-%d %H:%M")
                dt_utc = dt.replace(tzinfo=pytz.timezone('America/New_York'))
                st = dt_utc.strftime("%Y-%m-%d %H:%M")
                u = User.objects(id=sig.target).first()
                temp2 += TEMPLATE.format(username=Markup(u.username), display_name=Markup(u.display_name), user_image=u.avatar_url, time=st+" EST") + "<br>"
            if user.signature_count == 1:
                badge = badge.replace('People', 'Person')
            return render_template('index.html', username=user.username, template=temp, gh_id=user.gh_id, template_again=temp2)
        else:
            res = make_response(redirect('https://smp.maxbridgland.com/'))
            res.set_cookie('auth_token', '', 0)
            return res
    else:
        return redirect('https://smp.maxbridgland.com/')

@app.route('/sign/<target>')
def sign(target):
    from app.models import Signatures, User
    if request.cookies.get('auth_token'):
        user = User.objects(github_oauth=request.cookies.get('auth_token')).first()
        if user:
            tar = User.objects(gh_id=target).first()
            if tar:
                if tar != user:
                    sig = Signatures.objects(target=tar.id, signee=user.id).first()
                    if not sig:
                        new_sig = {
                            'target': tar.id,
                            'signee': user.id,
                            'time': time.time()
                        }
                        sign = Signatures(**new_sig)
                        sign.save()
                        tar.signature_count += 1
                        tar.save()
                        return redirect('https://github.com/' + tar.username, 302)
                else:
                    return redirect('https://github.com/' + tar.username)
        return redirect('https://smp.maxbridgland.com/')
    else:
        return redirect('https://smp.maxbridgland.com/loginandsign/' + target, 302)

@app.route('/loginandsign/<target>')
def loginandsign(target):
    if request.cookies.get('loginandsigntarget'):
        res = make_response(redirect('https://smp.maxbridgland.com/loginandsign/' + target, 302))
        res.set_cookie('loginandsigntarget', '', 0)
        return res
    res = make_response(redirect('https://github.com/login/oauth/authorize?scope=read:user&client_id=0ea3c43634a76b9a4b7f', 302))
    res.set_cookie('loginandsigntarget', target, 3600)
    return res

@app.route('/redir/<amt>')
def img_redir(amt):
    if amt == 1:
        api = 'https://img.shields.io/badge/Sign%20My%20Profile-{}%20Person%20Has-red'.format(amt)
    else:
        api = 'https://img.shields.io/badge/Sign%20My%20Profile-{}%20People%20Have-red'.format(amt)
    r = requests.get(api).content
    res = Response(r, mimetype='image/svg+xml', headers={'Expires': 100})
    return res, 200

@app.route('/badge')
def card():
    parser = badge_parser()
    args = parser.parse_args()
    target = args['target']
    from app.models import User
    u = User.objects(gh_id=target).first()
    if u:
        amt = u.signature_count
        return redirect('https://smp.maxbridgland.com/redir/' + str(amt) + '?__random=' + str(uuid.uuid4()))
    else:
        return 404