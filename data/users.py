import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship


class User(SqlAlchemyBase, UserMixin):
    """
        User: данные о пользователе

        Методы
        -------
        set_password() :
        check_password() :
    """
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    age = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    specialization = sqlalchemy.Column(sqlalchemy.String(100), default='')
    bio = sqlalchemy.Column(sqlalchemy.Text, default='')
    city = sqlalchemy.Column(sqlalchemy.String(100), default='')
    number = sqlalchemy.Column(sqlalchemy.String(20), default='')
    code_word = sqlalchemy.Column(sqlalchemy.String(100), default='')
    avatar = sqlalchemy.Column(sqlalchemy.String(100), default='1.jpg')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    posts = relationship('Post', backref='author', lazy=True)
    projects = relationship('Project', backref='author', lazy=True)
    likes = relationship('Like', backref='user', lazy=True)
    reviews = relationship('Review', backref='author', lazy=True)
    gallery = relationship('Gallery', backref='user', lazy=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Post(SqlAlchemyBase):
    """
        Post: данные о постах пользователя

        Методы
        -------
        likes_count() :
        is_liked_by() :
    """
    __tablename__ = 'post'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    image = sqlalchemy.Column(sqlalchemy.String(100))
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    likes = relationship('Like', backref='post', lazy=True)
    favorites = relationship('Favorite', backref='post', lazy=True)

    @property
    def likes_count(self):
        return len(self.likes)

    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return any(like.user_id == user.id for like in self.likes)


class Project(SqlAlchemyBase):
    """
        Project: данные о проектах пользователя
    """
    __tablename__ = 'project'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    image = sqlalchemy.Column(sqlalchemy.String(100))
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    reviews = relationship('Review', backref='project', lazy=True)


class Like(SqlAlchemyBase):
    """
        Like: данные о лайках на посты
    """
    __tablename__ = 'like'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    post_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('post.id'), nullable=False)


class Friendship(SqlAlchemyBase):
    """
        Friendship: данные о дружеских отношениях между пользователями
    """
    __tablename__ = 'friendship'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    friend_id = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)


class Review(SqlAlchemyBase):
    """
        Review: данные об отзывах на проекты
    """
    __tablename__ = 'review'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    project_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('project.id'), nullable=False)


class Favorite(SqlAlchemyBase):
    """
        Favorite: данные о постах, которые добавлены в избранное
    """
    __tablename__ = 'favorite'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    post_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('post.id'))
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)


class Gallery(SqlAlchemyBase):
    __tablename__ = 'gallery'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    image = sqlalchemy.Column(sqlalchemy.String(100))
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
