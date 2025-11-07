# POS Web App (Flask) - Complete Project
**وصف:** مشروع نظام مبيعات ومشتريات ومخزون يعمل كـ Web App ويعمل على الموبايل (iPhone/Android) عبر المتصفح.
**المتطلبات:** Python 3.8+, pip
**التقنيات:** Flask, SQLite, Bootstrap (CDN), JQuery (CDN)

## كيفية التشغيل محليًا
1. افتح الترمينال وادخل المجلد المشروع
   ```bash
   cd pos_webapp_complete
   ```
2. أنشئ بيئة افتراضية (اختياري لكن موصى به)
   ```bash
   python -m venv venv
   source venv/bin/activate  # على mac/linux
   venv\Scripts\activate   # على ويندوز
   ```
3. ثبّت الحزم
   ```bash
   pip install -r requirements.txt
   ```
4. شغّل التطبيق
   ```bash
   flask run
   ```
5. افتح المتصفح واذهب إلى `http://127.0.0.1:5000`

**ملاحظة:** يمكنك إضافة مستخدم جديد عن طريق تعديل قاعدة البيانات أو إضافة واجهة تسجيل.
