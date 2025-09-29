# main.py

ADMINS = [5031018716] # استبدل هذا بمعرف تيليجرام الخاص بك
import telebot
import os
import time
import threading
from dotenv import load_dotenv
from telebot import types
from modules.keyboards import main_menu_keyboard, remove_keyboard, welcome_keyboard, collect_points_keyboard, social_platform_keyboard, admin_keyboard
from modules.functions import (
    load_users, save_users, register_user, add_social_link, get_user_profile,
    load_ads, save_ads, add_points, log_proof, create_or_update_user,
    save_user_ad, get_user_published_ads, load_user_ads, save_user_ads,
    get_admin_ads_with_points, get_user_published_ads_with_index,
    get_user_watched_ads, update_user_watched_ads, load_structured_user_ads,
    save_structured_user_ads, save_structured_user_ad, update_social_profile,
    get_user_data, load_visit_links
)


from modules.functions import (
    register_user,
    add_social_link,
    get_user_profile,
    get_random_ad,
    get_user_proofs,
    add_points,
    get_random_visit_link,
    get_invite_code,
    get_user_id_from_ref_code,
    has_been_invited,
    mark_as_invited,
    save_user_ad,
    deduct_points,
    get_admin_ads_with_points,
    get_user_published_ads,
    get_user_watched_ads,
    update_user_watched_ads,
    get_user_published_ads_with_index,
    save_structured_user_ad,
    load_structured_user_ads,
    update_social_profile,
    get_user_data # ✅ قم بإضافة هذه الدالة إلى قائمة الاستيراد
)

from modules.keyboards import (
    welcome_keyboard,
    social_platform_keyboard,
    main_menu_keyboard,
    remove_keyboard,
    collect_points_keyboard  # ✅ تم التصحيح: استيراد collect_points_keyboard
)

load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

user_social_link = {}
user_watching_ad = {}
WAIT_TIME_FOR_AD = 5
AD_POINTS = 10

def clear_ad_watching_state(user_id, chat_id, message_text=None):
    if user_id in user_watching_ad:
        del user_watching_ad[user_id]
        if message_text:
            bot.send_message(chat_id, message_text, reply_markup=main_menu_keyboard())
        return True
    return False
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        bot.send_message(message.chat.id, "🔑 مرحبًا بك في لوحة الإدارة!", reply_markup=admin_keyboard())
    else:
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحية الوصول إلى لوحة الإدارة.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username

    register_user(user_id, username)
    clear_ad_watching_state(user_id, message.chat.id, "تم إلغاء مشاهدة الإعلان.")

    # معالجة رابط الدعوة
    if message.text.startswith('/start '):
        invite_code = message.text.split()[1]
        inviter_id = get_user_id_from_ref_code(invite_code)
        if inviter_id and not has_been_invited(user_id) and user_id != inviter_id:
            mark_as_invited(user_id, inviter_id)
            # يمكنك هنا إضافة منطق لمنح نقاط للمدعو والداعي
            invitation_points = 20
            add_points(user_id, invitation_points, "invite_received", f"invited_by_{inviter_id}")
            add_points(inviter_id, invitation_points, "invite_sent", f"invited_{user_id}")
            bot.send_message(message.chat.id, f"🎉 لقد تم دعوتك بنجاح! حصلت على {invitation_points} نقطة إضافية.", reply_markup=main_menu_keyboard())
            # إرسال رسالة شكر للمدعو (اختياري)
            try:
                bot.send_message(inviter_id, f"🎉 قام @{username} بالانضمام عبر رابط الدعوة الخاص بك! حصلت على {invitation_points} نقطة إضافية.")
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Error sending invite notification: {e}")
        elif invite_code:
            if has_been_invited(user_id):
                bot.send_message(message.chat.id, "👋 أهلاً بك مجددًا! لقد انضممت بالفعل عبر رابط دعوة سابقًا.", reply_markup=main_menu_keyboard())
            elif user_id == inviter_id:
                bot.send_message(message.chat.id, "🤔 لا يمكنك دعوة نفسك.", reply_markup=main_menu_keyboard())
            else:
                bot.send_message(message.chat.id, "⚠️ رمز الدعوة غير صالح.", reply_markup=main_menu_keyboard())
        else:
            bot.send_message(
                message.chat.id,
                f"أهلاً بك {message.from_user.first_name} 👋\n\n"
                "ماذا تود أن تفعل؟",
                reply_markup=welcome_keyboard()
            )
    else:
        bot.send_message(
            message.chat.id,
            f"أهلاً بك {message.from_user.first_name} 👋\n\n"
            "ماذا تود أن تفعل؟",
            reply_markup=welcome_keyboard()
        )
