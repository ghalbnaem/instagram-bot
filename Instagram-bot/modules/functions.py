# modules/functions.py

import os
import json
import random
from datetime import datetime
import uuid  # For generating unique invite codes

# File paths
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
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_users():
    """Load user data"""
    return load_data(USERS_FILE)

def save_users(users):
    """Save user data"""
    save_data(users, USERS_FILE)

def load_ads():
    """Load advertisement data"""
    return load_data(ADS_FILE)

def save_ads(ads):
    """Save advertisement data"""
    save_data(ads, ADS_FILE)

def load_visit_links():
    """Load visit links data"""
    return load_data(VISIT_LINKS_FILE)

def save_visit_links(links):
    """Save visit links data"""
    save_data(links, VISIT_LINKS_FILE)

def load_user_ads():
    """Load user ads data"""
    return load_data(USER_ADS_FILE)

def save_user_ads(user_ads):
    """Save user ads data"""
    save_data(user_ads, USER_ADS_FILE)

def load_structured_user_ads():
    """Load structured user ads data"""
    return load_data(USER_ADS_FILE)

def save_structured_user_ads(user_ads):
    """Save structured user ads data"""
    save_data(user_ads, USER_ADS_FILE)

def generate_invite_code(user_id):
    """Generate a unique invite code for a user"""
    return str(uuid.uuid4().hex[:8])

def register_user(user_id, username):
    """Register a new user or update existing user data"""
    users = load_users()
    user_str_id = str(user_id)
    
    if user_str_id not in users:
        invite_code = generate_invite_code(user_id)
        users[user_str_id] = {
            "username": username,
            "social_links": {},
            "points": 50,  # Starting points
            "registered_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "proofs": [],
            "invite_code": invite_code,
            "invited_by": None,
            "watched_ads": []  # Track which ads the user has seen
        }
        save_users(users)
        log_proof(user_id, "registration", 50, "initial_points")

def create_or_update_user(user_id, username):
    """Create a new user or update an existing one"""
    return register_user(user_id, username)

def add_social_link(user_id, platform, link):
    """Add or update a social media link for a user"""
    users = load_users()
    user_str_id = str(user_id)
    if user_str_id in users:
        if "social_links" not in users[user_str_id]:
            users[user_str_id]["social_links"] = {}
        users[user_str_id]["social_links"][platform] = link
        save_users(users)
        log_proof(user_id, f"add_social_link_{platform}", 0, "link_added")

def update_social_profile(user_id, platform, link):
    """Update social media profile link for a user"""
    return add_social_link(user_id, platform, link)

def get_user_profile(user_id):
    """Get user profile information"""
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        profile_text = f"👤 الملف الشخصي\n\n"
        profile_text += f"🔹 اسم المستخدم: @{user_data.get('username', 'غير محدد')}\n"
        profile_text += f"🔹 رقم المعرف: {user_id}\n"
        profile_text += f"💰 رصيدك الحالي: {user_data.get('points', 0)} نقطة\n"
        
        # Show invite link
        invite_code = user_data.get('invite_code')
        if invite_code:
            profile_text += f"\n🔗 رابط الدعوة الخاص بك:\nt.me/<اسم_البوت>?start={invite_code}\n"
        
        # Show social links
        if user_data.get('social_links'):
            profile_text += "\n📱 حساباتي الاجتماعية:\n"
            for platform, link in user_data['social_links'].items():
                profile_text += f"- {platform}: {link}\n"
        
        # Show stats
        total_invited = 0
        for u in users.values():
            if u.get('invited_by') == str(user_id):
                total_invited += 1
        
        profile_text += f"\n📊 إحصائيات:\n"
        profile_text += f"👥 عدد المدعوين: {total_invited}\n"
        profile_text += f"👁️ عدد الإعلانات المشاهدة: {len(user_data.get('watched_ads', []))}\n"
        
        return profile_text
    return "⚠️ لم يتم العثور على ملفك الشخصي."

def get_user_data(user_id):
    """Get all data for a specific user"""
    users = load_users()
    return users.get(str(user_id))

def log_proof(user_id, service_name, points, details=None):
    """Log a proof of transaction for a user"""
    users = load_users()
    user_str_id = str(user_id)
    if user_str_id in users:
        proof = {
            "service": service_name,
            "points": points,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "details": details
        }
        if "proofs" not in users[user_str_id]:
            users[user_str_id]["proofs"] = []
        users[user_str_id]["proofs"].append(proof)
        save_users(users)

def get_user_proofs(user_id):
    """Get all transaction proofs for a user"""
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        return user_data.get("proofs", [])
    return []

