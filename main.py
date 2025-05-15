from flask import Flask, render_template, redirect, request, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms.loginform import RegisterForm, LoginForm, ProfileForm, FogotForm
from werkzeug.utils import secure_filename
from data import db_session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc as sa_exc
from sqlalchemy import func
from data.users import User, Post, Project, Like, Friendship, Review, Favorite, Gallery
from mainwindow import MainWindow
import datetime
import os
import warnings


warnings.simplefilter("default")
warnings.simplefilter("ignore", category=sa_exc.LegacyAPIWarning)

app = Flask(__name__)

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

login_manager = LoginManager()
login_manager.init_app(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy()


class LengthError(Exception):
    pass


def number(s):
    """
        number : проверка на коректность номера телефона
    """
    try:
        if s[0] != '8' and (s[:2] != '+7') and s[0] != ' ':
            raise LengthError('неверный формат')
        if s.find('--') != -1 or s[-1] == '-':
            raise LengthError('неверный формат')
        cnt1 = s.count('(')
        cnt2 = s.count(')')
        if cnt1 > 1 or cnt2 > 1 or cnt1 != cnt2:
            raise LengthError('неверный формат')
        indx1 = s.find('(')
        indx2 = s.find(')')
        if indx1 > indx2:
            raise LengthError('неверный формат')
        ans = ""
        for i in range(len(s)):
            if s[i].isdigit():
                ans += s[i]
        if len(ans) != 11:
            raise LengthError('неверное количество цифр')
        if ans[0] != '8' and ans[0] != '7':
            raise LengthError('неверный формат')
        if ans[0] == '8':
            res = '+7' + ans[1:]
        else:
            res = '+' + ans
    except LengthError:
        return False
    return res


@login_manager.user_loader
def load_user(user_id):
    """
        load_user : загрузка пользователя
    """
    db_sess = db_session.create_session()
    return db_sess.query(User).get(int(user_id))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    """
        index : начальная страница
    """
    form = MainWindow()
    if form.validate_on_submit():
        if form.submit_login.data:
            return redirect('/login')
        return redirect('/register')
    return render_template('index.html', title='Главная страница', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
        register : регистрация
    """
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
            surname=form.surname.data,
            code_word=form.code_word.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/index')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        login : авторизация
    """
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
    """
        logout : выход
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/fogot_password', methods=['GET', 'POST'])
def fogot_password():
    """
        fogot_password : создание нового пароля, если пользователь забыл старый
    """
    form = FogotForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        users = db_sess.query(User).all()
        for user in users:
            if user.code_word == form.code_word.data and user.email == form.email.data:
                curr_user = db_sess.query(User).get(user.id)
                curr_user.set_password(form.new_password.data)
                db_sess.commit()
                return redirect("/index")
        return render_template('fogot_password.html',
                               message="Неправильный логин или кодовое слово",
                               form=form)
    return render_template('fogot_password.html', form=form)


@app.route('/profile_edit', methods=['GET', 'POST'])
def profile_edit():
    """
        profile_edit : редактирование профиля
    """
    db_sess = db_session.create_session()
    form = ProfileForm(obj=current_user)
    user = db_sess.query(User).get(current_user.id)
    if form.validate_on_submit():
        if form.number.data == '' or number(form.number.data) != False:
            form.populate_obj(current_user)
            user.name = form.name.data
            user.surname = form.surname.data
            user.email = form.email.data
            user.age = form.age.data
            user.city = form.city.data
            if form.number.data == '':
                user.number = form.number.data
            else:
                user.number = number(form.number.data)
            user.code_word = form.code_word.data
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
                        flash(f'Ошибка при сохранении изображения')
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = secure_filename(file.filename)
                    unique_filename = f"{timestamp}.{filename}"
                    try:
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                        user.avatar = unique_filename
                    except  Exception as e:
                        flash(f'Ошибка при сохранении изображения: {str(e)}')
            db_sess.commit()
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('profile_view'))
        else:
            return render_template('profile_edit.html', form=form,
                                   message="Неверный формат номера телефона")
    return render_template('profile_edit.html', form=form)


@app.route('/profile_view')
def profile_view():
    """
        profile_view : профиль пользователя
    """
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    return render_template('profile_view.html', user=user)


@app.route('/home', methods=['GET', 'POST'])
def home():
    """
        home : начальная страница с постами
    """
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


@app.route('/home_project', methods=['GET', 'POST'])
def home_project():
    """
        home_project : начальная страница с проектами
    """
    db_sess = db_session.create_session()
    projects = db_sess.query(Project).options(
        db.joinedload(Project.author)).order_by(Project.date_created.desc()).all()
    projects_data = []
    for project in projects:
        project_data = {
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'image': project.image,
            'date_created': project.date_created,
            'name': project.author.name if project.author else 'Неизвестный автор',
            'user_id': project.author.id if project.author else None
        }
        projects_data.append(project_data)
    return render_template('home_project.html',
                           projects=projects_data,
                           current_user=current_user,
                           title='Домашняя страница')


@app.route('/posts')
def posts():
    """
        posts : все посты пользователя
    """
    db_sess = db_session.create_session()
    all_posts = db_sess.query(Post).order_by(Post.date_created.desc()).all()
    return render_template('posts.html', posts=all_posts)


@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    """
        add_post : добавить пост
    """
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
                        new_photo = Gallery(
                            image=filename,
                            user=user
                        )
                        db_sess.add(new_photo)
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
    """
        post_detail : детали поста

        Атрибуты:
        --------
        post_id : int
            id поста
    """
    db_sess = db_session.create_session()
    post = db_sess.query(Post).get(post_id)
    if not post:
        os.abort(404)
    return render_template('post_detail.html', post=post)


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """
        edit_post : редактирование поста

        Атрибуты:
        --------
        post_id : int
            id поста
    """
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
                    ext = image.filename.split('.')[-1]
                    filename = f"post_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    new_photo = Gallery(
                        image=filename,
                        user=user
                    )
                    db_sess.add(new_photo)
                    post.image = filename
            db_sess.commit()
            flash('Пост успешно обновлен!', 'success')
            return redirect(url_for('post_detail', post_id=post.id))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при обновлении поста: {str(e)}', 'danger')
            app.logger.error(f"Ошибка при обновлении поста: {e}")
    return render_template('edit_post.html', post=post)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """
        delete_post : удаление поста

        Атрибуты:
        --------
        post_id : int
            id поста
    """
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
        db_sess.delete(post)
        db_sess.commit()
        flash('Пост успешно удален!', 'success')
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении поста: {str(e)}', 'danger')
        app.logger.error(f"Ошибка при удалении поста: {e}")
    return redirect(url_for('posts'))


@app.route('/reviews/<int:project_id>', methods=['GET', 'POST'])
def reviews(project_id):
    """
        reviews : отзывы

        Атрибуты:
        --------
        project_id : int
            id проекта
    """
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(project_id)
    all_reviews = db_sess.query(Review).filter(
        Review.project_id == project_id).order_by(Review.project_id.desc()).all()
    return render_template('reviews.html', reviews=all_reviews, project_id=project_id, project=project)


@app.route('/add_review/<int:project_id>', methods=['GET', 'POST'])
@login_required
def add_review(project_id):
    """
        add_review : добавить отзыв

        Атрибуты:
        --------
        project_id : int
            id проекта
    """
    if request.method == 'POST':
        db_sess = db_session.create_session()
        try:
            if not request.form.get('description'):
                flash('Заполните все обязательные поля', 'danger')
                return redirect(url_for('add_review'))
            user = db_sess.query(User).get(current_user.id)
            project = db_sess.query(Project).get(project_id)
            new_review = Review(
                description=request.form['description'],
                author=user,
                project=project
            )
            db_sess.add(new_review)
            db_sess.commit()
            flash('Отзыв успешно добавлен!', 'success')
            return redirect(url_for('reviews', project_id=project_id))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при сохранении отзыва: {str(e)}', 'danger')
            return redirect(url_for('add_review', project_id=project_id))
    return render_template('add_review.html', project_id=project_id)


@app.route('/review/<int:project_id>/<int:review_id>')
def review_detail(project_id, review_id):
    """
        review_detail : детали отзыва

        Атрибуты:
        --------
        project_id : int
            id проекта
        review_id : int
            id отзыва
    """
    db_sess = db_session.create_session()
    review = db_sess.query(Review).get(review_id)
    if not review:
        os.abort(404)
    return render_template('review_detail.html', project_id=project_id, review=review)


@app.route('/edit_review/<int:project_id>/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(project_id, review_id):
    """
        edit_review : редактирование отзыва

        Атрибуты:
        --------
        project_id : int
            id проекта
        review_id : int
            id отзыва
    """
    db_sess = db_session.create_session()
    review = db_sess.query(Review).get(review_id)
    user = db_sess.query(User).get(current_user.id)
    if not review:
        flash('Отзыв не найден', 'danger')
        return redirect(url_for('reviews'))
    if review.author != user:
        flash('Вы не можете редактировать этот отзыв', 'danger')
        return redirect(url_for('reviews', project_id=project_id))
    if request.method == 'POST':
        try:
            review.description = request.form['description']
            db_sess.commit()
            flash('Отзыв успешно обновлен!', 'success')
            return redirect(url_for('review_detail', project_id=project_id, review_id=review.id))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при обновлении отзыва: {str(e)}', 'danger')
            app.logger.error(f"Error editing review: {e}")
    return render_template('edit_review.html', project_id=project_id, review=review)


@app.route('/delete_review/<int:project_id>/<int:review_id>', methods=['POST'])
@login_required
def delete_review(project_id, review_id):
    """
        delete_review : удаление отзыва

        Атрибуты:
        --------
        project_id : int
            id проекта
        review_id : int
            id отзыва
    """
    db_sess = db_session.create_session()
    try:
        review = db_sess.query(Review).get(review_id)
        user = db_sess.query(User).get(current_user.id)
        if not review:
            flash('Отзыв не найден', 'danger')
            return redirect(url_for('reviews'))
        if review.author != user:
            flash('Вы не можете удалить этот отзыв', 'danger')
            return redirect(url_for('reviews'))
        db_sess.delete(review)
        db_sess.commit()
        flash('Отзыв успешно удален!', 'success')
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении отзыва: {str(e)}', 'danger')
        app.logger.error(f"Ошибка при удалении отзыва: {e}")
    return redirect(url_for('reviews', project_id=project_id))


@app.route('/friends')
def friends():
    """
        friends : друзья пользователя
    """
    db_sess = db_session.create_session()
    friend = db_sess.query(Friendship).all()
    friends = []
    for i in friend:
        if i.user_id == current_user.id:
            user = db_sess.query(User).get(i.friend_id)
            friends += [(user.name, user.surname, user.avatar, user.id)]
    db_sess.commit()
    return render_template('friends.html', friends=friends)


@app.route('/profile_author_post/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile_author_post(user_id):
    """
        profile_author_post : профиль автора поста/проекта

        Атрибуты:
        --------
        user_id : int
            id пользователя
    """
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)
    return render_template('profile_author.html', user=user)


@app.route('/find')
def find():
    """
        find : поиск
    """
    return render_template('search.html')


@app.route('/search', methods=['GET'])
def search():
    """
        search : поиск
    """
    db_sess = db_session.create_session()
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = set()
        try:
            i = 1
            while True:
                user = db_sess.query(User).get(i)
                data.add(user.name)
                data.add(user.surname)
                data.add(user.specialization)
                data.add(user.city)
                i += 1
        except:
            ans = []
            for s in data:
                if type(s) == str and s.lower().startswith(query):
                    ans.append(s)
            return jsonify(ans[:5])
    users = db_sess.query(User).filter(
        (func.lower(User.name).startswith(query)) |
        (func.lower(User.surname).startswith(query)) |
        (func.lower(User.specialization).startswith(query)) |
        (func.lower(User.city).startswith(query))
    ).all()
    return render_template('search_results.html', users=users, query=query)


@app.route('/search_results')
def search_results():
    """
        search_results : результаты поиска
    """
    db_sess = db_session.create_session()
    query = request.args.get('q', '').lower()
    users = db_sess.query(User).filter(
        (func.lower(User.name).startswith(query)) |
        (func.lower(User.surname).startswith(query)) |
        (func.lower(User.specialization).startswith(query)) |
        (func.lower(User.city).startswith(query))
    ).all()
    return render_template('search_results.html', users=users, query=query)


@app.route('/projects')
def projects():
    """
        projects : проекты пользователя
    """
    db_sess = db_session.create_session()
    all_projects = db_sess.query(Project).order_by(Project.date_created.desc()).all()
    return render_template('projects.html', projects=all_projects)


@app.route('/toggle_like/<int:post_id>', methods=['POST'])
@login_required
def toggle_like(post_id):
    """
        toggle_like : лайки на посты

        Атрибуты:
        --------
        post_id : int
            id поста
    """
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
    """
        add_project : добавить проект
    """
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
                        new_photo = Gallery(
                            image=filename,
                            user=user
                        )
                        db_sess.add(new_photo)
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
    """
        project_detail : детали проекта

        Атрибуты:
        --------
        project_id : int
            id проекта
    """
    db_sess = db_session.create_session()
    project = db_sess.query(Project).get(project_id)
    if not project:
        os.abort(404)
    return render_template('project_detail.html', project=project)


@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """
        edit_project : редактирование проекта

        Атрибуты:
        --------
        project_id : int
            id проекта
    """
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
                    ext = image.filename.split('.')[-1]
                    filename = f"project_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    project.image = filename
                    new_photo = Gallery(
                        image=filename,
                        user=user
                    )
                    db_sess.add(new_photo)
            db_sess.commit()
            flash('Проект успешно обновлен!', 'success')
            return redirect(url_for('project_detail', project_id=project.id))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при обновлении проекта: {str(e)}', 'danger')
            app.logger.error(f"Ошибка при обновлении проекта: {e}")
    return render_template('edit_project.html', project=project)


@app.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    """
        delete_project : удаление проекта

        Атрибуты:
        --------
        project_id : int
            id проекта
    """
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
        db_sess.delete(project)
        db_sess.commit()
        flash('Проект успешно удален!', 'success')
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении проекта: {str(e)}', 'danger')
        app.logger.error(f"Ошибка при удалении проекта: {e}")
    return redirect(url_for('projects'))


@app.route('/add_friend/<int:friend_id>')
@login_required
def add_friend(friend_id):
    """
        add_friend : добавление друга

        Атрибуты:
        --------
        friend_id : int
            id друга
    """
    if current_user.id == friend_id:
        flash('Вы не можете добавить себя в друзья', 'danger')
    else:
        db_sess = db_session.create_session()
        friend = db_sess.query(Friendship).all()
        friends = set()
        for i in friend:
            if i.user_id == current_user.id:
                friends.add(i.friend_id)
        if friend_id in friends:
            flash('Этот пользователь уже в ваших друзьях', 'danger')
        else:
            try:
                new_friendship = Friendship(user_id=current_user.id, friend_id=friend_id)
                db_sess.add(new_friendship)
                new_friendship = Friendship(user_id=friend_id, friend_id=current_user.id)
                db_sess.add(new_friendship)
                db_sess.commit()
                flash('Пользователь добавлен в друзья!', 'success')
            except:
                flash(f'Ошибка при добавление пользователя в друзья', 'danger')
    return redirect(url_for('home'))


@app.route('/delete_friend/<int:friend_id>')
@login_required
def delete_friend(friend_id):
    """
        delete_friend : удаление друга

        Атрибуты:
        --------
        friend_id : int
            id друга
    """
    db_sess = db_session.create_session()
    try:
        friend = db_sess.query(Friendship).all()
        friend_delete = None
        for i in friend:
            if i.user_id == current_user.id and i.friend_id == friend_id:
                friend_delete = i
        if friend_delete != None:
            db_sess.delete(friend_delete)
            flash('Друг успешно удален!', 'success')
        else:
            flash('Вы не можете удалить этого пользователя из друзей!', 'danger')
        db_sess.commit()
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении друга: {str(e)}', 'danger')
        app.logger.error(f"Ошибка при удалении друга: {e}")
    return redirect(url_for('friends'))


@app.route('/favorite', methods=['GET', 'POST'])
def favorite():
    """
        favorite : избранные посты
    """
    db_sess = db_session.create_session()
    all_favorite = db_sess.query(Favorite).all()
    posts = []
    for favorite in all_favorite:
        if favorite.user_id == current_user.id:
            posts += [favorite.post_id]
    favorite_data = []
    for i in posts:
        post = db_sess.query(Post).get(i)
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
        favorite_data.append(post_data)
    return render_template('favorite.html', posts=favorite_data)


@app.route('/add_favorite/<int:post_id>', methods=['GET', 'POST'])
@login_required
def add_favorite(post_id):
    """
        add_favorite : добавить в избранные пост

        Атрибуты:
        --------
        post_id : int
            id поста
    """
    db_sess = db_session.create_session()
    try:
        db_sess = db_session.create_session()
        favorite = db_sess.query(Favorite).all()
        favorites = set()
        for i in favorite:
            if i.user_id == current_user.id:
                favorites.add(i.post_id)
        if post_id in favorites:
            flash('Этот пост уже в ваших избранных', 'danger')
        else:
            new_favorite = Favorite(
                user_id=current_user.id,
                post_id=post_id
            )
            db_sess.add(new_favorite)
            db_sess.commit()
            flash('Пост успешно добавлен в избранные!', 'success')
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при сохранении в избранные: {str(e)}', 'danger')
    return redirect(url_for('home'))


@app.route('/delete_favorite/<int:post_id>', methods=['GET', 'POST'])
@login_required
def delete_favorite(post_id):
    """
        delete_favorite : добавить в избранные пост

        Атрибуты:
        --------
        post_id : int
            id поста
    """
    db_sess = db_session.create_session()
    try:
        favorite = db_sess.query(Favorite).all()
        favorite_delete = None
        for i in favorite:
            if i.user_id == current_user.id and i.post_id == post_id:
                favorite_delete = i
        if favorite_delete != None:
            db_sess.delete(favorite_delete)
            flash('Пост из избранных успешно удален!', 'success')
        else:
            flash('Вы не можете удалить этот пост из избранных!', 'danger')
        db_sess.commit()
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении поста из избранных: {str(e)}', 'danger')
        app.logger.error(f"Error deleting friend: {e}")
    return redirect(url_for('favorite'))


@app.route('/gallery')
def gallery():
    """
        gallery : галерея
    """
    db_sess = db_session.create_session()
    all_photo = db_sess.query(Gallery).order_by(Gallery.date_created.desc()).all()
    return render_template('gallery.html', photos=all_photo)


@app.route('/download/<string:filename>')
def download(filename):
    """
        download : загрузка фотографии из галереи

        Атрибуты:
        --------
        filename : str
            имя изображения
    """
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        flash("фотография успешно скачалась!", 'success')
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError:
        flash("Ошибка при скачивание фотографии", 404)
        return redirect(url_for('gallery'))


def main():
    """
        main : запуск сайта
    """
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db_session.global_init("db/date.db")
    app.run()


if __name__ == '__main__':
    main()
    # app.run(port=8080, host='127.0.0.1')
