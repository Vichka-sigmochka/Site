from flask import Flask, render_template, redirect, request, url_for, flash
from mainwindow import MainWindow
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms.loginform import RegisterForm, LoginForm
from werkzeug.utils import secure_filename
from data import db_session
from data.users import User, Post
import datetime
import os
from PIL import Image
#from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

login_manager = LoginManager()
login_manager.init_app(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_size=(800, 800)):
    img = Image.open(image_path)
    img.thumbnail(max_size)
    img.save(image_path)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = MainWindow()
    if form.validate_on_submit():
        if form.submit_login.data:
            return redirect('/login')
        return redirect('/register')
    return render_template('index.html', title='Главная страница', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/lk')
@login_required
def dashboard():
    return render_template('lk.html', username=current_user.name)


@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html', title='Домашняя страница')

@app.route('/about')
def about():
    db_sess = db_session.create_session()
    posts = db_sess.query(Post).order_by(Post.id.desc()).all()
    return render_template('about.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        db_sess = db_session.create_session()
        try:
            title = request.form['title']
            content = request.form['content']
            image = request.files['image']
            new_post = Post(
                title=title,
                content=content,
                user_id=current_user.id
            )
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                resize_image(image_path)
                new_post.image = filename

            db_sess.add(new_post)
            db_sess.commit()

            flash('Пост успешно создан!')
            return redirect(url_for('about'))

        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при создании поста: {str(e)}')
            app.logger.error(f'Error creating post: {str(e)}')

    return render_template('post.html')

@app.route('/delete/<int:post_id>')
@login_required
def delete(post_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).get(post_id)
    if not post:
        os.abort(404)

    if post.author != current_user:
        flash('Вы не можете удалить этот пост')
        return redirect(url_for('about'))

    try:
        if post.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.image))
            except:
                pass

        db_sess.delete(post)
        db_sess.commit()
        flash('Пост успешно удален')
    except:
        db_sess.rollback()
        flash('Ошибка при удалении поста')

    return redirect(url_for('about'))

@app.route('/projects')
def projects():
    return "Мои проекты"


def main():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db_session.global_init("db/postusers.db")
    app.run()

if __name__ == '__main__':
    main()
    #app.run(port=8080, host='127.0.0.1')