# حالة إضافة إعلان (لتتبع خطوات المسؤول)
admin_adding_ad = {}

@bot.message_handler(func=lambda message: message.text == "➕ إضافة إعلان" and message.from_user.id in ADMINS)
def ask_for_new_ad_text(message):
    user_id = message.from_user.id
    admin_adding_ad[user_id] = {}
    bot.send_message(message.chat.id, "📝 أرسل نص الإعلان الجديد:")
    bot.register_next_step_handler(message, get_new_ad_points)

def get_new_ad_points(message):
    user_id = message.from_user.id
    ad_text = message.text
    admin_adding_ad[user_id]['text'] = ad_text
    bot.send_message(message.chat.id, "💰 أرسل عدد النقاط التي سيحصل عليها المستخدم مقابل مشاهدة هذا الإعلان:")
    bot.register_next_step_handler(message, save_new_ad)

def save_new_ad(message):
    user_id = message.from_user.id
    try:
        points = int(message.text)
        ad_text = admin_adding_ad[user_id]['text']
        ads = load_ads()
        if isinstance(ads, dict):
            ads[ad_text] = points # يمكنك تغيير المفتاح إذا أردت
        elif isinstance(ads, list):
            ads.append({ad_text: points}) # أو هيكلة مختلفة إذا كنت تستخدم قائمة
        else:
            ads = {ad_text: points}
        save_ads(ads)
        bot.send_message(message.chat.id, f"✅ تم إضافة الإعلان بنجاح:\n{ad_text} (+{points} نقطة).", reply_markup=admin_keyboard())
        del admin_adding_ad[user_id] # تنظيف الحالة
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ عدد النقاط يجب أن يكون رقمًا. يرجى المحاولة مرة أخرى.")
        bot.register_next_step_handler(message, save_new_ad)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء حفظ الإعلان: {e}")

user_publishing_ad = {}  # قاموس لتتبع المستخدمين الذين يقومون بنشر إعلان

user_creating_ad = {} # قاموس لتخزين بيانات الإعلان المؤقتة للمستخدم

@bot.message_handler(func=lambda message: message.text == "➕ إضافة إعلان" and message.from_user.id in ADMINS)
def handle_add_ad(message):
    bot.send_message(message.chat.id, "جاري العمل على إضافة إعلان...")
    # هنا سيتم استدعاء دالة إضافة الإعلان



@bot.message_handler(func=lambda message: message.text == "🗑️ حذف إعلان" and message.from_user.id in ADMINS)
def handle_delete_ad(message):
    bot.send_message(message.chat.id, "جاري العمل على حذف إعلان...")
    # هنا سيتم استدعاء دالة حذف الإعلان

@bot.message_handler(func=lambda message: message.text == "👤 معلومات مستخدم" and message.from_user.id in ADMINS)
def handle_user_info(message):
    bot.send_message(message.chat.id, "يرجى إدخال معرف المستخدم أو اسم المستخدم...")
    # هنا سيتم استدعاء دالة عرض معلومات المستخدم

@bot.message_handler(func=lambda message: message.text == "📊 إحصائيات" and message.from_user.id in ADMINS)
def handle_stats(message):
    bot.send_message(message.chat.id, "جاري عرض الإحصائيات...")
    # هنا سيتم استدعاء دالة عرض الإحصائيات
admin_editing_ad = {} # لتتبع حالة تعديل الإعلان

