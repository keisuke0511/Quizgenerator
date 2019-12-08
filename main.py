from questionselect.parsedoc import ParseDocument
from questionselect.getdoc import get_response
from questionselect.getdoc_j import get_response_ja
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# クイズ生成に関するクエリ受付
@app.route('/quiz_generate', methods=['POST'])
def quiz_generate():
    # コンテンツ取得
    response = request.args.get('contents')
    view_url = request.args.get('view_url')
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

    return render_template('index.html', quiz_list=quiz_distracter, view_url=view_url)
    # return jsonify({'quiz_list': quiz_distracter})

# クイズ生成に関するクエリ受付(日本語)
@app.route('/quiz_generate_ja', methods=['POST'])
def quiz_generate_ja():
    # コンテンツ取得
    # response = request.args.get('contents')
    # view_url = request.args.get('view_url')
    response = request.form['contents']
    view_url = request.form['view_url']
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

    return render_template('index.html', quiz_list=quiz_distracter, view_url=view_url)

# クイズ採点に関するクエリ受付
@app.route('/quiz_score', methods=['POST'])
def quiz_score():
    return "GET Success"

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0', port=50000)
