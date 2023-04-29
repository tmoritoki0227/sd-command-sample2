#!/usr/bin/env python3

import json
import requests 
from requests.auth import HTTPBasicAuth
from distutils.version import StrictVersion
   
import os # 環境変数取得に必要
import re

class VersionNotFoundError(Exception): # 指定したバージョンがArtifactoryにないとき
    pass # 何もしない宣言らしい

def main():
    url = 'https://moritoki.jfrog.io/artifactory/api/storage/xraysample-local/release/'
    # ユーザー名を指定(これはそのうち使えなくなるよ)
    username = 'tmoritoki0227@gmail.com'
    # パスワードを指定(これはそのうち使えなくなるよ)
    password = 'cmVmdGtuOjAxOjE3MTM5NjM4ODI6SG5RV3ZGMXdjeXhieklLc1loNDdsNHdMeTF2'

    # print(os.environ) # 環境変数全部表示

    # 環境変数取得
    # export SD_COLLECTION="/aaa/release/1.0.0 , /bbb/release/1.*.0, /ccc/release/1.0.*, /ddd/release/1.*.*, /aaa/test/3.0.0"
    # export SD_COLLECTION="/aaa/release/1.0.0 , /bbb/release/1.*.0, /ccc/release/1.0.*, /ddd/release/1.*.*, /aaa/test/3.0.1"
    sd_collection: str = os.getenv('SD_COLLECTION')

    # collectionをカンマで区切って配列に格納。splitは分割メソッド。stripは前後の空白削除
    collections: list = sd_collection.split(',')
    print("collections = " + str(collections))

    # for でcollectionを１つずつ処理していく
    for collection in collections:
        print ("------------------------loopスタート-------------------------")
        collection_parts = collection.strip().split('/') # 空白除去して/で分割
        print ("collection_parts = " + str(collection_parts))

        # name 取得
        name = collection_parts[1]
        print ("name = " + str(name))
        
        # version取得
        user_specified_version = str(collection_parts[3]) # 1.0.0が欲しい。a[3]に入っている
        print ("user_specified_version = " + str(user_specified_version) )
        
        # バージョン一覧取得.api実行
        response = requests.get(url, auth=requests.auth.HTTPBasicAuth(username, password),timeout=3)
        print(response.status_code)

        # Response オブジェクトの raise_for_status メソッドをコールすることで 400-599 の時に HTTPError を raise します。
        response.raise_for_status()
        res_json = json.loads(response.text)

        # キーchildrenの値を取得
        children_info = res_json['children']
        print ("children_info = " + str(children_info) )

        # キーuriの値を取得
        available_version: list = []
        for c in children_info:
            # print(c['uri'])
            available_version.append(c['uri'].replace('/', ''))

        print ("available_version前 = " + str(available_version))
        available_version.sort(key=StrictVersion) # 並び替えだが、最初から昇順ぽく並んでいるので変化が見られない
        print ("available_version後 = " + str(available_version))

        match = re.match(r'(?P<major>.+)\.(?P<minor>.+)\.(?P<micro>.+)', user_specified_version)
        if match:
            print('major:' + match.group('major').strip());
            print('minor:' + match.group('minor').strip());
            print('micro:' + match.group('micro').strip());
        else:
            print('みつかりませんでした.終了させる処理を入れよう')

        majaor_version = match.group('major').strip()
        minor_version = match.group('minor').strip()
        micro_version = match.group('micro').strip()

        print('majaor_version = ' + majaor_version)
        print('minor_version = ' + minor_version)
        print('micro_version = ' + micro_version)

        match_version : list = []
        if re.match(r'[0-9]+', majaor_version) and re.match(r'[0-9]+', minor_version) and re.match(r'[0-9]+', micro_version):
            print ("ALL数字でマッチンぐしたよ")
            match_version = [v for v in available_version if re.match(majaor_version + r'\.' + minor_version + r'\.' + micro_version, v)] # user_specified_versionと同じだが他と処理を同じにしている

        elif re.match(r'[0-9]+', majaor_version) and re.match(r'[0-9]+', minor_version) and re.match(r'\*', micro_version):
            print ("最後に＊ありでマッチンぐしたよ")
            match_version = [v for v in available_version if re.match(majaor_version + r'\.' + minor_version + r'\.[0-9]+', v)]

        elif re.match(r'[0-9]+', majaor_version) and re.match(r'\*', minor_version) and re.match(r'[0-9]+', micro_version):
            print ("真ん中に＊ありでマッチンぐしたよ")
            match_version = [v for v in available_version if re.match(majaor_version  + r'\.[0-9]+\.' + micro_version, v)]

        elif re.match(r'[0-9]+', majaor_version) and re.match(r'\*', minor_version) and re.match(r'\*', micro_version):
            print ("真ん中、最後に＊ありでマッチンぐしたよ")
            match_version = [v for v in available_version if re.match(majaor_version  + r'\.[0-9]+' + r'\.[0-9]+', v)]
        
        if not match_version: raise VersionNotFoundError('指定されたバージョンがArtifactoryにありませんでした') # 入ってなければfalseを返す
            # matchはしているが、ユーザ指定のバージョンがartifactoryにはなかった状況
            # raise VersionNotFoundError('指定されたバージョンがArtifactoryにありませんでした') 
        # Traceback (most recent call last):
        #   File "/home/moritoki/python_test/test3.py", line 101, in <module>
        #     raise VersionNotFoundError('指定されたバージョンがArtifactoryにありませんでした')
        # __main__.VersionNotFoundError: 指定されたバージョンがArtifactoryにありませんでした

    match_version.sort(key=StrictVersion) # match_versionの中身がソートされて保存もされる
    print("match_version_sorted = " + str(match_version))
    install_version = match_version[-1] # 配列最後を取得。１番大きいもの

    # ansible-gallaxyコマンド生成
    ansible_gallaxy_command = "ansible-gallaxy install " + str(name) + "-" + str(install_version) + ".tar.gz"
    print ("ansible_gallaxy_command = " + str(ansible_gallaxy_command))

    # ここまでループ


if __name__ == "__main__":
    main()