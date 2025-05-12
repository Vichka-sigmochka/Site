from flask_wtf import FlaskForm
from wtforms import SubmitField

class MainWindow(FlaskForm):
    """
        MainWindow: начальная(главная) страница
    """
    submit_login = SubmitField('Войти')
    submit_registration = SubmitField('Зарегистрироваться')
