import os
import datetime
import secrets
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# Настройка приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 МБ макс размер файла

# Убедимся, что папка для загрузок существует
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

# Создаем аватар по умолчанию, если его нет
default_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], 'default.png')
if not os.path.exists(default_avatar_path):
    img = Image.new('RGB', (150, 150), color='grey')
    img.save(default_avatar_path)

# Инициализация БД и менеджера входа
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модели данных
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    avatar = db.Column(db.String(100), default='uploads/default.png')
    coins = db.Column(db.Integer, default=0)
    nickname_color = db.Column(db.String(20), default='#000000')
    status = db.Column(db.String(100), default='')
    joined_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Загрузчик пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Функция для сохранения загруженного изображения
def save_image(file, folder):
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(file.filename)
    file_name = random_hex + file_ext
    file_path = os.path.join(app.root_path, 'static', folder, file_name)
    
    # Оптимизируем и сохраняем изображение
    img = Image.open(file)
    if folder == 'uploads/avatars':
        output_size = (150, 150)
        img = img.resize(output_size)
    else:
        max_size = (800, 800)
        img.thumbnail(max_size)
    img.save(file_path)
    
    return file_name

# Добавляем фильтр для переноса строк
@app.template_filter('nl2br')
def nl2br(value):
    if isinstance(value, str):
        return value.replace('\n', '<br>')
    return value

# Маршруты
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        
        if not username:
            flash('Введите никнейм!', 'danger')
            return redirect(url_for('login'))
        
        # Ищем пользователя или создаем нового
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
            flash(f'Создан новый аккаунт с ником {username}!', 'success')
        
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/forum')
def forum():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('forum.html', posts=posts)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Заполните все поля!', 'danger')
            return redirect(url_for('new_post'))
        
        post = Post(title=title, content=content, author=current_user)
        
        # Обработка загрузки изображения
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}:
                image_file = save_image(file, 'uploads')
                post.image = image_file
        
        db.session.add(post)
        db.session.commit()
        flash('Ваш пост опубликован!', 'success')
        return redirect(url_for('forum'))
    
    return render_template('create_post.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('Комментарий не может быть пустым!', 'danger')
        return redirect(url_for('post', post_id=post_id))
    
    comment = Comment(content=content, author=current_user, post=post)
    db.session.add(comment)
    
    # Начисляем монетки за комментарий
    current_user.coins += 1
    db.session.commit()
    
    flash('Комментарий добавлен! Вам начислена 1 монетка.', 'success')
    return redirect(url_for('post', post_id=post_id))

@app.route('/profile/<string:username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('profile.html', user=user, posts=posts)

@app.route('/profile/customize', methods=['GET', 'POST'])
@login_required
def customize_profile():
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Смена аватара
        if action == 'change_avatar' and 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}:
                    # Создаем папку для аватаров если ее нет
                    avatar_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')
                    os.makedirs(avatar_folder, exist_ok=True)
                    
                    image_file = save_image(file, 'uploads/avatars')
                    current_user.avatar = f'uploads/avatars/{image_file}'
                    db.session.commit()
                    flash('Аватар обновлен!', 'success')
        
        # Смена цвета ника
        elif action == 'change_color':
            color = request.form.get('nickname_color')
            cost = 5  # Стоимость смены цвета
            
            if not color:
                flash('Выберите цвет!', 'danger')
            elif current_user.coins < cost:
                flash(f'Недостаточно монет! Нужно {cost}, у вас {current_user.coins}', 'danger')
            else:
                current_user.nickname_color = color
                current_user.coins -= cost
                db.session.commit()
                flash(f'Цвет ника изменен! Списано {cost} монет.', 'success')
        
        # Изменение статуса
        elif action == 'change_status':
            status = request.form.get('status')
            cost = 3  # Стоимость смены статуса
            
            if current_user.coins < cost:
                flash(f'Недостаточно монет! Нужно {cost}, у вас {current_user.coins}', 'danger')
            else:
                current_user.status = status
                current_user.coins -= cost
                db.session.commit()
                flash(f'Статус обновлен! Списано {cost} монет.', 'success')
        
        return redirect(url_for('customize_profile'))
    
    return render_template('customize.html')

# Создаем БД если ее нет
with app.app_context():
    db.create_all()

# Запускаем приложение
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)