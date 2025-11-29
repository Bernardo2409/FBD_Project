import os
import secrets
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, jsonify, session, url_for

from persistence.equipa import adicionar_jogador_equipa, criar_equipa, obter_equipa_por_utilizador, obter_jogadores_equipa, remover_jogador_equipa, verificar_limites_equipa
from persistence.leagues import (
    abandonar_liga,
    criar_liga,
    criar_liga_publica,
    juntar_liga,
    juntar_liga_automatico,
    obter_liga_por_id,
    obter_ligas_por_utilizador,
    obter_participantes_liga,
    obter_tipos_liga,
    obter_liga_pelo_pais,
    obter_ligas_publicas_para_utilizador,
    obter_liga_id_por_codigo,
)
from persistence.players import list_all, list_paginated, read
from persistence.clubs import list_all_clubs, list_paginated_clubs, read_club
from persistence.users import create_user, login_user, get_users, get_user_by_id
from persistence.countries import get_pais


import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'chave-temporaria-para-desenvolvimento' 


@app.route("/", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_submit():
    email = request.form.get("email")
    password = request.form.get("password")

    user = login_user(email, password)

    if user:
        session['user_id'] = user["id"]
        session['user_name'] = user["first"]
        return redirect("/index")

    return render_template("login.html", error="Email ou palavra-passe incorretos")


@app.route("/signup", methods=["GET"])
def signup_page():
    pais = get_pais()  # Obtém os países com suas imagens da tabela Pais
    return render_template("signup.html", pais=pais)


@app.route("/signup", methods=["POST"])
def signup_submit():
    first = request.form.get("first")
    last = request.form.get("last")
    email = request.form.get("email")
    password = request.form.get("password")
    country = request.form.get("country")
    nationality = request.form.get("nationality")
    birthdate = request.form.get("birthdate")

    user_id = create_user(first, last, email, password, country, nationality, birthdate)

    # 1) Liga Mundial → se não existir é criada, depois utilizador é adicionado
    liga_mundial = obter_liga_pelo_pais("Mundial")
    if not liga_mundial:
        liga_id = criar_liga_publica("Mundial")
        liga_mundial = obter_liga_por_id(liga_id)
    juntar_liga_automatico(user_id, liga_mundial)

    # 2) Liga do país → automática
    liga_pais = obter_liga_pelo_pais(country)
    if not liga_pais:
        liga_id = criar_liga_publica(country)
        liga_pais = obter_liga_por_id(liga_id)
    juntar_liga_automatico(user_id, liga_pais)

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/index")
def index():
    user_has_team = False
    if 'user_id' in session:
        user_id = session['user_id']
        equipa_user = obter_equipa_por_utilizador(user_id)
        user_has_team = equipa_user is not None
        return render_template("index.html", user_has_team=user_has_team)
    else:
        return redirect("/")


@app.route("/players")
def players_list():
    if 'user_id' not in session:
        return redirect("/")
    page = int(request.args.get("page", 1))
    per_page = 10

    jogadores, total = list_paginated(page, per_page)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "players.html",
        jogadores=jogadores,
        page=page,
        total_pages=total_pages
    )


@app.route("/players/<j_id>")
def player_details(j_id):
    jogador = read(j_id)

    if jogador:
        return render_template("player_details.html", jogador=jogador)
    else:
        return "Jogador não encontrado", 404


@app.route("/clubs")
def clubs_list():
    if 'user_id' not in session:
        return redirect("/")

    page = int(request.args.get("page", 1))
    per_page = 10

    clubes, total = list_paginated_clubs(page, per_page)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "clubs.html",
        clubes=clubes,
        page=page,
        total_pages=total_pages
    )


@app.route("/clubs/<c_id>")
def club_details(c_id):
    clube = read_club(c_id)

    if clube:
        return render_template("club_details.html", clube=clube)
    else:
        return "Clube não encontrado", 404


@app.route("/equipa")
def equipa():
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']

    equipa_user = obter_equipa_por_utilizador(user_id)

    if not equipa_user:
        return redirect("/criar-equipa")

    jogadores_equipa = obter_jogadores_equipa(equipa_user.id)

    guarda_redes = [j for j in jogadores_equipa if j['posicao'] == "Goalkeeper"]
    defesas = [j for j in jogadores_equipa if j['posicao'] == "Defender"]
    medios = [j for j in jogadores_equipa if j['posicao'] == "Midfielder"]
    avancados = [j for j in jogadores_equipa if j['posicao'] == "Forward"]

    todos_jogadores = list_all()
    todos_avancados = [j for j in todos_jogadores if j.posicao == "Forward"]
    todos_medios = [j for j in todos_jogadores if j.posicao == "Midfielder"]
    todos_defesas = [j for j in todos_jogadores if j.posicao == "Defender"]
    todos_gr = [j for j in todos_jogadores if j.posicao == "Goalkeeper"]

    return render_template("equipa.html", 
                         equipa={
                             'gr': guarda_redes,
                             'defesas': defesas,
                             'medios': medios,
                             'avancados': avancados,
                             'info': equipa_user
                         },
                         todos_jogadores={
                             'Goalkeeper': todos_gr,
                             'Defender': todos_defesas,
                             'Midfielder': todos_medios,
                             'Forward': todos_avancados
                         })


