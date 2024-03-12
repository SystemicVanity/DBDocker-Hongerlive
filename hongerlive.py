import os, io, sys
import datetime, requests, sqlite3
from bs4 import BeautifulSoup as bs
from time import time, sleep

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

#변수 설정
##게시판ID 및 기타
dbName = sys.argv[1]
slugName = sys.argv[2]
##각종 위치 설정
os.makedirs(f"/arcalive/list", exist_ok=True)
dbPath = f"/arcalive/{dbName}.db"
listPath = f"/arcalive/list/{slugName}.txt"
##API링크 셋업
apiUrl = "https://arca.live/api/app"
##헤더 설정
headers = {'Host': 'arca.live', 'X-Device-Token': '', 'User-Agent': 'live.arca.android/0.9.42'}
##마지막 before 체크
if os.path.isfile(listPath) == True:
    with open(listPath, "r") as lastRead:
        lastfor = lastRead.readlines()[-1].strip()
else:
    lastfor = ""

#함수설정
##json key 체커
def keyChecker(json, key):
    try: yesu = json[key]
    except KeyError: return False
    return True
##포스트 전용 백업 함수
###포스트 전용 - 얻기
def postGet(id):
    postUrl = f"{apiUrl}/view/article/{slugName}/{id}"
    postResponse = requests.get(postUrl, headers=headers)
    postJson = postResponse.json()
    if keyChecker(postJson, "result") == True:
        print(f"{id} : 글삭", flush=True)
        return None
    else:
        category = postJson["category"]
        createdDate = datetime.datetime.strptime(postJson["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y.%m.%d %H:%M:%S")
        updatedDate = datetime.datetime.strptime(postJson["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y.%m.%d %H:%M:%S")
        title = postJson["title"]
        nickname = postJson["nickname"]
        if keyChecker(postJson, "ip") == True: ip = postJson["ip"]
        else: ip = None
        viewCount = postJson["viewCount"]
        upVote = postJson["ratingUp"]
        downVote = postJson["ratingDown"]
        cmtNo = postJson["commentCount"]
        html = postJson["content"]
        soup = bs(html, "html.parser")
        videos = soup.find_all("video")
        for video in videos: video.decompose()
        content = soup.get_text("\n").strip()
        return {"id": id, "category" : category, "createdDate" : createdDate, "updatedDate" : updatedDate, "title" : title, "nickname" : nickname, "ip" : ip,
                "viewCount" : viewCount, "upVote" : upVote, "downVote" : downVote, "cmtNo" : cmtNo, "html" : html, "content" : content}
##댓글 전용 백업 함수
###댓글 전용 - 얻기
def cmtGet(id):
    comments = list()
    cmtGo, since = True, ""
    while cmtGo == True:
        cmtUrl = f"{apiUrl}/list/comment/{slugName}/{id}?limit=100&since={since}"
        cmtResponse = requests.get(cmtUrl, headers=headers, timeout=30)
        cmtJson = cmtResponse.json()
        if len(cmtJson) == 0: cmtGo = False
        else:
            for cmt in cmtJson:
                cmtId = cmt["id"]
                parentId = cmt["parentId"]
                depth = cmt["depth"]
                createdDate = datetime.datetime.strptime(cmt["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y.%m.%d %H:%M:%S")
                updatedDate = datetime.datetime.strptime(cmt["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y.%m.%d %H:%M:%S")
                if cmt["contentType"] == "text": content = cmt["content"]
                else: content = "아카콘"
                nickname = cmt["nickname"]
                if keyChecker(cmt, "ip") == True: ip = cmt["ip"]
                else: ip = None
                comments.append((id, cmtId, parentId, depth, createdDate, updatedDate, content, nickname, ip))
            since = cmtJson[-1]["id"]
    return comments
##본 함수
def main(idList, cur):
    for id in idList:
        post = postGet(id)
        if post != None:
            cur.execute(f"INSERT OR IGNORE INTO {slugName} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (post["id"], post["category"], post["createdDate"], post["updatedDate"], post["title"], post["nickname"], post["ip"], post["viewCount"], post["upVote"], post["downVote"], post["cmtNo"], post["content"], post["html"]))
            #댓글 백업
            if post["cmtNo"] > 0:
                comments = cmtGet(id)
                cur.executemany(f"INSERT OR IGNORE INTO {slugName}_comm VALUES(?,?,?,?,?,?,?,?,?)", comments)
        else: pass

if __name__ == '__main__':
    #DB 연결
    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()
    #DB 테이블 생성
    conn.execute(f"CREATE TABLE IF NOT EXISTS {slugName}(id INTERGER PRIMARY KEY NOT NULL, category TEXT, createdDate TEXT, updatedDate TEXT, title TEXT, nickname TEXT, ip TEXT, viewCount INTERGER, upVote INTERGER, downVote INTERGER, cmtNo INTERGER, content TEXT, html TEXT)")
    conn.execute(f"CREATE TABLE IF NOT EXISTS {slugName}_comm(id INTERGER NOT NULL, cmtId INTERGER PRIMARY KEY NOT NULL, parentId INTERGER, depth INTERGER, createdDate TEXT, updatedDate TEXT, content TEXT, nickname TEXT, ip TEXT)")
    #완료한 ID 추출
    doneList = cur.execute(f"SELECT id FROM {slugName}").fetchall()
    doneList = [id[0] for id in doneList]
    doneList.sort()
    doneList.reverse()
    #ID 추출 및 진행
    listGo, before = True, lastfor
    while listGo == True:
        startTime = time()
        listUrl = f"{apiUrl}/list/channel/{slugName}?before={before}"
        listResponse = requests.get(listUrl, headers=headers)
        listJson = listResponse.json()
        if len(listJson["articles"]) <= 1: listGo = False
        else:
            ##ID 추출
            idList = [article["id"] for article in listJson["articles"]]
            idList = sorted(list(set(idList)-set(doneList)), reverse=True)
            main(idList, cur)
            conn.commit()
            ##다음 회차 얻기 및 기록
            before = listJson["next"]["before"].rsplit(".",1)[0].replace(":", "%3A") + "Z"
            with open(listPath, "a") as listWrite:
                print(before, file=listWrite)
            doneList += idList
            sleep(0.05)