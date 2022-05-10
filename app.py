from flask import Flask
from flask import render_template
from flask import request
from flask_bootstrap import Bootstrap
from keyword_tweet import bkend_main

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route("/")
def hello():
  return render_template('index.html', title = 'IOoC (Information Organize of Collection)')

@app.route("/keyword", methods=["POST", "GET"])
def index():
  twitter_keyword = request.form["key"]
  header, record = bkend_main(twitter_keyword)
  return render_template("result.html", record=record)

# サーバーを起動
if __name__ == "__main__":
  app.run(debug=True, port=5000)