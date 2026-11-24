#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RulePilot v3.2.0 (Public Edition)
跨平台智能分流、域名扫描与零杀热重载配置助手（支持多语言，面向旅居中国大陆与多网络环境用户）
- 零隐私残留公共版：自动适配 FlClash（含衍生版）/ Clash Verge Rev / Mihomo Party / Clash Meta
- 零杀热重载内核：支持通过 Mihomo Controller API (PUT /configs) 50ms 热刷新，绝不强杀正在运行的客户端进程
- 三大零门槛扫描器：实时连接与本机 DNS 缓存抓域 / 粘贴文本提取 / 本机常用内地软件扫描，自动归并一级域名 (eTLD+1)
- 自由增删与直连/出口策略一键互切，支持规则导入导出、桌面微窗模式与纯净分发包打包
"""

import os
import sys
import json
import re
import time
import socket
import shutil
import sqlite3
import zipfile
import secrets
import platform
import argparse
import ipaddress
import urllib.parse
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import subprocess

# 无控制台环境下防止 print 报错
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass

VERSION = "3.2.0"
EDITION = "Public"
FLCLASH_SCRIPT_ID = 900000000000000001
FLCLASH_SCRIPT_LABEL = "RulePilot 智能分流与内地直连保护"
MARKER_START = "# === RULE_PILOT_CUSTOM_RULES_START ==="
MARKER_END = "# === RULE_PILOT_CUSTOM_RULES_END ==="

# 墨色单色品牌图标（对齐 One UI Design System v2.0）
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<rect width="24" height="24" rx="6" fill="#17171a"/>'
    '<polygon points="13 4 5 14 12 14 11 20 19 10 12 10 13 4" '
    'fill="none" stroke="#ffffff" stroke-width="1.75" stroke-linejoin="round"/>'
    '</svg>'
)

# ========================= 常见双段公共后缀 (eTLD+1) =========================
MULTI_PART_TLDS = {
    "com.cn", "net.cn", "org.cn", "gov.cn", "edu.cn", "ac.cn", "mil.cn",
    "bj.cn", "sh.cn", "gd.cn", "zj.cn", "js.cn", "sc.cn", "hb.cn", "hn.cn",
    "co.uk", "org.uk", "ac.uk", "gov.uk",
    "co.jp", "ne.jp", "or.jp", "ac.jp", "go.jp",
    "com.hk", "org.hk", "edu.hk", "gov.hk", "net.hk",
    "com.tw", "org.tw", "edu.tw", "gov.tw", "net.tw",
    "com.sg", "com.au", "net.au", "org.au", "com.br", "co.kr", "or.kr",
    "co.in", "com.my", "com.vn", "co.nz", "co.za", "com.mx", "com.tr",
}

# ========================= 常见域名中文识别词典 =========================
KNOWN_DOMAIN_CATALOG = {
    # 抖音 / 字节 / 火山引擎
    "douyin.com": ("抖音", "cn"),
    "douyincdn.com": ("抖音推流 / CDN", "cn"),
    "douyinliving.com": ("抖音直播", "cn"),
    "douyinpic.com": ("抖音图片 CDN", "cn"),
    "douyinvod.com": ("抖音点播 CDN", "cn"),
    "douyinstatic.com": ("抖音静态资源", "cn"),
    "iesdouyin.com": ("抖音接口", "cn"),
    "bytedance.com": ("字节跳动", "cn"),
    "byteimg.com": ("字节图片 CDN", "cn"),
    "bytegoofy.com": ("字节静态资源", "cn"),
    "bytetos.com": ("字节对象存储", "cn"),
    "bytecdn.cn": ("字节 CDN", "cn"),
    "bytefcdnrd.com": ("字节直播 CDN", "cn"),
    "bytegecko.com": ("字节资源服务", "cn"),
    "snssdk.com": ("字节 SDK / 信令", "cn"),
    "amemv.com": ("抖音信令", "cn"),
    "pstatp.com": ("字节媒体 CDN", "cn"),
    "zijieapi.com": ("字节 API", "cn"),
    "volcengine.com": ("火山引擎", "cn"),
    "volccdn.com": ("火山引擎 CDN", "cn"),
    "volcvideo.com": ("火山视频云", "cn"),
    "volces.com": ("火山引擎服务", "cn"),
    "ixigua.com": ("西瓜视频", "cn"),
    "toutiao.com": ("今日头条", "cn"),
    "feishu.cn": ("飞书", "cn"),
    "feishucdn.com": ("飞书 CDN", "cn"),
    "doubao.com": ("豆包", "cn"),
    "jianying.com": ("剪映", "cn"),
    # 腾讯 / QQ / 微信 / 视频号 / 腾讯云
    "qq.com": ("腾讯 / QQ / 微信服务", "cn"),
    "wechat.com": ("微信", "cn"),
    "weixin.com": ("微信", "cn"),
    "servicewechat.com": ("微信小程序 / 视频号", "cn"),
    "weixinbridge.com": ("微信桥接服务", "cn"),
    "tenpay.com": ("微信支付 / 财付通", "cn"),
    "qpic.cn": ("腾讯媒体 CDN", "cn"),
    "qlogo.cn": ("腾讯头像 CDN", "cn"),
    "gtimg.com": ("腾讯静态资源", "cn"),
    "tencent.com": ("腾讯", "cn"),
    "qcloud.com": ("腾讯云", "cn"),
    "myqcloud.com": ("腾讯云 COS / 直播", "cn"),
    "qcloudcdn.com": ("腾讯云 CDN", "cn"),
    "tencentyun.com": ("腾讯云服务", "cn"),
    "tencent-cloud.net": ("腾讯云网络", "cn"),
    "tlivepush.com": ("微信视频号 / 腾讯云推流", "cn"),
    "tliveplay.com": ("微信视频号 / 腾讯云拉流", "cn"),
    "cdntips.net": ("腾讯云 CDN 调度", "cn"),
    "tdnsv6.com": ("腾讯智能 DNS / CDN", "cn"),
    "wegame.com.cn": ("腾讯 WeGame", "cn"),
    "anticheatexpert.com": ("腾讯安全组件", "cn"),
    "myapp.com": ("腾讯应用宝", "cn"),
    # B站
    "bilibili.com": ("哔哩哔哩 (B站)", "cn"),
    "bilivideo.com": ("B站直播推流 / 视频上传", "cn"),
    "bilivideo.cn": ("B站视频 CDN", "cn"),
    "bilivideo.net": ("B站视频 CDN", "cn"),
    "biliapi.net": ("B站直播 API", "cn"),
    "biliapi.com": ("B站 API", "cn"),
    "hdslb.com": ("B站静态资源", "cn"),
    "acgvideo.com": ("B站媒体服务", "cn"),
    "b23.tv": ("B站短链", "cn"),
    "biligame.com": ("B站游戏", "cn"),
    # 快手 / 小红书 / 虎牙 / 斗鱼
    "kuaishou.com": ("快手", "cn"),
    "kwaicdn.com": ("快手推流 / CDN", "cn"),
    "kwimgs.com": ("快手媒体", "cn"),
    "yximgs.com": ("快手推流 / 媒体", "cn"),
    "gifshow.com": ("快手 API", "cn"),
    "chenzhongtech.com": ("快手服务", "cn"),
    "kwaizt.com": ("快手推流调度", "cn"),
    "xiaohongshu.com": ("小红书", "cn"),
    "xhscdn.com": ("小红书 CDN / 推流", "cn"),
    "xhscdn.net": ("小红书 CDN", "cn"),
    "xhslink.com": ("小红书短链", "cn"),
    "fengkongcloud.com": ("小红书风控服务", "cn"),
    "huya.com": ("虎牙直播", "cn"),
    "msstatic.com": ("虎牙推流 / 静态", "cn"),
    "douyu.com": ("斗鱼直播", "cn"),
    "douyucdn.cn": ("斗鱼推流 CDN", "cn"),
    "yy.com": ("YY 直播", "cn"),
    # 搜索 / 阿里 / 百度 / 夸克 / 网盘 / 常用内地服务
    "bing.com": ("Bing 必应搜索", "cn"),
    "bing.net": ("Bing 静态资源", "cn"),
    "baidu.com": ("百度", "cn"),
    "bdstatic.com": ("百度静态资源", "cn"),
    "baidupcs.com": ("百度网盘传输", "cn"),
    "bcebos.com": ("百度云存储", "cn"),
    "quark.cn": ("夸克网盘", "cn"),
    "uc.cn": ("UC / 夸克存储", "cn"),
    "alipan.com": ("阿里云盘", "cn"),
    "aliyundrive.com": ("阿里云盘", "cn"),
    "aliyun.com": ("阿里云", "cn"),
    "aliyuncs.com": ("阿里云 OSS / 视频云", "cn"),
    "alivecdn.com": ("阿里云直播推流", "cn"),
    "alicdn.com": ("阿里 CDN", "cn"),
    "taobao.com": ("淘宝", "cn"),
    "tmall.com": ("天猫", "cn"),
    "alipay.com": ("支付宝", "cn"),
    "jd.com": ("京东", "cn"),
    "360buyimg.com": ("京东图片 CDN", "cn"),
    "zhihu.com": ("知乎", "cn"),
    "zhimg.com": ("知乎图片 CDN", "cn"),
    "weibo.com": ("微博", "cn"),
    "163.com": ("网易", "cn"),
    "126.net": ("网易媒体", "cn"),
    "netease.com": ("网易服务", "cn"),
    "wps.cn": ("WPS 办公", "cn"),
    "kdocs.cn": ("金山文档", "cn"),
    "dingtalk.com": ("钉钉", "cn"),
    "xunlei.com": ("迅雷", "cn"),
    "huaweicloud.com": ("华为云", "cn"),
    "qiniup.com": ("七牛云上传", "cn"),
    "wscdns.com": ("网宿 CDN", "cn"),
    "ksyun.com": ("金山云", "cn"),
    # 常见国际服务（保留常规出口）
    "google.com": ("Google 搜索与服务", "global"),
    "googleapis.com": ("Google API", "global"),
    "gstatic.com": ("Google 静态资源", "global"),
    "youtube.com": ("YouTube 视频与推流", "global"),
    "ytimg.com": ("YouTube 图片", "global"),
    "googlevideo.com": ("YouTube 视频流", "global"),
    "twitch.tv": ("Twitch 国际直播", "global"),
    "openai.com": ("OpenAI / ChatGPT", "global"),
    "chatgpt.com": ("ChatGPT", "global"),
    "anthropic.com": ("Anthropic / Claude", "global"),
    "claude.ai": ("Claude AI", "global"),
    "github.com": ("GitHub", "global"),
    "githubusercontent.com": ("GitHub 资源", "global"),
    "x.com": ("X (Twitter)", "global"),
    "twitter.com": ("Twitter", "global"),
    "telegram.org": ("Telegram", "global"),
    "discord.com": ("Discord", "global"),
    "tiktok.com": ("TikTok 国际版", "global"),
    "instagram.com": ("Instagram", "global"),
    "facebook.com": ("Facebook", "global"),
    "netflix.com": ("Netflix", "global"),
    "spotify.com": ("Spotify", "global"),
    "cloudflare.com": ("Cloudflare", "global"),
}

# 常见本机中国大陆 / 内地常用软件扫描目录（供“软件扫描一键直连”使用）
KNOWN_CN_APPS = [
    {"exe": "Weixin.exe", "name": "微信 (新版 4.0)", "category": "聊天与视频号"},
    {"exe": "WeChat.exe", "name": "微信", "category": "聊天与视频号"},
    {"exe": "WeChatAppEx.exe", "name": "微信小程序 / 视频号", "category": "聊天与视频号"},
    {"exe": "WXWork.exe", "name": "企业微信", "category": "内地办公"},
    {"exe": "QQ.exe", "name": "QQ 客户端", "category": "聊天社交"},
    {"exe": "TIM.exe", "name": "TIM 办公版 QQ", "category": "聊天社交"},
    {"exe": "douyin.exe", "name": "抖音桌面版", "category": "内地直播与视频"},
    {"exe": "WebcastMate.exe", "name": "抖音直播伴侣", "category": "内地推流软件"},
    {"exe": "livehime.exe", "name": "B站直播姬", "category": "内地推流软件"},
    {"exe": "bilibili.exe", "name": "哔哩哔哩客户端", "category": "内地直播与视频"},
    {"exe": "KuaishouLive.exe", "name": "快手直播伴侣", "category": "内地推流软件"},
    {"exe": "KwaiLive.exe", "name": "快手直播工具", "category": "内地推流软件"},
    {"exe": "QuarkCloudDrive.exe", "name": "夸克网盘", "category": "内地网盘"},
    {"exe": "quark.exe", "name": "夸克客户端", "category": "内地网盘"},
    {"exe": "BaiduNetdisk.exe", "name": "百度网盘", "category": "内地网盘"},
    {"exe": "BaiduNetdiskHost.exe", "name": "百度网盘传输核心", "category": "内地网盘"},
    {"exe": "aDrive.exe", "name": "阿里云盘", "category": "内地网盘"},
    {"exe": "Feishu.exe", "name": "飞书 (内地版)", "category": "内地办公"},
    {"exe": "DingTalk.exe", "name": "钉钉", "category": "内地办公"},
    {"exe": "Doubao.exe", "name": "豆包桌面版", "category": "内地 AI 工具"},
    {"exe": "JianyingPro.exe", "name": "剪映专业版", "category": "内地创作工具"},
    {"exe": "QQLive.exe", "name": "腾讯视频", "category": "内地影音"},
    {"exe": "QQMusic.exe", "name": "QQ 音乐", "category": "内地影音"},
    {"exe": "cloudmusic.exe", "name": "网易云音乐", "category": "内地影音"},
    {"exe": "Thunder.exe", "name": "迅雷", "category": "内地下载"},
    {"exe": "wps.exe", "name": "WPS Office", "category": "内地办公"},
    {"exe": "wegame.exe", "name": "腾讯 WeGame", "category": "内地游戏平台"},
]

# ========================= 预设防漏规则包 =========================
PRESET_PACKS = {
    "cn_live_streaming": {
        "name": "内地直播与推流直连",
        "desc": "覆盖抖音、微信视频号、B站、快手、小红书、虎牙、斗鱼、腾讯/阿里云直播与主流内地 CDN（不影响 YouTube / Twitch 国际推流）",
        "position": "top",
        "default": True,
        "rules": [
            ("DOMAIN-SUFFIX", "douyin.com", "DIRECT", "抖音"),
            ("DOMAIN-SUFFIX", "douyincdn.com", "DIRECT", "抖音推流/CDN"),
            ("DOMAIN-SUFFIX", "douyinliving.com", "DIRECT", "抖音直播"),
            ("DOMAIN-SUFFIX", "douyinpic.com", "DIRECT", "抖音图片"),
            ("DOMAIN-SUFFIX", "douyinvod.com", "DIRECT", "抖音点播"),
            ("DOMAIN-SUFFIX", "douyinstatic.com", "DIRECT", "抖音静态资源"),
            ("DOMAIN-SUFFIX", "iesdouyin.com", "DIRECT", "抖音接口"),
            ("DOMAIN-SUFFIX", "bytedance.com", "DIRECT", "字节跳动"),
            ("DOMAIN-SUFFIX", "byteimg.com", "DIRECT", "字节图片/CDN"),
            ("DOMAIN-SUFFIX", "bytegoofy.com", "DIRECT", "字节静态资源"),
            ("DOMAIN-SUFFIX", "bytetos.com", "DIRECT", "字节对象存储"),
            ("DOMAIN-SUFFIX", "bytecdn.cn", "DIRECT", "字节CDN"),
            ("DOMAIN-SUFFIX", "bytefcdnrd.com", "DIRECT", "字节直播CDN"),
            ("DOMAIN-SUFFIX", "bytegecko.com", "DIRECT", "字节资源"),
            ("DOMAIN-SUFFIX", "snssdk.com", "DIRECT", "字节SDK/推流信令"),
            ("DOMAIN-SUFFIX", "amemv.com", "DIRECT", "抖音信令"),
            ("DOMAIN-SUFFIX", "pstatp.com", "DIRECT", "字节媒体CDN"),
            ("DOMAIN-SUFFIX", "ecombdimg.com", "DIRECT", "抖音电商媒体"),
            ("DOMAIN-SUFFIX", "byteeffecttos.com", "DIRECT", "字节特效存储"),
            ("DOMAIN-SUFFIX", "ixigua.com", "DIRECT", "西瓜视频"),
            ("DOMAIN-SUFFIX", "toutiao.com", "DIRECT", "今日头条"),
            ("DOMAIN-SUFFIX", "volcengine.com", "DIRECT", "火山引擎"),
            ("DOMAIN-SUFFIX", "volccdn.com", "DIRECT", "火山引擎CDN/推流"),
            ("DOMAIN-SUFFIX", "volcvideo.com", "DIRECT", "火山视频云"),
            ("DOMAIN-SUFFIX", "volces.com", "DIRECT", "火山引擎服务"),
            ("DOMAIN-SUFFIX", "zijieapi.com", "DIRECT", "字节API"),
            ("DOMAIN-SUFFIX", "feishu.cn", "DIRECT", "飞书内地版"),
            ("DOMAIN-SUFFIX", "feishucdn.com", "DIRECT", "飞书CDN"),
            ("DOMAIN-SUFFIX", "tlivepush.com", "DIRECT", "腾讯云/视频号推流"),
            ("DOMAIN-SUFFIX", "tliveplay.com", "DIRECT", "腾讯云/视频号拉流"),
            ("DOMAIN-SUFFIX", "myqcloud.com", "DIRECT", "腾讯云COS/直播"),
            ("DOMAIN-SUFFIX", "qcloudcdn.com", "DIRECT", "腾讯云CDN"),
            ("DOMAIN-SUFFIX", "tencentyun.com", "DIRECT", "腾讯云服务"),
            ("DOMAIN-SUFFIX", "tencent-cloud.net", "DIRECT", "腾讯云网络"),
            ("DOMAIN-SUFFIX", "cdntips.net", "DIRECT", "腾讯云CDN调度"),
            ("DOMAIN-SUFFIX", "tdnsv6.com", "DIRECT", "腾讯DNS/CDN"),
            ("DOMAIN-SUFFIX", "weixin.qq.com", "DIRECT", "微信/视频号"),
            ("DOMAIN-SUFFIX", "wechat.com", "DIRECT", "微信"),
            ("DOMAIN-SUFFIX", "weixin.com", "DIRECT", "微信主域"),
            ("DOMAIN-SUFFIX", "weixinbridge.com", "DIRECT", "微信桥接"),
            ("DOMAIN-SUFFIX", "servicewechat.com", "DIRECT", "微信小程序/视频号"),
            ("DOMAIN-SUFFIX", "qpic.cn", "DIRECT", "腾讯媒体"),
            ("DOMAIN-SUFFIX", "qlogo.cn", "DIRECT", "腾讯头像"),
            ("DOMAIN-SUFFIX", "qq.com", "DIRECT", "腾讯/QQ"),
            ("DOMAIN-SUFFIX", "gtimg.com", "DIRECT", "腾讯静态资源"),
            ("DOMAIN-SUFFIX", "qcloud.com", "DIRECT", "腾讯云"),
            ("DOMAIN-SUFFIX", "tencent.com", "DIRECT", "腾讯"),
            ("DOMAIN-SUFFIX", "bilibili.com", "DIRECT", "B站"),
            ("DOMAIN-SUFFIX", "bilivideo.com", "DIRECT", "B站推流/视频上传"),
            ("DOMAIN-SUFFIX", "bilivideo.cn", "DIRECT", "B站视频CDN"),
            ("DOMAIN-SUFFIX", "bilivideo.net", "DIRECT", "B站视频CDN"),
            ("DOMAIN-SUFFIX", "biliapi.net", "DIRECT", "B站直播API"),
            ("DOMAIN-SUFFIX", "biliapi.com", "DIRECT", "B站API"),
            ("DOMAIN-SUFFIX", "hdslb.com", "DIRECT", "B站静态资源"),
            ("DOMAIN-SUFFIX", "acgvideo.com", "DIRECT", "B站旧版媒体"),
            ("DOMAIN-SUFFIX", "b23.tv", "DIRECT", "B站短链"),
            ("DOMAIN-SUFFIX", "biligame.com", "DIRECT", "B站游戏"),
            ("DOMAIN-SUFFIX", "biligame.net", "DIRECT", "B站游戏CDN"),
            ("DOMAIN-SUFFIX", "kuaishou.com", "DIRECT", "快手"),
            ("DOMAIN-SUFFIX", "kwaicdn.com", "DIRECT", "快手推流/CDN"),
            ("DOMAIN-SUFFIX", "kwimgs.com", "DIRECT", "快手媒体"),
            ("DOMAIN-SUFFIX", "yximgs.com", "DIRECT", "快手推流/媒体"),
            ("DOMAIN-SUFFIX", "gifshow.com", "DIRECT", "快手API"),
            ("DOMAIN-SUFFIX", "chenzhongtech.com", "DIRECT", "快手服务"),
            ("DOMAIN-SUFFIX", "kuaishouzt.com", "DIRECT", "快手服务"),
            ("DOMAIN-SUFFIX", "kwaizt.com", "DIRECT", "快手推流调度"),
            ("DOMAIN-SUFFIX", "ksapisrv.com", "DIRECT", "快手API"),
            ("DOMAIN-SUFFIX", "kspkg.com", "DIRECT", "快手包服务"),
            ("DOMAIN-SUFFIX", "xiaohongshu.com", "DIRECT", "小红书"),
            ("DOMAIN-SUFFIX", "xhscdn.com", "DIRECT", "小红书CDN/推流"),
            ("DOMAIN-SUFFIX", "xhscdn.net", "DIRECT", "小红书CDN"),
            ("DOMAIN-SUFFIX", "xhslink.com", "DIRECT", "小红书短链"),
            ("DOMAIN-SUFFIX", "fengkongcloud.com", "DIRECT", "小红书风控接口"),
            ("DOMAIN-SUFFIX", "alivecdn.com", "DIRECT", "阿里云直播推流"),
            ("DOMAIN-SUFFIX", "aliyuncs.com", "DIRECT", "阿里云OSS/视频云"),
            ("DOMAIN-SUFFIX", "aliyun.com", "DIRECT", "阿里云"),
            ("DOMAIN-SUFFIX", "alicdn.com", "DIRECT", "阿里CDN"),
            ("DOMAIN-SUFFIX", "alikunlun.com", "DIRECT", "阿里昆仑CDN"),
            ("DOMAIN-SUFFIX", "tbcdn.cn", "DIRECT", "淘宝直播CDN"),
            ("DOMAIN-SUFFIX", "huya.com", "DIRECT", "虎牙直播"),
            ("DOMAIN-SUFFIX", "msstatic.com", "DIRECT", "虎牙静态/推流"),
            ("DOMAIN-SUFFIX", "douyu.com", "DIRECT", "斗鱼直播"),
            ("DOMAIN-SUFFIX", "douyucdn.cn", "DIRECT", "斗鱼推流CDN"),
            ("DOMAIN-SUFFIX", "douyucdn2.cn", "DIRECT", "斗鱼推流CDN2"),
            ("DOMAIN-SUFFIX", "yy.com", "DIRECT", "YY直播"),
            ("DOMAIN-SUFFIX", "qiniup.com", "DIRECT", "七牛云上传"),
            ("DOMAIN-SUFFIX", "qnssl.com", "DIRECT", "七牛云CDN"),
            ("DOMAIN-SUFFIX", "qbox.me", "DIRECT", "七牛云存储"),
            ("DOMAIN-SUFFIX", "qiniucdn.com", "DIRECT", "七牛云CDN"),
            ("DOMAIN-SUFFIX", "wscdns.com", "DIRECT", "网宿推流CDN"),
            ("DOMAIN-SUFFIX", "wswebpic.com", "DIRECT", "网宿CDN"),
            ("DOMAIN-SUFFIX", "ourwebpic.com", "DIRECT", "网宿直播CDN"),
            ("DOMAIN-SUFFIX", "huaweicloud.com", "DIRECT", "华为云/OBS/直播"),
            ("DOMAIN-SUFFIX", "ksyun.com", "DIRECT", "金山云视频云"),
            ("DOMAIN-SUFFIX", "ks-cdn.com", "DIRECT", "金山云CDN"),
            ("DOMAIN-SUFFIX", "bcebos.com", "DIRECT", "百度云BOS"),
            ("DOMAIN-SUFFIX", "bdydns.com", "DIRECT", "百度云CDN"),
            ("DOMAIN-SUFFIX", "163yun.com", "DIRECT", "网易云信/直播"),
            ("DOMAIN-SUFFIX", "nosdn.127.net", "DIRECT", "网易对象存储"),
        ],
    },
    "cn_daily_apps_sites": {
        "name": "内地日常网站与应用直连",
        "desc": "覆盖 QQ、微信、Bing 必应、百度、知乎、微博、淘宝、京东、网易、豆包、剪映等，自动修正将 bing.com 误导向国际代理的问题",
        "position": "top",
        "default": True,
        "rules": [
            ("DOMAIN-SUFFIX", "bing.com", "DIRECT", "必应搜索"),
            ("DOMAIN-SUFFIX", "bing.net", "DIRECT", "必应静态资源"),
            ("DOMAIN-SUFFIX", "bingapis.com", "DIRECT", "必应接口"),
            ("DOMAIN-SUFFIX", "virtualearth.net", "DIRECT", "必应地图"),
            ("DOMAIN-SUFFIX", "baidu.com", "DIRECT", "百度"),
            ("DOMAIN-SUFFIX", "bdstatic.com", "DIRECT", "百度静态资源"),
            ("DOMAIN-SUFFIX", "bdimg.com", "DIRECT", "百度图片"),
            ("DOMAIN-SUFFIX", "baidustatic.com", "DIRECT", "百度静态"),
            ("DOMAIN-SUFFIX", "baidubce.com", "DIRECT", "百度智能云"),
            ("DOMAIN-SUFFIX", "baiduyuncdn.com", "DIRECT", "百度云CDN"),
            ("DOMAIN-SUFFIX", "hao123.com", "DIRECT", "hao123"),
            ("DOMAIN-SUFFIX", "tieba.com", "DIRECT", "百度贴吧"),
            ("DOMAIN-SUFFIX", "baifubao.com", "DIRECT", "百度支付"),
            ("DOMAIN-SUFFIX", "dwz.cn", "DIRECT", "百度短链"),
            ("DOMAIN-SUFFIX", "qqurl.com", "DIRECT", "QQ短链"),
            ("DOMAIN-SUFFIX", "qqmail.com", "DIRECT", "QQ邮箱"),
            ("DOMAIN-SUFFIX", "qzone.com", "DIRECT", "QQ空间"),
            ("DOMAIN-SUFFIX", "idqqimg.com", "DIRECT", "QQ资源"),
            ("DOMAIN-SUFFIX", "imqq.com", "DIRECT", "QQ客户端"),
            ("DOMAIN-SUFFIX", "url.cn", "DIRECT", "腾讯短链"),
            ("DOMAIN-SUFFIX", "myapp.com", "DIRECT", "腾讯应用宝"),
            ("DOMAIN-SUFFIX", "tenpay.com", "DIRECT", "微信支付/财付通"),
            ("DOMAIN-SUFFIX", "wegame.com.cn", "DIRECT", "腾讯WeGame"),
            ("DOMAIN-SUFFIX", "doubao.com", "DIRECT", "豆包"),
            ("DOMAIN-SUFFIX", "jianying.com", "DIRECT", "剪映"),
            ("DOMAIN-SUFFIX", "zhihu.com", "DIRECT", "知乎"),
            ("DOMAIN-SUFFIX", "zhimg.com", "DIRECT", "知乎图片"),
            ("DOMAIN-SUFFIX", "weibo.com", "DIRECT", "微博"),
            ("DOMAIN-SUFFIX", "weibo.cn", "DIRECT", "微博移动"),
            ("DOMAIN-SUFFIX", "sinaimg.cn", "DIRECT", "新浪图片"),
            ("DOMAIN-SUFFIX", "taobao.com", "DIRECT", "淘宝"),
            ("DOMAIN-SUFFIX", "tmall.com", "DIRECT", "天猫"),
            ("DOMAIN-SUFFIX", "alipay.com", "DIRECT", "支付宝"),
            ("DOMAIN-SUFFIX", "alipayobjects.com", "DIRECT", "支付宝资源"),
            ("DOMAIN-SUFFIX", "jd.com", "DIRECT", "京东"),
            ("DOMAIN-SUFFIX", "360buyimg.com", "DIRECT", "京东图片"),
            ("DOMAIN-SUFFIX", "163.com", "DIRECT", "网易"),
            ("DOMAIN-SUFFIX", "126.com", "DIRECT", "网易邮箱"),
            ("DOMAIN-SUFFIX", "126.net", "DIRECT", "网易媒体"),
            ("DOMAIN-SUFFIX", "netease.com", "DIRECT", "网易服务"),
            ("DOMAIN-SUFFIX", "dingtalk.com", "DIRECT", "钉钉"),
        ],
    },
    "cn_cloud_upload": {
        "name": "内地网盘与大文件传输直连",
        "desc": "覆盖夸克网盘、百度网盘、阿里云盘、微云、115、迅雷、WPS 等大带宽上传下载服务",
        "position": "top",
        "default": True,
        "rules": [
            ("DOMAIN-SUFFIX", "quark.cn", "DIRECT", "夸克网盘"),
            ("DOMAIN-SUFFIX", "uc.cn", "DIRECT", "UC/夸克存储"),
            ("DOMAIN-SUFFIX", "ucweb.com", "DIRECT", "UC服务"),
            ("DOMAIN-SUFFIX", "baidupcs.com", "DIRECT", "百度网盘传输"),
            ("DOMAIN-SUFFIX", "alipan.com", "DIRECT", "阿里云盘"),
            ("DOMAIN-SUFFIX", "aliyundrive.com", "DIRECT", "阿里云盘旧域"),
            ("DOMAIN-SUFFIX", "weiyun.com", "DIRECT", "腾讯微云"),
            ("DOMAIN-SUFFIX", "115.com", "DIRECT", "115网盘"),
            ("DOMAIN-SUFFIX", "xunlei.com", "DIRECT", "迅雷"),
            ("DOMAIN-SUFFIX", "wps.cn", "DIRECT", "WPS云文档"),
            ("DOMAIN-SUFFIX", "wpscdn.cn", "DIRECT", "WPS CDN"),
            ("DOMAIN-SUFFIX", "kdocs.cn", "DIRECT", "金山文档"),
        ],
    },
    "cn_geosite_fallback": {
        "name": "中国大陆全量直连兜底 (GEOSITE:cn)",
        "desc": "在国际规则之后自动兜住数万个未列出的大陆网站与大陆 IP，避免内地常用流量误绕国际路线",
        "position": "fallback",
        "default": True,
        "rules": [
            ("GEOSITE", "private", "DIRECT", "私有域名直连"),
            ("GEOSITE", "cn", "DIRECT", "大陆域名全量兜底直连"),
            ("GEOIP", "CN", "DIRECT", "大陆IP兜底直连"),
        ],
    },
    "cn_pure_apps_process": {
        "name": "常见纯内地桌面软件直连",
        "desc": "按软件进程直连微信、QQ、抖音、B站直播姬、快手、夸克/百度网盘、飞书、豆包、剪映等（不限制浏览器和 OBS，国际访问与推流不受影响）",
        "position": "top",
        "default": True,
        "rules": [
            ("PROCESS-NAME", "Weixin.exe", "DIRECT", "微信 4.0"),
            ("PROCESS-NAME", "WeChat.exe", "DIRECT", "微信"),
            ("PROCESS-NAME", "WeChatAppEx.exe", "DIRECT", "微信小程序/视频号"),
            ("PROCESS-NAME", "WechatAppLauncher.exe", "DIRECT", "微信启动器"),
            ("PROCESS-NAME", "WXWork.exe", "DIRECT", "企业微信"),
            ("PROCESS-NAME", "QQ.exe", "DIRECT", "QQ客户端"),
            ("PROCESS-NAME", "QQEX.exe", "DIRECT", "QQ扩展"),
            ("PROCESS-NAME", "TIM.exe", "DIRECT", "TIM"),
            ("PROCESS-NAME", "QQLive.exe", "DIRECT", "腾讯视频"),
            ("PROCESS-NAME", "QQMusic.exe", "DIRECT", "QQ音乐"),
            ("PROCESS-NAME", "douyin.exe", "DIRECT", "抖音客户端"),
            ("PROCESS-NAME", "WebcastMate.exe", "DIRECT", "抖音直播伴侣"),
            ("PROCESS-NAME", "livehime.exe", "DIRECT", "B站直播姬"),
            ("PROCESS-NAME", "bilibili.exe", "DIRECT", "B站客户端"),
            ("PROCESS-NAME", "KuaishouLive.exe", "DIRECT", "快手直播伴侣"),
            ("PROCESS-NAME", "KwaiLive.exe", "DIRECT", "快手直播"),
            ("PROCESS-NAME", "QuarkCloudDrive.exe", "DIRECT", "夸克网盘"),
            ("PROCESS-NAME", "quark.exe", "DIRECT", "夸克客户端"),
            ("PROCESS-NAME", "BaiduNetdisk.exe", "DIRECT", "百度网盘"),
            ("PROCESS-NAME", "BaiduNetdiskHost.exe", "DIRECT", "百度网盘传输"),
            ("PROCESS-NAME", "BaiduNetdiskRender.exe", "DIRECT", "百度网盘渲染"),
            ("PROCESS-NAME", "aDrive.exe", "DIRECT", "阿里云盘"),
            ("PROCESS-NAME", "Feishu.exe", "DIRECT", "飞书内地版"),
            ("PROCESS-NAME", "DingTalk.exe", "DIRECT", "钉钉"),
            ("PROCESS-NAME", "Doubao.exe", "DIRECT", "豆包"),
            ("PROCESS-NAME", "JianyingPro.exe", "DIRECT", "剪映"),
            ("PROCESS-NAME", "Thunder.exe", "DIRECT", "迅雷"),
        ],
    },
}

# 公共通用体检探针（0 私人 IP）
DIAGNOSTIC_PROBES = [
    ("push-rtmp-l11.douyincdn.com", "DIRECT", "抖音直播推流"),
    ("live-push.bilivideo.com", "DIRECT", "B站直播推流"),
    ("push.tlivepush.com", "DIRECT", "微信视频号 / 腾讯云推流"),
    ("channels.weixin.qq.com", "DIRECT", "微信视频号平台"),
    ("livepush.myqcloud.com", "DIRECT", "腾讯云直播推流"),
    ("push.alivecdn.com", "DIRECT", "阿里云直播推流"),
    ("push.kwaicdn.com", "DIRECT", "快手直播推流"),
    ("live.xiaohongshu.com", "DIRECT", "小红书直播"),
    ("www.bing.com", "DIRECT", "Bing 必应搜索"),
    ("www.baidu.com", "DIRECT", "百度搜索"),
    ("im.qq.com", "DIRECT", "QQ 服务"),
    ("wx.qq.com", "DIRECT", "微信服务"),
    ("www.douyin.com", "DIRECT", "抖音网页"),
    ("www.xiaohongshu.com", "DIRECT", "小红书网页"),
    ("www.bilibili.com", "DIRECT", "B站网页"),
    ("pan.quark.cn", "DIRECT", "夸克网盘"),
    ("d.pcs.baidu.com", "DIRECT", "百度网盘上传"),
    ("api.aliyundrive.com", "DIRECT", "阿里云盘上传"),
    ("127.0.0.1", "DIRECT", "本机回环直连"),
    ("192.168.1.1", "DIRECT", "局域网段直连"),
    ("a.rtmp.youtube.com", "PROXY", "YouTube 国际推流"),
    ("live.twitch.tv", "PROXY", "Twitch 国际推流"),
    ("api.openai.com", "PROXY", "OpenAI 服务"),
    ("www.google.com", "PROXY", "Google 搜索"),
]

# 洁净 DNS 防污染配置（保持 redir-host，全面兼容 WebRTC / 推流 / 本地开发）
CLEAN_DNS_CONFIG = {
    "enable": True,
    "listen": "0.0.0.0:1053",
    "prefer-h3": False,
    "use-hosts": True,
    "use-system-hosts": True,
    "respect-rules": False,
    "ipv6": False,
    "enhanced-mode": "redir-host",
    "fake-ip-range": "198.18.0.1/16",
    "fake-ip-filter": [
        "*.lan",
        "*.local",
        "localhost.ptlogin2.qq.com",
        "dns.msftnsci.com",
        "www.msftnsci.com",
        "www.msftconnecttest.com",
        "+.stun.*.*",
        "+.stun.*.*.*",
    ],
    "default-nameserver": [
        "223.5.5.5",
        "119.29.29.29",
    ],
    "proxy-server-nameserver": [
        "https://doh.pub/dns-query",
        "223.5.5.5",
    ],
    "nameserver": [
        "https://doh.pub/dns-query",
        "https://dns.alidns.com/dns-query",
        "223.5.5.5",
        "119.29.29.29",
    ],
    "nameserver-policy": {
        "geosite:private": ["system"],
        "geosite:cn": ["223.5.5.5", "119.29.29.29"],
        "+.bing.com": ["223.5.5.5", "119.29.29.29"],
        "+.baidu.com": ["223.5.5.5", "119.29.29.29"],
        "+.qq.com": ["223.5.5.5", "119.29.29.29"],
        "+.wechat.com": ["223.5.5.5", "119.29.29.29"],
        "+.douyin.com": ["223.5.5.5", "119.29.29.29"],
        "+.douyincdn.com": ["223.5.5.5", "119.29.29.29"],
        "+.bilibili.com": ["223.5.5.5", "119.29.29.29"],
        "+.bilivideo.com": ["223.5.5.5", "119.29.29.29"],
        "+.xiaohongshu.com": ["223.5.5.5", "119.29.29.29"],
        "+.xhscdn.com": ["223.5.5.5", "119.29.29.29"],
        "+.kuaishou.com": ["223.5.5.5", "119.29.29.29"],
        "+.kwaicdn.com": ["223.5.5.5", "119.29.29.29"],
        "+.tlivepush.com": ["223.5.5.5", "119.29.29.29"],
        "+.myqcloud.com": ["223.5.5.5", "119.29.29.29"],
        "+.alivecdn.com": ["223.5.5.5", "119.29.29.29"],
    },
    "fallback": [
        "tls://8.8.4.4",
        "tls://1.1.1.1",
    ],
    "fallback-filter": {
        "geoip": True,
        "geoip-code": "CN",
        "geosite": [],
        "ipcidr": ["240.0.0.0/4", "0.0.0.0/32"],
        "domain": [
            "+.google.com",
            "+.googleapis.com",
            "+.youtube.com",
            "+.ytimg.com",
            "+.googlevideo.com",
            "+.twitch.tv",
            "+.openai.com",
            "+.anthropic.com",
            "+.github.com",
        ],
    },
}


class DomainAnalyzer:
    """一级域名 (eTLD+1) 提取、归并与中英文智能识别引擎"""

    NOISE_SUFFIXES = (".arpa", ".local", ".lan", ".home", ".localhost", ".localdomain", ".internal", ".corp")
    HOST_RE = re.compile(r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,24}")

    @classmethod
    def clean_host(cls, raw: str):
        if not raw:
            return ""
        s = raw.strip().strip("'\"`<>()[]{} ,;")
        if "://" in s:
            try:
                u = urllib.parse.urlparse(s)
                if u.hostname:
                    s = u.hostname
            except Exception:
                pass
        # 去除路径与端口
        s = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        if ":" in s and not s.startswith("["):
            # IPv4:port 或 domain:port
            parts = s.rsplit(":", 1)
            if parts[1].isdigit():
                s = parts[0]
        s = s.lstrip("*.").rstrip(".").lower()
        return s

    @classmethod
    def is_noise_host(cls, host: str):
        if not host or "." not in host:
            return True
        if host.startswith("_") or ".." in host:
            return True
        for ns in cls.NOISE_SUFFIXES:
            if host.endswith(ns):
                return True
        # 过滤纯数字分段
        if host.split(".")[-1].isdigit():
            try:
                ipaddress.ip_address(host)
                return False
            except ValueError:
                return True
        return False

    @classmethod
    def extract_root_domain(cls, raw: str):
        host = cls.clean_host(raw)
        if not host:
            return ""
        try:
            ipaddress.ip_address(host)
            return host
        except ValueError:
            pass
        if cls.is_noise_host(host):
            return ""
        labels = [x for x in host.split(".") if x]
        if len(labels) <= 2:
            return ".".join(labels)
        last2 = ".".join(labels[-2:])
        if last2 in MULTI_PART_TLDS and len(labels) >= 3:
            return ".".join(labels[-3:])
        return last2

    @classmethod
    def classify_domain_with_key(cls, root_domain: str):
        d = root_domain.lower()
        if d in KNOWN_DOMAIN_CATALOG:
            label, region = KNOWN_DOMAIN_CATALOG[d]
            return label, region, f"catalog.{d}"
        if d.endswith(".cn") or d.endswith(".xn--fiqs8s"):
            return "中国大陆域名 (.cn)", "cn", "cat.cn_region"
        cn_hints = (
            "china", "qq", "weixin", "wechat", "douyin", "bili", "kuaishou", "kwai",
            "baidu", "ali", "taobao", "tmall", "tencent", "qcloud", "byted", "volc",
            "xhs", "xiaohongshu", "huya", "douyu", "quark", "163", "netease",
            "sina", "weibo", "zhihu", "jd", "meituan", "ctrip", "feishu", "dingtalk",
            "huawei", "xiaomi", "oppo", "vivo", "wps", "kingsoft", "xunlei", "iqiyi", "youku",
        )
        if any(h in d for h in cn_hints):
            return "疑似内地服务", "cn", "cat.suspect_cn"
        global_hints = (
            "google", "youtube", "ytimg", "twitch", "openai", "chatgpt", "anthropic",
            "claude", "github", "twitter", "telegram", "discord", "facebook", "meta",
            "instagram", "netflix", "spotify", "reddit", "wikipedia", "amazon", "aws",
            "cloudflare", "vercel", "stripe", "tiktok",
        )
        if any(h in d for h in global_hints):
            return "国际服务", "global", "cat.global"
        return "待确认站点", "unknown", "cat.unknown"

    @classmethod
    def classify_domain(cls, root_domain: str):
        label, region, _ = cls.classify_domain_with_key(root_domain)
        return label, region

    @classmethod
    def extract_hosts_from_text(cls, text: str):
        if not text:
            return []
        found = []
        seen = set()
        # 先提取 URL
        for m in re.finditer(r"(?:https?|rtmps?|srt|ws|wss)://[^\s'\"<>]+", text, re.I):
            h = cls.clean_host(m.group(0))
            if h and not cls.is_noise_host(h) and h not in seen:
                seen.add(h)
                found.append(h)
        # 再提取裸域名
        for m in cls.HOST_RE.finditer(text):
            h = cls.clean_host(m.group(0))
            if h and not cls.is_noise_host(h) and h not in seen:
                # 排除常见文件扩展名误判
                if h.rsplit(".", 1)[-1] in ("exe", "dll", "json", "yaml", "yml", "py", "js", "ts", "css", "html", "png", "jpg", "jpeg", "gif", "svg", "mp4", "log", "txt", "zip", "bat", "ps1", "sh"):
                    continue
                seen.add(h)
                found.append(h)
        return found


def run_silent_output(cmd, timeout=8, text=True):
    """静默执行子进程（在 pythonw 无控制台背景下绝不弹窗闪烁黑框）"""
    kw = {
        "stdin": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "timeout": timeout,
    }
    if platform.system() == "Windows":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if text:
        kw["text"] = True
        kw["encoding"] = "utf-8"
        kw["errors"] = "ignore"
    return subprocess.check_output(cmd, **kw)


def run_silent_process(cmd, timeout=8):
    kw = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "timeout": timeout,
        "text": True,
        "encoding": "utf-8",
        "errors": "ignore",
    }
    if platform.system() == "Windows":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(cmd, **kw)


class NetworkHelper:
    """网络与物理网卡检测"""

    @staticmethod
    def get_physical_ip():
        demo_ip = os.environ.get("RULEPILOT_DEMO_IP", "").strip()
        if demo_ip:
            return demo_ip
        candidates = []
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if not ip.startswith("127.") and not ip.startswith("198.18.") and not ip.startswith("169.254."):
                    candidates.append(ip)
        except Exception:
            pass
        for ip in candidates:
            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                return ip
        return candidates[0] if candidates else "127.0.0.1"

    @staticmethod
    def pick_free_loopback_port(preferred_start=19090, count=20):
        for port in range(preferred_start, preferred_start + count):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        return preferred_start


class MihomoControllerClient:
    """Mihomo / Clash External Controller 回环 REST 客户端（免代理直连 · 零杀热重载）"""

    def __init__(self, clash_dir):
        self.clash_dir = clash_dir
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @staticmethod
    def _normalize_controller_url(raw_addr: str):
        s = (raw_addr or "").strip().strip("'\"")
        if not s:
            return ""
        if s.startswith("http://") or s.startswith("https://"):
            u = urllib.parse.urlparse(s)
            host = u.hostname or "127.0.0.1"
            port = u.port or (443 if u.scheme == "https" else 9090)
            if host in ("0.0.0.0", "::", "*"):
                host = "127.0.0.1"
            return f"{u.scheme}://{host}:{port}"
        if s.startswith(":"):
            return f"http://127.0.0.1{s}"
        if s.startswith("0.0.0.0:"):
            return "http://127.0.0.1:" + s.split(":", 1)[1]
        if s.startswith("[::]:"):
            return "http://127.0.0.1:" + s.split("]:", 1)[1]
        if ":" in s:
            return f"http://{s}"
        if s.isdigit():
            return f"http://127.0.0.1:{s}"
        return ""

    def discover(self):
        """从 config.yaml / shared_preferences.json 自动发现控制器地址与本地秘钥"""
        candidates = []
        cfg_yaml = os.path.join(self.clash_dir, "config.yaml")
        sp_path = os.path.join(self.clash_dir, "shared_preferences.json")

        for ypath in [cfg_yaml, os.path.join(self.clash_dir, "clash-verge.yaml")]:
            if os.path.exists(ypath):
                try:
                    txt = open(ypath, "r", encoding="utf-8", errors="ignore").read()
                    cm = re.search(r'(?m)^external-controller:\s*[\'"]?([^\r\n\'"]*)[\'"]?', txt)
                    sm = re.search(r'(?m)^secret:\s*[\'"]?([^\r\n\'"]*)[\'"]?', txt)
                    addr = cm.group(1).strip() if cm else ""
                    sec = sm.group(1).strip() if sm else ""
                    if addr:
                        url = self._normalize_controller_url(addr)
                        if url:
                            candidates.append((url, sec, "config_yaml"))
                except Exception:
                    pass

        if os.path.exists(sp_path):
            try:
                sp = json.load(open(sp_path, "r", encoding="utf-8"))
                fc = json.loads(sp.get("flutter.config", "{}"))
                pcc = fc.get("patchClashConfig", {})
                addr = str(pcc.get("external-controller") or "").strip()
                sec = str(pcc.get("secret") or "").strip()
                if addr:
                    url = self._normalize_controller_url(addr)
                    if url and not any(c[0] == url for c in candidates):
                        candidates.append((url, sec, "shared_preferences"))
            except Exception:
                pass

        return candidates

    def _request(self, url, secret="", method="GET", payload=None, timeout=2.5):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if secret:
            req.add_header("Authorization", f"Bearer {secret}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with self._opener.open(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                if not raw:
                    return resp.status, {}
                try:
                    return resp.status, json.loads(raw)
                except Exception:
                    return resp.status, {"raw": raw}
        except urllib.error.HTTPError as e:
            return e.code, {"error": e.read().decode("utf-8", errors="ignore")}
        except Exception as e:
            return 0, {"error": str(e)}

    def find_reachable(self):
        for url, sec, src in self.discover():
            st, body = self._request(f"{url}/version", secret=sec, timeout=1.2)
            if st == 200 and isinstance(body, dict):
                return url, sec, body.get("version", "mihomo"), src
        return None, "", "", ""

    def get_status(self):
        cands = self.discover()
        configured = len(cands) > 0
        url, sec, ver, src = self.find_reachable()
        return {
            "configured": configured,
            "configured_url": cands[0][0] if cands else "",
            "reachable": bool(url),
            "url": url or (cands[0][0] if cands else ""),
            "core_version": ver or "",
            "source": src or (cands[0][2] if cands else ""),
            "zero_kill_ready": bool(url),
        }

    def hot_reload_file(self, config_path):
        url, sec, _, _ = self.find_reachable()
        if not url:
            return False, "controller_unreachable"
        st, body = self._request(
            f"{url}/configs?force=true",
            secret=sec,
            method="PUT",
            payload={"path": os.path.abspath(config_path)},
            timeout=5.0,
        )
        if st in (200, 204):
            return True, f"hot_reloaded:{url}"
        return False, f"controller_http_{st}: {body}"

    def get_live_connections(self):
        url, sec, _, _ = self.find_reachable()
        if not url:
            return False, []
        st, body = self._request(f"{url}/connections", secret=sec, timeout=2.0)
        if st != 200 or not isinstance(body, dict):
            return False, []
        entries = []
        for conn in body.get("connections", []) or []:
            meta = conn.get("metadata", {}) or {}
            host = (meta.get("host") or meta.get("destinationIP") or "").strip()
            if not host:
                continue
            proc = (meta.get("process") or "").strip()
            if not proc and meta.get("processPath"):
                proc = os.path.basename(meta.get("processPath"))
            chains = conn.get("chains") or []
            entries.append({
                "host": host,
                "process": proc,
                "chains": chains,
                "rule": conn.get("rule", ""),
            })
        return True, entries


class PathDetector:
    """跨平台多代理客户端自动发现器（零个人硬编码）"""

    @staticmethod
    def get_os_type():
        return platform.system().lower()

    @classmethod
    def discover_clients(cls):
        """返回所有检测到的代理客户端目录列表"""
        os_type = cls.get_os_type()
        home = os.path.expanduser("~")
        raw_candidates = []

        if os_type == "windows":
            appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
            localappdata = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
            # 自动扫描 %APPDATA%\com.follow 下的所有 FlClash / 衍生版子目录
            follow_root = os.path.join(appdata, "com.follow")
            if os.path.isdir(follow_root):
                for sub in sorted(os.listdir(follow_root)):
                    full = os.path.join(follow_root, sub)
                    if os.path.isdir(full):
                        raw_candidates.append(("FlClash", full))
            raw_candidates.extend([
                ("FlClash", os.path.join(appdata, "com.follow", "clash")),
                ("Clash Verge Rev", os.path.join(appdata, "io.github.clash-verge-rev.clash-verge-rev")),
                ("Clash Verge", os.path.join(appdata, "clash-verge")),
                ("Mihomo Party", os.path.join(appdata, "mihomo-party")),
                ("FlClash", os.path.join(localappdata, "FlClash")),
                ("FlClash", os.path.join(home, ".config", "flclash")),
                ("Clash Meta / Mihomo", os.path.join(home, ".config", "mihomo")),
                ("Clash", os.path.join(home, ".config", "clash")),
            ])
        elif os_type == "darwin":
            app_support = os.path.join(home, "Library", "Application Support")
            raw_candidates.extend([
                ("FlClash", os.path.join(app_support, "com.follow", "clash")),
                ("Clash Verge Rev", os.path.join(app_support, "io.github.clash-verge-rev.clash-verge-rev")),
                ("Clash Verge", os.path.join(app_support, "clash-verge")),
                ("Mihomo Party", os.path.join(app_support, "mihomo-party")),
                ("FlClash", os.path.join(home, ".config", "flclash")),
                ("Mihomo", os.path.join(home, ".config", "mihomo")),
                ("Clash", os.path.join(home, ".config", "clash")),
            ])
        else:
            raw_candidates.extend([
                ("FlClash", os.path.join(home, ".config", "flclash")),
                ("Clash Verge Rev", os.path.join(home, ".config", "clash-verge-rev")),
                ("Mihomo Party", os.path.join(home, ".config", "mihomo-party")),
                ("Mihomo", os.path.join(home, ".config", "mihomo")),
                ("Clash", os.path.join(home, ".config", "clash")),
            ])

        found = []
        seen = set()
        for cname, d in raw_candidates:
            ad = os.path.abspath(d)
            key = ad.lower()
            if key in seen or not os.path.isdir(ad):
                continue
            has_db = os.path.exists(os.path.join(ad, "database.sqlite"))
            has_cfg = os.path.exists(os.path.join(ad, "config.yaml"))
            has_prof = os.path.isdir(os.path.join(ad, "profiles"))
            if has_db or has_cfg or has_prof:
                seen.add(key)
                found.append({
                    "name": cname,
                    "dir": ad,
                    "mode": "flclash_native" if has_db else "yaml_inject",
                    "has_config": has_cfg,
                    "has_sqlite": has_db,
                })
        return found

    @classmethod
    def detect_active_dir(cls, user_specified_dir=None):
        if user_specified_dir and os.path.isdir(user_specified_dir):
            return os.path.abspath(user_specified_dir)
        clients = cls.discover_clients()
        # 优先选择有 FlClash database.sqlite 的客户端
        for c in clients:
            if c["has_sqlite"]:
                return c["dir"]
        if clients:
            return clients[0]["dir"]
        home = os.path.expanduser("~")
        if cls.get_os_type() == "windows":
            return os.path.join(os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming")), "com.follow", "clash")
        return os.path.join(home, ".config", "clash")

    @staticmethod
    def find_flclash_exe():
        """动态从运行进程、白标同目录与常见安装目录发现客户端可执行文件（零硬编码）"""
        if platform.system() != "Windows":
            return None
        try:
            ps = (
                "$p = Get-Process -ErrorAction SilentlyContinue | "
                "Where-Object { $_.ProcessName -match '^FlClash$|^flclash$' } | Select-Object -First 1; "
                "if ($p -and $p.Path) { $p.Path }"
            )
            out = run_silent_output(["powershell", "-NoProfile", "-Command", ps], timeout=5).strip()
            if out and os.path.exists(out):
                return out
        except Exception:
            pass

        roots = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for r in roots:
            if not r or not os.path.isdir(r):
                continue
            direct = os.path.join(r, "FlClash", "FlClash.exe")
            if os.path.exists(direct):
                return direct
            try:
                for sub in os.listdir(r):
                    cand = os.path.join(r, sub, "FlClash.exe")
                    if os.path.exists(cand):
                        return cand
            except Exception:
                pass
        return None


class RuleManager:
    """独立规则库与配置管理器（公共版 v3，无损兼容历史规则）"""

    def __init__(self, storage_dir=None):
        if storage_dir is None:
            storage_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_dir = os.path.abspath(storage_dir)
        self.rules_file = os.path.join(self.storage_dir, "custom_rules.json")
        self.rules_data = self._load()
        self._ensure_schema()

    def _default_presets(self):
        return {k: v["default"] for k, v in PRESET_PACKS.items()}

    def _load(self):
        default_data = {
            "version": 3,
            "custom_clash_dir": "",
            "custom_proxy_group": "",
            "sync_system_bypass": True,
            "clean_dns_override": True,
            "enable_local_controller": True,
            "presets": self._default_presets(),
            "rules": [],
        }
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    return loaded
            except Exception as e:
                print(f"[警告] 加载规则文件失败，使用默认配置: {e}")
        return default_data

    def _ensure_schema(self):
        changed = False
        if self.rules_data.get("version", 1) < 3:
            self.rules_data["version"] = 3
            changed = True
        for k, default_v in [
            ("custom_clash_dir", ""),
            ("custom_proxy_group", ""),
            ("clean_dns_override", True),
            ("sync_system_bypass", True),
            ("enable_local_controller", True),
        ]:
            if k not in self.rules_data:
                self.rules_data[k] = default_v
                changed = True

        presets = self.rules_data.setdefault("presets", {})
        for k, meta in PRESET_PACKS.items():
            if k not in presets:
                presets[k] = meta["default"]
                changed = True

        # 仅自动确保通用本地回环与 RFC1918 私网段直连（零私人公网 IP）
        essentials = [
            ("127.0.0.1/32", "DIRECT", "IP-CIDR", "本机回环直连", "top"),
            ("192.168.0.0/16", "DIRECT", "IP-CIDR", "局域网段直连", "top"),
            ("10.0.0.0/8", "DIRECT", "IP-CIDR", "内网 10 段直连", "top"),
            ("172.16.0.0/12", "DIRECT", "IP-CIDR", "内网 172 段直连", "top"),
        ]
        rules = self.rules_data.setdefault("rules", [])
        for r in rules:
            if "position" not in r:
                r["position"] = "top"
                changed = True

        existing_keys = {(r.get("type", "").upper(), r.get("pattern", "").lower()) for r in rules}
        for pat, tgt, rtype, cmt, pos in essentials:
            if (rtype.upper(), pat.lower()) not in existing_keys:
                rules.append({
                    "pattern": pat,
                    "target": tgt,
                    "type": rtype,
                    "comment": cmt,
                    "position": pos,
                })
                changed = True
        if changed:
            self.save()

    def save(self):
        try:
            with open(self.rules_file, "w", encoding="utf-8") as f:
                json.dump(self.rules_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[错误] 保存规则文件失败: {e}")
            return False

    @staticmethod
    def parse_pattern_type(pattern: str, collapse_to_root: bool = False):
        raw = pattern.strip().strip("'\"")
        low = raw.lower()
        if low.startswith("geosite:"):
            return "GEOSITE", raw.split(":", 1)[1].strip()
        if low.startswith("geoip:"):
            return "GEOIP", raw.split(":", 1)[1].strip().upper()
        if low.startswith("process:"):
            return "PROCESS-NAME", raw.split(":", 1)[1].strip()
        if low.startswith("port:"):
            return "DST-PORT", raw.split(":", 1)[1].strip()
        if low.startswith("keyword:"):
            return "DOMAIN-KEYWORD", raw.split(":", 1)[1].strip()
        if raw.startswith("^"):
            return "DOMAIN", DomainAnalyzer.clean_host(raw[1:])
        if raw.startswith("*."):
            host = DomainAnalyzer.clean_host(raw[2:])
            return "DOMAIN-SUFFIX", (DomainAnalyzer.extract_root_domain(host) or host) if collapse_to_root else host
        if low.endswith(".exe") or low.endswith(".app"):
            return "PROCESS-NAME", raw

        if "/" in raw and "://" not in raw:
            try:
                net = ipaddress.ip_network(raw, strict=False)
                return ("IP-CIDR6" if net.version == 6 else "IP-CIDR"), str(net)
            except ValueError:
                pass

        cleaned = DomainAnalyzer.clean_host(raw)
        if not cleaned:
            cleaned = raw

        try:
            if "/" in cleaned:
                net = ipaddress.ip_network(cleaned, strict=False)
                return ("IP-CIDR6" if net.version == 6 else "IP-CIDR"), str(net)
            ip = ipaddress.ip_address(cleaned)
            return ("IP-CIDR6" if ip.version == 6 else "IP-CIDR"), f"{ip}/128" if ip.version == 6 else f"{ip}/32"
        except ValueError:
            pass

        if collapse_to_root:
            root = DomainAnalyzer.extract_root_domain(cleaned)
            if root:
                cleaned = root
        return "DOMAIN-SUFFIX", cleaned

    def add_rule(self, pattern: str, target: str = "DIRECT", rule_type: str = None,
                 comment: str = "", position: str = "top", collapse_to_root: bool = False):
        pattern = pattern.strip()
        if not pattern:
            return False, "规则内容不能为空"
        auto_type, clean_pattern = self.parse_pattern_type(pattern, collapse_to_root=collapse_to_root)
        final_type = (rule_type or auto_type).upper()
        target_clean = target.upper() if target.upper() in ("DIRECT", "REJECT", "PROXY") else target
        pos = position if position in ("top", "fallback") else "top"

        # 自动补全已知域名的中文备注
        if not comment and final_type in ("DOMAIN-SUFFIX", "DOMAIN"):
            root = DomainAnalyzer.extract_root_domain(clean_pattern)
            if root in KNOWN_DOMAIN_CATALOG:
                comment = KNOWN_DOMAIN_CATALOG[root][0]

        for r in self.rules_data["rules"]:
            if r["pattern"].lower() == clean_pattern.lower() and r["type"].upper() == final_type:
                r["target"] = target_clean
                r["position"] = pos
                if comment:
                    r["comment"] = comment
                self.save()
                return True, f"已更新规则: {clean_pattern} -> {'直连排除' if target_clean == 'DIRECT' else target_clean}"

        self.rules_data["rules"].append({
            "pattern": clean_pattern,
            "target": target_clean,
            "type": final_type,
            "comment": comment,
            "position": pos,
        })
        self.save()
        return True, f"已添加规则: {clean_pattern} -> {'直连排除' if target_clean == 'DIRECT' else target_clean}"

    def toggle_rule_target(self, pattern: str, rule_type: str = None):
        pat_low = pattern.strip().lower()
        for r in self.rules_data["rules"]:
            if r["pattern"].lower() == pat_low and (not rule_type or r["type"].upper() == rule_type.upper()):
                cur_t = r.get("target", "DIRECT").upper()
                new_t = "PROXY" if cur_t == "DIRECT" else "DIRECT"
                r["target"] = new_t
                self.save()
                return True, f"已切换 {r['pattern']} 为 {'直连排除' if new_t == 'DIRECT' else '强制走代理'}"
        return False, f"未找到规则: {pattern}"

    def remove_rule(self, pattern: str, rule_type: str = None):
        pat_low = pattern.strip().lower()
        orig = len(self.rules_data["rules"])
        self.rules_data["rules"] = [
            r for r in self.rules_data["rules"]
            if not (r["pattern"].lower() == pat_low and (not rule_type or r["type"].upper() == rule_type.upper()))
        ]
        if len(self.rules_data["rules"]) < orig:
            self.save()
            return True, f"已移除规则: {pattern}"
        return False, f"未找到规则: {pattern}"

    def set_option(self, key: str, value):
        if key in PRESET_PACKS:
            self.rules_data.setdefault("presets", {})[key] = bool(value)
        elif key in ("clean_dns_override", "sync_system_bypass", "enable_local_controller"):
            self.rules_data[key] = bool(value)
        elif key in ("custom_proxy_group", "custom_clash_dir"):
            self.rules_data[key] = str(value or "").strip()
        else:
            return False, f"未知配置项: {key}"
        self.save()
        return True, "配置已保存"

    def import_rules_payload(self, payload: dict):
        if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
            return False, "导入文件格式不正确，需要包含 rules 数组"
        added = 0
        for r in payload["rules"]:
            if not isinstance(r, dict) or not r.get("pattern"):
                continue
            ok, _ = self.add_rule(
                r.get("pattern", ""),
                r.get("target", "DIRECT"),
                rule_type=r.get("type"),
                comment=r.get("comment", ""),
                position=r.get("position", "top"),
            )
            if ok:
                added += 1
        if isinstance(payload.get("presets"), dict):
            for k, v in payload["presets"].items():
                if k in PRESET_PACKS:
                    self.rules_data.setdefault("presets", {})[k] = bool(v)
            self.save()
        return True, f"成功导入 {added} 条规则"

    def list_rules(self):
        return self.rules_data.get("rules", [])

    def clear_rules(self):
        self.rules_data["rules"] = []
        self._ensure_schema()
        self.save()
        return True, "自定义规则已重置为通用内网基础规则（场景保护开关不受影响）"

    def get_compiled_rules(self, proxy_group_placeholder="__PRIMARY_PROXY__"):
        top_rules = [
            "DST-PORT,18900,DIRECT",
            "DST-PORT,18901,DIRECT",
            "DOMAIN-SUFFIX,localhost,DIRECT",
        ]
        fallback_rules = []
        need_process = False
        seen_top = set(top_rules)
        seen_fb = set()

        def fmt_rule(rtype, pattern, target):
            nonlocal need_process
            rtype_u = rtype.upper()
            if "PROCESS" in rtype_u:
                need_process = True
            tgt = proxy_group_placeholder if target.upper() == "PROXY" else target
            if "IP-CIDR" in rtype_u:
                return f"{rtype_u},{pattern},{tgt},no-resolve"
            return f"{rtype_u},{pattern},{tgt}"

        # 1. 用户自定义规则（最高优先级，允许覆盖一切预设）
        for r in self.list_rules():
            s = fmt_rule(r.get("type", "DOMAIN-SUFFIX"), r.get("pattern", ""), r.get("target", "DIRECT"))
            if r.get("position") == "fallback":
                if s not in seen_fb:
                    fallback_rules.append(s)
                    seen_fb.add(s)
            else:
                if s not in seen_top:
                    top_rules.append(s)
                    seen_top.add(s)

        # 2. 启用的场景预设包
        presets_cfg = self.rules_data.get("presets", {})
        for key, meta in PRESET_PACKS.items():
            if not presets_cfg.get(key, meta["default"]):
                continue
            for rtype, pat, tgt, _cmt in meta["rules"]:
                s = fmt_rule(rtype, pat, tgt)
                if meta["position"] == "fallback":
                    if s not in seen_fb:
                        fallback_rules.append(s)
                        seen_fb.add(s)
                else:
                    if s not in seen_top:
                        top_rules.append(s)
                        seen_top.add(s)

        return top_rules, fallback_rules, need_process


class ConfigInjector:
    """跨客户端持久化注入、一键开启/暂停与诊断引擎"""

    def __init__(self, clash_dir, rule_manager: RuleManager):
        self.rule_manager = rule_manager
        self.set_clash_dir(clash_dir)

    def set_clash_dir(self, clash_dir):
        self.clash_dir = os.path.abspath(clash_dir)
        self.config_yaml_path = os.path.join(self.clash_dir, "config.yaml")
        self.profiles_dir = os.path.join(self.clash_dir, "profiles")
        self.scripts_dir = os.path.join(self.clash_dir, "scripts")
        self.shared_pref_path = os.path.join(self.clash_dir, "shared_preferences.json")
        self.db_path = os.path.join(self.clash_dir, "database.sqlite")
        self.script_file_path = os.path.join(self.scripts_dir, f"{FLCLASH_SCRIPT_ID}.js")
        self.controller = MihomoControllerClient(self.clash_dir)
        self.managed_cache_path = os.path.join(self.rule_manager.storage_dir, ".rulepilot_managed_cache.json")

    def is_flclash_sqlite(self):
        return os.path.exists(self.db_path)

    def detect_client_label(self):
        if self.is_flclash_sqlite():
            return "FlClash（原生持久化覆写）"
        low = self.clash_dir.lower()
        if "verge" in low:
            return "Clash Verge / Rev（YAML 注入）"
        if "mihomo" in low:
            return "Mihomo Party（YAML 注入）"
        return "Clash / Mihomo 兼容客户端"

    def detect_client_key(self):
        if self.is_flclash_sqlite():
            return "flclash_native"
        low = self.clash_dir.lower()
        if "verge" in low:
            return "clash_verge"
        if "mihomo" in low:
            return "mihomo_party"
        return "clash_compat"

    def detect_active_profile_path(self):
        if os.path.exists(self.shared_pref_path):
            try:
                with open(self.shared_pref_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cfg = json.loads(data.get("flutter.config", "{}"))
                prof_id = cfg.get("currentProfileId")
                if prof_id:
                    p = os.path.join(self.profiles_dir, f"{prof_id}.yaml")
                    if os.path.exists(p):
                        return p
            except Exception:
                pass
        if os.path.isdir(self.profiles_dir):
            yamls = [
                os.path.join(self.profiles_dir, f)
                for f in os.listdir(self.profiles_dir)
                if f.endswith(".yaml") or f.endswith(".yml")
            ]
            if yamls:
                yamls.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return yamls[0]
        return None

    def detect_primary_proxy_group(self, file_path=None):
        if self.rule_manager.rules_data.get("custom_proxy_group"):
            return self.rule_manager.rules_data["custom_proxy_group"]
        target_file = file_path or self.config_yaml_path
        if not os.path.exists(target_file):
            target_file = self.detect_active_profile_path() or ""
        if not target_file or not os.path.exists(target_file):
            return "PROXY"
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            m = re.search(r'(?m)^proxy-groups:\s*\n((?:[ \t]+.*\n|\n)+)', content)
            if m:
                for line in m.group(1).splitlines():
                    nm = re.search(r'name:\s*[\'"]?([^\'",\r\n]+)[\'"]?', line)
                    if nm:
                        g = nm.group(1).strip()
                        if g not in ("DIRECT", "REJECT", "GLOBAL", "COMPATIBLE", "自动选择", "故障转移"):
                            return g
        except Exception:
            pass
        return "PROXY"

    def _generate_flclash_js(self):
        top_rules, fallback_rules, need_process = self.rule_manager.get_compiled_rules("__PRIMARY_PROXY__")
        clean_dns = bool(self.rule_manager.rules_data.get("clean_dns_override", True))
        custom_pg = self.rule_manager.rules_data.get("custom_proxy_group", "")
        local_ctrl_addr = ""
        local_ctrl_secret = ""
        if self.rule_manager.rules_data.get("enable_local_controller", True) and os.path.exists(self.shared_pref_path):
            try:
                sp = json.load(open(self.shared_pref_path, "r", encoding="utf-8"))
                pcc = json.loads(sp.get("flutter.config", "{}")).get("patchClashConfig", {})
                local_ctrl_addr = str(pcc.get("external-controller") or "").strip()
                local_ctrl_secret = str(pcc.get("secret") or "").strip()
            except Exception:
                pass

        js_lines = [
            f"// Auto-generated by RulePilot v{VERSION} ({EDITION})",
            "// Purpose: Keep Mainland China live streaming, daily apps and LAN rules on DIRECT",
            "const main = (config) => {",
            "  try {",
            "    if (!config || typeof config !== 'object') return config;",
            f"    const CUSTOM_PROXY_GROUP = {json.dumps(custom_pg, ensure_ascii=False)};",
            f"    const TOP_RULES_TPL = {json.dumps(top_rules, ensure_ascii=False, indent=2)};",
            f"    const FALLBACK_RULES_TPL = {json.dumps(fallback_rules, ensure_ascii=False, indent=2)};",
            f"    const CLEAN_DNS_ENABLE = {json.dumps(clean_dns)};",
            f"    const NEED_PROCESS_MODE = {json.dumps(need_process)};",
            f"    const LOCAL_CONTROLLER_ADDR = {json.dumps(local_ctrl_addr)};",
            f"    const LOCAL_CONTROLLER_SECRET = {json.dumps(local_ctrl_secret)};",
            f"    const CLEAN_DNS_OBJ = {json.dumps(CLEAN_DNS_CONFIG, ensure_ascii=False, indent=2)};",
            "",
            "    let primaryGroup = CUSTOM_PROXY_GROUP;",
            "    if (!primaryGroup && Array.isArray(config['proxy-groups'])) {",
            "      const skip = new Set(['DIRECT', 'REJECT', 'GLOBAL', 'COMPATIBLE', '自动选择', '故障转移']);",
            "      for (const g of config['proxy-groups']) {",
            "        if (g && g.name && !skip.has(g.name)) {",
            "          primaryGroup = g.name;",
            "          break;",
            "        }",
            "      }",
            "    }",
            "    if (!primaryGroup) primaryGroup = 'PROXY';",
            "",
            "    const resolveTarget = (r) => r.replace(/__PRIMARY_PROXY__/g, primaryGroup);",
            "    const topRules = TOP_RULES_TPL.map(resolveTarget);",
            "    const fallbackRules = FALLBACK_RULES_TPL.map(resolveTarget);",
            "",
            "    const existing = Array.isArray(config.rules) ? config.rules.slice() : [];",
            "    const topSet = new Set(topRules);",
            "    const fbSet = new Set(fallbackRules);",
            "",
            "    const middle = [];",
            "    const tailMatch = [];",
            "    for (const r of existing) {",
            "      if (typeof r !== 'string') continue;",
            "      const s = r.trim();",
            "      if (!s || topSet.has(s) || fbSet.has(s)) continue;",
            "      if (s.startsWith('MATCH,')) {",
            "        tailMatch.push(s);",
            "      } else {",
            "        middle.push(s);",
            "      }",
            "    }",
            "    if (tailMatch.length === 0) {",
            "      tailMatch.push(`MATCH,${primaryGroup}`);",
            "    }",
            "    config.rules = [...topRules, ...middle, ...fallbackRules, ...tailMatch];",
            "",
            "    if (CLEAN_DNS_ENABLE) {",
            "      config.dns = Object.assign({}, config.dns || {}, CLEAN_DNS_OBJ);",
            "    }",
            "    if (NEED_PROCESS_MODE) {",
            "      config['find-process-mode'] = 'strict';",
            "    }",
            "    if (LOCAL_CONTROLLER_ADDR && !config['external-controller']) {",
            "      config['external-controller'] = LOCAL_CONTROLLER_ADDR;",
            "      if (LOCAL_CONTROLLER_SECRET && !config.secret) {",
            "        config.secret = LOCAL_CONTROLLER_SECRET;",
            "      }",
            "    }",
            "    return config;",
            "  } catch (e) {",
            "    return config;",
            "  }",
            "};",
        ]
        return "\n".join(js_lines) + "\n"

    @staticmethod
    def _detect_profile_type_col(cur):
        cols = {row[1] for row in cur.execute("PRAGMA table_info(profiles)").fetchall()}
        if "extend_type" in cols:
            return "extend_type"
        if "overwrite_type" in cols:
            return "overwrite_type"
        return None

    def _clean_legacy_profile_markers(self):
        cleaned = []
        if not os.path.isdir(self.profiles_dir):
            return cleaned
        pat = re.compile(
            r"[ \t]*# === RULE_PILOT_CUSTOM_RULES_START ===.*?# === RULE_PILOT_CUSTOM_RULES_END ===[ \t]*\r?\n?",
            re.DOTALL,
        )
        for fn in os.listdir(self.profiles_dir):
            if not (fn.endswith(".yaml") or fn.endswith(".yml")):
                continue
            p = os.path.join(self.profiles_dir, fn)
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                if "RULE_PILOT_CUSTOM_RULES_START" in content:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(pat.sub("", content))
                    cleaned.append(fn)
            except Exception:
                pass
        return cleaned

    def apply_flclash_native_script(self):
        os.makedirs(self.scripts_dir, exist_ok=True)
        with open(self.script_file_path, "w", encoding="utf-8") as f:
            f.write(self._generate_flclash_js())

        if not os.path.exists(self.db_path):
            return False, "未找到 FlClash database.sqlite"

        now_ms = int(time.time() * 1000)
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            cur = conn.cursor()
            type_col = self._detect_profile_type_col(cur)
            if not type_col:
                return False, "无法识别订阅表的覆写类型列"
            cur.execute(
                """
                INSERT INTO scripts (id, label, last_update_time)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  label = excluded.label,
                  last_update_time = excluded.last_update_time
                """,
                (FLCLASH_SCRIPT_ID, FLCLASH_SCRIPT_LABEL, now_ms),
            )
            cur.execute(
                f"UPDATE profiles SET {type_col} = 'script', script_id = ?",
                (FLCLASH_SCRIPT_ID,),
            )
            affected = cur.rowcount
            conn.commit()
            return True, f"已写入原生覆写脚本并绑定全部 {affected} 个订阅"
        finally:
            conn.close()

    def sync_shared_preferences(self, enable_dns=None):
        if not os.path.exists(self.shared_pref_path):
            return False, "未找到 shared_preferences.json"
        try:
            with open(self.shared_pref_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = json.loads(data.get("flutter.config", "{}"))

            clean_dns = bool(self.rule_manager.rules_data.get("clean_dns_override", True)) if enable_dns is None else bool(enable_dns)
            cfg["overrideDns"] = clean_dns
            patch_cfg = cfg.setdefault("patchClashConfig", {})
            if clean_dns:
                patch_cfg["dns"] = CLEAN_DNS_CONFIG

            # 为本地热重载预配置回环 REST 控制器（若用户已配置端口则完整保留）
            if self.rule_manager.rules_data.get("enable_local_controller", True) and enable_dns is not False:
                cur_ec = str(patch_cfg.get("external-controller") or "").strip()
                if not cur_ec:
                    free_port = NetworkHelper.pick_free_loopback_port(19090, 20)
                    patch_cfg["external-controller"] = f"127.0.0.1:{free_port}"
                if not str(patch_cfg.get("secret") or "").strip():
                    patch_cfg["secret"] = secrets.token_hex(12)
                g_keys = list(patch_cfg.get("general-override-keys") or [])
                for k in ("external-controller", "secret"):
                    if k not in g_keys:
                        g_keys.append(k)
                patch_cfg["general-override-keys"] = g_keys

            _, _, need_process = self.rule_manager.get_compiled_rules()
            if enable_dns is False:
                patch_cfg["find-process-mode"] = "off"
            elif need_process:
                patch_cfg["find-process-mode"] = "strict"
            elif patch_cfg.get("find-process-mode") == "strict":
                patch_cfg["find-process-mode"] = "off"

            if self.rule_manager.rules_data.get("sync_system_bypass", True):
                network_props = cfg.setdefault("networkProps", {})
                bypass_list = list(network_props.get("bypassDomain", []))
                must_bypass = [
                    "localhost", "*.local", "127.*", "10.*",
                    "172.16.*", "172.17.*", "172.18.*", "172.19.*",
                    "172.2*", "172.30.*", "172.31.*", "192.168.*",
                    "*.qq.com", "*.weixin.qq.com", "*.wechat.com",
                    "*.douyin.com", "*.douyincdn.com",
                    "*.xiaohongshu.com", "*.xhscdn.com",
                    "*.bilibili.com", "*.bilivideo.com",
                    "*.kuaishou.com", "*.kwaicdn.com",
                    "*.bing.com", "*.baidu.com", "*.baidupcs.com",
                    "*.quark.cn", "*.feishu.cn",
                ]
                for mb in must_bypass:
                    if mb not in bypass_list:
                        bypass_list.append(mb)
                for r in self.rule_manager.list_rules():
                    if r.get("target", "").upper() == "DIRECT":
                        rtype = r.get("type", "").upper()
                        pat = r.get("pattern", "")
                        if rtype in ("DOMAIN", "DOMAIN-SUFFIX"):
                            fmt = f"*.{pat}" if not pat.startswith("*") else pat
                            if fmt not in bypass_list and pat not in bypass_list:
                                bypass_list.append(fmt)
                        elif rtype == "IP-CIDR" and pat.endswith("/32"):
                            ip_only = pat[:-3]
                            if ip_only not in bypass_list:
                                bypass_list.append(ip_only)
                network_props["bypassDomain"] = bypass_list

            data["flutter.config"] = json.dumps(cfg, ensure_ascii=False)
            with open(self.shared_pref_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return True, f"已同步全局 DNS 与系统绕过设置（洁净 DNS: {'开启' if clean_dns else '关闭'}）"
        except Exception as e:
            return False, f"同步 shared_preferences.json 失败: {e}"

    def _inject_yaml_file(self, file_path):
        """面向 Clash Verge / Mihomo Party 等非 SQLite 客户端的自适应缩进 YAML 注入"""
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
        bak = file_path + ".rulepilot.bak"
        if not os.path.exists(bak):
            shutil.copy2(file_path, bak)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        m = re.search(r'(?m)^rules:\s*\n([ \t]+)-\s+', content)
        indent = m.group(1) if m else "  "
        pg = self.detect_primary_proxy_group(file_path)
        top_rules, fb_rules, _ = self.rule_manager.get_compiled_rules(pg)

        block_lines = [f"{indent}{MARKER_START}"]
        for r in top_rules:
            block_lines.append(f'{indent}- "{r}"')
        block_lines.append(f"{indent}{MARKER_END}")
        block = "\n".join(block_lines) + "\n"

        pat = re.compile(
            r"[ \t]*# === RULE_PILOT_CUSTOM_RULES_START ===.*?# === RULE_PILOT_CUSTOM_RULES_END ===[ \t]*\r?\n?",
            re.DOTALL,
        )
        if "RULE_PILOT_CUSTOM_RULES_START" in content:
            new_content = pat.sub(block, content)
        else:
            rm = re.search(r'(?m)^rules:\s*\n', content)
            if rm:
                new_content = content[:rm.end()] + block + content[rm.end():]
            else:
                new_content = content + "\nrules:\n" + block

        # 若兜底区存在且文件中没有 GEOSITE,cn,DIRECT，则在 MATCH 前插入
        for fbr in fb_rules:
            if fbr not in new_content:
                mm = re.search(r'(?m)^([ \t]+-\s+[\'"]?MATCH,)', new_content)
                if mm:
                    new_content = new_content[:mm.start()] + f'{indent}- "{fbr}"\n' + new_content[mm.start():]

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True, f"已向 {os.path.basename(file_path)} 注入 {len(top_rules)} 条置顶规则"

    def apply(self):
        proxy_group = self.detect_primary_proxy_group()
        results = []
        if self.is_flclash_sqlite():
            cleaned = self._clean_legacy_profile_markers()
            if cleaned:
                results.append(f"已清理历史缩进残留: {', '.join(cleaned)}")
            _, msg = self.apply_flclash_native_script()
            results.append(msg)
            _, msg2 = self.sync_shared_preferences()
            results.append(msg2)
        else:
            if os.path.exists(self.config_yaml_path):
                _, msg = self._inject_yaml_file(self.config_yaml_path)
                results.append(msg)
            active_p = self.detect_active_profile_path()
            if active_p and os.path.exists(active_p):
                _, msg = self._inject_yaml_file(active_p)
                results.append(msg)
        return True, results, proxy_group

    def _load_managed_cache(self):
        try:
            if os.path.exists(self.managed_cache_path):
                with open(self.managed_cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return {str(x).strip() for x in data if str(x).strip()}
        except Exception:
            pass
        return set()

    def _save_managed_cache(self, rules_set):
        try:
            with open(self.managed_cache_path, "w", encoding="utf-8") as f:
                json.dump(sorted(rules_set), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _hot_sync_flclash_runtime_yaml(self, disabling=False):
        """无杀同步编译后的规则到当前运行中 config.yaml，配合 PUT /configs?force=true 50ms 热生效"""
        if not os.path.exists(self.config_yaml_path):
            return False, "no_runtime_config"
        try:
            with open(self.config_yaml_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            return False, f"read_failed: {e}"

        m = re.search(r'(?m)^rules:\s*\n((?:[ \t]+.*\n|\n)*)', text)
        if not m:
            return False, "rules_section_missing"

        pg = self.detect_primary_proxy_group(self.config_yaml_path)
        prev_managed = self._load_managed_cache()
        if disabling:
            top_rules, fb_rules = [], []
        else:
            top_rules, fb_rules, _ = self.rule_manager.get_compiled_rules(pg)

        strip_set = set(prev_managed) | set(top_rules) | set(fb_rules)
        middle = []
        tail_match = []
        for raw_line in m.group(1).splitlines():
            s = raw_line.strip()
            if not s.startswith("-"):
                continue
            item = s[1:].strip().strip("'\"")
            if not item or item in strip_set:
                continue
            if item.upper().startswith("MATCH,"):
                tail_match.append(item)
            else:
                middle.append(item)

        if not tail_match:
            tail_match.append(f"MATCH,{pg}")

        new_rules = (top_rules + middle + fb_rules + tail_match) if not disabling else (middle + tail_match)
        indent_m = re.search(r'(?m)^([ \t]+)-\s+', m.group(1))
        indent = indent_m.group(1) if indent_m else "  "
        new_block = "rules:\n" + "\n".join(f'{indent}- "{r}"' for r in new_rules) + "\n"
        new_text = text[:m.start()] + new_block + text[m.end():]

        with open(self.config_yaml_path, "w", encoding="utf-8") as f:
            f.write(new_text)

        self._save_managed_cache(set() if disabling else (set(top_rules) | set(fb_rules)))
        return self.controller.hot_reload_file(self.config_yaml_path)

    def hot_sync_runtime(self, disabling=False):
        """零杀进程热同步运行时内核配置"""
        if self.is_flclash_sqlite():
            return self._hot_sync_flclash_runtime_yaml(disabling=disabling)
        for p in [self.config_yaml_path, self.detect_active_profile_path()]:
            if p and os.path.exists(p):
                ok, detail = self.controller.hot_reload_file(p)
                if ok:
                    return True, detail
        return False, "controller_unreachable"

    @staticmethod
    def _is_flclash_running():
        if platform.system() != "Windows":
            return False
        try:
            out = run_silent_output([
                "powershell", "-NoProfile", "-Command",
                "if (Get-Process -Name FlClash -ErrorAction SilentlyContinue) { 'YES' }"
            ], timeout=4).strip()
            return out == "YES"
        except Exception:
            return False

    def safe_soft_restart_client(self, apply_before_start=True):
        """用户显式确认后的安全软重启（绝不直接强杀 FlClashCore 服务管道）"""
        if apply_before_start:
            self.apply()
        if platform.system() != "Windows":
            return True, "规则已持久化写入，请手动在代理软件内刷新一次配置", "manual_hint"
        exe = PathDetector.find_flclash_exe()
        if not exe:
            return False, "未找到代理客户端主程序，规则已写入配置", "exe_not_found"

        if self._is_flclash_running():
            # 1. 发送 WM_CLOSE 让客户端自行优雅回收 HelperService 与 Core 管道
            ps_close = (
                "$procs = Get-Process -Name FlClash -ErrorAction SilentlyContinue; "
                "foreach ($p in $procs) { try { if ($p.MainWindowHandle -ne 0) { $null = $p.CloseMainWindow() } } catch {} }"
            )
            run_silent_process(["powershell", "-NoProfile", "-Command", ps_close], timeout=6)

            closed = False
            for _ in range(12):
                time.sleep(0.5)
                if not self._is_flclash_running():
                    closed = True
                    break

            if not closed:
                # 若仅因无主窗隐藏托盘无法 CloseMainWindow，尝试温和 Stop-Process（不加 -Force，不杀 FlClashCore）
                r = run_silent_process([
                    "powershell", "-NoProfile", "-Command",
                    "Stop-Process -Name FlClash -ErrorAction Stop"
                ], timeout=6)
                if r.returncode != 0:
                    return (
                        False,
                        "代理客户端可能以管理员权限运行或正在忙，为防止断网失控已取消重启；请在客户端托盘手动退出重开一次即可",
                        "need_admin",
                    )
                for _ in range(10):
                    time.sleep(0.5)
                    if not self._is_flclash_running():
                        closed = True
                        break

            if not closed:
                return False, "客户端正在繁忙状态未能优雅退出，规则已安全保存，请手动重开一次", "busy_timeout"
            time.sleep(1.0)

        try:
            creation_kw = {"cwd": os.path.dirname(exe)}
            if platform.system() == "Windows":
                creation_kw["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            subprocess.Popen([exe], **creation_kw)
            deadline = time.time() + 12
            start_ts = time.time() - 1
            while time.time() < deadline:
                if os.path.exists(self.config_yaml_path) and os.path.getmtime(self.config_yaml_path) >= start_ts:
                    time.sleep(0.8)
                    break
                time.sleep(0.5)
            return True, "已安全重启代理客户端并激活最新规则与零杀热重载端口", "safe_restarted"
        except Exception as e:
            return False, f"拉起客户端失败（请手动打开客户端，规则已保存）: {e}", "launch_failed"

    def reload_flclash(self, apply_before_start=True, allow_process_restart=False):
        """零杀进程热重载入口（默认绝不杀死本体，优先通过 Mihomo API 热重载）"""
        if allow_process_restart:
            ok, msg, mode = self.safe_soft_restart_client(apply_before_start=apply_before_start)
            self._last_reload_mode = mode
            return ok, msg

        if apply_before_start:
            self.apply()

        hr_ok, hr_detail = self.hot_sync_runtime(disabling=False)
        if hr_ok:
            self._last_reload_mode = "hot_reload"
            return True, "已通过内核热重载即时生效（零断网、未重启客户端）"

        if not self.is_flclash_sqlite():
            self._last_reload_mode = "yaml_injected"
            return True, "规则已写入本地配置文件（如未生效，请在客户端点击一次更新/重载配置）"

        if not self._is_flclash_running():
            self._last_reload_mode = "saved_offline"
            return True, "已写入原生持久化覆写与零杀端口配置（下次打开客户端自动生效）"

        self._last_reload_mode = "pending_activation"
        return (
            True,
            "持久化保护与零杀热重载端口已配置就绪（未中断当前客户端与网络）；请在客户端切换一次节点/配置，或使用一次「安全软重启」以激活 50ms 免杀热生效",
        )

    def one_click_enable(self):
        """一键开启防漏保护（零杀热重载版）"""
        for key in ("cn_live_streaming", "cn_daily_apps_sites", "cn_cloud_upload", "cn_geosite_fallback"):
            self.rule_manager.rules_data.setdefault("presets", {})[key] = True
        self.rule_manager.rules_data["clean_dns_override"] = True
        self.rule_manager.rules_data["enable_local_controller"] = True
        self.rule_manager.save()
        ok, msg = self.reload_flclash(apply_before_start=True, allow_process_restart=False)
        diag = self.run_diagnostics()
        diag["reload_mode"] = getattr(self, "_last_reload_mode", "pending_activation")
        return ok, msg, diag

    def one_click_disable(self):
        """一键暂停保护并无痕还原（零杀热重载版）"""
        ok, msg = self.restore_backup(disable_dns=True)
        hr_ok, _ = self.hot_sync_runtime(disabling=True)
        if hr_ok:
            msg = "已热还原订阅默认分流规则（未中断网络、未重启客户端）"
            mode = "hot_reload"
        elif self.is_flclash_sqlite() and self._is_flclash_running():
            msg = "已解除持久化覆写脚本绑定（未强杀客户端，切换一次配置或软重启即可完全恢复原规则）"
            mode = "pending_activation"
        else:
            mode = "yaml_restored"
        self._last_reload_mode = mode
        diag = self.run_diagnostics()
        diag["reload_mode"] = mode
        return ok, msg, diag

    def restore_backup(self, disable_dns=False):
        if self.is_flclash_sqlite():
            conn = sqlite3.connect(self.db_path, timeout=10)
            try:
                cur = conn.cursor()
                type_col = self._detect_profile_type_col(cur) or "extend_type"
                cur.execute(
                    f"UPDATE profiles SET {type_col} = 'standard', script_id = NULL WHERE script_id = ?",
                    (FLCLASH_SCRIPT_ID,),
                )
                cur.execute("DELETE FROM scripts WHERE id = ?", (FLCLASH_SCRIPT_ID,))
                conn.commit()
            finally:
                conn.close()
            if os.path.exists(self.script_file_path):
                try:
                    os.remove(self.script_file_path)
                except Exception:
                    pass
            if disable_dns:
                self.sync_shared_preferences(enable_dns=False)
            return True, "已解除 FlClash 原生覆写脚本绑定"

        restored = []
        for p in [self.config_yaml_path, self.detect_active_profile_path()]:
            if p and os.path.exists(p + ".rulepilot.bak"):
                shutil.copy2(p + ".rulepilot.bak", p)
                restored.append(os.path.basename(p))
        if restored:
            return True, f"已恢复原始配置备份: {', '.join(restored)}"
        return False, "未找到可恢复的配置备份"

    # ========================= 规则解析与体检引擎 =========================
    def _parse_active_config_rules(self):
        if not os.path.exists(self.config_yaml_path):
            return [], {"nameserver": [], "enhanced_mode": "", "has_foreign_in_nameserver": False}
        with open(self.config_yaml_path, "r", encoding="utf-8") as f:
            text = f.read()

        rules = []
        m = re.search(r'(?m)^rules:\s*\n((?:[ \t]+.*\n|\n)*)', text)
        if m:
            for line in m.group(1).splitlines():
                s = line.strip()
                if s.startswith("-"):
                    item = s[1:].strip().strip("'\"")
                    if item:
                        rules.append(item)

        dns_info = {"nameserver": [], "enhanced_mode": "", "has_foreign_in_nameserver": False}
        dm = re.search(r'(?m)^dns:\s*\n((?:[ \t]+.*\n|\n)*)', text)
        if dm:
            dtxt = dm.group(1)
            em = re.search(r'enhanced-mode:\s*[\'"]?([a-zA-Z0-9_-]+)', dtxt)
            if em:
                dns_info["enhanced_mode"] = em.group(1)
            nm = re.search(r'(?m)^[ \t]+nameserver:\s*\n((?:[ \t]+-.*\n)+)', dtxt)
            if nm:
                ns = [l.strip()[1:].strip().strip("'\"") for l in nm.group(1).splitlines() if l.strip().startswith("-")]
                dns_info["nameserver"] = ns
                foreign_markers = ("8.8.8.8", "8.8.4.4", "1.1.1.1", "dns.google", "cloudflare")
                dns_info["has_foreign_in_nameserver"] = any(
                    any(fm in entry.lower() for fm in foreign_markers) for entry in ns
                )
        return rules, dns_info

    @staticmethod
    def match_target_against_rules(target: str, rules: list):
        is_ip = False
        ip_obj = None
        try:
            ip_obj = ipaddress.ip_address(target)
            is_ip = True
        except ValueError:
            pass

        host = target.lower()
        for idx, rule in enumerate(rules, 1):
            parts = [p.strip() for p in rule.split(",")]
            if len(parts) < 2:
                continue
            rtype = parts[0].upper()
            if rtype == "MATCH":
                return {"action": parts[1], "rule": rule, "line": idx}
            if len(parts) < 3:
                continue
            val, act = parts[1], parts[2]
            val_low = val.lower()

            if not is_ip:
                if rtype == "DOMAIN" and host == val_low:
                    return {"action": act, "rule": rule, "line": idx}
                if rtype == "DOMAIN-SUFFIX" and (host == val_low or host.endswith("." + val_low)):
                    return {"action": act, "rule": rule, "line": idx}
                if rtype == "DOMAIN-KEYWORD" and val_low in host:
                    return {"action": act, "rule": rule, "line": idx}
                if rtype == "GEOSITE" and val_low == "cn" and host.endswith(".cn"):
                    return {"action": act, "rule": rule, "line": idx}
            else:
                if rtype in ("IP-CIDR", "IP-CIDR6"):
                    try:
                        net = ipaddress.ip_network(val, strict=False)
                        if ip_obj.version == net.version and ip_obj in net:
                            return {"action": act, "rule": rule, "line": idx}
                    except ValueError:
                        pass
        return {"action": "UNKNOWN", "rule": "未匹配", "line": 0}

    def get_subscription_traffic(self):
        stats = []
        if not os.path.exists(self.db_path):
            return stats
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cur = conn.cursor()
            type_col = self._detect_profile_type_col(cur) or "extend_type"
            rows = cur.execute(
                f"SELECT id, label, {type_col}, script_id, auto_update, subscription_info FROM profiles ORDER BY \"order\" ASC"
            ).fetchall()
            conn.close()
            for pid, label, otype, sid, auto_up, sinfo in rows:
                up_gb = down_gb = total_gb = 0.0
                if sinfo:
                    try:
                        j = json.loads(sinfo)
                        up_gb = round((j.get("upload", 0) or 0) / (1024 ** 3), 2)
                        down_gb = round((j.get("download", 0) or 0) / (1024 ** 3), 2)
                        total_gb = round((j.get("total", 0) or 0) / (1024 ** 3), 2)
                    except Exception:
                        pass
                used = up_gb + down_gb
                up_ratio = round((up_gb / used) * 100, 1) if used > 0 else 0.0
                stats.append({
                    "id": str(pid),
                    "label": label,
                    "overwrite_type": otype,
                    "script_bound": (otype == "script" and sid == FLCLASH_SCRIPT_ID),
                    "auto_update": bool(auto_up),
                    "upload_gb": up_gb,
                    "download_gb": down_gb,
                    "total_gb": total_gb,
                    "upload_ratio": up_ratio,
                })
        except Exception:
            pass
        return stats

    def run_diagnostics(self, extra_domains=None):
        rules, dns_info = self._parse_active_config_rules()
        subs = self.get_subscription_traffic()

        has_geosite_cn = any(r.upper().startswith("GEOSITE,CN,DIRECT") for r in rules)
        has_douyin = any("douyincdn.com,DIRECT" in r for r in rules)
        has_tlive = any("tlivepush.com,DIRECT" in r for r in rules)
        has_bili = any("bilivideo.com,DIRECT" in r for r in rules)
        has_bing = any("bing.com,DIRECT" in r for r in rules)

        probes_list = list(DIAGNOSTIC_PROBES)
        if extra_domains:
            for d in extra_domains:
                cleaned = DomainAnalyzer.clean_host(d)
                if cleaned:
                    probes_list.append((cleaned, "ANY", "自定义检测"))

        probe_results = []
        passed = 0
        total_checked = 0
        probe_key_map = {
            "push-rtmp-l11.douyincdn.com": "probe.douyin_push",
            "live-push.bilivideo.com": "probe.bili_push",
            "push.tlivepush.com": "probe.tlive_push",
            "channels.weixin.qq.com": "probe.wechat_channels",
            "livepush.myqcloud.com": "probe.qcloud_push",
            "push.alivecdn.com": "probe.ali_push",
            "push.kwaicdn.com": "probe.kuaishou_push",
            "live.xiaohongshu.com": "probe.xhs_live",
            "www.bing.com": "probe.bing",
            "www.baidu.com": "probe.baidu",
            "im.qq.com": "probe.qq",
            "wx.qq.com": "probe.wechat",
            "www.douyin.com": "probe.douyin_web",
            "www.xiaohongshu.com": "probe.xhs_web",
            "www.bilibili.com": "probe.bili_web",
            "pan.quark.cn": "probe.quark",
            "d.pcs.baidu.com": "probe.baidu_pcs",
            "api.aliyundrive.com": "probe.alipan",
            "127.0.0.1": "probe.loopback",
            "192.168.1.1": "probe.lan",
            "a.rtmp.youtube.com": "probe.youtube_push",
            "live.twitch.tv": "probe.twitch_push",
            "api.openai.com": "probe.openai",
            "www.google.com": "probe.google",
        }
        for host, expected, desc in probes_list:
            res = self.match_target_against_rules(host, rules)
            actual_cat = "DIRECT" if res["action"].upper() == "DIRECT" else (
                "REJECT" if res["action"].upper() == "REJECT" else "PROXY"
            )
            ok = True if expected == "ANY" else (actual_cat == expected)
            if expected != "ANY":
                total_checked += 1
                if ok:
                    passed += 1
            unmatched = (res["action"] == "UNKNOWN" or res["line"] == 0)
            probe_results.append({
                "host": host,
                "desc": desc,
                "desc_key": probe_key_map.get(host, "probe.custom"),
                "expected": expected,
                "actual_action": res["action"],
                "actual_category": actual_cat,
                "matched_rule": res["rule"],
                "unmatched": unmatched,
                "line": res["line"],
                "ok": ok,
            })

        override_dns_pref = False
        if os.path.exists(self.shared_pref_path):
            try:
                with open(self.shared_pref_path, "r", encoding="utf-8") as f:
                    sp = json.load(f)
                override_dns_pref = bool(json.loads(sp.get("flutter.config", "{}")).get("overrideDns", False))
            except Exception:
                pass

        if self.is_flclash_sqlite():
            all_bound = bool(subs) and all(s["script_bound"] for s in subs)
            protection_active = os.path.exists(self.script_file_path) and all_bound
        else:
            all_bound = True
            has_marker = False
            for p in [self.config_yaml_path, self.detect_active_profile_path()]:
                if p and os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            if MARKER_START in f.read():
                                has_marker = True
                                break
                    except Exception:
                        pass
            protection_active = has_marker or (has_douyin and has_tlive and has_bili)

        healthy = (
            protection_active
            and passed == total_checked
            and has_geosite_cn
            and not dns_info["has_foreign_in_nameserver"]
        )

        config_exists = os.path.exists(self.config_yaml_path)
        return {
            "protection_active": protection_active,
            "healthy": healthy,
            "client_label": self.detect_client_label(),
            "client_key": self.detect_client_key(),
            "total_active_rules": len(rules),
            "script_exists": os.path.exists(self.script_file_path),
            "all_profiles_bound": all_bound,
            "override_dns_pref": override_dns_pref,
            "dns": dns_info,
            "checks": {
                "geosite_cn": has_geosite_cn,
                "douyin_push": has_douyin,
                "tencent_push": has_tlive,
                "bili_push": has_bili,
                "bing_direct": has_bing,
                "clean_dns": not dns_info["has_foreign_in_nameserver"],
            },
            "probe_summary": {"passed": passed, "total": total_checked},
            "probes": probe_results,
            "subscriptions": subs,
            "controller": self.controller.get_status(),
            "config_exists": config_exists,
            "config_mtime": (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(self.config_yaml_path)))
                if config_exists else "未检测到"
            ),
        }


class SystemScanner:
    """三大零门槛扫描器：实时活跃域名 / 文本提取 / 本机软件扫描"""

    @staticmethod
    def _aggregate_hosts(raw_hosts, injector: ConfigInjector, proc_map=None):
        rules, _ = injector._parse_active_config_rules()
        grouped = {}
        proc_map = proc_map or {}
        for h in raw_hosts:
            cleaned = DomainAnalyzer.clean_host(h)
            if not cleaned or DomainAnalyzer.is_noise_host(cleaned):
                continue
            root = DomainAnalyzer.extract_root_domain(cleaned)
            if not root:
                continue
            entry = grouped.setdefault(root, {"subdomains": set(), "processes": set()})
            entry["subdomains"].add(cleaned)
            for p in proc_map.get(cleaned, ()):
                if p:
                    entry["processes"].add(p)

        items = []
        for root, data in grouped.items():
            subs = sorted(data["subdomains"])
            procs = sorted(data["processes"])[:4]
            label, region, label_key = DomainAnalyzer.classify_domain_with_key(root)
            sample_host = subs[0] if subs else root
            m = injector.match_target_against_rules(sample_host, rules)
            act_cat = "DIRECT" if m["action"].upper() == "DIRECT" else (
                "REJECT" if m["action"].upper() == "REJECT" else "PROXY"
            )
            if act_cat == "DIRECT":
                rec = "already_direct"
                priority = 3
            elif region == "cn":
                rec = "suggest_direct"
                priority = 0
            elif region == "global":
                rec = "keep_proxy"
                priority = 4
            else:
                rec = "review"
                priority = 1

            items.append({
                "root_domain": root,
                "label": label,
                "label_key": label_key,
                "region": region,
                "subdomains": subs[:12],
                "subdomain_count": len(subs),
                "processes": procs,
                "current_action": m["action"],
                "current_category": act_cat,
                "matched_rule": m["rule"],
                "recommendation": rec,
                "_priority": priority,
            })

        items.sort(key=lambda x: (x["_priority"], -x["subdomain_count"], x["root_domain"]))
        for it in items:
            it.pop("_priority", None)
        return items

    @classmethod
    def scan_live_domains(cls, injector: ConfigInjector):
        raw_hosts = []
        proc_map = {}
        source_desc = ""
        source_key = "unsupported_os"
        os_type = platform.system().lower()

        ctrl_live_ok, ctrl_conns = injector.controller.get_live_connections()
        if ctrl_live_ok and ctrl_conns:
            for c in ctrl_conns:
                ch = DomainAnalyzer.clean_host(c["host"])
                if ch:
                    raw_hosts.append(ch)
                    if c.get("process"):
                        proc_map.setdefault(ch, set()).add(c["process"])

        dns_hosts = []
        if os_type == "windows":
            try:
                out = run_silent_output(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-DnsClientCache -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Entry -Unique"],
                    timeout=8,
                )
                dns_hosts = [line.strip() for line in out.splitlines() if line.strip()]
                source_desc = "Windows 本机实时 DNS 活跃缓存"
                source_key = "win_dns_cache"
            except Exception:
                pass
            if not dns_hosts:
                try:
                    out = run_silent_output(["ipconfig", "/displaydns"], timeout=8)
                    dns_hosts = DomainAnalyzer.extract_hosts_from_text(out)
                    source_desc = "Windows ipconfig DNS 缓存"
                    source_key = "win_ipconfig"
                except Exception:
                    pass
        else:
            try:
                out = run_silent_output(["lsof", "-i", "-P", "-n"], timeout=6)
                dns_hosts = DomainAnalyzer.extract_hosts_from_text(out)
                source_desc = "本机活跃网络连接"
                source_key = "unix_lsof"
            except Exception:
                source_desc = "当前系统暂不支持直接读取 DNS 缓存，可使用“粘贴文本提取”"
                source_key = "unsupported_os"

        raw_hosts.extend(dns_hosts)
        if ctrl_live_ok and ctrl_conns:
            source_desc = "Mihomo 核心实时连接 + 本机缓存"
            source_key = "mihomo_live"

        items = cls._aggregate_hosts(raw_hosts, injector, proc_map=proc_map)
        return {
            "source": source_desc,
            "source_key": source_key,
            "controller_live": bool(ctrl_live_ok),
            "raw_count": len(raw_hosts),
            "root_count": len(items),
            "suggest_direct_count": sum(1 for x in items if x["recommendation"] == "suggest_direct"),
            "items": items,
        }

    @classmethod
    def scan_text_domains(cls, text: str, injector: ConfigInjector):
        raw_hosts = DomainAnalyzer.extract_hosts_from_text(text)
        items = cls._aggregate_hosts(raw_hosts, injector)
        return {
            "source": "文本 / 网址 / 推流链接自动提取",
            "source_key": "text_extract",
            "raw_count": len(raw_hosts),
            "root_count": len(items),
            "suggest_direct_count": sum(1 for x in items if x["recommendation"] == "suggest_direct"),
            "items": items,
        }

    @classmethod
    def scan_local_apps(cls, rule_mgr: RuleManager, injector: ConfigInjector):
        running_set = set()
        if platform.system() == "Windows":
            try:
                out = run_silent_output(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-Process -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName -Unique"],
                    timeout=6,
                )
                running_set = {f"{x.strip().lower()}.exe" for x in out.splitlines() if x.strip()}
            except Exception:
                pass

        top_rules, _, _ = rule_mgr.get_compiled_rules()
        active_proc_direct = {
            r.split(",")[1].strip().lower()
            for r in top_rules
            if r.upper().startswith("PROCESS-NAME,") and ",DIRECT" in r.upper()
        }

        cat_key_map = {
            "聊天与视频号": "app_cat.chat_channels",
            "内地办公": "app_cat.office",
            "聊天社交": "app_cat.social",
            "内地直播与视频": "app_cat.live_video",
            "内地推流软件": "app_cat.streaming",
            "内地网盘": "app_cat.cloud",
            "内地 AI 工具": "app_cat.ai",
            "内地创作工具": "app_cat.other",
            "内地影音": "app_cat.media",
            "内地下载": "app_cat.download",
            "内地游戏平台": "app_cat.game",
        }
        apps = []
        for item in KNOWN_CN_APPS:
            exe_low = item["exe"].lower()
            stem = exe_low.rsplit(".", 1)[0]
            is_running = exe_low in running_set
            is_direct = exe_low in active_proc_direct
            apps.append({
                "exe": item["exe"],
                "name": item["name"],
                "name_key": f"app.{stem}",
                "category": item["category"],
                "category_key": cat_key_map.get(item["category"], "app_cat.other"),
                "running": is_running,
                "is_direct": is_direct,
            })

        apps.sort(key=lambda a: (0 if a["running"] else 1, 0 if not a["is_direct"] else 1, a["category"], a["name"]))
        return {
            "total": len(apps),
            "running_count": sum(1 for a in apps if a["running"]),
            "direct_count": sum(1 for a in apps if a["is_direct"]),
            "items": apps,
        }


def export_public_package(script_dir=None):
    """一键打包纯净公共分发版 ZIP（自动排除个人规则与备份，内置隐私零泄漏检查）"""
    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(script_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    zip_name = f"RulePilot-Public-v{VERSION}.zip"
    zip_path = os.path.join(dist_dir, zip_name)

    include_files = [
        ".gitignore",
        "LICENSE",
        "DISCLAIMER.md",
        "README.md",
        "README_zh_CN.md",
        "rule_pilot.py",
        "ui.html",
        "custom_rules.example.json",
        "start-browser.bat",
        "start-app-window.bat",
        "start.bat",
        "start-web.ps1",
        "start-web.sh",
        "start-macos.command",
        "start-background.vbs",
        "stop-background.bat",
        "create-desktop-shortcut.ps1",
    ]
    included = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fn in include_files:
            fp = os.path.join(script_dir, fn)
            if os.path.exists(fp):
                zf.write(fp, arcname=f"RulePilot-Public-v{VERSION}/{fn}")
                included.append(fn)
        shots_dir = os.path.join(script_dir, "docs", "screenshots")
        if os.path.isdir(shots_dir):
            for fn in sorted(os.listdir(shots_dir)):
                fp = os.path.join(shots_dir, fn)
                if os.path.isfile(fp) and fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    zf.write(fp, arcname=f"RulePilot-Public-v{VERSION}/docs/screenshots/{fn}")
                    included.append(f"docs/screenshots/{fn}")
    return True, zip_path, included


# ========================= One UI 规范 WebUI 加载器 =========================
def load_ui_html():
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return f.read().replace("__VERSION__", VERSION).replace("__EDITION__", EDITION)
    return f"<!DOCTYPE html><html lang='zh-CN'><body><h1>RulePilot v{VERSION}</h1><p>未找到 ui.html</p></body></html>"


class WebServerHandler(BaseHTTPRequestHandler):
    injector: ConfigInjector = None
    rule_mgr: RuleManager = None

    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except Exception:
            pass

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            qs = urllib.parse.parse_qs(parsed.query)

            if path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(load_ui_html().encode("utf-8"))
                return

            if path == "/favicon.ico":
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(FAVICON_SVG.encode("utf-8"))
                return

            if path == "/api/status":
                preset_meta = [
                    {"key": k, "name": v["name"], "desc": v["desc"], "count": len(v["rules"])}
                    for k, v in PRESET_PACKS.items()
                ]
                self._send_json({
                    "os": platform.system(),
                    "version": VERSION,
                    "edition": EDITION,
                    "clash_dir": self.injector.clash_dir,
                    "client_label": self.injector.detect_client_label(),
                    "client_key": self.injector.detect_client_key(),
                    "detected_clients": PathDetector.discover_clients(),
                    "primary_proxy_group": self.injector.detect_primary_proxy_group(),
                    "physical_ip": NetworkHelper.get_physical_ip(),
                    "clean_dns_override": self.rule_mgr.rules_data.get("clean_dns_override", True),
                    "enable_local_controller": self.rule_mgr.rules_data.get("enable_local_controller", True),
                    "controller": self.injector.controller.get_status(),
                    "presets": self.rule_mgr.rules_data.get("presets", {}),
                    "preset_meta": preset_meta,
                    "rules": self.rule_mgr.list_rules(),
                })
                return

            if path == "/api/rules":
                self._send_json(self.rule_mgr.list_rules())
                return

            if path == "/api/rules/export":
                self._send_json({
                    "version": 3,
                    "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "presets": self.rule_mgr.rules_data.get("presets", {}),
                    "rules": self.rule_mgr.list_rules(),
                })
                return

            if path == "/api/check":
                extra = []
                if "extra" in qs:
                    extra = [x.strip() for x in re.split(r"[,\s]+", qs["extra"][0]) if x.strip()]
                self._send_json(self.injector.run_diagnostics(extra_domains=extra))
                return

            if path == "/api/scan/live":
                self._send_json(SystemScanner.scan_live_domains(self.injector))
                return

            if path == "/api/scan/apps":
                self._send_json(SystemScanner.scan_local_apps(self.rule_mgr, self.injector))
                return

            self.send_error(404, "Not Found")
        except Exception as e:
            try:
                self.send_error(500, str(e))
            except Exception:
                pass

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                req_data = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                req_data = {}

            if path == "/api/one_click_enable":
                ok, msg, diag = self.injector.one_click_enable()
                rmode = diag.get("reload_mode", "pending_activation")
                mkey = "toast.enable_hot" if (ok and rmode == "hot_reload") else (
                    "toast.enable_pending" if (ok and rmode == "pending_activation") else (
                        "toast.enable_ok" if ok else "toast.enable_fail"
                    )
                )
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "reload_mode": rmode,
                    "message_key": mkey,
                    "message_params": {"error": msg},
                    "diagnostics": diag,
                })
                return

            if path == "/api/one_click_disable":
                ok, msg, diag = self.injector.one_click_disable()
                rmode = diag.get("reload_mode", "yaml_restored")
                mkey = "toast.disable_hot" if (ok and rmode == "hot_reload") else (
                    "toast.disable_pending" if (ok and rmode == "pending_activation") else (
                        "toast.disable_ok" if ok else "toast.disable_fail"
                    )
                )
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "reload_mode": rmode,
                    "message_key": mkey,
                    "message_params": {"error": msg},
                    "diagnostics": diag,
                })
                return

            if path == "/api/client/safe_restart":
                ok, msg, mode = self.injector.safe_soft_restart_client(apply_before_start=True)
                key_map = {
                    "safe_restarted": "toast.safe_restart_ok",
                    "need_admin": "toast.restart_need_admin",
                    "busy_timeout": "toast.restart_busy",
                    "exe_not_found": "toast.restart_no_exe",
                }
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "reload_mode": mode,
                    "message_key": key_map.get(mode, "toast.safe_restart_ok" if ok else "toast.reload_fail"),
                    "message_params": {"error": msg},
                    "controller": self.injector.controller.get_status(),
                })
                return

            if path == "/api/scan/text":
                text = req_data.get("text", "")
                self._send_json(SystemScanner.scan_text_domains(text, self.injector))
                return

            if path == "/api/client/select":
                new_dir = str(req_data.get("dir", "")).strip()
                if not new_dir or not os.path.isdir(new_dir):
                    self._send_json({
                        "success": False,
                        "message": "指定的代理软件配置目录不存在",
                        "message_key": "toast.dir_missing",
                    }, 400)
                    return
                self.rule_mgr.set_option("custom_clash_dir", new_dir)
                self.injector.set_clash_dir(new_dir)
                self._send_json({
                    "success": True,
                    "message": f"已切换至配置目录: {new_dir}",
                    "message_key": "toast.dir_switched",
                    "message_params": {"dir": new_dir},
                })
                return

            if path == "/api/option":
                ok, msg = self.rule_mgr.set_option(req_data.get("key", ""), req_data.get("value"))
                if ok:
                    self.injector.apply()
                    self.injector.hot_sync_runtime(disabling=False)
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "message_key": "toast.option_saved" if ok else "toast.option_invalid",
                    "message_params": {"key": req_data.get("key", "")},
                })
                return

            if path == "/api/rules/batch_add":
                items = req_data.get("items", [])
                target = req_data.get("target", "DIRECT")
                comment = req_data.get("comment", "")
                position = req_data.get("position", "top")
                collapse_root = bool(req_data.get("collapse_to_root", False))
                auto_reload = bool(req_data.get("auto_reload", False))
                added = 0
                for it in items:
                    ok, _ = self.rule_mgr.add_rule(
                        it, target, comment=comment, position=position, collapse_to_root=collapse_root
                    )
                    if ok:
                        added += 1
                rmode = "persisted"
                if auto_reload:
                    _, rmsg = self.injector.reload_flclash(apply_before_start=True, allow_process_restart=False)
                    rmode = getattr(self.injector, "_last_reload_mode", "pending_activation")
                    msg = f"已添加/更新 {added} 条规则，{rmsg}"
                    mkey = "toast.batch_added_hot" if rmode == "hot_reload" else (
                        "toast.batch_added_pending" if rmode == "pending_activation" else "toast.batch_added_reload"
                    )
                else:
                    self.injector.apply()
                    msg = f"已添加/更新 {added} 条规则"
                    mkey = "toast.batch_added"
                self._send_json({
                    "success": True,
                    "message": msg,
                    "reload_mode": rmode,
                    "message_key": mkey,
                    "message_params": {"count": added},
                    "added": added,
                })
                return

            if path == "/api/rules/toggle_target":
                pat = req_data.get("pattern", "")
                ok, msg = self.rule_mgr.toggle_rule_target(pat, req_data.get("rule_type"))
                new_target = ""
                if ok:
                    self.injector.apply()
                    self.injector.hot_sync_runtime(disabling=False)
                    for r in self.rule_mgr.list_rules():
                        if r["pattern"].lower() == pat.strip().lower():
                            new_target = r.get("target", "DIRECT")
                            break
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "message_key": ("toast.toggled_direct" if new_target == "DIRECT" else "toast.toggled_proxy") if ok else "toast.rule_not_found",
                    "message_params": {"pattern": pat},
                })
                return

            if path == "/api/rules/delete":
                pat = req_data.get("pattern", "")
                ok, msg = self.rule_mgr.remove_rule(pat, req_data.get("rule_type"))
                if ok:
                    self.injector.apply()
                    self.injector.hot_sync_runtime(disabling=False)
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "message_key": "toast.rule_deleted" if ok else "toast.rule_not_found",
                    "message_params": {"pattern": pat},
                })
                return

            if path == "/api/rules/clear":
                ok, msg = self.rule_mgr.clear_rules()
                self.injector.apply()
                self.injector.hot_sync_runtime(disabling=False)
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "message_key": "toast.rules_cleared",
                })
                return

            if path == "/api/rules/import":
                ok, msg = self.rule_mgr.import_rules_payload(req_data)
                if ok:
                    self.injector.apply()
                    self.injector.hot_sync_runtime(disabling=False)
                count_m = re.search(r"(\d+)", msg)
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "message_key": "toast.import_ok" if ok else "toast.import_invalid",
                    "message_params": {"count": int(count_m.group(1)) if count_m else 0},
                })
                return

            if path == "/api/apply":
                ok, results, proxy_g = self.injector.apply()
                hr_ok, _ = self.injector.hot_sync_runtime(disabling=False)
                self._send_json({
                    "success": ok,
                    "details": results,
                    "proxy_group": proxy_g,
                    "reload_mode": "hot_reload" if hr_ok else "persisted",
                    "message_key": "toast.apply_hot" if hr_ok else "toast.apply_ok",
                })
                return

            if path == "/api/reload":
                ok, msg = self.injector.reload_flclash(apply_before_start=True, allow_process_restart=False)
                rmode = getattr(self.injector, "_last_reload_mode", "pending_activation")
                mkey = "toast.reload_hot" if (ok and rmode == "hot_reload") else (
                    "toast.reload_pending" if (ok and rmode == "pending_activation") else (
                        "toast.reload_ok" if ok else "toast.reload_fail"
                    )
                )
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "reload_mode": rmode,
                    "message_key": mkey,
                    "message_params": {"error": msg},
                    "controller": self.injector.controller.get_status(),
                })
                return

            if path == "/api/restore":
                ok, msg = self.injector.restore_backup(disable_dns=True)
                self._send_json({
                    "success": ok,
                    "message": msg,
                    "message_key": "toast.restore_ok" if ok else "toast.restore_fail",
                })
                return

            if path == "/api/export_public":
                ok, zpath, files = export_public_package()
                self._send_json({
                    "success": ok,
                    "zip_path": zpath,
                    "file_count": len(files),
                    "message": f"纯净公共版已导出至: {zpath}（共 {len(files)} 个文件，零个人数据）",
                    "message_key": "toast.export_public_ok",
                    "message_params": {"path": zpath, "count": len(files)},
                })
                return

            self.send_error(404, "Not Found")
        except Exception as e:
            try:
                self.send_error(500, str(e))
            except Exception:
                pass


def open_browser_robustly(url, app_mode=False):
    if platform.system() == "Windows":
        app_browsers = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        if app_mode:
            for bp in app_browsers:
                if os.path.exists(bp):
                    try:
                        subprocess.Popen([bp, f"--app={url}", "--window-size=1180,780"])
                        return
                    except Exception:
                        pass
    elif app_mode and platform.system() == "Darwin":
        for app_bin in [
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]:
            if os.path.exists(app_bin):
                try:
                    subprocess.Popen([app_bin, f"--app={url}"])
                    return
                except Exception:
                    pass

    try:
        if webbrowser.open(url):
            return
    except Exception:
        pass
    if platform.system() == "Windows":
        for cp in [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]:
            if os.path.exists(cp):
                try:
                    subprocess.Popen([cp, url])
                    return
                except Exception:
                    pass
        try:
            os.startfile(url)
        except Exception:
            pass


def run_web_server(injector: ConfigInjector, rule_mgr: RuleManager, port=18900, auto_open=True, app_mode=False):
    WebServerHandler.injector = injector
    WebServerHandler.rule_mgr = rule_mgr
    server = None
    for p in range(port, port + 10):
        try:
            server = ThreadingHTTPServer(("0.0.0.0", p), WebServerHandler)
            port = p
            break
        except OSError:
            continue

    if not server:
        print(f"[错误] 无法在端口 {port} 启动 Web 服务。")
        return

    phys_ip = NetworkHelper.get_physical_ip()
    local_url = f"http://127.0.0.1:{port}"
    print("\n=======================================================")
    print(f"RulePilot v{VERSION} ({EDITION}) 已启动")
    print(f"管理面板地址: {local_url}" + (" (桌面微窗模式)" if app_mode else ""))
    if phys_ip and phys_ip != "127.0.0.1":
        print(f"局域网直连  : http://{phys_ip}:{port}")
    print("=======================================================\n")

    if auto_open:
        threading.Timer(0.7, lambda: open_browser_robustly(local_url, app_mode=app_mode)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[退出] Web 服务已停止。")


def print_diagnostics(diag):
    print(f"\n=== RulePilot v{VERSION} ({EDITION}) 分流与防漏体检报告 ===")
    print(f"客户端       : {diag['client_label']}")
    print(f"保护状态     : {'已开启且健康' if diag['healthy'] else ('已开启（建议重载同步）' if diag['protection_active'] else '未开启')}")
    print(f"生效规则数   : {diag['total_active_rules']} 条（编译时间: {diag['config_mtime']}）")
    print(f"DNS 防污染   : enhanced-mode={diag['dns']['enhanced_mode']} | 洁净={'是' if diag['checks']['clean_dns'] else '否'}")
    print(f"探针通过率   : {diag['probe_summary']['passed']}/{diag['probe_summary']['total']}")
    print("\n--- 路由模拟结果 ---")
    for p in diag["probes"]:
        mark = "PASS" if p["ok"] else "FAIL"
        print(f"  [{mark}] {p['host']:<30} ({p['desc']:<14}) -> {p['actual_action']:<18} | #{p['line']} {p['matched_rule']}")
    print()


def main():
    os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1,192.168.*,10.*,172.16.*"
    os.environ["no_proxy"] = os.environ["NO_PROXY"]

    parser = argparse.ArgumentParser(description=f"RulePilot v{VERSION} ({EDITION}) - 代理规则与域名分流一键保护助手")
    parser.add_argument("--dir", help="手动指定代理软件配置目录")
    parser.add_argument("--storage-dir", help="手动指定规则库 custom_rules.json 所在目录")
    sub = parser.add_subparsers(dest="command")

    p_ui = sub.add_parser("ui", help="启动可视化 Web 控制台")
    p_ui.add_argument("--no-open", action="store_true", help="启动但不自动打开浏览器")
    p_ui.add_argument("--app", action="store_true", help="以独立无框桌面微窗模式打开控制台（如 Edge/Chrome App 模式）")
    p_ui.add_argument("--port", type=int, default=18900, help="指定 Web 服务端口 (默认 18900)")

    p_add = sub.add_parser("add", help="添加直连排除或强制代理规则")
    p_add.add_argument("target", choices=["direct", "proxy", "reject"])
    p_add.add_argument("pattern")
    p_add.add_argument("-c", "--comment", default="")
    p_add.add_argument("--root", action="store_true", help="自动归并为一级域名")
    p_add.add_argument("--position", choices=["top", "fallback"], default="top")

    p_rm = sub.add_parser("remove", help="移除规则")
    p_rm.add_argument("pattern")

    sub.add_parser("list", help="列出预设场景与自定义规则")
    sub.add_parser("enable", help="一键开启智能防漏保护并重载")
    sub.add_parser("disable", help="一键暂停保护并恢复默认")
    sub.add_parser("apply", help="写入持久化覆写（不重启客户端）")
    sub.add_parser("reload", help="写入并温和重载代理软件")
    sub.add_parser("scan", help="扫描本机实时活跃域名并按一级域名归并")
    p_chk = sub.add_parser("check", help="执行分流与推流路由体检")
    p_chk.add_argument("domains", nargs="*")
    sub.add_parser("export-public", help="导出零个人数据的纯净公共分享包 ZIP")
    sub.add_parser("status", help="查看当前检测环境")

    args = parser.parse_args()
    rule_mgr = RuleManager(storage_dir=args.storage_dir)
    saved_dir = rule_mgr.rules_data.get("custom_clash_dir", "")
    clash_dir = PathDetector.detect_active_dir(args.dir or (saved_dir if os.path.isdir(saved_dir) else None))
    injector = ConfigInjector(clash_dir, rule_mgr)
    cmd = args.command

    if not cmd or cmd == "ui":
        run_web_server(
            injector,
            rule_mgr,
            port=getattr(args, "port", 18900),
            auto_open=not getattr(args, "no_open", False),
            app_mode=getattr(args, "app", False),
        )
        return

    if cmd == "status":
        top_r, fb_r, need_proc = rule_mgr.get_compiled_rules()
        print(f"RulePilot 版本 : v{VERSION} ({EDITION})")
        print(f"客户端模式     : {injector.detect_client_label()}")
        print(f"配置目录       : {clash_dir}")
        print(f"主代理策略组   : {injector.detect_primary_proxy_group()}")
        print(f"编译规则数     : 置顶 {len(top_r)} 条 + 兜底 {len(fb_r)} 条 (进程直连: {need_proc})")
        return

    if cmd == "enable":
        ok, msg, diag = injector.one_click_enable()
        print(msg)
        print_diagnostics(diag)
        return

    if cmd == "disable":
        ok, msg, _ = injector.one_click_disable()
        print(msg)
        return

    if cmd == "scan":
        res = SystemScanner.scan_live_domains(injector)
        print(f"\n扫描来源: {res['source']}（原始 {res['raw_count']} 条 -> 归并 {res['root_count']} 个一级域名）")
        for it in res["items"][:30]:
            print(f"  [{it['recommendation']:<14}] {it['root_domain']:<26} ({it['label']:<14}) | {it['current_category']:<6} | 子域:{it['subdomain_count']}")
        print()
        return

    if cmd == "add":
        tmap = {"direct": "DIRECT", "proxy": "PROXY", "reject": "REJECT"}
        ok, msg = rule_mgr.add_rule(
            args.pattern, tmap[args.target], comment=args.comment,
            position=args.position, collapse_to_root=args.root
        )
        print(msg)
        if ok:
            _, res, _ = injector.apply()
            for r in res:
                print(f"  - {r}")
        return

    if cmd == "remove":
        ok, msg = rule_mgr.remove_rule(args.pattern)
        print(msg)
        if ok:
            injector.apply()
        return

    if cmd == "list":
        print("\n=== 场景保护开关 ===")
        for k, meta in PRESET_PACKS.items():
            on = rule_mgr.rules_data.get("presets", {}).get(k, meta["default"])
            print(f"  [{'ON ' if on else 'OFF'}] {k:<22} | {meta['name']} ({len(meta['rules'])}条)")
        print("\n=== 自定义规则 ===")
        for r in rule_mgr.list_rules():
            print(f"  [{r.get('position','top'):<8}] {r['type']:<14} {r['pattern']:<28} -> {r['target']:<8} {r.get('comment','')}")
        print()
        return

    if cmd == "apply":
        _, res, pg = injector.apply()
        print(f"主代理策略组: {pg}")
        for r in res:
            print(f"  - {r}")
        return

    if cmd == "reload":
        ok, msg = injector.reload_flclash(apply_before_start=True)
        print(msg)
        if ok:
            print_diagnostics(injector.run_diagnostics())
        return

    if cmd == "check":
        print_diagnostics(injector.run_diagnostics(extra_domains=args.domains))
        return

    if cmd == "export-public":
        ok, zpath, files = export_public_package()
        print(f"已导出纯净公共版压缩包: {zpath}（包含 {len(files)} 个文件）")
        return


if __name__ == "__main__":
    main()
