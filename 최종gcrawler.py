from multiprocessing import Process, freeze_support, Queue, Lock, current_process
import requests
import re
from time import sleep
import random
import os
from tqdm import tqdm
import sqlite3

#데이터누락이 조금 있는 듯 함. 근데 속도가 압도적
#실행하기전에 url1이랑 place 바꿔주기

def crawler(count,countcut,lock) :
    #sqlite3 DB파일 만들기. 수정 없을시 crawler3.sqlite에 계속 추가함
    conn = sqlite3.connect('crawler9.sqlite')
    cur = conn.cursor()
    #서버에서 로봇으로 인지 안되도록 사용자 정보 기입
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36'}
    #구글리뷰에서 페이지 로딩시 새롭게 요청되는 url주소를 1i부분을 기점으로 나눈것.
    proc_name = current_process().name
    
    #중간 숫자만 10씩 증가하므로 count에 0 부여해서 전체url 조립
    url2 = '!2i10!3e3!4m5!3b1!4b1!5b1!6b1!7b1!5m2!1spXlfXvj5DsT7wAPnrIn4BQ!7e81'  #2020.03.04기준! 매일 바뀌는듯

    #sqlist3에서 DB 테이블 생성
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS Date (
        id      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        date    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Fivecontinent (
        id      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        fivecon    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Continent (
        id      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        continent    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Country (
        id      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        country    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS City (
        id      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        city    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Reviewtext (
        id      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        text    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Place (
        id      INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        place   TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Review (
        date_id         INTEGER,
        text_id         INTEGER,
        place_id        INTEGER,
        city_id         INTEGER,
        country_id      INTEGER,
        continent_id    INTEGER,
        fivecon_id      INTEGER,
        PRIMARY KEY (date_id, text_id, place_id, city_id, country_id, continent_id, fivecon_id)
    )

    ''')
    #대륙명, 나라명, 도시명, 공원명, url1 으로 이루어진 txt파일을 불러와서 한줄씩 반복
    #각각의 프로세스가 450개씩(총 10개의 프로세스) 맡아서 크롤링 하게 함
    with open('대륙별공원 리스트업추가.txt', encoding='utf-8') as fh:
        for line in fh :
            contents = line.split(',')
            fivecon = contents[0].strip()
            continent = contents[1].strip()
            country = contents[2].strip()
            city = contents[3].strip()
            place = contents[4].strip()
            url1 = contents[5].strip()
            holy = 0
            result = []
            count_real = count
            countcut_real = countcut
            while count_real < countcut_real:
                try:
                    response = requests.get(url1+str(count_real)+url2, headers = headers)
                    
                    html = response.text
                    html = html.rstrip()
                    html2 = html.split('\n')
                    for line in html2 :
                        c = re.compile('(^,"\d+\S 전",null,".+)",5,null', re.DOTALL)
                        review = c.findall(line)
                        trigger = re.findall('(^,"\d+\S 전"),null,null.+', line)
                        if review != []:
                            reviewtxt = str(review)
                            reviewtxt = reviewtxt.replace(',','').replace('\\n',' ').replace('(Google 번역 제공)', '***').replace('\\','').replace('null','').replace('\'','').replace('"','').replace('.','').replace('(원문)','/').replace('달 전','달 전::').replace('일 전','일 전::').replace('년 전','년 전::').replace('초 전','초 전::').replace('분 전','분 전::').replace('시간 전','시간 전::').replace('주 전','주 전::')
                            result.append(reviewtxt)
                        elif trigger != [] and review == [] :
                            holy = holy + 1
                        elif holy > 300 :
                            print('리뷰 내용이 없으므로 크롤링을 중단합니다')
                            break
                    if holy > 300 :
                        break
                    count_real = count_real + 10
                    sleep(random.uniform(2,4))
                    # print(str(count_real)+'/'+str(countcut_real))
                except:
                    print('------------------------------Error----------------------------------')
                    continue
            print('총',str(len(result)),'개의 리뷰 수집 완료')

            #얻은 데이터를 #####을 기준으로 구분
            sep = '#####'
            vstr=str('')
            for index in result:
                review = index
                vstr = vstr + str(review) + sep
                vstr = vstr.replace('\n',' ').replace('-',' ')
            xxxx = 0
            i = vstr.split('#####')

            #구분된 데이터들에서 필요없는부분 잘라내고 ::을 기준으로 날짜, 텍스트 나누기
            for sss in i:
                x = sss.replace('[','').replace(']','')
                x = x.split('/')
                x = str(x[0])
                try:
                    y = x.split('***')
                    y = str(y[1])
                except:
                    y = '번역없음'
                    pass
                x = x.split('::')
                x.append(y)
                #맨 마지막 데이터는 빈 리스트가 반환되므로 빈 리스트가 아닌 경우에만 코드 실행
                #날짜, 텍스트, 장소를 DB에 저장
                if x[0] != '' and y == '번역없음':
                    date = x[0].strip();
                    text = x[1].strip();
                    # print(text)
                    # print('----------------------',x)
                    #전송과정의 누락을 방지하기 위해 다른 프로세스 잠금
                    lock.acquire()
                    cur.execute('''INSERT OR IGNORE INTO Date (date)
                        VALUES ( ? )''', ( date, ) )
                    cur.execute('SELECT id FROM Date WHERE date = ? ', (date, ))
                    date_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Fivecontinent (fivecon)
                        VALUES ( ? )''', ( fivecon, ) )
                    cur.execute('SELECT id FROM Fivecontinent WHERE fivecon = ? ', (fivecon, ))
                    fivecon_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Continent (continent)
                        VALUES ( ? )''', ( continent, ) )
                    cur.execute('SELECT id FROM Continent WHERE continent = ? ', (continent, ))
                    continent_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Country (country)
                        VALUES ( ? )''', ( country, ) )
                    cur.execute('SELECT id FROM Country WHERE country = ? ', (country, ))
                    country_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO City (city)
                        VALUES ( ? )''', ( city, ) )
                    cur.execute('SELECT id FROM City WHERE city = ? ', (city, ))
                    city_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Reviewtext (text)
                        VALUES ( ? )''', ( text, ) )
                    cur.execute('SELECT id FROM Reviewtext WHERE text = ? ', (text, ))
                    text_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Place (place)
                        VALUES ( ? )''', ( place, ) )
                    cur.execute('SELECT id FROM Place WHERE place = ? ', (place, ))
                    place_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR REPLACE INTO Review
                        (date_id, text_id, place_id, city_id, country_id, continent_id, fivecon_id) VALUES ( ?, ?, ?, ?, ?, ?, ?)''',
                        ( date_id, text_id, place_id, city_id, country_id, continent_id, fivecon_id) )

                    xxxx += 1
                    if xxxx % 10 == 0:
                        print (str(xxxx), '/', str(len(i)-1),'저장중')
                    #데이터를 전송 후 저장. 다른 프로세스들의 lock을 풀어주어서 다시 작업 재개
                    conn.commit()
                    lock.release()

                elif x[0] != '' and y != '번역없음':
                    date = x[0].strip();
                    text = x[2].strip();
                    # print(text)
                    # print('-----------------------------', x)
                    #전송과정의 누락을 방지하기 위해 다른 프로세스 잠금
                    lock.acquire()
                    cur.execute('''INSERT OR IGNORE INTO Date (date)
                        VALUES ( ? )''', ( date, ) )
                    cur.execute('SELECT id FROM Date WHERE date = ? ', (date, ))
                    date_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Fivecontinent (fivecon)
                        VALUES ( ? )''', ( fivecon, ) )
                    cur.execute('SELECT id FROM Fivecontinent WHERE fivecon = ? ', (fivecon, ))
                    fivecon_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Continent (continent)
                        VALUES ( ? )''', ( continent, ) )
                    cur.execute('SELECT id FROM Continent WHERE continent = ? ', (continent, ))
                    continent_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Country (country)
                        VALUES ( ? )''', ( country, ) )
                    cur.execute('SELECT id FROM Country WHERE country = ? ', (country, ))
                    country_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO City (city)
                        VALUES ( ? )''', ( city, ) )
                    cur.execute('SELECT id FROM City WHERE city = ? ', (city, ))
                    city_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Reviewtext (text)
                        VALUES ( ? )''', ( text, ) )
                    cur.execute('SELECT id FROM Reviewtext WHERE text = ? ', (text, ))
                    text_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR IGNORE INTO Place (place)
                        VALUES ( ? )''', ( place, ) )
                    cur.execute('SELECT id FROM Place WHERE place = ? ', (place, ))
                    place_id = cur.fetchone()[0]

                    cur.execute('''INSERT OR REPLACE INTO Review
                        (date_id, text_id, place_id, city_id, country_id, continent_id, fivecon_id) VALUES ( ?, ?, ?, ?, ?, ?, ?)''',
                        ( date_id, text_id, place_id, city_id, country_id, continent_id, fivecon_id) )

                    xxxx += 1
                    if xxxx % 10 == 0:
                        print (str(xxxx), '/', str(len(i)-1),'저장중')
                    #데이터를 전송 후 저장. 다른 프로세스들의 lock을 풀어주어서 다시 작업 재개
                    conn.commit()
                    lock.release()
            conn.commit()
            print('------------------------',continent, country, place, proc_name, 'end','------------------------------')

#멀티프로세스 코드
if __name__ == '__main__':
    #DB를 sqlite3로 보내는 과정에서 여러 프로세스가 동시에 기입하면 에러가 발생하여 데이터 누락이 생김
    #따라서 Lock을 통해 데이터를 전송할때만 싱글프로세스로 돌아가도록 작성
    lock = Lock()
    countcut = 4500
    process = []
    for p in range(1,11):
        xxx = Process(target=crawler, args=(int(countcut*(p-1)/10), int(countcut*p/10),lock))
        process.append(xxx)
    for index in process:
        index.start()

    for inde in process:
        inde.join()

