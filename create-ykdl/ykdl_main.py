#!/usr/bin/env python


# This is a runtime patcher
# Patch ykdl at runtime to make it provide enouth message for imchenwen
# Add support for danmaku and cookies

from __future__ import print_function
import os, sys, json, platform, io
from importlib import import_module
from os.path import expanduser


# Patch bilibase
danmaku_url = ''
from ykdl.extractors.bilibili.bilibase import BiliBase
old_bilibase_prepare = BiliBase.prepare
def bilibase_prepare(self):
    retVal = old_bilibase_prepare(self)
    global danmaku_url
    danmaku_url = 'http://comment.bilibili.com/{}.xml'.format(self.vid)
    return retVal
BiliBase.prepare = bilibase_prepare


# Patch jsonlize
from ykdl.videoinfo import VideoInfo
from ykdl.util.html import fake_headers
old_jsonlize = VideoInfo.jsonlize
def jsonlize(self):
    retVal = old_jsonlize(self)
    retVal['danmaku_url'] = danmaku_url
    if retVal['extra']['ua'] == '':
        retVal['extra']['ua'] = fake_headers['User-Agent']
    return retVal
VideoInfo.jsonlize = jsonlize


# Patch iqiyi
from ykdl.extractors.iqiyi.video import Iqiyi
from ykdl.util.html import fake_headers, get_content
from ykdl.util.match import matchall

def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def iqiyi_list_only(self):
    return 'www.iqiyi.com/lib/' in self.url

def iqiyi_prepare_list(self):
    html = get_content(self.url)
    urls = matchall(html, ['<a .*?title=".+?" .*?href="(http://www\.iqiyi\.com/v_.+?)"'])
    return remove_duplicates(urls)

Iqiyi.list_only = iqiyi_list_only
Iqiyi.prepare_list = iqiyi_prepare_list


# Run ykdl
from ykdl.common import url_to_module, alias, exclude_list
from ykdl.compact import ProxyHandler, build_opener, install_opener
from ykdl.util.match import match1
from argparse import ArgumentParser
import socket
try:
    from http.cookiejar import MozillaCookieJar
    from urllib.request import HTTPCookieProcessor
except:
    from cookielib import MozillaCookieJar
    from urllib2 import HTTPCookieProcessor

def arg_parser():
    parser = ArgumentParser(description="Ykdl for imchenwen")
    parser.add_argument('--check-support', default=False, action='store_true', help="Check if the URL is supported.")
    parser.add_argument('--http-proxy', type=str, help="set proxy HOST:PORT for http(s) transfer. default: no proxy")
    parser.add_argument('--socks-proxy', type=str, help="set socks proxy HOST:PORT. default: no proxy")
    parser.add_argument('-t', '--timeout', type=int, default=60, help="set socket timeout seconds, default 60s")
    parser.add_argument('-u', '--user-agent', type=str, help="Custom User-Agent")
    parser.add_argument('video_url', type=str, help="video url")
    return parser.parse_args()


def check_support(url):
    video_host = url.split('/')[2]
    host_list = video_host.split('.')
    if host_list[-2] in exclude_list:
        short_name = host_list[-3]
    else:
        short_name = host_list[-2]
    if short_name in alias.keys():
        short_name = alias[short_name]
    try:
        import_module('.'.join(['ykdl','extractors', short_name]))
        print('Url is supported.')
        exit(0)
    except ImportError:
        print('Url is not supported')
        exit(1)

        
def main():
    args = arg_parser()
    handlers = []
    
    if args.check_support:
        return check_support(args.video_url)

    if args.timeout:
        socket.setdefaulttimeout(args.timeout)

    if args.user_agent:
        fake_headers['User-Agent'] = args.user_agent

    if args.http_proxy:
        proxy_handler = ProxyHandler({
            'http': args.http_proxy,
            'https': args.http_proxy
        })
        handlers.append(proxy_handler)

    elif args.socks_proxy:
        try:
            import socks
            addr, port = args.socks_proxy.split(':')
            socks.set_default_proxy(socks.SOCKS5, addr, int(port))
            socket.socket = socks.socksocket
        except:
            print('Failed to set socks5 proxy. Please install PySocks.', file=sys.stderr)

    opener = build_opener(*handlers)
    install_opener(opener)

    m, u = url_to_module(args.video_url)
    info = m.parser(u)

    # Is a playlist?
    if m.list_only():
        video_list = m.prepare_list()
        result = [ {'title': match1(get_content(url), r'<title>(.+?)</title>'), 'url': url} for url in video_list ]
    else:
        result = info.jsonlize()
    print(json.dumps(result, indent=4, sort_keys=True, ensure_ascii=False))

if __name__ == '__main__':
    main()
