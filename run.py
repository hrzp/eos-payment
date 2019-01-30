from apscheduler.schedulers.background import BackgroundScheduler
from flask import request, redirect, session, g, jsonify
from datetime import timedelta
from flask import Flask
import requests
import random
import atexit
import string
import json
import time
import os

import sqlalchemy.orm as saorm
import sqlalchemy.ext.declarative
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, ForeignKey, Integer, String, Float, TIMESTAMP, Boolean, Date


Base = sqlalchemy.ext.declarative.declarative_base()
db_engine = sqlalchemy.create_engine("sqlite:///myDataBase.db", echo=False, encoding='utf-8', pool_recycle=3600)
Session = saorm.sessionmaker(bind=db_engine)

# here, enter you eos account name
your_account = 'privatelight'

def _get_timestamp():
    return time.time()

# This is a simple database
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

class PaymentOrder(Base):
    __tablename__ = 'payment_order'
    id = Column(Integer, primary_key=True)
    order = Column(String(12), nullable=False, unique=True)
    state = Column(String(24), default="waiting")
    amount = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User')
    cdate = Column(Integer, default=_get_timestamp)
Base.metadata.create_all(db_engine)




def check_net_for_new_deposit():
    # in this line, we can replace our light node instance API
    # it just recive greater than 0.0003 eos
    url = 'https://eospark.com/api/account/%s/actions?action_type=token&show_trx_small=0&show_trx_in=1&show_trx_out=0&page=1&size=50' %your_account
    r = requests.get(url)
    if r.status_code != 200:
        return
    data = r.json()['data']['transactions']

    db = Session()
    orders = db.query(PaymentOrder).filter_by(state='waiting').all()
    order_list = [order.order for order in orders]

    for transaction in data:
        if transaction['symbol'] != "EOS":
            continue
        if transaction['memo'] not in order_list:
            continue
        order = db.query(PaymentOrder).filter_by(order=transaction['memo']).first()
        order.state = 'paid'
        order.amount = float(transaction['quantity'])
        db.commit()
        # Here, you can charge you user asset in your main database
        # you can find the user id by this code `order.user_id`
    db.close()


# this part of code run a cron job
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_net_for_new_deposit, trigger="interval", seconds=7)
atexit.register(lambda: scheduler.shutdown())


# This is my api routes
app = Flask(__name__)

app.secret_key = os.urandom(24)


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    g.db_session = Session()

@app.teardown_request
def teardown_request(exception):
    db_session = getattr(g, 'db_session', None)
    if db_session is not None:
        db_session.close()

@app.route("/")
def index():
    return redirect("static/index.html")

@app.route("/login", methods=['POST'])
def login():
    data = json.loads(request.data)
    username = data['username']
    password = data['password']
    u = g.db_session.query(User).filter_by(username=username, password=password).first()
    if u == None:
        return jsonify({'data': 'wrong user or password'}), 400
    session['user'] = u.id
    return jsonify({'data': 'successfuly'})

@app.route("/new_order")
def new_order():
    if session['user'] == None:
        return jsonify({'data': 'you are not loged in'}), 400
    random_order_key = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    order = PaymentOrder()
    order.order = random_order_key
    order.user_id = session['user']
    order.cdate = _get_timestamp()
    g.db_session.add(order)
    g.db_session.commit()
    data = {'address': your_account, 'memo': random_order_key}
    return jsonify(data)

@app.route("/order_state/<order>")
def order_state(order):
    res = g.db_session.query(PaymentOrder).filter_by(order=order).first()
    if res == None:
        return jsonify({'state': 'not found'})
    return jsonify({'state': res.state})

@app.route("/withdraw")
def withdraw():
    # it just can run by admin
    if session['user'] == None:
        return jsonify({'data': 'you are not loged in'}), 400
    # sign trx and send it to mainnet

if __name__ == '__main__':
    scheduler.start()
    app.run(debug=False, threaded=True)