def add_points(user_id, points, service_name, details=None):
    """Add points to a user's balance"""
    users = load_users()
    user_str_id = str(user_id)
    if user_str_id in users:
        users[user_str_id]["points"] = users[user_str_id].get("points", 0) + points
        save_users(users)
        log_proof(user_id, service_name, points, details)
        return True
    return False

def deduct_points(user_id, points, service_name, details=None):
    """Deduct points from a user's balance"""
    users = load_users()
    user_str_id = str(user_id)
    if user_str_id in users and users[user_str_id].get("points", 0) >= points:
        users[user_str_id]["points"] = users[user_str_id].get("points", 0) - points
        save_users(users)
        log_proof(user_id, service_name, -points, details)
        return True
    return False

def get_random_ad():
    """Get a random advertisement for users to view"""
    ads = load_ads()
    if not ads:
        return None
    
    if isinstance(ads, dict):
        ad_items = list(ads.items())
        if ad_items:
            ad_text, points = random.choice(ad_items)
            return (ad_text, points)
    elif isinstance(ads, list):
        if ads:
            ad_item = random.choice(ads)
            for text, points in ad_item.items():
                return (text, points)
    
    return None

def get_random_visit_link():
    """Get a random link for users to visit"""
    links = load_visit_links()
    if links:
        return random.choice(links)
    return None

def get_invite_code(user_id):
    """Get the invite code for a user"""
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        invite_code = user_data.get('invite_code')
        if not invite_code:
            # Generate a new code if one doesn't exist
            invite_code = generate_invite_code(user_id)
            users[str(user_id)]['invite_code'] = invite_code
            save_users(users)
        return invite_code
    return None

def get_user_id_from_ref_code(ref_code):
    """Get user ID from a referral code"""
    users = load_users()
    for user_id, user_data in users.items():
        if user_data.get('invite_code') == ref_code:
            return int(user_id)
    return None

def has_been_invited(user_id):
    """Check if a user has already been invited"""
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        return user_data.get('invited_by') is not None
    return False

def mark_as_invited(user_id, inviter_id):
    """Mark a user as invited by another user"""
    users = load_users()
    user_str_id = str(user_id)
    if user_str_id in users:
        users[user_str_id]['invited_by'] = str(inviter_id)
        save_users(users)
        return True
    return False

def save_user_ad(user_id, ad_text, points=10):
    """Save a user's advertisement"""
    user_ads = load_user_ads()
    user_str_id = str(user_id)
    
    if user_str_id not in user_ads:
        user_ads[user_str_id] = []
    
    user_ads[user_str_id].append({
        "text": ad_text,
        "points": points,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "views": 0
    })
    
    save_user_ads(user_ads)
    return True

def save_structured_user_ad(user_id, ad_text, points=10):
    """Save a user's advertisement with structured data"""
    user_ads = load_structured_user_ads()
    user_str_id = str(user_id)
    
    if user_str_id not in user_ads:
        user_ads[user_str_id] = []
    
    user_ads[user_str_id].append({
        "text": ad_text,
        "points": points,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "views": 0,
        "active": True
    })
    
    save_structured_user_ads(user_ads)
    return True

def get_user_published_ads(user_id):
    """Get all ads published by a user"""
    user_ads = load_user_ads()
    return user_ads.get(str(user_id), [])

def get_user_published_ads_with_index(user_id):
    """Get all ads published by a user with indexes"""
    user_ads = load_structured_user_ads()
    user_str_id = str(user_id)
    
    if user_str_id in user_ads:
        ads_with_index = []
        for ad in user_ads[user_str_id]:
            ads_with_index.append((ad['text'], {
                'points': ad['points'],
                'date': ad['date'],
                'views': ad['views'],
                'active': ad.get('active', True)
            }))
        return ads_with_index
    
    return []

def get_admin_ads_with_points():
    """Get all ads added by admins with their points"""
    ads = load_ads()
    admin_ads = []
    
    if isinstance(ads, dict):
        for text, points in ads.items():
            admin_ads.append((text, points))
    elif isinstance(ads, list):
        for ad_item in ads:
            for text, points in ad_item.items():
                admin_ads.append((text, points))
    
    return admin_ads

def get_user_watched_ads(user_id):
    """Get all ads watched by a user"""
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        return user_data.get('watched_ads', [])
    return []

def update_user_watched_ads(user_id, ad_text):
    """Update a user's watched ads list"""
    users = load_users()
    user_str_id = str(user_id)
    
    if user_str_id in users:
        if 'watched_ads' not in users[user_str_id]:
            users[user_str_id]['watched_ads'] = []
        
        # Add the ad to watched list if not already there
        if ad_text not in users[user_str_id]['watched_ads']:
            users[user_str_id]['watched_ads'].append(ad_text)
            save_users(users)
            return True
    
    return False
