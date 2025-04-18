from flask import Flask, render_template, redirect
from mainwindow import MainWindow
from flask_login import LoginManager, login_user, login_required, logout_user
from forms.loginform import RegisterForm, LoginForm
from data import db_session
from data.users import User
import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/')
def title():
    return render_template('base.html',  title='Главная')

@app.route('/index', methods=['GET', 'POST'])
def index():
    form = MainWindow()
    if form.validate_on_submit():
        if form.submit_login.data:
            return redirect('/login')
        return redirect('/register')
    return render_template('index.html', title='Главная страница', form=form)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            surname=form.surname.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/index')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/home")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html', title='Домашняя страница')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

def main():
    db_session.global_init("db/user1.db")
    app.run()

if __name__ == '__main__':
    main()
    #app.run(port=8080, host='127.0.0.1')