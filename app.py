from flask import Flask, render_template, request
from flaskext.markdown import Markdown
from search import Search

app = Flask(__name__)
Markdown(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

s = Search()

@app.route('/', methods=['GET', 'POST'])
def main_page():
    return render_template("main.html")


@app.route('/tags.html', methods=['GET', 'POST'])
def reranker():
    return render_template("tags.html")

@app.route('/query_rules.html', methods=['GET', 'POST'])
def bm25():
    return render_template("query_rules.html")

@app.route('/search.html', methods=['GET', 'POST'])
def result():
    return render_template("search.html")

@app.route('/search', methods=['GET', 'POST'])
def answer_search():
    query = request.form["query"]
    if not query:
        query = ""
    indices, metadata, htmls = s.search(query)
    return render_template('result.html', indices=indices, metadata=metadata, htmls=htmls)

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    app.run() 