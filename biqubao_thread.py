#!/usr/bin/env python
# -*- coding:utf-8 -*-

import threading
import time
import queue
import requests
from bs4 import BeautifulSoup
import os

SHARE_Q = queue.Queue()  #构造一个不限制大小的的队列
_WORKER_THREAD_NUM = 20  #设置线程的个数
#所要爬取的小说主页，每次使用时，修改该网址即可，同时保证本地保存根路径存在即可
#target-小说地址
target="https://www.biqubao.com/book/14761/"
# target="https://www.biqubao.com/book/5677/"
# target="https://www.biqubao.com/book/17817/"
# target="https://www.biqubao.com/book/29674/"
# 本地保存爬取的文本根路径
save_path = 'C:/Users/Administrator/Desktop/xiaoshuo'
#笔趣阁网站根路径
index_path='https://www.biqubao.com'
_dir_path=''
#按章节顺序存放小说内容，最后按顺序写入一个txt文件
_txt_content = {}
#按章节顺序存放小说章节标题，最后按顺序写入一个txt文件
_txt_title={}
class MyThread(threading.Thread) :
    """
    doc of class
    Attributess:
        func: 线程函数逻辑
    """
    def __init__(self, func) :
        super(MyThread, self).__init__()  #调用父类的构造函数
        self.func = func  #传入线程函数逻辑

    def run(self) :
        """
        重写基类的run方法

        """
        self.func()

def do_something(item) :
    """
    运行逻辑, 比如抓站
    """
    global _dir_path
    global _txt_content
    global _txt_title
    # 章节名称
    dd_tag=item[1]
    i=item[0]
    chapter_name = dd_tag.string
    # print(chapter_name+ threading.currentThread().name)
    # 章节网址
    chapter_url = index_path + dd_tag.a.get('href')
    # print("章节名称【" + chapter_name + "】,章节网址【" + chapter_url+"】")
    # 访问该章节详情网址，爬取该章节正文
    chapter_req = requests.get(url=chapter_url)
    chapter_req.encoding = 'gbk'
    chapter_soup = BeautifulSoup(chapter_req.text, "html.parser")
    # 解析出来正文所在的标签
    content_tag = chapter_soup.div.find(id="content")
    if len(content_tag) < 1:
        print("content_tag长度小于1,未找到content正文,章节名称："+chapter_name)
        with open(_dir_path + '-未写入章节.txt', 'a+') as f:
            f.write('\n')
            f.write(chapter_name)
        return
    content_text = str(content_tag.text.replace('\xa0','\n'))
    print("章节名称【" + chapter_name + "】,章节网址【" + chapter_url + "】")
    #此处存入数组标记第i章节和内容，获取完整小说后再按顺序写入txt
    _txt_content[i]=content_text
    _txt_title[i]=chapter_name
    #单个章节一个txt文件写入
    with open(_dir_path + '/' + chapter_name + '.txt', 'w') as f:
        # f.write('本文网址:'+chapter_url)
        f.write(content_text)
    return chapter_name,content_text,chapter_url

def write2txt():
    global _dir_path
    global _txt_content
    global _txt_title
    if os.path.exists(_dir_path+'.txt'):
        os.remove(_dir_path+'.txt')
        file=open(_dir_path + '.txt', 'w')
        file.close()
    for i in range(len(_txt_content)):
        chapter_name=_txt_title[i]
        content_text=_txt_content[i]
        # a+方式在末尾写
        with open(_dir_path + '.txt', 'a+') as f:
            f.write('\n')
            f.write(chapter_name)
            f.write(content_text)
        print("finish:"+chapter_name)



def worker() :
    global _dir_path
    """
    主要用来写工作逻辑, 只要队列不空持续处理
    队列为空时, 检查队列, 由于Queue中已经包含了wait,
    notify和锁, 所以不需要在取任务或者放任务的时候加锁解锁
    """
    global SHARE_Q
    while True :
        if not SHARE_Q.empty():
            # print("队列大小:"+str(SHARE_Q.qsize()))
            item = SHARE_Q.get() #获得任务
            do_something(item)
            # time.sleep(1)
            SHARE_Q.task_done()
        else:
            break

#获取章节数和各章节访问地址
def cnt_story():
    global _dir_path
    req = requests.get(url=target)
    # 查看request默认的编码，发现与网站response不符，改为网站使用的gdk
    print(req.encoding)
    req.encoding = 'gbk'
    # 解析html
    soup = BeautifulSoup(req.text, "html.parser")
    list_tag = soup.div(id="list")
    #print('list_tag:', list_tag)
    # 获取小说名称
    story_title = list_tag[0].dl.dt.string
    # 根据小说名称创建一个文件夹,如果不存在就新建
    _dir_path = save_path + '/' + story_title
    if not os.path.exists(_dir_path):
        os.path.join(save_path, story_title)
        os.mkdir(_dir_path)
    cnt = len(list_tag[0].dl.find_all('dd'))
    story_content=list_tag[0].dl.find_all('dd')
    print("章节数量：" + str(cnt))
    print(story_content)
    return story_content

#多线程爬取指定章节内容
def main(story_content) :
    global SHARE_Q
    threads = []
    #向队列中放入任务, 真正使用时, 应该设置为可持续的放入任务
    # 记录章节先后
    i=0
    j=0
    for dd_tag in story_content :
        print("第"+str(i)+"个节点---"+dd_tag.text)
        #指定下载3722之后的
        if i>3722 and i<10000:
            item=[j,dd_tag]
            SHARE_Q.put(item)
            j=j+1
        i = i + 1
    #开启_WORKER_THREAD_NUM个线程
    for i in range(_WORKER_THREAD_NUM) :
        thread = MyThread(worker)
        thread.start()  #线程开始处理任务
        threads.append(thread)
    for thread in threads :
        thread.join()
    #等待所有任务完成
    SHARE_Q.join()

if __name__ == '__main__':
    starttimeStr=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    starttime=time.time()
    story_content = cnt_story()
    main(story_content)
    write2txt()
    endtime = time.time()
    taketime = endtime - starttime
    print("take(s):"+taketime)
    print("starttime:"+starttimeStr)
    endtimeStr=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print("endtime:"+ endtimeStr)
    print("结束!!!")