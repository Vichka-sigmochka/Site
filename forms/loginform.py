from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, IntegerField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from wtforms.validators import DataRequired

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
    submit = SubmitField('Зарегистрироваться')

class ProfileForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    age = IntegerField('Возраст')
    specialization = StringField('Специализация')
    bio = TextAreaField('О себе')
    avatar = FileField('Аватар')
    submit = SubmitField('Сохранить')

    def validate_avatar(self, field):
        if field.data:
            filename = field.data.filename.lower()
            allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
            if '.' not in filename or filename.rsplit('.', 1)[1] not in allowed_extensions:
                raise ValidationError('Разрешены только файлы с расширениями: .jpg, .jpeg, .png, .gif')