@bot.message_handler(func=lambda message: message.text == "📝 تعديل إعلان" and message.from_user.id in ADMINS)
def list_existing_ads_for_edit(message):
    user_id = message.from_user.id
    ads = load_ads()
    if not ads:
        bot.send_message(message.chat.id, "⚠️ لا يوجد إعلانات حاليًا.")
        return

    markup = types.InlineKeyboardMarkup()
    ad_list_text = "📝 اختر الإعلان الذي تود تعديله:\n\n"
    if isinstance(ads, dict):
        for index, (text, points) in enumerate(ads.items()):
            ad_list_text += f"{index + 1}. {text} (+{points} نقطة)\n"
            markup.add(types.InlineKeyboardButton(f"{index + 1}", callback_data=f"edit_ad_{index}"))
    elif isinstance(ads, list):
        for index, ad_item in enumerate(ads):
            for text, points in ad_item.items():
                ad_list_text += f"{index + 1}. {text} (+{points} نقطة)\n"
                markup.add(types.InlineKeyboardButton(f"{index + 1}", callback_data=f"edit_ad_{index}"))

    bot.send_message(message.chat.id, ad_list_text, reply_markup=markup)
    bot.register_next_step_handler(message, get_ad_index_to_edit)
def get_ad_index_to_edit(message):
    user_id = message.from_user.id
    try:
        ad_index = int(message.text) - 1 # الفهرس يبدأ من 0 في القائمة
        ads = load_ads()
        if isinstance(ads, dict):
            ad_list = list(ads.items())
        elif isinstance(ads, list):
            ad_list = []
            for item in ads:
                ad_list.extend(item.items())

        if 0 <= ad_index < len(ad_list):
            admin_editing_ad[user_id] = {'index': ad_index, 'original_ad': ad_list[ad_index]}
            bot.send_message(message.chat.id, f"✏️ أرسل النص الجديد للإعلان (اتركه كما هو للمحافظة عليه):")
            bot.register_next_step_handler(message, get_new_ad_text)
        else:
            bot.send_message(message.chat.id, "⚠️ فهرس إعلان غير صالح. يرجى المحاولة مرة أخرى.")
            list_existing_ads_for_edit(message)
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ يرجى إدخال رقم الفهرس.")
        list_existing_ads_for_edit(message)
def get_new_ad_text(message):
    user_id = message.from_user.id
    new_text = message.text
    admin_editing_ad[user_id]['new_text'] = new_text
    bot.send_message(message.chat.id, "💰 أرسل عدد النقاط الجديد للإعلان (اتركه كما هو للمحافظة عليه):")
    bot.register_next_step_handler(message, get_new_ad_points_for_edit)

def get_new_ad_points_for_edit(message):
    user_id = message.from_user.id
    new_points_str = message.text
    try:
        if new_points_str.lower() == 'كما هو':
            new_points = admin_editing_ad[user_id]['original_ad'][1] # استرداد النقاط الأصلية
        else:
            new_points = int(new_points_str)
            if new_points < 0:
                raise ValueError("يجب أن يكون عدد النقاط غير سالب.")

        admin_editing_ad[user_id]['new_points'] = new_points
        save_edited_ad(message)

    except ValueError:
        bot.send_message(message.chat.id, "⚠️ عدد النقاط يجب أن يكون رقمًا غير سالب أو 'كما هو'. يرجى المحاولة مرة أخرى.")
        bot.register_next_step_handler(message, get_new_ad_points_for_edit)

def save_edited_ad(message):
    user_id = message.from_user.id
    edited_data = admin_editing_ad[user_id]
    index_to_edit = edited_data['index']
    new_text = edited_data['new_text']
    new_points = edited_data['new_points']

    ads = load_ads()
    if isinstance(ads, dict):
        ad_list = list(ads.items())
        old_text = ad_list[index_to_edit][0]
        del ads[old_text]
        ads[new_text] = new_points
    elif isinstance(ads, list):
        # نفترض أن كل عنصر في القائمة هو قاموس {نص: نقاط}
        if index_to_edit < len(ads):
            old_item = list(ads[index_to_edit].items())[0]
            ads[index_to_edit] = {new_text: new_points}

    save_ads(ads)
    bot.send_message(message.chat.id, f"✅ تم تعديل الإعلان بنجاح:\n{new_text} (+{new_points} نقطة).", reply_markup=admin_keyboard())
    del admin_editing_ad[user_id] # تنظيف الحالة
    
@bot.message_handler(func=lambda message: message.text == "⬅️ القائمة الرئيسية" and message.from_user.id in ADMINS)
def handle_admin_back_to_main(message):
    bot.send_message(message.chat.id, "تم العودة إلى القائمة الرئيسية.", reply_markup=main_menu_keyboard())
