
from flask import Flask, request, jsonify, render_template, abort
from style.styleOllama import get_trustworthiness_score
from reputation.reputation import get_reputation_score
from style.geminiClean import clean_text
#from reputation import calculate_credibility_score, get_linkedin_profile, get_google_scholar_data
import sys
import os
import sqlite3
import hashlib
import base64
import contextlib
import io
import asyncio
import nest_asyncio
import threading
import time
from datetime import datetime
import style.geminiReasoning
import progressHold
# OpenFactVerification dependency
fact_dir = os.path.join(os.path.dirname(__file__), 'fact')
if fact_dir not in sys.path:
    sys.path.append(fact_dir)
from fact.factExtraction import get_fact_score

nest_asyncio.apply()
app = Flask(__name__)



DATABASE = 'history.db'

def analyze_text(text):
    score = get_trustworthiness_score(text)
    return score

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE,
                style_score REAL,
                style_reasoning TEXT,
                reputation_score REAL,
                reputation_reasoning TEXT,
                fact_score REAL,
                fact_reasoning TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE fact_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER,
                claim TEXT,
                factuality TEXT,
                FOREIGN KEY(result_id) REFERENCES results(id) ON DELETE CASCADE
            )
        ''')
        c.execute('''
            CREATE TABLE sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_check_id INTEGER,
                source_name TEXT,
                publisher TEXT,
                url TEXT,
                relationship TEXT,
                reasoning TEXT,
                FOREIGN KEY(fact_check_id) REFERENCES fact_checks(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

init_db()

def generate_hash(data):
    now = datetime.now().isoformat()
    unique_string = f"{data}-{now}"
    hash_object = hashlib.md5(unique_string.encode())
    base64_encoded = base64.urlsafe_b64encode(hash_object.digest()).decode('utf-8')
    return base64_encoded[:8]

def insert_record(hash_value, style_score, style_reasoning,
                  reputation_score, reputation_reasoning,
                  fact_score, fact_reasoning):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO results (hash, style_score, style_reasoning,
                                 reputation_score, reputation_reasoning,
                                 fact_score, fact_reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (hash_value, style_score, style_reasoning,
              reputation_score, reputation_reasoning,
              fact_score, fact_reasoning))
        conn.commit()
    except sqlite3.IntegrityError:
        # Handle duplicate hash scenario
        pass
    finally:
        conn.close()

def insert_facts(result_hash, facts):
    """
    Inserts facts and their sources into the database.

    Parameters:
    - result_hash (str): The hash value from the results table to associate the facts with.
    - facts (list of dict): Each dict should contain:
        - 'claim' (str)
        - 'factuality' (str)
        - 'source_name' (str)
        - 'publisher' (str, optional)
        - 'url' (str, optional)
        - 'relationship' (str, optional)
        - 'reasoning' (str, optional)
    """
    conn = get_db_connection()
    try:
        # Fetch the result_id using the hash
        cur = conn.execute('SELECT id FROM results WHERE hash = ?', (result_hash,))
        result = cur.fetchone()
        if not result:
            raise ValueError(f"No result found with hash: {result_hash}")
        result_id = result['id']

        for fact in facts:
            # Insert into fact_checks
            cur = conn.execute('''
                INSERT INTO fact_checks (result_id, claim, factuality)
                VALUES (?, ?, ?)
            ''', (result_id, fact['claim'], fact['factuality']))
            fact_check_id = cur.lastrowid

            # Insert into sources
            conn.execute('''
                INSERT INTO sources (fact_check_id, source_name, publisher, url, relationship, reasoning)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                fact_check_id,
                fact.get('source_name'),
                fact.get('publisher'),
                fact.get('url'),
                fact.get('relationship'),
                fact.get('reasoning')
            ))

        conn.commit()
    except Exception as e:
        print(f"Error inserting facts: {e}")
        conn.rollback()
    finally:
        conn.close()

def fetch_record_by_hash(hash_value):
    conn = get_db_connection()
    try:
        # Fetch the main result record
        cur = conn.execute('SELECT * FROM results WHERE hash = ?', (hash_value,))
        result = cur.fetchone()
        if not result:
            return None
        
        # Convert result Row object to dict
        record = dict(result)

        # Fetch related fact_checks
        cur = conn.execute('SELECT * FROM fact_checks WHERE result_id = ?', (result['id'],))
        fact_checks = cur.fetchall()

        # Initialize list to hold fact_checks + their sources
        attached_fact_checks = []

        for fc in fact_checks:
            cur_sources = conn.execute('SELECT * FROM sources WHERE fact_check_id = ?', (fc['id'],))
            sources = cur_sources.fetchall()

            # Include all sources, regardless of whether a URL is present
            fact_check = dict(fc)
            fact_check['sources'] = [dict(source) for source in sources]
            attached_fact_checks.append(fact_check)

        record['fact_checks'] = attached_fact_checks

        return record
    finally:
        conn.close()
@app.route('/submit', methods=['POST'])
def submit_text():
    content = request.json
    progressHold.reset_progress()
    #hash_value = generate_hash(content['text'])
    article_url = content.get('url')
    article_text = content.get('text')
    hash_value = generate_hash(content['text'])
    #hash_value = '5j7SJFBQ'
    thread = threading.Thread(target=evaluate_everything, args=(article_text, article_url, hash_value))
    thread.start()
    return jsonify({
        'hash': hash_value,
        'progress_url': '' + request.host_url + 'progress/' + hash_value,
    })

@app.route('/progress/<hash_value>', methods=['GET'])
def get_progress(hash_value):
    print(hash_value)
    record = fetch_record_by_hash(hash_value)
    print(record)
    if record:
        return jsonify({'progress': 100, 'url': f"{request.host_url}result/{hash_value}"})
    with progressHold._progress_lock:
        current = progressHold.progress
        print(f"Current progress for {hash_value}: {current}")
    if current >= 100:
        return jsonify({'progress': 100, 'url': f"{request.host_url}result/{hash_value}"})
    else:
        return jsonify({'progress': current, 'url': ""})



def evaluate_everything_test(text, url, hash_value):
    print("sleeping")
    for i in range(20):
        time.sleep(5)
        progressHold.add_progress()
        print("sleeping")
    return 
#@app.route('/evaluate-text', methods=['POST'])
def evaluate_everything(text, url, hash_value):
    try:
        progressHold.add_progress()
        article_text = clean_text(text)
        progressHold.add_progress()
        print(text)
        article_url = url
        print("Article URL:")
        print(article_url)
        if not article_text:
            return jsonify({'error': 'No text provided'}), 400
        #hash_value = generate_hash(article_text)
        #style_score, style_reasoning = get_trustworthiness_score(article_text)
        #reputation_score, reputation_reasoning = get_reputation_score(article_text, article_url)
        #fact_score, fact_list = get_fact_score(article_text)
        try:
            style_score, style_reasoning, reputation_score, reputation_reasoning, fact_score, fact_list = asyncio.run(run_all(article_text, article_url))
        except Exception as e:
            print(f"Error during async evaluation: {e}")
        fact_score = round(fact_score, 2)
        fact_reasoning = style.geminiReasoning.generate_reasoning(fact_score, article_text, 'fact')
        progressHold.add_progress()
        #reputation_reasoning = style.geminiReasoning.generate_reasoning(reputation_score, article_text, 'reputation')
        insert_record(hash_value, style_score, style_reasoning,
                      reputation_score, reputation_reasoning,
                      fact_score, fact_reasoning)
        insert_facts(hash_value, fact_list)
        result_url = f"{request.host_url}result/{hash_value}"
        response_data = {
            'style_score': style_score,
            'reputation_score': reputation_score,
            'fact_score': fact_score,
            'hash': hash_value,
            'result_url': result_url
        }
        return response_data
    except Exception as e:
        progress = 0
        return 500


async def run_all(text, url):
    style_future = asyncio.to_thread(get_trustworthiness_score, text)
    reputation_future = asyncio.to_thread(get_reputation_score, text, url)
    fact_future = asyncio.to_thread(get_fact_score, text)
    
    print("About to run")
    style_result, reputation_result, fact_result = await asyncio.gather(
        style_future, reputation_future, fact_future
    )
    style_score, style_reasoning = style_result
    reputation_score, reputation_reasoning = reputation_result
    fact_score, fact_list = fact_result
    print("Success, done running async")

    return style_score, style_reasoning, reputation_score, reputation_reasoning, fact_score, fact_list

@app.route('/result/<hash_value>', methods=['GET'])
def show_result(hash_value):
    record = fetch_record_by_hash(hash_value)
    if not record:
        abort(404, description="Result not found.")
    return render_template('result.html', record=record)

@app.route('/real')
def real_article():
    return render_template('real.html')

@app.route('/fake')
def fake_article():
    return render_template('fake.html')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)

