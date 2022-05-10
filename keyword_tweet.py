import json
import config
from requests_oauthlib import OAuth1Session
import sort_tweet as SoTwee
import pandas as pd

# 定数定義
TWEET_NUM = 50
# CK = process.env.React_APP_CONSUMER_KEY;

def fetch_keyword_tweet(keyword):
  # OAuth認証部分
  CK      = config.CONSUMER_KEY
  CS      = config.CONSUMER_SECRET
  AT      = config.ACCESS_TOKEN
  ATS     = config.ACCESS_TOKEN_SECRET
  twitter = OAuth1Session(CK, CS, AT, ATS)

  # Twitter Endpoint(ユーザータイムラインを取得する)
  url = "https://api.twitter.com/1.1/search/tweets.json?exclude_replies=true"

  params ={
           'count'       : TWEET_NUM,   # 取得するtweet数
           'q'           : keyword,     # 検索キーワード
           'result_type' : 'recent',     # popular: 人気のツイート、recent: 最新のツイート、mixed: 全てのツイート
           'exclude'     : 'retweets',  # リツイートは取得しないようにする
          }

  req = twitter.get(url, params = params)

  # メイン処理
  # resという配列に全てのツイートが格納
  if req.status_code == 200:
    res = json.loads(req.text)
    return res

  else:
    return print("Failed: %d" % req.status_code)

def bkend_main(key):
  # ツイートの各情報を指定数取得する
  res = fetch_keyword_tweet(key)

  data = SoTwee.SortTweet(res)
  df = data.analyze_tweet()
  header = df.columns
  record = df.values.tolist()
  return header, record

if __name__ == "__main__":
  bkend_main('コロナ')