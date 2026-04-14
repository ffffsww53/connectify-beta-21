import os
from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurações básicas
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELO DO BANCO DE DADOS ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50))
    image = db.Column(db.String(500))
    text = db.Column(db.Text)

# --- CORREÇÃO VITAL: CRIAÇÃO DAS TABELAS NO START ---
with app.app_context():
    db.create_all()
    print("Tabelas do Connectify criadas/verificadas com sucesso!")

# --- TEMPLATE VISUAL (HTML/CSS) ---
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connectify | Rede Social</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-white p-4 shadow-md mb-6 sticky top-0 z-50">
        <div class="max-w-2xl mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-black text-indigo-600 tracking-tighter">CONNECTIFY</h1>
            {% if session.get('user') %}
                <div class="flex items-center gap-4">
                    <span class="text-sm font-bold text-gray-700">@{{ session['user'] }}</span>
                    <a href="/logout" class="text-red-500 text-xs font-bold uppercase">Sair</a>
                </div>
            {% endif %}
        </div>
    </nav>

    <div class="max-w-xl mx-auto px-4">
        {% if not session.get('user') %}
            <div class="bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
                <h2 class="text-xl font-bold mb-6 text-center">Entrar na Rede</h2>
                <form method="POST" action="/login" class="space-y-4">
                    <input name="user" placeholder="Seu nome de usuário" class="w-full border p-3 rounded-xl outline-none focus:ring-2 ring-indigo-500" required>
                    <input name="pass" type="password" placeholder="Senha (apenas para admin)" class="w-full border p-3 rounded-xl outline-none focus:ring-2 ring-indigo-500">
                    <button class="w-full bg-indigo-600 text-white py-3 rounded-xl font-bold hover:bg-indigo-700 transition">Acessar</button>
                </form>
                <p class="text-[10px] text-gray-400 mt-4 text-center">Dica: Se entrar como 'admin' com a senha correta, você poderá moderar posts.</p>
            </div>
        {% else %}
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-200 mb-8">
                <form method="POST" action="/post">
                    <textarea name="txt" placeholder="O que você quer compartilhar?" class="w-full border-none focus:ring-0 text-lg mb-2" required></textarea>
                    <input name="img" placeholder="URL da imagem (opcional)" class="w-full bg-gray-50 border p-2 rounded-lg text-xs outline-none focus:ring-1 ring-indigo-400 mb-4">
                    <div class="flex justify-end border-t pt-3">
                        <button class="bg-indigo-600 text-white px-6 py-2 rounded-full font-bold text-sm hover:shadow-md transition">Publicar</button>
                    </div>
                </form>
            </div>

            <div class="space-y-6 pb-10">
                {% for post in posts %}
                    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                        <div class="p-4 flex justify-between items-center bg-gray-50/50 border-b">
                            <span class="font-bold text-indigo-600">@{{ post.author }}</span>
                            {% if session.get('is_admin') %}
                                <a href="/del/{{ post.id }}" class="bg-red-50 text-red-600 px-3 py-1 rounded-lg text-[10px] font-black hover:bg-red-100 transition">APAGAR POST</a>
                            {% endif %}
                        </div>
                        {% if post.image %}
                            <img src="{{ post.image }}" class="w-full max-h-96 object-cover border-b" onerror="this.style.display='none'">
                        {% endif %}
                        <div class="p-4">
                            <p class="text-gray-800 leading-relaxed">{{ post.text }}</p>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def home():
    try:
        # Busca todos os posts do mais novo para o mais antigo
        posts = Post.query.order_by(Post.id.desc()).all()
        return render_template_string(HTML, posts=posts)
    except Exception as e:
        return f"Erro crítico no banco de dados: {str(e)}"

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user').strip()
    password = request.form.get('pass')
    
    session['user'] = user
    # DEFINA SUA SENHA DE ADMIN AQUI
    if user.lower() == 'admin' and password == '12345':
        session['is_admin'] = True
    else:
        session['is_admin'] = False
        
    return redirect('/')

@app.route('/post', methods=['POST'])
def post():
    if not session.get('user'):
        return redirect('/')
    
    text = request.form.get('txt')
    image = request.form.get('img')
    
    if text:
        new_post = Post(author=session['user'], image=image, text=text)
        db.session.add(new_post)
        db.session.commit()
        
    return redirect('/')

@app.route('/del/<int:id>')
def delete(id):
    if not session.get('is_admin'):
        return "Acesso Negado", 403
        
    post_to_del = Post.query.get(id)
    if post_to_del:
        db.session.delete(post_to_del)
        db.session.commit()
        
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- INICIALIZAÇÃO PARA AMBIENTE LOCAL ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
