from flask_wtf import FlaskForm
from wtforms import SubmitField

class MainWindow(FlaskForm):
    submit_login = SubmitField('Войти')
    submit_registration = SubmitField('Зарегистрироваться')