from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired

class MainWindow(FlaskForm):
    submit_login = SubmitField('Войти')
    submit_registration = SubmitField('Зарегистрироваться')