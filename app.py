import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'connectify_ultra_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectify_final.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    bio = db.Column(db.String(150), default="Explorando o Connectify!")
    is_verified = db.Column(db.Boolean, default=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50))
    image = db.Column(db.String(500))
    text = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    author = db.Column(db.String(50))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

with app.app_context():
    db.create_all()

# --- INTERFACE (FOCO EM RESPONSIVIDADE) ---
HTML = """
<!DOCTYPE html>
<html lang="pt-br" :class="darkMode ? 'dark' : ''" x-data="{ darkMode: false, openMenu: false }">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Connectify</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script>
        tailwind.config = { darkMode: 'class' }
    </script>
    <style>
        [x-cloak] { display: none !important; }
        body { -webkit-tap-highlight-color: transparent; }
    </style>
</head>
<body class="bg-gray-50 dark:bg-gray-900 transition-colors duration-300 min-h-screen font-sans text-gray-900 dark:text-gray-100">
    
    <nav class="bg-white dark:bg-gray-800 p-3 shadow-sm sticky top-0 z-50 border-b dark:border-gray-700">
        <div class="max-w-4xl mx-auto flex justify-between items-center">
            <h1 @click="window.location.href='/'" class="text-xl md:text-2xl font-black text-indigo-600 tracking-tighter cursor-pointer">
                CONNECTIFY
            </h1>
            
            <div class="flex items-center gap-3 md:gap-5">
                <button @click="darkMode = !darkMode" class="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
                    <i :class="darkMode ? 'fa-solid fa-sun' : 'fa-solid fa-moon'"></i>
                </button>
                
                {% if session.get('user') %}
                    <div class="hidden md:flex items-center gap-3">
                        <span class="font-bold">@{{ session['user'] }}</span>
                        <a href="/logout" class="bg-red-50 dark:bg-red-900/30 text-red-500 px-3 py-1 rounded-lg text-xs font-bold uppercase">Sair</a>
                    </div>
                    <button @click="openMenu = !openMenu" class="md:hidden p-2 text-indigo-600">
                        <i class="fa-solid fa-bars-staggered text-xl"></i>
                    </button>
                {% endif %}
            </div>
        </div>

        <div x-show="openMenu" x-cloak @click.away="openMenu = false" class="md:hidden mt-2 p-4 bg-white dark:bg-gray-800 border-t dark:border-gray-700">
            <p class="font-bold mb-2 uppercase text-[10px] text-gray-400">Logado como</p>
            <p class="font-bold mb-4">@{{ session['user'] }}</p>
            <a href="/logout" class="block w-full text-center bg-red-500 text-white p-2 rounded-xl font-bold">Encerrar Sessão</a>
        </div>
    </nav>

    <div class="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-6 p-3 md:p-6">
        
        <aside class="col-span-1 md:col-span-4 space-y-4 order-2 md:order-1">
            {% if session.get('user') %}
            <div class="bg-white dark:bg-gray-800 p-5 rounded-2xl shadow-sm border dark:border-gray-700">
                <div class="flex items-center gap-3 mb-3">
                    <div class="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/50 rounded-full flex items-center justify-center text-indigo-600 font-bold">
                        {{ session['user'][0]|upper }}
                    </div>
                    <div>
                        <p class="font-bold">@{{ session['user'] }}</p>
                        <p class="text-[10px] text-gray-500 italic">{{ user_info.bio }}</p>
                    </div>
                </div>
                <form action="/update_bio" method="POST" class="mt-4">
                    <input name="new_bio" placeholder="Mudar minha bio..." class="text-xs w-full p-3 bg-gray-50 dark:bg-gray-700 border-none rounded-xl dark:text-white outline-none focus:ring-2 ring-indigo-500">
                </form>
            </div>
            {% endif %}

            <div class="bg-white dark:bg-gray-800 p-5 rounded-2xl shadow-sm border dark:border-gray-700">
                <h3 class="font-bold mb-4 text-xs uppercase tracking-widest text-gray-400">Trending Influencers</h3>
                {% for inf in influencers %}
                    <div class="flex justify-between items-center mb-3">
                        <span class="text-sm font-medium">@{{ inf[0] }}</span>
                        <span class="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 px-2 py-1 rounded-full font-bold">{{ inf[1] }} pts</span>
                    </div>
                {% endfor %}
            </div>
        </aside>

        <main class="col-span-1 md:col-span-8 space-y-6 order-1 md:order-2">
            
            {% if not session.get('user') %}
                <div class="bg-white dark:bg-gray-800 p-8 rounded-3xl shadow-xl border dark:border-gray-700">
                    <h2 class="text-2xl font-bold mb-6 text-center">Entrar no Connectify</h2>
                    <form method="POST" action="/login" class="space-y-4">
                        <input name="user" placeholder="Nome de usuário" class="w-full p-4 rounded-2xl border dark:bg-gray-700 dark:border-gray-600 outline-none focus:ring-2 ring-indigo-500" required>
                        <input name="pass" type="password" placeholder="Senha (apenas admin)" class="w-full p-4 rounded-2xl border dark:bg-gray-700 dark:border-gray-600 outline-none focus:ring-2 ring-indigo-500">
                        <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-4 rounded-2xl font-bold shadow-lg shadow-indigo-200 dark:shadow-none transition-all">Acessar Conta</button>
                    </form>
                </div>
            {% else %}
                <div class="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border dark:border-gray-700">
                    <form method="POST" action="/post">
                        <textarea name="txt" rows="3" placeholder="O que está acontecendo?" class="w-full border-none focus:ring-0 dark:bg-gray-800 dark:text-white text-lg resize-none" required></textarea>
                        <div class="flex flex-col gap-3 mt-2">
                            <input name="img" placeholder="URL da imagem (opcional)" class="w-full bg-gray-50 dark:bg-gray-700 border-none p-3 rounded-xl text-xs dark:text-white">
                            <button class="w-full md:w-auto self-end bg-indigo-600 text-white px-8 py-2 rounded-full font-bold hover:scale-105 transition-transform">Publicar</button>
                        </div>
                    </form>
                </div>

                {% for post in posts %}
                <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border dark:border-gray-700 overflow-hidden">
                    <div class="p-4 flex justify-between items-center">
                        <div class="flex items-center gap-2">
                            <span class="font-bold text-indigo-600">@{{ post.author }}</span>
                            {% if post.is_verified %}
                                <i class="fa-solid fa-circle-check text-blue-400 text-sm"></i>
                            {% endif %}
                        </div>
                        <div class="flex gap-2">
                            {% if session.get('is_admin') %}
                                <a href="/verify/{{ post.author }}" class="p-2 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg"><i class="fa-solid fa-user-check"></i></a>
                                <a href="/del/{{ post.id }}" class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"><i class="fa-solid fa-trash-can"></i></a>
                            {% endif %}
                        </div>
                    </div>
                    
                    {% if post.image %}
                        <img src="{{ post.image }}" class="w-full max-h-[500px] object-cover border-y dark:border-gray-700">
                    {% endif %}
                    
                    <div class="p-4">
                        <p class="text-gray-800 dark:text-gray-200 mb-4 whitespace-pre-wrap">{{ post.text }}</p>
                        
                        <div class="flex items-center gap-6 text-gray-500 dark:text-gray-400 text-sm mb-4">
                            <a href="/like/{{ post.id }}" class="flex items-center gap-2 hover:text-red-500 transition">
                                <i class="fa-solid fa-heart text-red-400"></i> <span class="font-bold">{{ post.likes }}</span>
                            </a>
                            <span class="flex items-center gap-2"><i class="fa-regular fa-comment"></i> {{ post.comments|length }}</span>
                            <span class="text-[10px] ml-auto">{{ post.date_posted.strftime('%H:%M - %d/%m') }}</span>
                        </div>

                        <div class="space-y-3 bg-gray-50 dark:bg-gray-700/30 p-4 rounded-2xl">
                            {% for com in post.comments %}
                                <div class="text-sm">
                                    <span class="font-bold text-indigo-500">@{{ com.author }}:</span> 
                                    <span class="dark:text-gray-300">{{ com.text }}</span>
                                </div>
                            {% endfor %}
                            <form method="POST" action="/comment/{{ post.id }}" class="mt-4 flex gap-2">
                                <input name="com_txt" placeholder="Responder..." class="flex-1 bg-white dark:bg-gray-800 border-none text-xs p-3 rounded-xl dark:text-white focus:ring-1 ring-indigo-500" required>
                                <button class="bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 p-3 rounded-xl"><i class="fa-solid fa-paper-plane"></i></button>
                            </form>
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% endif %}
        </main>
    </div>

    <footer class="text-center p-10 text-gray-400 text-[10px] uppercase tracking-widest">
        Connectify &copy; 2026 • Made for Friends
    </footer>
</body>
</html>
"""