@bot.message_handler(func=lambda message: message.text == "📢 نشر إعلاني")
def ask_for_ad_type(message):
    user_id = message.from_user.id
    user_creating_ad[user_id] = {}
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📝 إعلان تعليق فيسبوك", callback_data="ad_type_facebook_comment"))
    markup.add(types.InlineKeyboardButton("⬅️ تراجع", callback_data="cancel_publish_ad")) # ✅ إضافة زر تراجع
    bot.send_message(message.chat.id, "اختر نوع الإعلان الذي تود نشره:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_publish_ad")
def cancel_publish_ad(call):
    user_id = call.from_user.id
    if user_id in user_creating_ad:
        del user_creating_ad[user_id]
    bot.answer_callback_query(call.id, "تم إلغاء عملية نشر الإعلان.")
    bot.send_message(call.message.chat.id, "تم إلغاء عملية نشر الإعلان.", reply_markup=main_menu_keyboard())

def get_facebook_comment_details(message):
    user_id = message.from_user.id
    user_creating_ad[user_id]['facebook_link'] = message.text
    bot.send_message(message.chat.id, "✍️ أرسل النص الذي تود أن يكتبه المستخدمون كتعليق:")
    bot.register_next_step_handler(message, get_comment_text)
@bot.message_handler(func=lambda message: message.text == "⚙️ لوحة الإدارة")
def show_admin_panel_from_main_menu(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        bot.send_message(message.chat.id, "🔑 مرحبًا بك في لوحة الإدارة!", reply_markup=admin_keyboard())
    else:
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحية الوصول إلى لوحة الإدارة.")
def get_comment_text(message):
    user_id = message.from_user.id
    user_creating_ad[user_id]['comment_text'] = message.text
    markup = types.InlineKeyboardMarkup(row_width=1)
    points_options = [5, 10, 15, 20]
    for points in points_options:
        markup.add(types.InlineKeyboardButton(f"{points} نقطة لكل تعليق", callback_data=f"set_points_{points}"))
    bot.send_message(message.chat.id, "💰 حدد عدد النقاط التي ستمنحها لكل مستخدم يضيف تعليقًا:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ad_type_facebook_comment")
def handle_facebook_comment_ad_type(call):
    bot.answer_callback_query(call.id) # يمكنك إضافة نص هنا إذا أردت ظهور تنبيه
    bot.send_message(call.message.chat.id, "🔗 أرسل رابط المنشور على فيسبوك الذي تود أن يعلق عليه المستخدمون:")
    bot.register_next_step_handler(call.message, get_facebook_comment_details)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_points_"))
def save_facebook_comment_ad(call):
    user_id = call.from_user.id
    try:
        points = int(call.data.replace("set_points_", ""))
        user_creating_ad[user_id]['points'] = points
        ad_data = user_creating_ad[user_id]

        if 'facebook_link' in ad_data and 'comment_text' in ad_data and 'points' in ad_data:
            save_structured_user_ad(user_id, ad_data)
            deduct_points(user_id, 50, "publish_ad") # ✅ إزالة المعامل الرابع
            bot.answer_callback_query(call.id, "تم حفظ إعلانك!")
            bot.send_message(call.message.chat.id, "✅ تم نشر إعلانك بنجاح! سيظهر للمستخدمين في قائمة الإعلانات.", reply_markup=main_menu_keyboard())
            del user_creating_ad[user_id]
        else:
            raise ValueError("بيانات ناقصة")
    except Exception as e:
        print(f"[ERROR] saving ad: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ أثناء حفظ الإعلان.")
        bot.send_message(call.message.chat.id, "⚠️ حدث خطأ أثناء حفظ إعلانك. يرجى المحاولة مرة أخرى.", reply_markup=main_menu_keyboard())
        if user_id in user_creating_ad:
            del user_creating_ad[user_id]

user_setting_profile = {} # قاموس لتتبع المستخدمين الذين يقومون بتحديث ملفهم الشخصي

@bot.message_handler(commands=['set_profile'])
def set_profile(message):
    user_id = message.from_user.id
    user_setting_profile[user_id] = {}
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔗 رابط فيسبوك", callback_data="set_facebook_profile"))
    # يمكنك إضافة المزيد من الأزرار للمنصات الأخرى لاحقًا
    markup.add(types.InlineKeyboardButton("⬅️ تراجع", callback_data="cancel_set_profile"))
    bot.send_message(message.chat.id, "اختر المنصة التي تود إضافة أو تحديث رابط حسابك الشخصي عليها:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "set_facebook_profile")
def ask_for_facebook_profile(call):
    user_id = call.from_user.id
    bot.send_message(call.message.chat.id, "🔗 أرسل رابط صفحتك الشخصية على فيسبوك:")
    bot.register_next_step_handler(call.message, save_facebook_profile_link)

def save_facebook_profile_link(message):
    user_id = message.from_user.id
    facebook_link = message.text
    update_social_profile(user_id, "facebook", facebook_link) # دالة جديدة لتحديث الرابط
    bot.send_message(message.chat.id, f"✅ تم حفظ رابط صفحتك على فيسبوك: {facebook_link}", reply_markup=main_menu_keyboard())
    if user_id in user_setting_profile:
        del user_setting_profile[user_id]

@bot.callback_query_handler(func=lambda call: call.data == "cancel_set_profile")
def cancel_set_profile(call):
    user_id = call.from_user.id
    if user_id in user_setting_profile:
        del user_setting_profile[user_id]
    bot.answer_callback_query(call.id, "تم إلغاء عملية تحديث الملف الشخصي.")
    bot.send_message(call.message.chat.id, "تم إلغاء عملية تحديث الملف الشخصي.", reply_markup=main_menu_keyboard())


        
@bot.message_handler(func=lambda message: message.text == "📱 إضافة رابط حساب")
def ask_platform(message):
    user_id = message.from_user.id
    clear_ad_watching_state(user_id, message.chat.id)
    bot.send_message(message.chat.id, "اختر المنصة:", reply_markup=social_platform_keyboard())
    bot.register_next_step_handler(message, get_platform)

def get_platform(message):
    platform = message.text
    if platform in ["Telegram", "Instagram", "Facebook", "YouTube"]:
        user_social_link[message.chat.id] = {"platform": platform}
        bot.send_message(message.chat.id, f"أرسل رابط حسابك على {platform}:")
        bot.register_next_step_handler(message, save_social_link)
    elif platform == "🚫 إلغاء":
        bot.send_message(message.chat.id, "تم إلغاء إضافة الرابط.", reply_markup=remove_keyboard())
    else:
        bot.send_message(message.chat.id, "الرجاء اختيار منصة من القائمة.", reply_markup=social_platform_keyboard())
        bot.register_next_step_handler(message, get_platform)

def save_social_link(message):
    user_id = message.from_user.id
    link = message.text
    if user_id in user_social_link and "platform" in user_social_link[user_id]:
        platform = user_social_link[user_id]["platform"]
        add_social_link(user_id, platform, link)
        del user_social_link[user_id]
        bot.send_message(message.chat.id, f"تم حفظ رابطك على {platform} بنجاح ✅", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "حدث خطأ، حاول مرة أخرى.", reply_markup=remove_keyboard())

@bot.message_handler(func=lambda message: message.text == "🚀 تخطي وإكمال")
def skip_link(message):
    user_id = message.from_user.id
    clear_ad_watching_state(user_id, message.chat.id)
    bot.send_message(message.chat.id, "تمام! يمكنك البدء في استخدام البوت.", reply_markup=main_menu_keyboard())
@bot.message_handler(func=lambda message: message.text == "🤝 دعوة صديق")
def show_invite_link(message):
    user_id = message.from_user.id
    invite_code = get_invite_code(user_id)
    if invite_code:
        invite_link = f"https://t.me/{bot.get_me().username}?start={invite_code}"
        bot.send_message(message.chat.id, f"🔗 رابط الدعوة الخاص بك:\n{invite_link}\n\nشاركه مع أصدقائك لدعوتهم!", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "⚠️ لم يتم إنشاء رابط دعوة لك بعد.", reply_markup=main_menu_keyboard())


@bot.message_handler(func=lambda message: message.text == "👤 ملفي الشخصي")
@bot.message_handler(commands=['myprofile', 'رصيدي'])
def show_profile(message):
    user_id = message.from_user.id
    clear_ad_watching_state(user_id, message.chat.id)
    profile = get_user_profile(user_id)
    bot.send_message(message.chat.id, profile, reply_markup=main_menu_keyboard())

import threading

user_watching_ad_list = {} # لتتبع ما إذا كان المستخدم يعرض قائمة الإعلانات

@bot.message_handler(func=lambda message: message.text == "🎁 مشاهدة إعلان")
def show_ad_list(message):
    user_id = message.from_user.id
    clear_ad_watching_state(user_id, message.chat.id)
    admin_ads = get_admin_ads_with_points()
    user_ads_with_index = get_user_published_ads_with_index()
    structured_ads_data = load_structured_user_ads()
    watched_ads = get_user_watched_ads(user_id)
    filtered_user_ads = [ad_info['text'] for ad_info in user_ads_with_index if ad_info['index'] not in watched_ads]

    markup = types.InlineKeyboardMarkup()
    has_ads = False

    if admin_ads:
        markup.add(types.InlineKeyboardButton("إعلانات الإدارة:", callback_data="admin_ads_header"))
        for index, ad_info in enumerate(admin_ads):
            markup.add(types.InlineKeyboardButton(f"🎬 {ad_info['text']} (+{ad_info['points']} نقطة)", callback_data=f"watch_admin_ad_{index}"))
            has_ads = True

    if filtered_user_ads:
        markup.add(types.InlineKeyboardButton("إعلانات المستخدمين:", callback_data="user_ads_header"))
        for index, ad_text in enumerate(filtered_user_ads):
            original_index = [item['index'] for item in user_ads_with_index if item['text'] == ad_text][0]
            markup.add(types.InlineKeyboardButton(f"📢 {ad_text}", callback_data=f"watch_user_ad_{original_index}"))
            has_ads = True

    if structured_ads_data:
        markup.add(types.InlineKeyboardButton("إعلانات تفاعلية:", callback_data="structured_ads_header"))
    for publisher_id, ads in structured_ads_data.items():
        for index, ad in enumerate(ads):
            if ad['ad_type'] == "facebook_comment":
                row = []
                row.append(types.InlineKeyboardButton(f"💬 تعليق فيسبوك (+{ad['points']} نقطة)", url=ad['facebook_link']))
                row.append(types.InlineKeyboardButton("✅ طلبت نقاطي", callback_data=f"request_points_fb_{publisher_id}_{index}"))
                markup.add(*row)
                has_ads = True

    markup.add(types.InlineKeyboardButton("⬅️ تراجع", callback_data="cancel_ad_view"))

    if has_ads or markup.keyboard:
        bot.send_message(message.chat.id, "اختر إعلانًا لمشاهدته:", reply_markup=markup)
        user_watching_ad_list[user_id] = True
    else:
        bot.send_message(message.chat.id, "لا توجد إعلانات متاحة حاليًا.", reply_markup=main_menu_keyboard())

        
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('watch_admin_ad_'))
def process_watch_admin_ad(call):
    user_id = call.from_user.id
    ad_index = int(call.data.split('_')[-1])
    admin_ads = get_admin_ads_with_points()
    if 0 <= ad_index < len(admin_ads):
        ad_info = admin_ads[ad_index]
        add_points(user_id, ad_info['points'], "watch_admin_ad", f"watched: {ad_info['text'][:20]}...")
        bot.answer_callback_query(call.id, f"🎉 حصلت على {ad_info['points']} نقطة!")
        bot.send_message(call.message.chat.id, f"🎉 تهانينا! حصلت على {ad_info['points']} نقطة مقابل مشاهدة إعلان الإدارة: {ad_info['text']}", reply_markup=main_menu_keyboard())
        if user_id in user_watching_ad_list:
            del user_watching_ad_list[user_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith('watch_user_ad_'))
def process_watch_user_ad(call):
    user_id = call.from_user.id
    ad_original_index = int(call.data.split('_')[-1]) # ✅ الحصول على الفهرس الأصلي
    user_ads_with_index = get_user_published_ads_with_index()
    ad_text = None
    for ad_info in user_ads_with_index:
        if ad_info['index'] == ad_original_index:
            ad_text = ad_info['text']
            break

    if ad_text:
        watched_ads = get_user_watched_ads(user_id)
        if ad_original_index not in watched_ads:
            watched_ads.append(ad_original_index)
            update_user_watched_ads(user_id, watched_ads)
            bot.answer_callback_query(call.id, "شكراً لمشاهدة إعلان المستخدم!")
            bot.send_message(call.message.chat.id, f"👍 شكراً لك على مشاهدة إعلان المستخدم: {ad_text}", reply_markup=main_menu_keyboard())
        else:
            bot.answer_callback_query(call.id, "لقد شاهدت هذا الإعلان بالفعل.")
            bot.send_message(call.message.chat.id, "⚠️ لقد شاهدت هذا الإعلان بالفعل.", reply_markup=main_menu_keyboard())
        if user_id in user_watching_ad_list:
            del user_watching_ad_list[user_id]
    else:
        bot.answer_callback_query(call.id, "الإعلان غير موجود.")
        bot.send_message(call.message.chat.id, "⚠️ الإعلان الذي طلبته غير موجود.", reply_markup=main_menu_keyboard())
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("request_points_fb_"))
def request_facebook_comment_points(call):
    user_id = call.from_user.id
    user_info = get_user_data(user_id)
    if user_info and user_info.get('social_profiles') and user_info['social_profiles'].get('facebook'):
        parts = call.data.split("_")
        if len(parts) == 4:
            publisher_id = parts[2]
            ad_index = int(parts[3])
            structured_ads = load_structured_user_ads()
            publisher_ads = structured_ads.get(publisher_id)
            if publisher_ads and len(publisher_ads) > ad_index:
                ad = publisher_ads[ad_index]
                if ad.get('ad_type') == "facebook_comment" and ad.get('points'):
                    facebook_link = ad['facebook_link']
                    comment_text = ad['comment_text']
                    points_to_award = ad['points']
                    user_facebook_profile = user_info['social_profiles']['facebook']

                    # إرسال إشعار إلى المعلن
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"approve_fb_comment_{user_id}_{points_to_award}_{publisher_id}_{ad_index}"))
                    markup.add(types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_fb_comment_{user_id}_{publisher_id}_{ad_index}"))

                    bot.send_message(publisher_id, f"⚠️ طلب جديد لنقاط تعليق فيسبوك:\n\n"
                                                     f"المستخدم: {call.from_user.username or call.from_user.first_name}\n"
                                                     f"رابط صفحة المستخدم: {user_facebook_profile}\n"
                                                     f"رابط المنشور: {facebook_link}\n"
                                                     f"نص التعليق المطلوب: {comment_text}\n\n"
                                                     f"هل قام المستخدم بالتعليق؟", reply_markup=markup)

                    bot.answer_callback_query(call.id, "تم إرسال طلبك للمعلن للمراجعة.")
                else:
                    bot.answer_callback_query(call.id, "خطأ في بيانات الإعلان.")
            else:
                bot.answer_callback_query(call.id, "الإعلان غير موجود.")
        else:
            bot.answer_callback_query(call.id, "خطأ في بيانات الطلب.")
    else:
        bot.answer_callback_query(call.id, "⚠️ يرجى إضافة رابط صفحتك على فيسبوك أولاً باستخدام أمر /set_profile.")
        bot.send_message(call.message.chat.id, "⚠️ يرجى إضافة رابط صفحتك على فيسبوك أولاً باستخدام أمر /set_profile.", reply_markup=main_menu_keyboard())

# سنقوم بإنشاء معالجات approve_fb_comment و reject_fb_comment لاحقًا
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_fb_comment_"))
def approve_facebook_comment(call):
    parts = call.data.split("_")
    if len(parts) == 6: # ✅ تم التعديل إلى 6 أجزاء
        user_to_award_id = int(parts[3])
        points_to_award = int(parts[2])
        publisher_id = parts[4]
        ad_index = int(parts[5]) # ✅ الفهرس الآن هو الجزء السادس

        add_points(user_to_award_id, points_to_award, "facebook_comment_approved", f"approved by {call.from_user.id} for ad index {ad_index}")
        bot.answer_callback_query(call.id, f"تم منح {points_to_award} نقطة للمستخدم.")
        bot.send_message(user_to_award_id, f"🎉 تهانينا! تم منحك {points_to_award} نقطة لمشاركتك في إعلان تعليق فيسبوك.", reply_markup=main_menu_keyboard())

        # يمكنك هنا تحديث رسالة الطلب للمعلن للإشارة إلى الموافقة
        try:
            bot.edit_message_text(f"✅ تم الموافقة على طلب نقاط تعليق فيسبوك للمستخدم {user_to_award_id}.",
                                   call.message.chat.id, call.message.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"[ERROR] editing message: {e}")
    else:
        bot.answer_callback_query(call.id, "خطأ في بيانات الموافقة.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_fb_comment_"))
