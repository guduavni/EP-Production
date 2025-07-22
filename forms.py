from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], 
                       render_kw={"placeholder": "Enter your email"})
    password = PasswordField('Password', validators=[DataRequired()],
                           render_kw={"placeholder": "Enter your password"})
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
    class Meta:
        csrf = True
        csrf_secret = 'your-secret-key-here'  # Should match WTF_CSRF_SECRET_KEY in app config
