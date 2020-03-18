import urllib.request, urllib.parse
import json
import time

def getMarkers():
    #全件取得するために、静岡県全域が含まれる緯度経度を整数値で設定
    xMax = 140
    xMin = 137
    yMax = 36
    yMin = 33

    params = {
        'request':'MarkerSet',
        'Xmax':xMax,
        'Xmin':xMin,
        'Ymax':yMax,
        'Ymin':yMin
    }
    p = urllib.parse.urlencode(params)

    url = "https://pointcloud.pref.shizuoka.jp/lasmap/ankenmapsrc?" + p

    #上記で生成したURLパラメータでSIZUOKA POINT CLOUD DBにリクエストし案件一覧文字列を取得
    allAnkenStr = ""
    with urllib.request.urlopen(url) as res:
        allAnkenStr = res.read().decode()

    #以下はDBから得られる文字列のサンプル
    #本来は改行されていない

    #30XXX01010001:平成30年度韮山反射炉計測業務:138.96214537214:35.03962001009?
    #28XXX00030007:白糸の滝滝見橋周辺整備事業　その７:138.58870495572:35.312506370532?
    #28XXX00030008:白糸の滝滝見橋周辺整備事業　その８:138.58881502806:35.312596432406?
    #28XXX00030009:白糸の滝滝見橋周辺整備事業　その９:138.58892510063:35.312686494178?
    #29C2001011361:平成２９年度［第２９-Ｃ２００１-０１号］　伊豆半島の屋外広告物の実態調査業務委託（函南町道_1-2号線）:138.93794860595:35.083520492945

    #案件ごとの区切りは'?'、1案件中の区切りは':'である

    ankensObj = {
        "ankenList":[]
    }

    ankenList = allAnkenStr.split('?')
    for anken in ankenList:
        ankenInfo = anken.split(':')
        #不適切なデータがあった場合、スキップする
        if len(ankenInfo) != 4:
            continue

        #和暦を西暦に変換
        yy = int(ankenInfo[0][:2])
        #令和
        if yy < 24:
            yyyy = 2018 + yy
        else:
            yyyy = 1988 + yy

        ankenObj = {
            "no":ankenInfo[0],
            "name":ankenInfo[1],
            "lon":ankenInfo[2],
            "lat":ankenInfo[3],
            "year":yyyy
        }
        ankensObj['ankenList'].append(ankenObj)
    return ankensObj

import bs4
def getAnkenDetail(ankenNo):
    params = {
        'ankenno':ankenNo
    }
    p = urllib.parse.urlencode(params)
    url = "https://pointcloud.pref.shizuoka.jp/lasmap/ankendetail?" + p

    opener = urllib.request.build_opener()
    opener.addheaders = [
        ('Referer', 'http://localhost'),
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36 Edg/79.0.309.65'),
    ]

    html = opener.open(url)
    soup = bs4.BeautifulSoup(html, features='html.parser')
    #<li>タグ
    linkLists = soup.find_all("li")

    #<li>タグ内の<a>タグ内のhref要素を全件取得
    links = []
    for li in linkLists:
        links.append("https://pointcloud.pref.shizuoka.jp/lasmap" + li.a["href"][1:])

    #tr要素すべて
    trLists = soup.find_all("tr")

    #請負業者
    firm = trLists[2].td.string

    #データ取得日
    sampleDate = trLists[5].td.string

    detailObj = {
        "links":links,
        "date":sampleDate,
        "firm":firm
    }

    return detailObj

if __name__ == "__main__":
    ankensObj = getMarkers()
    
    #既に読み込んだ案件リスト
    loaded_details = {}
    with open('./json/details.json') as f:
        loaded_details = json.load(f)

    loaded_ankenNo = list(loaded_details.keys())

    detailObj_list = loaded_details
    for anken in ankensObj['ankenList']:
        if anken['no'] in loaded_ankenNo:
            continue

        detailObj_list[anken['no']] = getAnkenDetail(anken['no'])
        print(detailObj_list[anken['no']])
        #スクレイピングの1秒制限
        break
        time.sleep(1)
    
    with open('./json/ankens.json', 'w') as f:
        json.dump(ankensObj, f, indent=4, ensure_ascii=False)
    with open('./json/details.json', 'w') as f:
        json.dump(detailObj_list, f, indent=4, ensure_ascii=False)
    