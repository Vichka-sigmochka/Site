# Portfolio #

Сайт.

### Описание ###

- попадая на сайт, пользователь регистрируется и авторизуется.

### Технологии в проекте ###
Приложение написано на языке программирования Python c использованием библиотеки Flask.

**Класс Users** класс для создания базы данных, для хранения информации о пользователе.

**Классы Post, Project, Like** наследуются от класса Users. В классах создаются базы данных, где хранятся посты, проекты и лайки пользователя.

**Класс LoginForm, RegisterForm, ProfileForm** наследуются от FlaskForm. Классы отвечают за создание форм.

**Класс MainWindow** первое окно.

**Функция register** отвечает за регистрацию.

**Функция login** отвечает за авторизацию.

**Функция home** отвечает за основную страницу сайта.

**Функция profile_edit** отвечает за страницу, где можно редактировать данные о пользователе.

**Функция profile_view** отвечает за страницу, на которой отображены данные о пользователе.

**Функция posts** отвечает за страницу, которая отображает все посты.

**Функция add_post** отвечает за страницу, где пользователь может добавить посты.

**Функция post_detail** отвечает за страницу, где можно посмотреть детали о посте.

**Функция edit_post** отвечает за страницу, на которой можно редактировать пост.

**Функция delete_post** отвечает за удаление поста.

**Функция profile_author_post** отвечает за страницу, где можно посмотреть информацию об авторе поста.

**Функция add_friend** отвечает за добавление друзей.

**Функция search** 

**Функция projects** отвечает за проекты.

**Функция toggle_like** 

**Функция add_project** отвечает за страницу, где можно добавить проект.

**Функция project_detail** отвечает за страницу, где можно посмотреть детали о проекте.

**Функция edit_project** отвечает за страницу, на которой можно редактировать проект.

**Функция delete_project** отвечает за удаление проекта.

**Функция main** основная функция, которая запускает сайт.


### Техническое описание проекта ###
Для запуска приложения необходимо запустить файл main.py


(Чтобы установить все зависимости (Flask) 
достаточно в консоли (терминале) вызвать команду  
pip install -r requirements.txt