@app.route("/criar-equipa", methods=['GET', 'POST'])
def criar_equipa_route():
    if 'user_id' not in session:
        return redirect("/")

    if request.method == 'POST':
        nome_equipa = request.form.get('nome_equipa')
        user_id = session['user_id']

        if nome_equipa:
            equipa_id = criar_equipa(nome_equipa, user_id)
            return redirect("/equipa")

    return render_template("criar_equipa.html")


@app.route("/equipa/adicionar/<posicao>/<jogador_id>")
def adicionar_jogador_equipa_route(posicao, jogador_id):
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)

    if equipa_user:
        try:
            limites = verificar_limites_equipa(equipa_user.id)

            if posicao == 'gr' and not limites['pode_adicionar_gr']:
                session['error'] = "Já tens 2 guarda-redes! Remove um primeiro."
            elif posicao == 'defesas' and not limites['pode_adicionar_defesa']:
                session['error'] = "Já tens 5 defesas! Remove um primeiro."
            elif posicao == 'medios' and not limites['pode_adicionar_medio']:
                session['error'] = "Já tens 5 médios! Remove um primeiro."
            elif posicao == 'avancados' and not limites['pode_adicionar_avancado']:
                session['error'] = "Já tens 3 avançados! Remove um primeiro."
            else:
                adicionar_jogador_equipa(equipa_user.id, jogador_id)

        except Exception as e:
            session['error'] = str(e)

    return redirect("/equipa")


@app.route("/equipa/remover/<jogador_id>")
def remover_jogador_equipa_route(jogador_id):
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)

    if equipa_user:
        try:
            remover_jogador_equipa(equipa_user.id, jogador_id)
            session['message'] = "Jogador removido com sucesso!"
        except Exception as e:
            session['error'] = f"Erro ao remover jogador: {str(e)}"

    return redirect("/equipa")


@app.route("/ligas")
def ligas_list():
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']
    minhas_ligas = obter_ligas_por_utilizador(user_id)
    # obter país do utilizador (se disponível) para filtrar ligas públicas
    user = get_user_by_id(user_id)
    user_country = None
    if user:
        user_country = user.get('pais') or user.get('country')

    ligas_publicas = obter_ligas_publicas_para_utilizador(user_country, user_id)

    return render_template("ligas.html", 
                         minhas_ligas=minhas_ligas,
                         ligas_publicas=ligas_publicas)


@app.route("/criar-liga", methods=['GET', 'POST'])
def criar_liga_route():
    if 'user_id' not in session:
        return redirect("/")

    if request.method == 'POST':
        nome = request.form.get('nome')
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        id_criador = session['user_id']

        if nome and data_inicio and data_fim:
            # tipo_liga pode vir do formulário (ex.: 'LT01' pública, 'LT02' privada)
            tipo_liga = request.form.get('tipo_liga') or 'LT01'
            codigo_convite = request.form.get('codigo_convite') or None

            liga_id = criar_liga(nome, data_inicio, data_fim, tipo_liga, id_criador, codigo_convite)
            session['message'] = "Liga criada com sucesso!"
            return redirect("/ligas")

    return render_template("criar_liga.html")


@app.route("/juntar-liga/<liga_id>", methods=['GET', 'POST'])
def juntar_liga_route(liga_id):
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        sucesso = juntar_liga(user_id, liga_id, codigo)

        if sucesso:
            session['message'] = "Juntaste-te à liga com sucesso!"
        else:
            session['error'] = "Erro ao juntar-se à liga. Verifica o código ou se já estás na liga."

    return redirect("/ligas")


@app.route("/liga/<liga_id>")
def liga_detalhes(liga_id):
    if 'user_id' not in session:
        return redirect("/")

    liga = obter_liga_por_id(liga_id)
    participantes = obter_participantes_liga(liga_id)

    if not liga:
        return "Liga não encontrada", 404

    return render_template("liga_details.html", 
                         liga=liga, 
                         participantes=participantes)


@app.route("/juntar-liga-codigo", methods=['POST'])
def juntar_liga_codigo():
    codigo = request.form.get("codigo")
    user_id = session["user_id"]

    liga_id = obter_liga_id_por_codigo(codigo)

    if not liga_id:
        session['error'] = "Código inválido"
        return redirect("/ligas")

    sucesso = juntar_liga(user_id, liga_id, codigo)

    if sucesso:
        session['message'] = "Você entrou na liga com sucesso!"
    else:
        session['error'] = "Falha ao entrar na liga"

    return redirect("/ligas")


@app.route("/abandonar-liga/<liga_id>", methods=['POST'])
def abandonar_liga_route(liga_id):
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']

    sucesso = abandonar_liga(user_id, liga_id)

    if sucesso:
        session['message'] = "Você saiu da liga com sucesso!"
    else:
        session['error'] = "Você não está nessa liga."

    return redirect("/ligas")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
