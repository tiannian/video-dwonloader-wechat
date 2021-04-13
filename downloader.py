import requests
import time
from wechatpy import WeChatClient
import os
import json
import tempfile
import uuid as uu

TARGET_SIZE = 104857600

class Downloader:
    def __init__(self, pop_url, appid, secret):
        self.pop_url = pop_url
        self.wechat = WeChatClient(appid, secret)
        self.sleep_time = 3

    def loop(self):
        try:
            r = requests.post(self.pop_url)
            if r.status_code != 200:
                time.sleep(self.sleep_time)
                return
            content = r.json()
            if content['status'] != 0:
                time.sleep(self.sleep_time)
                return
            print("begin download. %s" % (content['data']['url']))
            event = content['data']
            self.is_downloadable(event)
        except e:
            print(e)
            time.sleep(self.sleep_time)

    def download(self, stream, event, name):
        url = event['url']
        tag = stream['tag']
        size = stream['size'] / 1024 / 1024
        quality = stream['quality'] if 'quality' in stream else '未知'

        suffix = 'mp4'
        if stream['container'] == 'flv':
            suffix = 'flv'
        
        message='下载的视频名：\n《%s》\n允许下载的大小为：%.2fM\n分辨率为：%s\n开始下载' % (name, size, quality)
        self.wechat.message.send_text(event['userid'], message)

        path = './temp'

        uuid = uu.uuid5(uu.NAMESPACE_OID, name)

        full_path = '%s/%s' % (path, uuid)
        print(full_path)
        command = ''
        print(tag)
        if tag == '__default__':
            command = 'you-get %s -O %s' % (url, full_path)
        else:
            command = 'you-get --format=%s %s -O %s' % (tag, url, full_path)
        status = ''
        if os.system(command) == 0:
            status = '下载成功'
        else:
            status = '下载失败'
        message='视频：\n《%s》\n%s' % (name, status)
        self.wechat.message.send_text(event['userid'], message)

        command = './bin/ossutil64 cp -u %s.%s oss://tiannian-aivideo/' % (full_path, suffix)
        print(command)
        download_path = 'http://aivideo.assets.top-net.top/%s.%s' % (uuid, suffix)
        if os.system(command) == 0:
            message='视频：\n《%s》上传成功\n请使用如下链接下载，有效期1小时' % (name)
            self.wechat.message.send_text(event['userid'], message)
            self.wechat.message.send_text(event['userid'], download_path)
            
        else:
            message='视频：\n《%s》上传失败，请重新下载' % (name)
            self.wechat.message.send_text(event['userid'], message)

    def is_downloadable(self, event):
        command = "you-get --json %s" % (event['url'])
        f = os.popen(command)
        # TODO: catah json parse error.
        info = json.load(f)

        name = info['title']
        size = 0.0
        quality = '未知'
        status = ''

        flag = False
        
        streams = info['streams']

        if len(streams) == 1 and '__default__' in streams:
            stream = streams['__default__']
            size = stream['size'] / 1024 / 1024
            if stream['size'] <= TARGET_SIZE:
                status = '开始下载'
                stream['tag'] = '__default__'
                self.download(stream, event, name)
            else:
                status = '文件大小大于100M，无法下载'
                flag = True
        elif len(streams) > 1:
            streams_list = []
            for k, v in streams.items():
                v['tag'] = k
                streams_list.append(v)

            selected_stream = []

            for stream in streams_list:
                stream['difference'] = TARGET_SIZE - stream['size']
                if stream['difference'] > 0:
                    selected_stream.append(stream)
            if len(selected_stream) >= 1:
                selected_stream.sort(key = lambda stream: stream['difference'])
                
                target_stream = selected_stream[0]
                size = target_stream['size'] / 1024 / 1024
                quality = target_stream['quality'] or quality
                status = '开始下载'
                self.download(target_stream, event, name)
            else:
                status = '文件大小大于100M，无法下载'
                flag = True
        else:
            status = '解析失败'
            flag = True
        if flag:
            message='下载的视频名：\n《%s》\n允许下载的大小为：%.2fM\n分辨率为：%s\n%s' % (name, size, quality, status)
            self.wechat.message.send_text(event['userid'], message)


if __name__ == '__main__':
    downloader = Downloader("http://localhost:8000/tasks/pop", 'wx5a3dbaf21ec95f39', '4c3e8320e3ea6b5b3a1d4878b40664d7')
    while True:
        downloader.loop()
    #  downloader.is_downloadable("https://www.bilibili.com/video/BV1nb4y1D78j")

