from questionselect.parsedoc import ParseDocument
from questionselect.getdoc import get_response
from questionselect.getdoc_j import get_response_ja
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import psycopg2
import requests

app = Flask(__name__)
CORS(app)

# ユーザー情報の登録
@app.route('/quiz_user_register', methods=['GET','POST'])
def quiz_user_register():
    # ユーザー情報の取得
    user_name = request.form['user']
    password = request.form['password']
    # 既にユーザーが登録されているかどうか調べる
    conn = psycopg2.connect('dbname=question user=keisuke') # データベースへの接続
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM user_info u WHERE u.name=%s and u.passwd=%s',(user_name, password))
        row = cur.fetchone()
        if row:
            return '既にユーザー情報が入っています'
        else:
            cur.execute('INSERT INTO user_info(name, passwd) VALUES(%s, %s)',(user_name, password))
    conn.commit()
    conn.close()
    return "ユーザー情報が登録されました。"

# クイズ生成に関するクエリ受付
@app.route('/quiz_generate', methods=['GET','POST'])
def quiz_generate():
    # コンテンツ取得
    # response = request.args.get('contents')
    # view_url = request.args.get('view_url')
    response = request.form['contents']
    view_url = request.form['view_url']
    http_conn = request.form['httpconn']
    response = get_response(response)
    # ドキュメントの選択
    parsedoc = ParseDocument(response['contents'], response['wikilinks'])
    # ドキュメントから文分割、タグ付け、チャンキングを行う
    parsed_sentences = parsedoc.doc_to_sentences()
    # 問題文の選択
    quiz_stem = parsedoc.sentence_select(parsed_sentences)
    # correct keyの選択と空所補充問題生成(stem, key)
    stem_key_list = parsedoc.stem_key_select(quiz_stem)
    # correct_keyと同じカテゴリに属するトピックをdistracterとして扱う
    quiz_distracter = parsedoc.get_distracters(stem_key_list)

    return render_template('index.html', quiz_list=quiz_distracter, view_url=view_url, http_conn=http_conn)
    # return jsonify({'quiz_list': quiz_distracter})

# クイズ生成に関するクエリ受付(日本語)
@app.route('/quiz_generate_ja', methods=['GET','POST'])
def quiz_generate_ja():
    # コンテンツ取得
    # response = request.args.get('contents')
    # view_url = request.args.get('view_url')
    response = request.form['contents']
    view_url = request.form['view_url']
    http_conn = request.form['httpconn']
    response = get_response_ja(response)
    # ドキュメントの選択
    parsedoc = ParseDocument(response['contents'], response['wikilinks'])
    # ドキュメントから文分割、形態素解析、句構文解析を行う
    parsed_sentences = parsedoc.doc_to_sentences_ja()
    # 問題文の選択
    quiz_stem = parsedoc.sentence_select_ja(parsed_sentences)
    # correct_keyの選択と空所補充問題生成(stem, key)
    stem_key_list = parsedoc.stem_key_select(quiz_stem)
    # correct_keyと同じカテゴリに属するトピックをdistracterとして扱う
    quiz_distracter = parsedoc.get_distracters_ja(stem_key_list)

    return render_template('index.html', quiz_list=quiz_distracter, view_url=view_url, http_conn=http_conn)

# クイズ生成に関するクエリ日本語テスト用
@app.route('/quiz_generate_ja_test', methods=['GET', 'POST'])
def quiz_generate_ja_test():
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    url = request.form['url']
    get_url_info = requests.get(url, headers=HEADERS)
    return get_url_info.text

# クイズ採点に関するクエリ受付
@app.route('/quiz_score', methods=['GET','POST'])
def quiz_score():
    # resultBox = request.args.get('resultBox')
    quiz_box = json.loads(request.form['resultBox'])

    # 各解答結果を採点
    quiz_num = len(quiz_box) # 解いた問題数
    result_list = [] # 解答結果リスト

    conn = psycopg2.connect('dbname=question user=keisuke') # データベースへの接続
    # 採点結果をデータベースに格納
    for quiz in quiz_box:
        quiz_user = quiz['quiz_user']
        quiz_user_password = quiz['quiz_user_password']
        with conn.cursor() as cur:
            # ユーザー情報が入っているかをチェック
            cur.execute('SELECT * FROM user_info u WHERE u.name=%s and u.passwd=%s',(quiz_user, quiz_user_password))
            row = cur.fetchone()
            if not row:
                result = quiz['result']
                if result == 'correct_key':
                    result_list.append(1)
                else:
                    result_list.append(0)
            else:
                u_id = row[0]
                q_id = ''
                # 採点結果をリストに追加
                result = quiz['result']
                if result == 'correct_key':
                    result_list.append(1)
                else:
                    result_list.append(0)

                stem = quiz['stem']
                url = quiz['url']
                correct_key = quiz['correct_key']
                distracter_0 = quiz['distracter_0']
                distracter_1 = quiz['distracter_1']
                distracter_2 = quiz['distracter_2']
                selected_choice = quiz['selected_key']

                # questionテーブルへの格納
                cur.execute('SELECT * FROM question q WHERE q.stem=%s', (stem,))
                row = cur.fetchone()
                if not row:
                    cur.execute('INSERT INTO question(URL, stem) VALUES(%s, %s) RETURNING id',(url, stem))
                    q_id = cur.fetchone()[0]
                else:
                    q_id = row[0]

                # user_questionテーブルへの格納
                query = 'INSERT INTO user_question(u_id, q_id, correct_key, distracter_0, distracter_1, distracter_2, selected_choice) VALUES(%s,%s,%s,%s,%s,%s,%s)'
                cur.execute(query, (u_id, q_id, correct_key, distracter_0, distracter_1, distracter_2, selected_choice))

    # 採点結果をデータベースへ反映させる
    conn.commit()
    conn.close()

    return jsonify(result_list=result_list)

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0', port=50000)
