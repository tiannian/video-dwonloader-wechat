from flask import Flask
from flask import request
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from wechatpy import parse_message
from wechatpy.replies import TextReply
import re
from url_loader import UrlLoader

app = Flask(__name__)
url_loader = UrlLoader("./urls.conf")
queue = []
increased_id = 0

@app.route('/wechat', methods=['GET'])
def get_wechat():
    signature = request.args['signature']
    timestamp = request.args['timestamp']
    echostr = request.args['echostr']
    nonce = request.args['nonce']
    token = 'abcdefgh'
    try:
        check_signature(token, signature, timestamp, nonce)
        return echostr
    except InvalidSignatureException:
        return 'error'

def is_url(url):
    reg = r'[a-zA-z]+://[^\s]*'
    return re.match(reg, url) != None

def do_url(msg):
    global increased_id
    url = msg.content
    if url_loader.match(url):
        queue.append({
            'url': url,
            'userid': msg.source,
            })
        increased_id = increased_id + 1
        reply = TextReply(message=msg)
        reply.content = "任务%d已创建....." % (increased_id)
        return reply.render()
    else:
        reply = TextReply(message=msg)
        reply.content = "i dont support this url"
        return reply.render()


def do_error(msg):
    reply = TextReply(message=msg)
    reply.content = "本公众号...."
    return reply.render()

@app.route('/tasks', methods=['GET'])
def list_tasks():
    return {
        'status': 0,
        'message': "success",
        'total': increased_id,
        'data': queue
        }

@app.route('/tasks/pop', methods=['POST'])
def pop_task():
    global queue
    if len(queue) == 0:
        return {
            'status': -1,
            'message': 'queue empty'
        }
    else:
        return {
            'status': 0,
            'message': "success",
            'data': queue.pop()
        }


@app.route('/wechat', methods=['POST'])
def post_wechat():
    msg = parse_message(request.data)
    print(msg.content)
    if is_url(msg.content):
        return do_url(msg)
    else:
        return do_error(msg)
