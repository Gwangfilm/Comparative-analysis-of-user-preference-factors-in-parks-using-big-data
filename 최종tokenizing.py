# -*- coding: utf-8 -*-
from konlpy.tag import Komoran
import pandas as pd
import numpy as np
import sqlite3
import re
from nltk import Text
from collections import Counter
from konlpy.utils import concordance, pprint

komoran = Komoran()

def lemmatize(words,exam,doc,sep):
    for sentence in words:
        newwords = ''
        if sentence != '':
            morphtags = komoran.pos(sentence)
        # print(morphtags)
        safe_words = ['굿','풀','성','탑','티','공','양','게','개','옷','숍','샵','해','뱀','벽','물',\
                    '왕','종','빵','소','샘','별','봄','밥','딸','땅','산','맛','꿈','술','섬','빛','차','색','숨',\
                    '배','낮','비','집','역','쇼','새','눈','책','숲','물','밤','길','말','꽃']
        for i in morphtags :
            if i[1] == 'VA' or i[1] == 'VV':
                xx = i[0] + '다'
                if i[0] == '좋아하' :
                    xx = '좋다'
                elif i[0] == '대하' :
                    xx = '거대하다'
                elif i[0] == '데리' :
                    xx = '데려가다'
                exam.append((xx,i[1]))
                newwords = newwords + xx + sep
            if i[1] == 'NNG' or i[1] == 'NNP' :
                pom = str(i[1]).replace('NNG','NN').replace('NNP','NN')
                xx = i[0]
                if i[0] == '트리' :
                    xx = '나무'
                    
                elif i[0] == '아이들' or i[0] == '아이' :
                    xx = '어린이'
                    
                elif i[0] == '스트리트' or i[0] == '메인 스트리트' or i[0] == '길':
                    xx = '도보'

                elif i[0] == '말' :
                    xx = '말하다'
                    pom = 'VV'
                    
                elif i[0] == '있다' or i[0] == '간다' or i[0] == '사랑합니다' or i[0] == '행복합니다' or i[0] == '반갑습니다' or i[0] == '보고 싶다' or i[0] == '고맙습니다' or i[0] == '산다' or i[0] == '보고싶다' or i[0] == '춥다' or i[0] == '후회합니다' or i[0] == '섰다' or i[0] == '잘 먹었습니다' or i[0] == '생일 축하합니다':
                    pom = 'VV'
                elif i[0] == '아름답다' :
                    pom = 'VA'
                elif len(i[0]) == 1 and i[0] not in safe_words :
                    continue
                newwords = newwords + xx + sep
                exam.append((xx,pom))

            elif i[1] == 'SL' :
                if i[0] == 'Forest' or i[0] == 'Garden' or i[0] == 'Street' or i[0] == 'Museum' :
                    if i[0] == 'Forest' :
                        xx = '숲'
                    elif i[0] == 'Garden' : 
                        xx = '정원'
                    elif i[0] == 'Street' : 
                        xx = '도로'
                    elif i[0] == 'Museum' :
                        xx = '박물관'
                    yy = 'NN'
                    newwords = newwords + xx + sep
                    exam.append((xx,yy))
                
        newwords = newwords.rstrip(sep)
        if newwords != '' :
            doc.append(newwords)

    return exam, doc

#java를 기반으로 하는 Komoran 분석기는 emoji가 들어갈 경우 에러가 발생하므로 emoji 제거
def replace_emoji(phrase):
    re_emoji = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
    return re_emoji.sub('', phrase).strip()

#DB열기
conn = sqlite3.connect('crawler9.sqlite')
cur = conn.cursor()

cur.executescript('''
    CREATE TABLE IF NOT EXISTS Textword_all (
        id          INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        word        TEXT NOT NULL UNIQUE,
        count       INTEGER,
        tag_id      INTEGER
    );

    CREATE TABLE IF NOT EXISTS Textword_doc (
        id              INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        doc             TEXT NOT NULL,
        continent_id    INTEGER,
        fivecon_id      INTEGER,
        city_id         INTEGER
    );

    CREATE TABLE IF NOT EXISTS Textword_tag (
        id          INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        tag         TEXT NOT NULL UNIQUE
    )

    ''')

#DB에서 필요한 정보 가져오기
cur.execute('''
    SELECT Reviewtext.text, Review.continent_id, Review.fivecon_id, Review.city_id
    FROM Review JOIN Reviewtext
    ON Review.text_id = Reviewtext.id
    ORDER BY Review.fivecon_id
    ''')

vstr = []
tags = []
places = []
fivecons = []
citylist = []
for row in cur:
    text = row[0].replace('!','').replace('?','')
    place = row[1]
    fivecon = row[2]
    city = row[3]
    text = replace_emoji(text)
    vstr.append(text)
    places.append(place)
    fivecons.append(fivecon)
    citylist.append(city)

exam = []
doc2 = []
sep = ', '
cccc, newdoc = lemmatize(vstr,exam,doc2,sep)
# print(cccc)
cnt = Counter(cccc)
dddd = cnt.most_common()
trigger = 0
trigger2 = 0
#정제된 단어 빈도수 도출
for line in dddd:
    word = str(line[0]).replace('\'','').replace('(','').replace(')','').replace(',',' /');
    tttt = word.split('/')
    word = str(tttt[0]).strip();
    tag = str(tttt[1]).strip();
    count = line[1];

    cur.execute('''INSERT OR IGNORE INTO Textword_tag (tag)
            VALUES (?)''',(tag, ))
    cur.execute('SELECT id FROM Textword_tag WHERE tag = ?', (tag, ))
    tag_id = cur.fetchone()[0]

    cur.execute('''REPLACE INTO Textword_all (word, count, tag_id)
            VALUES (?, ?, ?)''',(word, count, tag_id))

    trigger += 1
    if trigger % 10 == 0:
        print(trigger,'/',str(len(dddd)))
        conn.commit()

conn.commit()

#newdoc에 정제된 단어문서를 집어넣기 - lda와 word2vec을 위한 기초자료 마련
for index in range(len(newdoc)):
    doc = newdoc[index]
    continentindex = places[index]
    fiveconindex = fivecons[index]
    cityindex = citylist[index]
    cur.execute('SELECT place_id FROM Review WHERE continent_id = ?', (continentindex,))
    continent_id = cur.fetchone()[0]

    cur.execute('SELECT place_id FROM Review WHERE fivecon_id = ?', (fiveconindex,))
    fivecon_id = cur.fetchone()[0]

    cur.execute('SELECT place_id FROM Review WHERE city_id = ?', (cityindex,))
    city_id = cur.fetchone()[0]

    cur.execute('''INSERT OR IGNORE INTO Textword_doc (doc, continent_id, fivecon_id, city_id)
            VALUES (?, ?, ?, ?)''',(doc, continent_id, fivecon_id, city_id))

    trigger2 += 1
    if trigger2 % 10 == 0:
        print(trigger2,'/',str(len(newdoc)))
        conn.commit()

conn.commit()
conn.close()
