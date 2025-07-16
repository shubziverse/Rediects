from flask import Flask, redirect, request, render_template, session, url_for
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MongoDB setup
client = MongoClient(os.getenv('MONGO_URI'))
db = client['redirect_app']
redirects = db['redirects']
users = db['users']

def get_redirect_url():
    doc = redirects.find_one({"name": "main"})
    return doc['url'] if doc else "https://example.com"

def set_redirect_url(new_url, user):
    redirects.update_one(
        {"name": "main"},
        {
            "$set": {
                "url": new_url.strip(),
                "last_updated_by": user,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )

def check_credentials(username, password):
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")
    return username == admin_user and password == admin_pass

@app.route('/r')
def redirect_main():
    return redirect(get_redirect_url(), code=302)

@app.route('/', methods=['GET', 'POST'])
def admin():
    if 'authenticated' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        new_url = request.form.get('url')
        if new_url:
            set_redirect_url(new_url, session.get("user", "unknown"))
    
    current_doc = redirects.find_one({"name": "main"})
    return render_template('admin.html', current_url=current_doc['url'], info=current_doc)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if check_credentials(user, pwd):
            session['authenticated'] = True
            session['user'] = user
            return redirect(url_for('admin'))
        else:
            error = "❌ Invalid credentials."
    return render_template('admin_login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
