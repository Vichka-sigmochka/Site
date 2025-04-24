from flask import Flask, render_template, redirect, request, url_for, flash, jsonify
from mainwindow import MainWindow
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms.loginform import RegisterForm, LoginForm
from werkzeug.utils import secure_filename
from data import db_session
from data.users import User, Post, Project
import datetime
import os
from PIL import Image
#import sqlite3
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
    db_sess = db_session.create_session()
    posts = db_sess.query(Post).order_by(Post.user_id.desc()).all()
    posts_data = []
    for post in posts:
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'image': post.image,
        })
    return render_template('home.html',
                           posts=posts_data,
                           current_user=current_user,
                           title='Домашняя страница')

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

@app.route('/friends')
def friends():
    return "friends"

@app.route('/find')
def find():
    return render_template('search.html')

@app.route('/search', methods=['GET'])
def search():
    db_sess = db_session.create_session()
    data = []
    try:
        i = 1
        while True:
            user = db_sess.query(User).get(i)
            data.append((user.name, user.surname))
            i += 1
    except:
        print(data)
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify([])
        ans = [f'{s[0]} {s[1]}' for s in data if s[0].lower().startswith(query)]
        return jsonify(ans[:5])

@app.route('/projects')
def projects():
    db_sess = db_session.create_session()
    all_projects = db_sess.query(Project).order_by(Project.date_created.desc()).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    if request.method == 'POST':
        db_sess = db_session.create_session()
        try:
            if not request.form.get('title') or not request.form.get('description'):
                flash('Заполните все обязательные поля', 'danger')
                return redirect(url_for('add_project'))
            user = db_sess.query(User).get(current_user.id)
            new_project = Project(
                title=request.form['title'],
                description=request.form['description'],
                author=user
            )
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename != '' and allowed_file(image.filename):
                    filename = secure_filename(
                        f"project_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{image.filename.split('.')[-1]}")
                    try:
                        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        new_project.image = filename
                    except Exception as e:
                        flash(f'Ошибка при сохранении изображения: {str(e)}', 'warning')
            db_sess.add(new_project)
            db_sess.commit()
            flash('Проект успешно добавлен!', 'success')
            return redirect(url_for('projects'))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при сохранении проекта: {str(e)}', 'danger')
            return redirect(url_for('add_project'))
    return render_template('add_project.html')

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(project_id)
    if not project:
        os.abort(404)
    return render_template('project_detail.html', project=project)

@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(project_id)
    user = db_sess.query(User).get(current_user.id)
    if not project:
        flash('Проект не найден', 'danger')
        return redirect(url_for('projects'))
    if project.author != user:
        flash('Вы не можете редактировать этот проект', 'danger')
        return redirect(url_for('projects'))
    if request.method == 'POST':
        try:
            project.title = request.form['title']
            project.description = request.form['description']
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename != '' and allowed_file(image.filename):
                    if project.image:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], project.image))
                        except Exception as e:
                            app.logger.error(f"Error deleting old image: {e}")
                    ext = image.filename.split('.')[-1]
                    filename = f"project_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    project.image = filename
            db_sess.commit()
            flash('Проект успешно обновлен!', 'success')
            return redirect(url_for('project_detail', project_id=project.id))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при обновлении проекта: {str(e)}', 'danger')
            app.logger.error(f"Error editing project: {e}")
    return render_template('edit_project.html', project=project)

@app.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    db_sess = db_session.create_session()
    try:
        project = db_sess.query(Project).get(project_id)
        user = db_sess.query(User).get(current_user.id)
        if not project:
            flash('Проект не найден', 'danger')
            return redirect(url_for('projects'))
        if project.author != user:
            flash('Вы не можете удалить этот проект', 'danger')
            return redirect(url_for('projects'))
        if project.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], project.image))
            except Exception as e:
                app.logger.error(f"Error deleting project image: {e}")
        db_sess.delete(project)
        db_sess.commit()
        flash('Проект успешно удален!', 'success')
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении проекта: {str(e)}', 'danger')
        app.logger.error(f"Error deleting project: {e}")
    return redirect(url_for('projects'))

def main():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db_session.global_init("db/postusers.db")
    app.run()

if __name__ == '__main__':
    main()
    #app.run(port=8080, host='127.0.0.1')