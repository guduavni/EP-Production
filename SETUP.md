# הוראות התקנה והרצה - EP Production

## דרישות מערכת
- Python 3.6 ומעלה
- MongoDB (גרסה 4.4 ומעלה מומלצת)

## התקנת MongoDB
### למשתמשי Mac (עם Homebrew):
```bash
# התקנת MongoDB
brew tap mongodb/brew
brew install mongodb-community

# הפעלת שרת MongoDB
brew services start mongodb-community
```

### למשתמשי Linux (אובונטו/דביאן):
```bash
# ייבוא המפתח הציבורי של MongoDB
sudo apt-get install gnupg
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -

# יצירת קובץ רשימת מקורות
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list

# עדכון והתקנת MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# הפעלת שרת MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

## התקנת האפליקציה
```bash
# מעבר לתיקיית הפרויקט
cd /path/to/EP-Production

# יצירת סביבה וירטואלית
python3 -m venv venv

# הפעלת הסביבה הוירטואלית
# ב-Mac/Linux:
source venv/bin/activate
# ב-Windows:
# venv\Scripts\activate

# התקת התלויות
pip install -r requirements_working.txt
```

## הרצת השרת
```bash
# הפעלת שרת הפיתוח
python3 app.py
```

לאחר ההרצה, האפליקציה תהיה זמינה בכתובת: http://127.0.0.1:5002/

## עצירת השרת
לחץ `Ctrl+C` בטרמינל שבו רץ השרת.

## שחזור מסד נתונים (אם נדרש)
```bash
# יצירת גיבוי
mongodump --db your_database_name --out /path/to/backup

# שחזור מגיבוי
mongorestore --db your_database_name /path/to/backup/your_database_name
```

## פתרון בעיות נפוצות
- **שגיאת חיבור ל-MongoDB**: ודא ש-MongoDB פועל (`brew services list` ב-Mac או `sudo systemctl status mongod` ב-Linux)
- **שגיאות תלויות**: מחק את התיקייה `venv` והתקן מחדש את החבילות
- **שגיאות הרשאות**: ודא שיש לך הרשאות כתיבה לתיקיית הפרויקט

## מידע נוסף
- סביבת פיתוח: Debug mode פעיל (טעינה אוטומטית של שינויים, הודעות שגיאה מפורטות)
- פורט ברירת מחדל: 5002
- קובץ הגדרות: `.env` (ניתן להעתיק מ-`.env.example` ולהתאים אישית)