# --- LÓGICA DO SERVIDOR ---

@app.route('/')
def home():
    posts_data = Post.query.order_by(Post.id.desc()).all()
    for p in posts_data:
        u = User.query.filter_by(username=p.author).first()
        p.is_verified = u.is_verified if u else False
    
    influencers = db.session.query(Post.author, db.func.sum(Post.likes)).group_by(Post.author).order_by(db.func.sum(Post.likes).desc()).limit(5).all()
    
    user_info = None
    if session.get('user'):
        user_info = User.query.filter_by(username=session['user']).first()
        if not user_info:
            user_info = User(username=session['user'])
            db.session.add(user_info)
            db.session.commit()

    return render_template_string(HTML, posts=posts_data, influencers=influencers, user_info=user_info)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user').strip().lower()
    password = request.form.get('pass')
    session['user'] = user
    # NOVA SENHA DEFINIDA: batima
    session['is_admin'] = (user == 'admin' and password == 'batima')
    
    if not User.query.filter_by(username=user).first():
        db.session.add(User(username=user))
        db.session.commit()
    return redirect('/')

@app.route('/post', methods=['POST'])
def post():
    if not session.get('user'): return redirect('/')
    txt = request.form.get('txt')
    new = Post(author=session['user'], image=request.form.get('img'), text=txt)
    db.session.add(new)
    db.session.commit()
    return redirect('/')

@app.route('/like/<int:id>')
def like(id):
    post = Post.query.get(id)
    if post:
        post.likes += 1
        db.session.commit()
    return redirect('/')

@app.route('/comment/<int:id>', methods=['POST'])
def comment(id):
    if not session.get('user'): return redirect('/')
    new_com = Comment(text=request.form.get('com_txt'), author=session['user'], post_id=id)
    db.session.add(new_com)
    db.session.commit()
    return redirect('/')

@app.route('/verify/<username>')
def verify(username):
    if not session.get('is_admin'): return "Negado", 403
    u = User.query.filter_by(username=username).first()
    if u:
        u.is_verified = not u.is_verified
        db.session.commit()
    return redirect('/')

@app.route('/update_bio', methods=['POST'])
def update_bio():
    if not session.get('user'): return redirect('/')
    u = User.query.filter_by(username=session['user']).first()
    if u:
        u.bio = request.form.get('new_bio')
        db.session.commit()
    return redirect('/')

@app.route('/del/<int:id>')
def delete(id):
    if session.get('is_admin'):
        db.session.delete(Post.query.get(id))
        db.session.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
