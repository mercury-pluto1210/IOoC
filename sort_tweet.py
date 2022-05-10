import json
import config
import keyword_tweet as KeyTwe
import time
import date_format
from datetime import datetime, date, timedelta
import MeCab
import requests
import pandas as pd
import numpy as np
import math

# 信頼性の高くなる辞書を作成
polite = ['公式', 'アカウント', 'ニュース', '市', '情報', 'です', 'ます']

# MeCab準備 辞書の指定
tagger = MeCab.Tagger(r'-Owakati -d "./mecab-ipadic-neologd"')

class SortTweet:
  def __init__(self, jsonData):
    # 習得したTwitterデータをpandas DataFramaに変換する
    data = []
    for line in jsonData['statuses']:
      data.append([line['user']['name'], line['user']['description'], line['entities']['urls'],
                  line['favorite_count'], line['created_at'], line['user']['listed_count'],
                  line['user']['verified'], line['user']['favourites_count'], line['text'],
                  line['user']['created_at'], line['retweet_count'], line['user']['friends_count'],
                  line['user']['statuses_count'], line['user']['followers_count']])

    self.df = pd.DataFrame(data,
                          columns=['user_name', 'user_description', 'entities_urls', 'favorite_count', 'created_at', 'user_listed_count', 'user_verified', 'user_favourites_count', 'text', 'user_created_at', 'retweet_count', 'user_friends_count', 'user_statuses_count', 'user_followers_count'])

    # str型のデータを適切な型に変換する
    self.df = self.df.astype({'favorite_count' : int})
    self.df = self.df.astype({'user_listed_count' : int})
    self.df = self.df.astype({'user_verified' : bool})
    self.df = self.df.astype({'user_favourites_count' : int})
    self.df = self.df.astype({'retweet_count' : int})
    self.df = self.df.astype({'user_friends_count' : int})
    self.df = self.df.astype({'user_statuses_count' : int})
    self.df = self.df.astype({'user_followers_count' : int})

  # user_name内の公式、情報などの文字列をカウントする
  def name_count(self, str):
    # nameの文字列を整形
    nameformat = str.strip()
    nameformat = nameformat.replace(',', ' ')
    namelines = nameformat.splitlines()
    nameformat = ''.join(namelines)

    polite_count1 = 0
    # user_nameを分かち書き
    namewords = tagger.parse(nameformat)

    for w in polite:
      polite_count1 += namewords.count(w)
    return polite_count1

  # descriptionの文字列を整形
  def description_format(self, str):
    descriptionformat = str.strip()
    descriptionformat = descriptionformat.replace(',', ' ')
    descriptionlines = descriptionformat.splitlines()
    descriptionformat = ''.join(descriptionlines)
    return descriptionformat

  # description内の公式、情報などの文字列をカウントする
  def description_count(self, str):
    polite_count2 = 0
    # descriptionを分かち書き
    descriptionwords = tagger.parse(str)

    for o in polite:
      polite_count2 += descriptionwords.count(o)
    return polite_count2

  # 本文中にURLが挿入されているか判定する
  def is_url(self, str):
    expanded_url = 0

    if not str:
      expanded_url = 0
    else:
      if str[0]['expanded_url'] == '':
        expanded_url = 0
      else:
        expanded_url = 1
    return expanded_url

  # 投稿曜日を0 ~ 6で判定する
  # 月曜: 0、火曜: 1、水曜: 2、木曜: 3、金曜: 4、土曜: 5、日曜: 6
  def judge_someday(self, str):
    src1 = str
    dst1 = date_format.convert_date_format(src1)
    someday = datetime.strptime(dst1, "%Y-%m-%d")
    week_num_someday = someday.weekday()
    return week_num_someday

  # 認証済みアカウントを0か1で判定する
  def is_verified(self, x):
    user_verified = 0

    if x:
      user_verified = 1
    else:
      user_verified = 0
    return user_verified

  # text内のポジネガ極性を測る
  def posinega_count(self, str):
    # Google APIキーの設定
    GK = config.GOOGLE_KEY
    url = 'https://language.googleapis.com/v1/documents:analyzeSentiment?key=' + GK

    # textの文字列を整形
    textformat = str.strip()
    textformat = textformat.replace(',', ' ')
    textlines = textformat.splitlines()
    textformat = ''.join(textlines)

    # Google Cloud Platformの基本設定
    header = {'Content-Type': 'application/json'}
    body = {
      "document": {
        "type": "PLAIN_TEXT",
        "language": "JA",
        "content": textformat
      },
      "encodingType": "UTF8"
    }

    #json形式で結果を受け取る。
    response = requests.post(url, headers=header, json=body).json()
    return response["documentSentiment"]["score"] + 1.0

  # アカウント年齢を計算
  def time_format(self, str):
    # 取得した今時間を年、月、日に分ける
    today = datetime.now()
    todayY = today.year
    todayM = today.month
    todayD = today.day

    src = str
    dst = date_format.convert_date_format(src)
    dstY = int(dst.split('-')[0])
    dstM = int(dst.split('-')[1])
    dstD = int(dst.split('-')[2])

    dt1 = datetime(dstY, dstM, dstD)
    dt2 = datetime(todayY, todayM, todayD)
    dtAge = (dt2 - dt1).days
    return dtAge

  # 正規化をする関数
  def normalization(self, x, min_x, max_x):
    # 例外処理
    if max_x == min_x:
      return 0
    return (x - min_x) / (max_x - min_x)

  # 正規化して新たな列として生成する(上限値が設定されていない値)
  def normalization_column(self, columnName):
    new_columnName = 'nomalization_' + columnName
    minimum = self.df[columnName].min() # 最小値
    maximum = self.df[columnName].max() # 最大値
    self.df[new_columnName] = self.df[columnName].apply(lambda x: self.normalization(x, minimum, maximum))

  # 正規化して新たな列として生成する(上限値が設定されている値)
  def upper_normalization_column(self, columnName, upperLimit):
    new_columnName = 'nomalization_' + columnName
    minimum = self.df[columnName].min() # 最小値
    self.df[new_columnName] = self.df[columnName].apply(lambda x: self.normalization(x, minimum, upperLimit))

  # シグモイド関数
  # 非常に大きい(10~)値だと1にしかならない
  def sigmoid(self, x):
    s = 1. / (1 + np.exp(-x))
    return s

  # 平均値、標準偏差を求める
  def deviation_information(self, columnName):
    avg = self.df[columnName].mean() # 列の平均値
    sd = self.df[columnName].std() # 標準偏差
    self.df[columnName] = self.df[columnName].apply(lambda x: self.deviation_value(x, avg, sd))

  # 偏差値を求める
  def deviation_value(self, x, avg, sd):
    # 標準偏差が0(全てのpointが同じ値)の場合偏差値は50になる
    if sd == 0:
      return 1
    return math.floor((x - avg) / sd * 10 + 50)

  def analyze_tweet(self):
    # 上限値の設定
    upper_description_length = 160
    upper_description_polite_count = 5
    upper_user_name_polite_count = 5
    upper_favorite_count = 200
    upper_user_ff_rate = 500.0
    upper_user_listed_count = 1100
    upper_user_favourites_count = 21000
    upper_account_age = 365
    upper_retweet_count = 10000
    upper_user_friends_count = 1200
    upper_user_statuses_count = 60000
    upper_user_followers_count = 3000

    # descriptionを整形する
    self.df['user_description'] = self.df['user_description'].apply(lambda str: self.description_format(str))
    # descriptionの文字数
    self.df['description_length'] = self.df['user_description'].apply(lambda x: len(x))
    # descriptionのです、ますカウント
    self.df['description_polite_count'] = self.df['user_description'].apply(lambda str: self.description_count(str))
    # nameの公式、情報カウント
    self.df['user_name_polite_count'] = self.df['user_name'].apply(lambda str: self.name_count(str))
    # 本文内のurlの有無
    self.df['is_urls'] = self.df['entities_urls'].apply(lambda str: self.is_url(str))
    # 何曜日に投稿されたか(0: 日曜、1: 月曜、、、)
    self.df['day_num'] = self.df['created_at'].apply(lambda str: self.judge_someday(str))
    # フォロワー数とフォロー数の比
    # フォロー数が0であると、計算が出来ないため0の場合は1として計算する
    self.df['user_friends_count'] = self.df['user_friends_count'].where(self.df['user_friends_count'] != 0, 1)
    self.df['user_ff_rate'] = self.df['user_followers_count'] / self.df['user_friends_count']
    # 公式マークの有無
    self.df['user_verified'] = self.df['user_verified'].apply(lambda x: self.is_verified(x))
    # アカウントの年齢
    self.df['account_age'] = self.df['user_created_at'].apply(lambda str: self.time_format(str))
    # ポジネガ極性
    self.df['PN_count'] = self.df['text'].apply(lambda str: self.posinega_count(str))

    # 正規化
    self.upper_normalization_column('description_length', upper_description_length)
    self.upper_normalization_column('description_polite_count', upper_description_polite_count)
    self.upper_normalization_column('user_name_polite_count', upper_user_name_polite_count)
    self.upper_normalization_column('favorite_count', upper_favorite_count)
    self.normalization_column('day_num')
    self.upper_normalization_column('user_ff_rate', upper_user_ff_rate)
    self.upper_normalization_column('user_listed_count', upper_user_listed_count)
    self.upper_normalization_column('user_favourites_count', upper_user_favourites_count)
    self.upper_normalization_column('account_age', upper_account_age)
    self.upper_normalization_column('retweet_count', upper_retweet_count)
    self.upper_normalization_column('user_friends_count', upper_user_friends_count)
    self.upper_normalization_column('user_statuses_count', upper_user_statuses_count)
    self.upper_normalization_column('user_followers_count', upper_user_followers_count)
    self.normalization_column('PN_count')

    # 線形和(評価値)を算出
    # 各特徴量の係数値 機械学習によって算出
    weight = [0.07576589, 0.05626076, 0.02081474, 0.06532632, 0.00431932, 0.0344098, 0.07515838, 0.05845529, 0.0043411,  0.11462243, 0.11761638, 0.00603965, 0.09278253, 0.12090105, 0.10188821, 0.05129817]
    self.df['point'] = weight[0] * self.df['nomalization_description_length'] \
                     + weight[1] * self.df['nomalization_description_polite_count'] \
                     + weight[2] * self.df['nomalization_user_name_polite_count'] \
                     + weight[3] * self.df['is_urls'] \
                     + weight[4] * self.df['nomalization_favorite_count'] \
                     + weight[5] * self.df['nomalization_day_num'] \
                     + weight[6] * self.df['nomalization_user_ff_rate'] \
                     + weight[7] * self.df['nomalization_user_listed_count'] \
                     + weight[8] * self.df['user_verified'] \
                     + weight[9] * self.df['nomalization_user_favourites_count'] \
                     + weight[10] * self.df['nomalization_account_age'] \
                     + weight[11] * self.df['nomalization_retweet_count'] \
                     + weight[12] * self.df['nomalization_user_friends_count'] \
                     + weight[13] * self.df['nomalization_user_statuses_count'] \
                     + weight[14] * self.df['nomalization_user_followers_count'] \
                     + weight[15] * self.df['nomalization_PN_count']

    # pointをシグモイド関数で正規化する
    self.df['point'] = self.df['point'].apply(lambda x: self.sigmoid(x))
    # pointを元に各値を偏差値に変換する
    self.deviation_information('point')
    # # 小数点以下を切り捨てる
    # self.df['point'] = math.floor(self.df['point'])
    # pointを降順に並べる
    self.df = self.df.sort_values('point', ascending=False)

    return self.df

# テスト用
if __name__ == "__main__":
  res = KeyTwe.fetch_keyword_tweet('コロナ', 1)
  x = SortTweet(res)
  print(x.df)