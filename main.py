from flask import Flask, render_template, redirect, request, url_for, flash, jsonify
from mainwindow import MainWindow
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms.loginform import RegisterForm, LoginForm, ProfileForm
from werkzeug.utils import secure_filename
from data import db_session
from data.users import User, Post, Project, Like, Friendship
import datetime
import os
import warnings
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc as sa_exc
from sqlalchemy import func
warnings.simplefilter("default")
warnings.simplefilter("ignore", category=sa_exc.LegacyAPIWarning)

app = Flask(__name__)

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

login_manager = LoginManager()
login_manager.init_app(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(int(user_id))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            if not user.avatar:
                user.avatar = '1.jpg'
                db_sess.commit()
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


@app.route('/profile_edit', methods=['GET', 'POST'])
def profile_edit():
    db_sess = db_session.create_session()
    form = ProfileForm(obj=current_user)
    user = db_sess.query(User).get(current_user.id)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        user.name = form.name.data
        user.surname = form.surname.data
        user.email = form.email.data
        user.age = form.age.data
        user.specialization = form.specialization.data
        user.bio = form.bio.data
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    if user.avatar and user.avatar != '1.jpg':
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], user.avatar)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                except:
                    flash(f'Ошибка при сохранение файла')
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = secure_filename(file.filename)
                unique_filename = f"{timestamp}.{filename}"
                try:
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    user.avatar = unique_filename
                except  Exception as e:
                    flash(f'Ошибка при сохранении изображения: {str(e)}', 'warning')
        db_sess.commit()
        flash('Профиль успешно обновлен!', 'success')
        return redirect(url_for('profile_view'))

    return render_template('profile_edit.html', form=form)


@app.route('/profile_view')
def profile_view():
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    return render_template('profile_view.html', user=user)


@app.route('/home', methods=['GET', 'POST'])
def home():
    db_sess = db_session.create_session()
    posts = db_sess.query(Post).options(
        db.joinedload(Post.author),
        db.joinedload(Post.likes)
    ).order_by(Post.date_created.desc()).all()
    posts_data = []
    for post in posts:
        post_data = {
            'id': post.id,
            'title': post.title,
            'description': post.description,
            'image': post.image,
            'date_created': post.date_created,
            'name': post.author.name if post.author else 'Неизвестный автор',
            'user_id': post.author.id if post.author else None,
            'likes': [like.user_id for like in post.likes],
            'is_liked': False
        }
        if current_user.is_authenticated:
            post_data['is_liked'] = current_user.id in post_data['likes']
        posts_data.append(post_data)
    return render_template('home.html',
                           posts=posts_data,
                           current_user=current_user,
                           title='Домашняя страница')


@app.route('/posts')
def posts():
    db_sess = db_session.create_session()
    all_posts = db_sess.query(Post).order_by(Post.date_created.desc()).all()
    return render_template('posts.html', posts=all_posts)


@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        db_sess = db_session.create_session()
        try:
            if not request.form.get('title') or not request.form.get('description'):
                flash('Заполните все обязательные поля', 'danger')
                return redirect(url_for('add_post'))
            user = db_sess.query(User).get(current_user.id)
            new_post = Post(
                title=request.form['title'],
                description=request.form['description'],
                author=user
            )
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename != '' and allowed_file(image.filename):
                    filename = secure_filename(
                        f"post_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{image.filename.split('.')[-1]}")
                    try:
                        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        new_post.image = filename
                    except Exception as e:
                        flash(f'Ошибка при сохранении изображения: {str(e)}', 'warning')
            db_sess.add(new_post)
            db_sess.commit()
            flash('Пост успешно добавлен!', 'success')
            return redirect(url_for('posts'))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при сохранении поста: {str(e)}', 'danger')
            return redirect(url_for('add_post'))
    return render_template('add_post.html')


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).get(post_id)
    if not post:
        os.abort(404)
    return render_template('post_detail.html', post=post)


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).get(post_id)
    user = db_sess.query(User).get(current_user.id)
    if not post:
        flash('Пост не найден', 'danger')
        return redirect(url_for('posts'))
    if post.author != user:
        flash('Вы не можете редактировать этот пост', 'danger')
        return redirect(url_for('posts'))
    if request.method == 'POST':
        try:
            post.title = request.form['title']
            post.description = request.form['description']
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename != '' and allowed_file(image.filename):
                    if post.image:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.image))
                        except Exception as e:
                            app.logger.error(f"Error deleting old image: {e}")
                    ext = image.filename.split('.')[-1]
                    filename = f"post_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    post.image = filename
            db_sess.commit()
            flash('Пост успешно обновлен!', 'success')
            return redirect(url_for('post_detail', post_id=post.id))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при обновлении поста: {str(e)}', 'danger')
            app.logger.error(f"Error editing post: {e}")
    return render_template('edit_post.html', post=post)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    db_sess = db_session.create_session()
    try:
        post = db_sess.query(Post).get(post_id)
        user = db_sess.query(User).get(current_user.id)
        if not post:
            flash('Пост не найден', 'danger')
            return redirect(url_for('posts'))
        if post.author != user:
            flash('Вы не можете удалить этот пост', 'danger')
            return redirect(url_for('posts'))
        if post.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.image))
            except Exception as e:
                app.logger.error(f"Error deleting post image: {e}")
        db_sess.delete(post)
        db_sess.commit()
        flash('Пост успешно удален!', 'success')
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении поста: {str(e)}', 'danger')
        app.logger.error(f"Error deleting post: {e}")
    return redirect(url_for('posts'))