def reject_facebook_comment(call):
    parts = call.data.split("_")
    if len(parts) == 4:
        user_to_notify_id = int(parts[2])
        publisher_id = parts[3]
        ad_index = int(parts[4]) # ✅ الفهرس الآن هو الجزء الخامس (تم تصحيحه)

        bot.answer_callback_query(call.id, "تم رفض طلب النقاط.")
        bot.send_message(user_to_notify_id, "❌ تم رفض طلبك لنقاط إعلان تعليق فيسبوك. يرجى التواصل مع صاحب الإعلان للمزيد من التفاصيل.", reply_markup=main_menu_keyboard())

        # يمكنك هنا تحديث رسالة الطلب للمعلن للإشارة إلى الرفض
        try:
            bot.edit_message_text(f"❌ تم رفض طلب نقاط تعليق فيسبوك للمستخدم {user_to_notify_id}.",
                                   call.message.chat.id, call.message.message_id)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"[ERROR] editing message: {e}")
    else:
        bot.answer_callback_query(call.id, "خطأ في بيانات الرفض.")


@bot.callback_query_handler(func=lambda call: call.data in ['admin_ads_header', 'user_ads_header'])
def ignore_header_callback(call):
    bot.answer_callback_query(call.id) # منع ظهور تنبيه عند الضغط على الهيدر


