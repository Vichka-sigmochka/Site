import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
#from datetime import datetime
from data import db_session


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    age = sqlalchemy.Column(sqlalchemy.Integer)
    specialization = sqlalchemy.Column(sqlalchemy.String(100))
    bio = sqlalchemy.Column(sqlalchemy.Text)
    avatar = sqlalchemy.Column(sqlalchemy.String(100))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    posts = relationship('Post', backref='author', lazy=True)
    projects = relationship('Project', backref='author', lazy=True)
    likes = relationship('Like', backref='user', lazy=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def is_friend(self, user):
        return self.friends.filter(Friendship.friend_id == user.id).count() > 0

class Post(SqlAlchemyBase):
    __tablename__ = 'post'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    image = sqlalchemy.Column(sqlalchemy.String(100))
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    likes = relationship('Like', backref='post', lazy=True)

    @property
    def likes_count(self):
        return len(self.likes)

    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return any(like.user_id == user.id for like in self.likes)

class Project(SqlAlchemyBase):
    __tablename__ = 'project'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    image = sqlalchemy.Column(sqlalchemy.String(100))
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

class Like(SqlAlchemyBase):
    __tablename__ = 'like'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    post_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('post.id'), nullable=False)

