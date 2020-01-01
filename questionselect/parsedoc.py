import nltk
import MeCab
import random
from questionselect.getdoc import get_category
from questionselect.getdoc import get_topic
from questionselect.getdoc_j import get_category_ja
from questionselect.getdoc_j import get_topic_ja

class ParseDocument(object):

    # 入力ドキュメントURLの初期化
    def __init__(self, doc, wikilinks):
        self.doc = doc
        self.wikilinks = wikilinks # wikipediaリンクのリスト

    # ドキュメントの出力
    def print_doc(self):
        print("<Document>")
        print(self.doc)
        print("-------------------------------------------")
        print("<Wikilinks>")
        print(self.wikilinks)
        print("-------------------------------------------")

    # センテンスにwikilinkを含むかチェック
    def wikilink_check(self, sent):
        wikilink_validity = False
        for wikilink in self.wikilinks:
            if wikilink in sent:
                wikilink_validity = True

        return wikilink_validity

    # センテンスに対するチャンキングを行う
    def sentence_chunking(self, sent):
        grammar = r"""
            NP: {<DT|JJ|NN.*>+}
            NP: {<NP><RB|VBN|PP|PPTO>+}
            PP: {<IN><NP>}
            VP: {<VB.*><NP|PP|RB|CLAUSE>+$}
            CLAUSE: {<NP><VP>}
            PPTO: {<TO><NP>}
            QUIZ: {<NP><QUIZV>}
            QUIZV: {<VBZ|VBD> | <VBZ|VBD><PP>}
            """

        chunk_parser = nltk.RegexpParser(grammar, loop=2)

        sent = chunk_parser.parse(sent)

        return sent

    # ドキュメントをセンテンスに分割(タグ付け・チャンキング付け済み)
    def doc_to_sentences(self):
        sentences = nltk.sent_tokenize(self.doc) # 文分割
        sentences = [nltk.word_tokenize(sent) for sent in sentences if self.wikilink_check(sent)]
        sentences = [nltk.pos_tag(sent) for sent in sentences] # タグ付け

        # チャンキング(wikilinkを持っている文を対象とする)
        sentences = [self.sentence_chunking(sent) for sent in sentences]

        return sentences

    # 日本語ドキュメントをセンテンスに分割(形態素解析・句構文解析も行う)
    def doc_to_sentences_ja(self):
        # 句構文分析の規則
        grammer = '''
            NP: {<形容詞-自立.*>*<名詞.*>+ | <記号.*>*}
            NP: {<NP>*<助詞-連体化><NP>*}
            VP: {<動詞.*>*<助動詞-*>*}
            VP: {<NP>+<VP>+ | <NP>+<動詞.*>}
            SHUKAKU: {<NP>+<助詞-格助詞-ガ> | <NP>+<助詞-格助詞-ハ> | <NP>+<助詞-係助詞>}
            MOKUTEKIKAKU: {<NP>+<助詞-格助詞-ニ> | <NP>+<助詞-格助詞-ヲ>}
            QUIZ: {<SHUKAKU>+<MOKUTEKIKAKU>*<VP>}
                  '''

        sentences = self.doc.split('。') # テキストを行ごとに分割

        # mecabオブジェクトの生成
        mecab = MeCab.Tagger('-Ochasen')

        # chank parserの生成
        cp = nltk.RegexpParser(grammer, loop=2)

        # 句構文リストのセット
        cp_text_list = []
        for sentence in sentences:
            # 解析結果をリスト化
            parse_result = mecab.parse(sentence)
            parse_result = parse_result.split('\n')
            parse_result = [result.split('\t') for result in parse_result]
             
            # 句構文解析を行う
            cp_text = []
            for pr_node in parse_result:
                # 読みがEOSであるときの処理
                if pr_node[0] == 'EOS':
                    cp_tuple = ('EOS', '*')
                    cp_text.append(cp_tuple)
                    break
		# 解析結果の情報整理
                yomi = pr_node[0] # 品詞の表層系 
                attr = ('-').join(pr_node[3].split('-')[:2]) #品詞情報
                # 品詞発音情報
                attr_h = pr_node[1]
                # 格助詞であれば、発音情報も取り入れる
                if attr=='助詞-格助詞':
                    attr = attr + '-' + attr_h
                if attr=='助詞-格助詞':
                    attr = attr + '-' + attr_h
                cp_tuple = (yomi, attr)
                cp_text.append(cp_tuple)
            # print(cp_text)
            # 各文の解析結果をリストに入れる
            cp_text_list.append(cp.parse(cp_text))

        return cp_text_list[1:]

    # センテンスリストから問題文形式とマッチする文を抽出する
    def sentence_select(self, sentlist):
        # sentence treeからQUIZチャンクタグを含むものを選択する
        quiz_stem = []
        for sent in sentlist:
            for subtree in sent.subtrees():
                if subtree.label() == 'QUIZ':
                    quiz_sent_add = [word for word, tag in sent.leaves()]
                    quiz_sent_add = " ".join(quiz_sent_add[:-1])
                    quiz_stem.append(quiz_sent_add)

        # 問題文の数が５個よりも多い場合に、リストからランダムに選択
        if len(quiz_stem) > 5:
            random.shuffle(quiz_stem)
            quiz_stem = quiz_stem[0:5]

        return quiz_stem

    # 日本語センテンスリストから問題文形式とマッチする文を抽出
    def sentence_select_ja(self, sentlist):
        # sentence treeからQUIZチャンクタグを含むものを選択する
        quiz_stem = []
        for sent in sentlist:
            if isinstance(sent, tuple):
                continue
            for subtree in sent.subtrees():
                if subtree.label() == 'QUIZ':
                    quiz_sent_add = [word for word, tag in sent.leaves()]
                    quiz_sent_add = ''.join(quiz_sent_add[:-1])
                    quiz_stem.append(quiz_sent_add)
        # 問題文の数が５個よりも多い場合に、リストからランダムに選択
        if len(quiz_stem) > 5:
            random.shuffle(quiz_stem)
            quiz_stem = quiz_stem[0:5]

        return quiz_stem

    # stemからcorrectkeyをランダムに選択
    def correct_key_select(self, stem):
        # wikilinksからstemにあるキーワードをまとめる
        keywords = []
        for wikilink in self.wikilinks:
            if wikilink == '':
                continue
            if wikilink in stem:
                keywords.append(wikilink)
        # keywordsからランダムにcorrect_keyを選択
        # keywords empty check
        if len(keywords) <= 0:
            return "nothing"
        correct_key = keywords[random.randint(0, len(keywords)-1)]

        return correct_key

    # stemリストからcorrect keyと空所補充問題の生成
    def stem_key_select(self, stemlist):
        stem_key_list = []
        for stem in stemlist:
            # stemのlength check
            if len(stem) < 5 or len(stem) > 100:
                continue
            # 各stemからcorrect keyを選択
            # print(stem)
            correct_key = self.correct_key_select(stem)
            # correct_keyがnothingである場合の対策
            if correct_key == 'nothing':
                continue
            # stemからcorrect_keyに対応するキーワードを空欄化
            stem = stem.replace(correct_key, "__________")
            # listに追加
            stem_key_list.append({"stem":stem, "correct_key":correct_key})

            #print("<stem>")
            #print(stem)
            #print("<correct key>")
            #print(correct_key)
            #print("-------------------------------------------")

        return stem_key_list

    # correct_keyからdistracterを選択
    def get_distracters(self, stem_key_list):
        # 問題文、正解、不正解の辞書リスト
        quiz_distracter = []
        # 各問題ごとに処理を行う(for)
        for stem_key in stem_key_list:
            # correct_keyのwikiページにとび、属するカテゴリを取得
            categories = get_category(stem_key["correct_key"])
            # カテゴリの数が３つよりも多い時、リストからランダムに３つ選択
            categories = categories[0:3]
            #print("<category>")
            #print(categories)
            #print("--------------------------------------------")

            # 各カテゴリから最大3つのトピックを取得する
            topics = []
            for category in categories:
                topics.append(get_topic(category))
            topics = sum(topics, []) # リストをflattenにする
            random.shuffle(topics)# リストをランダムソート
            # トピックリストの数が少ないかどうかを検証
            if len(topics) < 3:
                continue
            # トピックのリストからランダムに３つのdistracterを取得する
            distracters = topics[:3]
            choice = [("correct_key" , stem_key["correct_key"]),
                        ("distracter_0" , distracters[0]),
                        ("distracter_1" , distracters[1]),
                        ("distracter_2" , distracters[2])]
            random.shuffle(choice)
            quiz_distracter.append({
                "stem" : stem_key["stem"],
                # "correct_key" : stem_key["correct_key"],
                # "distracters" : distracters
                "choice" : choice
            })

        return quiz_distracter

    # correct_keyからdistracterを選択
    def get_distracters_ja(self, stem_key_list):
        # 問題文、正解、不正解の辞書リスト
        quiz_distracter = []
        # 各問題ごとに処理を行う(for)
        for stem_key in stem_key_list:
            # correct_keyのwikiページにとび、属するカテゴリを取得
            categories = get_category_ja(stem_key["correct_key"])
            # カテゴリの数が３つよりも多い時、リストからランダムに３つ選択
            if len(categories) > 3:
                random.shuffle(categories)
                categories = categories[0:3]
            # print("<category>")
            # print(categories)
            # print("--------------------------------------------")

            # 各カテゴリから最大3つのトピックを取得する
            topics = []
            for category in categories:
                topics.append(get_topic_ja(category))
            topics = sum(topics, []) # リストをflattenにする
            random.shuffle(topics)# リストをランダムソート
            # リストの重複を削除する
            topics = list(set(topics))
            # トピックリストの数が少ないかどうかを検証
            if len(topics) < 3:
                continue
            # トピックのリストからランダムに３つのdistracterを取得する
            distracters = topics[:3]
            choice = [("correct_key" , stem_key["correct_key"]),
                        ("distracter_0" , distracters[0]),
                        ("distracter_1" , distracters[1]),
                        ("distracter_2" , distracters[2])]
            random.shuffle(choice)
            quiz_distracter.append({
                "stem" : stem_key["stem"],
                # "correct_key" : stem_key["correct_key"],
                # "distracters" : distracters
                "choice" : choice
            })

        return quiz_distracter

    # 問題文の表示
    def quiz_display(self, quiz_distracter):
        # get_distractersで仕様が変更されているため、ここも変える必要あり
        for dic in quiz_distracter:
            print("--Question--")
            print(dic["stem"])
            for k, choice in dic["choice"]:
                print("%s: %s"%(k, choice))
            print("")

        return