@bot.message_handler(func=lambda message: message.text == "📝 الإثباتات")
def show_proofs(message):
    user_id = message.from_user.id
    proofs = get_user_proofs(user_id)
    if proofs:
        proofs_text = "📜 سجل الإثباتات الخاص بك:\n"
        for proof in proofs:
            action = proof.get('action', 'غير معروف') # استخدام get مع قيمة افتراضية
            points = proof.get('points', 0)
            timestamp = proof.get('timestamp', 'غير محدد')
            proofs_text += f"- {action} ({points} نقطة) في {timestamp}\n"

        # تقسيم النص إلى رسائل أصغر إذا كان طويلًا جدًا
        max_length = 4096
        if len(proofs_text) > max_length:
            parts = [proofs_text[i:i + max_length] for i in range(0, len(proofs_text), max_length)]
            for part in parts:
                bot.send_message(message.chat.id, part)
        else:
            bot.send_message(message.chat.id, proofs_text, reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "لا يوجد لديك أي إثباتات حتى الآن.", reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "💰 جمع النقاط")
def show_collect_points(message):
    bot.send_message(message.chat.id, "اختر طريقة جمع النقاط:", reply_markup=collect_points_keyboard())

@bot.message_handler(func=lambda message: message.text == "📢 نشر إعلاني")
def publish_ad(message):
    user_id = message.from_user.id
    clear_ad_watching_state(user_id, message.chat.id)
    # هنا راح يكون منطق السماح للمستخدمين بنشر إعلاناتهم مقابل نقاط
    bot.send_message(message.chat.id, "سيتم إضافة ميزة نشر الإعلانات قريبًا...", reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "🎁 زيارة رابط")
