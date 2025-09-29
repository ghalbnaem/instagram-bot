"""
Flask web app for the Telegram bot dashboard.
This provides a web interface to manage the bot, view statistics,
and see user data.
"""

import os
import json
import datetime
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///telegram_bot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
db.init_app(app)

# File paths for JSON data
USERS_FILE = 'data/users.json'
ADS_FILE = 'data/ads.json'
VISIT_LINKS_FILE = 'data/visit_links.json'
USER_ADS_FILE = 'data/user_ads.json'

def load_data(file_path):
    """Load data from a JSON file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return appropriate empty structure
            if file_path == USERS_FILE:
                return {}
            elif file_path == ADS_FILE:
                return {}
            elif file_path == VISIT_LINKS_FILE:
                return []
            elif file_path == USER_ADS_FILE:
                return {}
    except (FileNotFoundError, json.JSONDecodeError):
        # Return appropriate empty structure
        if file_path == USERS_FILE or file_path == ADS_FILE or file_path == USER_ADS_FILE:
            return {}
        elif file_path == VISIT_LINKS_FILE:
            return []
    return {}

def save_data(data, file_path):
    """Save data to a JSON file"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_statistics():
    """Get bot statistics"""
    users = load_data(USERS_FILE)
    ads = load_data(ADS_FILE)
    visit_links = load_data(VISIT_LINKS_FILE)
    user_ads = load_data(USER_ADS_FILE)

    # Calculate statistics
    total_users = len(users)
    total_admin_ads = len(ads)
    total_user_ads = sum(len(ads_list) for ads_list in user_ads.values()) if isinstance(user_ads, dict) else 0
    total_links = len(visit_links)
    
    # Calculate total points in the system
    total_points = sum(user.get('points', 0) for user in users.values())
    
    # Calculate recent registrations (last 7 days)
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)
    recent_registrations = 0
    
    for user_data in users.values():
        registered_at = user_data.get('registered_at')
        if registered_at:
            try:
                reg_date = datetime.datetime.strptime(registered_at, '%Y-%m-%d %H:%M:%S')
                if reg_date >= seven_days_ago:
                    recent_registrations += 1
            except ValueError:
                pass
    
    return {
        'total_users': total_users,
        'total_admin_ads': total_admin_ads,
        'total_user_ads': total_user_ads,
        'total_links': total_links,
        'total_points': total_points,
        'recent_registrations': recent_registrations
    }

@app.route('/')
def index():
    """Render the dashboard home page"""
    stats = get_statistics()
    now = datetime.datetime.now()
    return render_template('index.html', statistics=stats, now=now)

@app.route('/users')
def users():
    """Render the users list page"""
    users_data = load_data(USERS_FILE)
    return render_template('users.html', users=users_data)

@app.route('/user/<user_id>')
def user_detail(user_id):
    """Render the user detail page"""
    users_data = load_data(USERS_FILE)
    user = users_data.get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('users'))
    
    return render_template('user_detail.html', user=user, user_id=user_id)

@app.route('/ads')
def ads():
    """Render the ads list page"""
    ads_data = load_data(ADS_FILE)
    return render_template('ads.html', ads=ads_data)

@app.route('/user_ads')
def user_ads():
    """Render the user ads list page"""
    user_ads_data = load_data(USER_ADS_FILE)
    return render_template('user_ads.html', user_ads=user_ads_data)

@app.route('/links')
def links():
    """Render the visit links page"""
    links_data = load_data(VISIT_LINKS_FILE)
    return render_template('links.html', links=links_data)

@app.route('/api/statistics')
def api_statistics():
    """API endpoint for statistics"""
    return jsonify(get_statistics())

@app.route('/add_ad', methods=['POST'])
def add_ad():
    """Add a new advertisement"""
    if request.method == 'POST':
        ad_text = request.form.get('ad_text')
        ad_points = int(request.form.get('ad_points', 10))
        
        if ad_text:
            ads = load_data(ADS_FILE)
            if isinstance(ads, dict):
                ads[ad_text] = ad_points
            elif isinstance(ads, list):
                ads.append({ad_text: ad_points})
            else:
                ads = {ad_text: ad_points}
                
            save_data(ads, ADS_FILE)
            flash('تم إضافة الإعلان بنجاح', 'success')
        else:
            flash('حدث خطأ. الرجاء التأكد من إدخال نص الإعلان', 'danger')
            
    return redirect(url_for('ads'))

