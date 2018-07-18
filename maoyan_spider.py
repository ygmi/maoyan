# -*- coding: utf-8 -*-

import requests
from lxml import etree
import re
import lorm
import pymysql
import datetime
import time
# from ..tools.utils import uploader


db = lorm.Hub(pymysql)
db.add_pool('default', host='192.168.0.209', port=3306, user='root',
    passwd='xxxxx', db='xxxx', autocommit=True, pool_size=8, wait_timeout=30)

headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Mobile Safari/537.36'}


def maoyan():
    """
    猫眼电影的api
    :return:
    """
    url = 'https://piaofang.maoyan.com/search?key=龙与地下城'
    res = requests.get(url=url, headers=headers).text
    response = etree.HTML(res)
    data_url = response.xpath("//article/@data-url")[0]  # 获取电影的链接
    movie_url = 'https://piaofang.maoyan.com' + data_url  # 拼接电影的url
    res_movie = requests.get(url=movie_url, headers=headers).text
    html_movie = etree.HTML(res_movie)
    cover = html_movie.xpath("//div[@class='info-poster']/img/@src")[0]  # 电影图片

    name = html_movie.xpath("//div[1][@class='info-title-bar']/p[1]/span/text()")[0]  # 电影中文名

    enname = html_movie.xpath("//div[2][@class='info-title-bar']/p[1]/span/text()")[0]  # 电影英文名

    movie_type = ''.join(html_movie.xpath("//p[@class='info-category']/text()"))  # 电影类型
    if movie_type:
        movie_type = re.sub(r'\n|\r| ', '', movie_type)
    else:
        movie_type = None

    movie_city = ''.join(html_movie.xpath("//div[@class='info-source-duration']/div/p/text()"))  # 电影拍摄地
    movie_city = re.sub(r'\n|\r| |/', '', movie_city)

    movie_time = ''.join(html_movie.xpath("//div[@class='info-source-duration']/div/p/span/text()"))  # 电影时长
    if movie_time:
        movie_time = re.sub(r'\n|\r| | ', '', movie_time)
        movie_time = re.sub(r'分钟', '', movie_time)
        movie_time = movie_time
    else:
        movie_time = None
    show_time = html_movie.xpath("//span[@class='score-info ellipsis-1']/text()")

    if show_time:
        show_city = re.findall(r'[\u4e00-\u9fa5]+', str(show_time))
        premiere = re.sub(r'上映', '', show_city[0])
        mat = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', str(show_time))
        restime = datetime.datetime.strptime(mat.group(0), '%Y-%m-%d')
        year = restime.year
        month = restime.month
        day = restime.day

    movie_info_url = movie_url + '/moresections'  # 电影的介绍是ajax加载的，拼接movie_info_url

    data = {'cover': 'http:' + cover,
            'name': name,
            'enname': enname,
            'movie_type': movie_type,
            'movie_city': movie_city,
            'movie_time': movie_time,
            'year':year,
            'month':month,
            'day':day,
            'premiere':premiere,
            }
    movie_info(movie_info_url, data, movie_url)


def movie_info(movie_info_url, data, movie_url):
    """

    :param movie_info_url: 电影基本介绍
    :param data: 构建的电影的基本信息
    :return:
    """
    response = requests.get(url=movie_info_url, headers=headers)
    movie_info_dict = eval(response.text)
    try:
        movie_info_html = movie_info_dict['sectionHTMLs']['detailSection']['html']
        movie_info = re.findall(r'<div class="detail-block-content">(.*?)</div>', movie_info_html)
        movie_info = ''.join(movie_info)
        movie_info = {'movie_info': movie_info}
        data.update(movie_info)
    except Exception as f:
        print(f)
    celebrity_url = movie_url + '/celebritylist'
    actor_watch(celebrity_url, data)


def actor_watch(celebrity_url, data):
    """
    演员表信息
    :return:
    """
    html_celebrity = requests.get(url=celebrity_url, headers=headers).text
    html_celebrity = etree.HTML(html_celebrity)
    url = html_celebrity.xpath("//*[@id='panelWrapper']/dl[1]/dd/div/div/a/@href")[0]
    if url:
        dir_url = 'https://piaofang.maoyan.com' + url
        s = html_celebrity.xpath(r'//div/dl')
        dict2 = {}
        for i in s:
            list1 = []
            """
            职业名称：导演、编剧、制片人.........
            """
            per_name = i.xpath(r'./dt/div/span/span/text()')
            name_s = i.xpath(r'./dd/div')
            for j in name_s:
                name_n = j.xpath(r'./div/a/div[@class="p-desc"]')
                for n in name_n:
                    dict1 = {}
                    dict1['performer_name'] = ''.join(n.xpath(r'./p[@class="p-item-name ellipsis-1"]/text()'))
                    dict1['performer_enname'] = ''.join(n.xpath(r'./p[@class="p-item-e-name ellipsis-1"]/text()'))
                    dict1['role_name'] = ''.join(n.xpath(r'./p[@class="p-item-play ellipsis-1"]/text()'))
                    list1.append(dict1)
                dict2[per_name[0]] = list1
        data.update(dict2)
        save_data(data)
    else:
        pass

def save_data(data):
    print(data)
    """保存数据"""
    name = data['name']
    enname = data['enname']
    area = data['movie_city']
    genre = re.sub(r',', '|', data['movie_type'])
    year = data['year']
    month = data['month']
    day = data['day']
    runtime = data['movie_time']
    poster = data['cover']
    intro  = data['movie_info']
    update_time = time.time()
    premiere = data['premiere']
    add_time = time.time()
    res = db.default.movie.get(name=name,year=year)
    if res:
        pass
    else:
        db.default.movie.create(id=0,oid=1234567,type='movie',name=name,enname=enname,area=area,year=year,genre=genre,
                                poster=poster,intro=intro,runtime=runtime,month=month,day=day,
                                premiere=premiere, add_time=int(add_time), update_time=int(update_time))
        
if __name__ == '__main__':
    maoyan()