def visit_link_reward(message):
    user_id = message.from_user.id
    link_info = get_random_visit_link()
    if link_info:
        link_id, link_data = link_info
        url = link_data['url']
        points = link_data['points']
        markup = types.InlineKeyboardMarkup(row_width=1)
        visit_button = types.InlineKeyboardButton("➡️ اضغط لزيارة الرابط", url=url)
        markup.add(visit_button)
        bot.send_message(message.chat.id, f"اضغط على الرابط التالي لربح {points} نقطة:", reply_markup=markup)
        # يمكنك هنا إضافة منطق لتتبع ما إذا قام المستخدم بزيارة الرابط بالفعل إذا كنت تريد نظامًا أكثر تعقيدًا
        add_points(user_id, points, "visit_link", f"visited_{link_id}")
        bot.send_message(message.chat.id, f"🎉 تم إضافة {points} نقطة إلى رصيدك!", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "لا توجد روابط متاحة حاليًا.", reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == "⬅️ رجوع للقائمة الرئيسية")
def go_back_to_main_menu(message):
    bot.send_message(message.chat.id, "تم الرجوع إلى القائمة الرئيسية.", reply_markup=main_menu_keyboard())


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # يمكنك إضافة معالجات أخرى هنا للأوامر أو النصوص غير المعرفة
    bot.reply_to(message, "لم أفهم ما تقصده.")

if __name__ == '__main__':
    bot.infinity_polling()