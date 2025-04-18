from flask import Flask, render_template, redirect
from loginform import LoginForm, RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Домашняя страница')

# @app.route('/<word>')
# @app.route('/index/<word>')
# def index1(word):
#     return render_template('base.html', title=word)
#
#
# #@app.route('/training/<prof>')
# #def training(prof):
#     #return render_template('training.html', prof=prof)
#
# @app.route('/list_prof/<list>')
# def list_prof(list):
#     return render_template('list_prof.html', param=list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = RegisterForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/authorization', methods=['GET', 'POST'])
def authorization():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('authorization.html', title='Авторизация', form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')