@app.route('/friends')
def friends():
    db_sess = db_session.create_session()
    friend = db_sess.query(Friendship).all()
    friends = []
    for i in friend:
        if i.user_id == current_user.id:
            user = db_sess.query(User).get(i.friend_id)
            friends += [user.name]
        elif i.friend_id == current_user.id:
            user = db_sess.query(User).get(i.user_id)
            friends += [user.name]
    db_sess.commit()
    return render_template('friends.html', friends=friends)


@app.route('/profile_author_post/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile_author_post(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    return render_template('profile_author.html', user=user)


@app.route('/find')
def find():
    return render_template('search.html')


@app.route('/search', methods=['GET'])
def search():
    db_sess = db_session.create_session()
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = []
        try:
            i = 1
            while True:
                user = db_sess.query(User).get(i)
                data.append((user.name, user.surname))
                data.append((user.specialization))
                data.append(user.town)
                i += 1
        except:
            ans = []
            for s in data:
                if type(s) == str and s.lower().startswith(query):
                    ans.append(s)
                if type(s) == tuple and s[0].lower().startswith(query):
                    ans.append(f'{s[0]} {s[1]}')
            return jsonify(ans[:5])
    users = db_sess.query(User).filter(
        (func.lower(User.name).startswith(query)) |
        (func.lower(User.surname).startswith(query)) |
        (func.lower(User.specialization).startswith(query)) |
        (func.lower(User.town).startswith(query))
    ).all()
    return render_template('search_results.html', users=users, query=query)


@app.route('/search_results')
def search_results():
    db_sess = db_session.create_session()
    query = request.args.get('q', '').lower()
    users = db_sess.query(User).filter(
        (func.lower(User.name).startswith(query)) |
        (func.lower(User.surname).startswith(query)) |
        (func.lower(User.specialization).startswith(query)) |
        (func.lower(User.town).startswith(query))
    ).all()
    return render_template('search_results.html', users=users, query=query)


@app.route('/projects')
def projects():
    db_sess = db_session.create_session()
    all_projects = db_sess.query(Project).order_by(Project.date_created.desc()).all()
    return render_template('projects.html', projects=all_projects)


@app.route('/toggle_like/<int:post_id>', methods=['POST'])
@login_required
def toggle_like(post_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).get(post_id)
    if not post:
        os.abort(404)
    like = db_sess.query(Like).filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()
    if like:
        db_sess.delete(like)
        action = 'unliked'
    else:
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db_sess.add(new_like)
        action = 'liked'
    db_sess.commit()
    likes_count = db_sess.query(Like).filter_by(post_id=post_id).count()
    return jsonify({
        'status': 'success',
        'action': action,
        'likes_count': likes_count,
        'post_id': post_id
    })


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


@app.route('/add_friend/<int:friend_id>')
@login_required
def add_friend(friend_id):
    if current_user.id == friend_id:
        flash('Вы не можете добавить себя в друзья', 'danger')
    else:
        db_sess = db_session.create_session()
        friend = db_sess.query(Friendship).all()
        friends = set()
        for i in friend:
            if i.user_id == current_user.id:
                friends.add(i.friend_id)
            elif i.friend_id == current_user.id:
                friends.add(i.user_id)
        if friend_id in friends:
            flash('Этот пользователь уже в ваших друзьях', 'danger')
        else:
            try:
                new_friendship = Friendship(user_id=current_user.id, friend_id=friend_id)
                db_sess.add(new_friendship)
                db_sess.commit()
                flash('Пользователь добавлен в друзья!', 'success')
            except:
                flash(f'Ошибка при добавление пользователя в друзья', 'danger')
    return redirect(url_for('home'))


@app.route('/delete_friend')
@login_required
def delete_friend():
    return 'delete'


def main():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db_session.global_init("db/new2.db")
    app.run()


if __name__ == '__main__':
    main()
    # app.run(port=8080, host='127.0.0.1')
