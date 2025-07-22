"""
Test email functionality
"""
import os
from flask import Blueprint, current_app
from ..services import email_service

# Create a blueprint for test routes
test_bp = Blueprint('test', __name__)

@test_bp.route('/test-email')
def test_email():
    """Test email sending functionality"""
    try:
        # Send a test email
        email_service.send_email(
            subject="בדיקת מערכת - EP Simulator",
            recipients=["recipient@example.com"],  # Change this to your email
            template='welcome',
            user={
                "full_name": "משתמש בדיקה",
                "email": "test@example.com"
            }
        )
        return """
        <h1>בדיקת אימייל</h1>
        <p>אימייל נשלח בהצלחה!</p>
        <p>אם לא קיבלת את האימייל, בדוק את תיבת הספאם או את לוגי השרת.</p>
        <a href="/">חזור לדף הבית</a>
        """
    except Exception as e:
        current_app.logger.error(f"שגיאה בשליחת אימייל: {str(e)}")
        return f"""
        <h1>שגיאה בשליחת אימייל</h1>
        <p>התרחשה שגיאה: {str(e)}</p>
        <p>אנא בדוק את לוגי השרת לפרטים נוספים.</p>
        <a href="/">חזור לדף הבית</a>
        """

@test_bp.route('/test-trainee-email')
def test_trainee_email():
    """Test trainee registration email"""
    try:
        # Mock trainee data
        class MockTrainee:
            full_name = "חניך בדיקה"
            id_number = "123456789"
            phone = "050-1234567"
            email = "trainee@example.com"  # Change this to your email
            birth_date = "01/01/1990"
            
            def __getitem__(self, key):
                return getattr(self, key, None)
        
        # Send trainee registration email
        email_service.send_trainee_registered_email(MockTrainee())
        
        return """
        <h1>בדיקת אימייל הרשמת חניך</h1>
        <p>אימייל הרשמת חניך נשלח בהצלחה!</p>
        <p>אם לא קיבלת את האימייל, בדוק את תיבת הספאם או את לוגי השרת.</p>
        <a href="/">חזור לדף הבית</a>
        """
    except Exception as e:
        current_app.logger.error(f"שגיאה בשליחת אימייל הרשמת חניך: {str(e)}")
        return f"""
        <h1>שגיאה בשליחת אימייל הרשמת חניך</h1>
        <p>התרחשה שגיאה: {str(e)}</p>
        <p>אנא בדוק את לוגי השרת לפרטים נוספים.</p>
        <a href="/">חזור לדף הבית</a>
        """
