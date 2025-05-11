from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import HiddenField


class LoginForm(FlaskForm):
    email = EmailField('Почта/Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта/Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    code_word = StringField('Кодовое слово', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class FogotForm(FlaskForm):
    email = EmailField('Почта/Логин', validators=[DataRequired()])
    code_word = StringField('Кодовое слово', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired()])
    submit = SubmitField('Восстановить пароль')


class ProfileForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(max=50)])
    surname = StringField('Фамилия', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    age = IntegerField('Возраст', validators=[NumberRange(min=0)])
    specialization = StringField('Специализация', validators=[Length(max=100)])
    city = StringField('Город', validators=[Length(max=100)])
    number = StringField('Номер телефона', validators=[Length(max=20)])
    code_word = StringField('Кодовое слово', validators=[DataRequired(), Length(min=1)])
    bio = TextAreaField('О себе')
    avatar = FileField('Аватар')
    submit = SubmitField('Сохранить')


    def validate_avatar(self, field):
        if field.data:
            try:
                filename = field.data.filename.lower()
            except:
                filename = field.data
            allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
            if '.' not in filename or filename.rsplit('.', 1)[1] not in allowed_extensions:
                raise ValidationError('Разрешены только файлы с расширениями: .jpg, .jpeg, .png, .gif')
