# modules/keyboards.py

from telebot import types

def remove_keyboard():
    """Create a remove keyboard markup"""
    return types.ReplyKeyboardRemove()

def welcome_keyboard():
    """Create the welcome keyboard markup"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📱 إضافة رابط حساب"))
    markup.row(types.KeyboardButton("🚀 تخطي وإكمال"))
    return markup

def social_platform_keyboard():
    """Create the social platform selection keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(
        types.KeyboardButton("Telegram"),
        types.KeyboardButton("Instagram")
    )
    markup.row(
        types.KeyboardButton("Facebook"),
        types.KeyboardButton("YouTube")
    )
    markup.row(types.KeyboardButton("🚫 إلغاء"))
    return markup

def main_menu_keyboard():
    """Create the main menu keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("👤 ملفي الشخصي"),
        types.KeyboardButton("💰 جمع النقاط")
    )
    markup.row(
        types.KeyboardButton("🎁 مشاهدة إعلان"),
        types.KeyboardButton("📢 نشر إعلاني")
    )
    markup.row(
        types.KeyboardButton("📊 إعلاناتي"),
        types.KeyboardButton("📜 الإثباتات")
    )
    markup.row(types.KeyboardButton("🔗 رابط الدعوة"))
    return markup

def collect_points_keyboard():
    """Create the collect points menu keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("🎁 مشاهدة إعلان"),
        types.KeyboardButton("🔗 زيارة روابط")
    )
    markup.row(
        types.KeyboardButton("👥 دعوة أصدقاء"),
        types.KeyboardButton("📢 نشر إعلاني")
    )
    markup.row(types.KeyboardButton("العودة للقائمة الرئيسية"))
    return markup

def admin_keyboard():
    """Create the admin panel keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("➕ إضافة إعلان"),
        types.KeyboardButton("📝 تعديل إعلان")
    )
    markup.row(
        types.KeyboardButton("🗑️ حذف إعلان"),
        types.KeyboardButton("👤 معلومات مستخدم")
    )
    markup.row(
        types.KeyboardButton("📊 إحصائيات"),
        types.KeyboardButton("العودة للقائمة الرئيسية")
    )
    return markup