@app.route('/edit_ad', methods=['POST'])
def edit_ad():
    """Edit an existing advertisement"""
    if request.method == 'POST':
        ad_index = int(request.form.get('ad_index', -1))
        ad_text = request.form.get('ad_text')
        ad_points = int(request.form.get('ad_points', 10))
        
        if ad_index >= 0 and ad_text:
            ads = load_data(ADS_FILE)
            if isinstance(ads, dict):
                old_keys = list(ads.keys())
                if 0 <= ad_index < len(old_keys):
                    old_text = old_keys[ad_index]
                    # Remove old ad
                    old_points = ads.pop(old_text)
                    # Add new ad
                    ads[ad_text] = ad_points
                    save_data(ads, ADS_FILE)
                    flash('تم تحديث الإعلان بنجاح', 'success')
                else:
                    flash('رقم الإعلان غير صحيح', 'danger')
            elif isinstance(ads, list) and 0 <= ad_index < len(ads):
                # Replace the item at the index
                ads[ad_index] = {ad_text: ad_points}
                save_data(ads, ADS_FILE)
                flash('تم تحديث الإعلان بنجاح', 'success')
            else:
                flash('حدث خطأ أثناء تحديث الإعلان', 'danger')
        else:
            flash('بيانات الإعلان غير صحيحة', 'danger')
            
    return redirect(url_for('ads'))

@app.route('/delete_ad', methods=['POST'])
def delete_ad():
    """Delete an advertisement"""
    if request.method == 'POST':
        ad_index = int(request.form.get('ad_index', -1))
        
        if ad_index >= 0:
            ads = load_data(ADS_FILE)
            if isinstance(ads, dict):
                ad_keys = list(ads.keys())
                if 0 <= ad_index < len(ad_keys):
                    del ads[ad_keys[ad_index]]
                    save_data(ads, ADS_FILE)
                    flash('تم حذف الإعلان بنجاح', 'success')
                else:
                    flash('رقم الإعلان غير صحيح', 'danger')
            elif isinstance(ads, list) and 0 <= ad_index < len(ads):
                ads.pop(ad_index)
                save_data(ads, ADS_FILE)
                flash('تم حذف الإعلان بنجاح', 'success')
            else:
                flash('حدث خطأ أثناء حذف الإعلان', 'danger')
        else:
            flash('بيانات الإعلان غير صحيحة', 'danger')
            
    return redirect(url_for('ads'))

@app.route('/add_link', methods=['POST'])
def add_link():
    """Add a new visit link"""
    if request.method == 'POST':
        link_title = request.form.get('link_title')
        link_url = request.form.get('link_url')
        link_points = int(request.form.get('link_points', 5))
        
        if link_title and link_url:
            links = load_data(VISIT_LINKS_FILE)
            links.append({
                'title': link_title,
                'url': link_url,
                'points': link_points
            })
            save_data(links, VISIT_LINKS_FILE)
            flash('تم إضافة الرابط بنجاح', 'success')
        else:
            flash('حدث خطأ. الرجاء التأكد من إدخال عنوان الرابط والرابط', 'danger')
            
    return redirect(url_for('links'))

@app.route('/edit_link', methods=['POST'])
def edit_link():
    """Edit an existing visit link"""
    if request.method == 'POST':
        link_index = int(request.form.get('link_index', -1))
        link_title = request.form.get('link_title')
        link_url = request.form.get('link_url')
        link_points = int(request.form.get('link_points', 5))
        
        if link_index >= 0 and link_title and link_url:
            links = load_data(VISIT_LINKS_FILE)
            if 0 <= link_index < len(links):
                links[link_index] = {
                    'title': link_title,
                    'url': link_url,
                    'points': link_points
                }
                save_data(links, VISIT_LINKS_FILE)
                flash('تم تحديث الرابط بنجاح', 'success')
            else:
                flash('رقم الرابط غير صحيح', 'danger')
        else:
            flash('بيانات الرابط غير صحيحة', 'danger')
            
    return redirect(url_for('links'))

@app.route('/delete_link', methods=['POST'])
def delete_link():
    """Delete a visit link"""
    if request.method == 'POST':
        link_index = int(request.form.get('link_index', -1))
        
        if link_index >= 0:
            links = load_data(VISIT_LINKS_FILE)
            if 0 <= link_index < len(links):
                links.pop(link_index)
                save_data(links, VISIT_LINKS_FILE)
                flash('تم حذف الرابط بنجاح', 'success')
            else:
                flash('رقم الرابط غير صحيح', 'danger')
        else:
            flash('بيانات الرابط غير صحيحة', 'danger')
            
    return redirect(url_for('links'))

@app.route('/toggle_user_ad', methods=['POST'])
def toggle_user_ad():
    """Activate or deactivate a user ad"""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        ad_index = int(request.form.get('ad_index', -1))
        action = request.form.get('action')
        
        if user_id and ad_index >= 0 and action in ['activate', 'deactivate']:
            user_ads = load_data(USER_ADS_FILE)
            if user_id in user_ads and 0 <= ad_index < len(user_ads[user_id]):
                # Set active status based on action
                user_ads[user_id][ad_index]['active'] = (action == 'activate')
                save_data(user_ads, USER_ADS_FILE)
                
                message = 'تم تفعيل الإعلان بنجاح' if action == 'activate' else 'تم تعطيل الإعلان بنجاح'
                flash(message, 'success')
            else:
                flash('بيانات الإعلان غير صحيحة', 'danger')
        else:
            flash('بيانات الطلب غير كاملة', 'danger')
            
    return redirect(url_for('user_ads'))

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)