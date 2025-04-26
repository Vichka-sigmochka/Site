from flask_wtf import FlaskForm
from data.users import User
from wtforms import EmailField, BooleanField
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo


class LoginForm(FlaskForm):
    email = EmailField('Почта/Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    email = EmailField('Почта/Логин', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Подтвердите пароль', validators=[
        DataRequired(), EqualTo('password')])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже занят')

class ProfileForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    age = IntegerField('Возраст')
    specialization = TextAreaField('Специализация')
    bio = TextAreaField('О себе')
    avatar = FileField('Аватарка')
    submit = SubmitField('Сохранить')

    def validate_avatar(self, field):
        if field.data:
            filename = field.data.filename.lower()
            allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
            if '.' not in filename or filename.rsplit('.', 1)[1] not in allowed_extensions:
                raise ValidationError('Разрешены только файлы с расширениями: .jpg, .jpeg, .png, .gif')