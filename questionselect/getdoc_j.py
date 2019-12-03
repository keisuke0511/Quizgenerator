import requests
import requests_cache
import re
from bs4 import BeautifulSoup

requests_cache.install_cache()

BASE_URL = "https://ja.wikipedia.org/wiki/"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# HTMLレスポンスからコンテンツを抽出
def get_response_ja(response):
    dict = {} # 辞書型で返す

    # BeautifulSoupによるタグツリー変換
    soup = BeautifulSoup(response, 'lxml')
    # コンテンツの抽出(body, pタグの中身を探索)
    body = soup.select_one('body')
    contents = body.select('p')
    # wikipediaのリンクを抽出
    wikilinks = body.find_all(href=re.compile("https://ja.wikipedia.org/wiki/"))

    # コンテンツをテキスト型に変換
    text = ''
    for content in contents:
        text += content.text

    # 正規表現により指定の文字列を削除
    rep = r"\s\(.*\)\s"
    rep2 = r"\s\(.*\)[,]?\s"
    text = re.sub(rep, " ", text)
    text = re.sub(rep2, " ", text)

    # wikilinksをリスト型に変換
    wikilinks = [wikilink.text for wikilink in wikilinks]

    # Wikipediaのリンクリスト, テキストを辞書に追加
    dict['contents'] = text
    dict['wikilinks'] = wikilinks

    return dict

# wikiページ内からカテゴリを所得
def get_category_ja(correct_key):
    categories = []
    # correct_keyに対応したwikiページへのリクエスト
    URL = BASE_URL + correct_key

    # コンテンツからcategoryリストの取得
    response = requests.get(URL, headers=HEADERS)
    content = response.content.decode('utf-8')
    soup = BeautifulSoup(content, "lxml")
    category_list = soup.select('div#mw-normal-catlinks ul li')
    for li in category_list:
        category = li.select_one('a').text
        # categoryをリストに追加
        categories.append(category)

    return categories

# カテゴリページからトピックを全取得
def get_topic_ja(category):
    topics = []
    # カテゴリページへのリクエスト
    URL = BASE_URL + "Category:" + category

    # コンテンツからtopicリストの取得
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, "lxml")
    alphabet_list = soup.select('div.mw-category-group')
    for topic_list in alphabet_list:
        topic_list = topic_list.select('ul li')
        for li in topic_list:
            topic = li.select_one('a').text
            topics.append(topic)
    return topics
