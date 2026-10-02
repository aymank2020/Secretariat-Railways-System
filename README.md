# نظام إدارة المراسلات - السكك الحديدية
# Railways Secretariat Management System

نظام متكامل لإدارة المراسلات الواردة والصادرة للسكك الحديدية

## المتطلبات
- Python 3.11+
- Node.js 18+

## تشغيل الخادم (Backend)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export INITIAL_ADMIN_USERNAME=admin
export INITIAL_ADMIN_PASSWORD="choose-a-private-strong-password"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

الخادم سيعمل على: http://localhost:8000

### إعداد الدخول

يحفظ المستخدم `SECRET_KEY` نفسه عبر إعادة التشغيل. في PowerShell استخدم
`$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"`.
اضبط `INITIAL_ADMIN_PASSWORD` قويًا لتهيئة المدير الأول لقاعدة بيانات فارغة.
لا ينشئ التطبيق حسابات بكلمات مرور منشورة. التسجيل يتطلب رمز مدير صالحًا.

## تشغيل الواجهة (Frontend)

```bash
cd frontend
npm install
npm run dev
```

الواجهة ستعمل على: http://localhost:5173

## واجهة برمجة التطبيقات (API)

### المصادقة
- `POST /auth/login` - تسجيل الدخول
- `POST /auth/register` - تسجيل مستخدم جديد بواسطة المدير

### المراسلات
- `GET /documents/` - قائمة المراسلات
- `POST /documents/` - إنشاء مراسلة
- `GET /documents/{id}` - عرض مراسلة
- `PUT /documents/{id}` - تعديل مراسلة
- `DELETE /documents/{id}` - حذف مراسلة (مدير فقط)
- `GET /documents/search?q=` - بحث
- `GET /documents/{id}/history` - سجل التعديلات

### المستخدمين (مدير فقط)
- `GET /users/` - قائمة المستخدمين
- `DELETE /users/{id}` - حذف مستخدم

## التقنيات المستخدمة
- **Backend:** FastAPI + SQLite + SQLAlchemy
- **Frontend:** Vue 3 + Vite + Tailwind CSS
- **المصادقة:** JWT (python-jose) + hashlib
