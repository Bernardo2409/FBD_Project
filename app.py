import os
import secrets
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, jsonify, session, url_for

from persistence.equipa import (
    adicionar_jogador_equipa, 
    criar_equipa, obter_equipa_por_utilizador, 
    obter_jogadores_equipa, 
    remover_jogador_equipa, 
    verificar_limites_equipa, 
    obter_detalhes_equipa_para_visualizacao, 
    trocar_jogador_banco_campo
)
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
    obter_ranking_liga,
    verificar_participacao_liga,
)
from persistence.jornadas import obter_jornada_info, obter_jornada_atual, obter_todas_jornadas
from persistence.players import list_all, list_paginated, read
from persistence.clubs import list_all_clubs, list_paginated_clubs, read_club
from persistence.users import create_user, login_user, get_users, get_user_by_id
from persistence.countries import get_pais

from persistence.pontuacoes import calcular_pontuacao_equipa, calcular_pontuacao_jogador, obter_pontuacoes_jornadas, obter_equipa_com_pontuacoes_jornada
from persistence import players
from persistence.match import list_paginated_matches, read_match


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
    pais = get_pais()
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

    try:
        user_id = create_user(first, last, email, password, country, nationality, birthdate)
        
        if not user_id:
            raise Exception("Erro ao criar utilizador")

        user_data = {
            "id": user_id,
            "first": first,
            "last": last,
            "email": email
        }
        
        session['user'] = user_data
        
        return redirect("/")

    except Exception as e:
        print(f"Erro no registo: {e}")
        
        pais = get_pais()
        
        mensagem_erro = str(e)
        if "email já está registado" in str(e).lower():
            mensagem_erro = "Este email já está registado."
        elif "país inválido" in str(e).lower():
            mensagem_erro = "País selecionado é inválido."
        
        return render_template("signup.html", 
                             pais=pais, 
                             error=mensagem_erro,
                             form_data={
                                 "first": first,
                                 "last": last,
                                 "email": email,
                                 "country": country,
                                 "nationality": nationality,
                                 "birthdate": birthdate
                             })


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
                session['message'] = "Jogador adicionado com sucesso!"

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
        id_criador = session['user_id']

        if nome and data_inicio:
            data_fim = '2026-05-30'
            
            tipo_liga = request.form.get('tipo_liga') or 'LT02'
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
    if not liga:
        return "Liga não encontrada", 404
    
    participantes = obter_participantes_liga(liga_id)
    
    jornada_selecionada = request.args.get('jornada', None)
    
    jornadas = obter_todas_jornadas()
    
    # Obter ranking
    ranking = obter_ranking_liga(liga_id, jornada_selecionada)

    return render_template("liga_details.html", 
                         liga=liga, 
                         participantes=participantes,
                         ranking=ranking,
                         jornadas=jornadas,
                         jornada_selecionada=jornada_selecionada)


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


def obter_jornada_atual():
    return 'jornada_1'


@app.route("/atualizar_pontuacao")
def atualizar_pontuacao():
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)

    if equipa_user:
        id_jornada = obter_jornada_atual()
        
        pontuacao_total = calcular_pontuacao_equipa(equipa_user.id, id_jornada)
        
        return render_template("pontuacao.html", pontuacao_total=pontuacao_total)
    else:
        return "Não tens uma equipa.", 404


@app.route("/pontuacao")
def pontuacao():
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']
    
    equipa_user = obter_equipa_por_utilizador(user_id)
    if equipa_user:
        try:
            pontuacoes_jornadas = obter_pontuacoes_jornadas(equipa_user.id)
            
            total_pontos = sum(p['pontuacao'] for p in pontuacoes_jornadas if p['pontuacao'])
            media_pontos = total_pontos / len(pontuacoes_jornadas) if pontuacoes_jornadas else 0
            melhor_jornada = max(pontuacoes_jornadas, key=lambda x: x['pontuacao']) if pontuacoes_jornadas else None
            
            return render_template("pontuacao.html", 
                                 equipa={'info': equipa_user}, 
                                 pontuacoes_jornadas=pontuacoes_jornadas,
                                 total_pontos=total_pontos,
                                 media_pontos=round(media_pontos, 2),
                                 melhor_jornada=melhor_jornada)
        except Exception as e:
            print(f"Erro ao obter pontuações: {e}")
            return render_template("pontuacao.html", 
                                 equipa={'info': equipa_user}, 
                                 pontuacoes_jornadas=[],
                                 error="Erro ao carregar pontuações")
    else:
        return redirect("/criar-equipa")


@app.route("/equipa/<id_equipa>/jornada/<id_jornada>")
def equipa_jornada(id_equipa, id_jornada):
    if 'user_id' not in session:
        return redirect("/")

    user_id = session['user_id']
    
    try:
        dados = obter_equipa_com_pontuacoes_jornada(id_equipa, id_jornada)
        
        equipa_user = obter_equipa_por_utilizador(user_id)
        
        if not equipa_user or str(equipa_user.id) != str(id_equipa):
            return "Não tens permissão para ver esta equipa.", 403
        
        jornada_info = obter_jornada_info(id_jornada)
        
        jogadores_campo = [j for j in dados['jogadores'] if not j.get('benched', 1)]
        jogadores_banco = [j for j in dados['jogadores'] if j.get('benched', 1)]
        
        def agrupar_por_posicao(jogadores):
            grupos = {
                'goalkeeper': [],
                'defender': [],
                'midfielder': [],
                'forward': []
            }
            
            for jogador in jogadores:
                posicao = jogador.get('posicao', '').lower()
                if 'goalkeeper' in posicao:
                    grupos['goalkeeper'].append(jogador)
                elif 'defender' in posicao:
                    grupos['defender'].append(jogador)
                elif 'midfielder' in posicao:
                    grupos['midfielder'].append(jogador)
                elif 'forward' in posicao:
                    grupos['forward'].append(jogador)
            
            return grupos
        
        campo_agrupado = agrupar_por_posicao(jogadores_campo)
        banco_agrupado = agrupar_por_posicao(jogadores_banco)
        
        total_pontos = dados.get('pontuacao_total', 0)
        total_jogadores = len(jogadores_campo)
        media_por_jogador = total_pontos / total_jogadores if total_jogadores > 0 else 0
        
        melhor_jogador = max(jogadores_campo, key=lambda x: x.get('pontuacao', 0)) if jogadores_campo else None
        
        return render_template("equipa.html", 
                             equipa=equipa_user,
                             jogadores_campo=jogadores_campo,
                             jogadores_banco=jogadores_banco,
                             campo_agrupado=campo_agrupado,
                             banco_agrupado=banco_agrupado,
                             pontuacao_total=total_pontos,
                             media_por_jogador=round(media_por_jogador, 2),
                             melhor_jogador=melhor_jogador,
                             jornada_info=jornada_info,
                             jornada_atual=id_jornada)
        
    except Exception as e:
        print(f"Erro na rota equipa_jornada: {e}")
        
        try:
            equipa_user = obter_equipa_por_utilizador(user_id)
            
            if equipa_user and str(equipa_user.id) == str(id_equipa):
                pontuacao_total = calcular_pontuacao_equipa(id_equipa, id_jornada)
                jogadores_equipa = obter_jogadores_equipa(id_equipa)

                for jogador in jogadores_equipa:
                    jogador['pontuacao'] = calcular_pontuacao_jogador(jogador['id'], id_jornada)
                
                jogadores_campo = [j for j in jogadores_equipa if not j.get('benched', 1)]
                jogadores_banco = [j for j in jogadores_equipa if j.get('benched', 1)]
                
                return render_template("equipa.html", 
                                     equipa=equipa_user, 
                                     jogadores_campo=jogadores_campo,
                                     jogadores_banco=jogadores_banco,
                                     pontuacao_total=pontuacao_total,
                                     jornada_atual=id_jornada)
        except Exception as e2:
            print(f"Erro no método fallback: {e2}")
        
        return render_template("error.html", 
                             message="Erro ao carregar dados da equipa",
                             details=str(e)), 500


@app.route("/equipa/banco/adicionar/<id_jogador>", methods=["POST"])
def adicionar_jogador_ao_banco_route(id_jogador):
    if 'user_id' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)
    
    if equipa_user:
        from persistence.equipa import adicionar_jogador_ao_banco
        sucesso, mensagem = adicionar_jogador_ao_banco(equipa_user.id, id_jogador)
        
        if sucesso:
            session['message'] = mensagem
        else:
            session['error'] = mensagem
    
    return redirect("/equipa")


@app.route("/equipa/banco/remover/<id_jogador>", methods=["POST"])
def remover_jogador_do_banco_route(id_jogador):
    if 'user_id' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)
    
    if equipa_user:
        from persistence.equipa import remover_jogador_do_banco
        sucesso, mensagem = remover_jogador_do_banco(equipa_user.id, id_jogador)
        
        if sucesso:
            session['message'] = mensagem
        else:
            session['error'] = mensagem
    
    return redirect("/equipa")


@app.route("/equipa/trocar/<id_jogador_campo>/<id_jogador_banco>", methods=["POST"])
def trocar_jogador_route(id_jogador_campo, id_jogador_banco):
    if 'user_id' not in session:
        return redirect("/")
    
    user_id = session['user_id']
    equipa_user = obter_equipa_por_utilizador(user_id)
    
    if equipa_user:
        sucesso, mensagem = trocar_jogador_banco_campo(equipa_user.id, id_jogador_banco, id_jogador_campo)
        
        if sucesso:
            session['message'] = mensagem
        else:
            session['error'] = mensagem
    
    return redirect("/equipa")


@app.route('/players/<player_id>')
def player_details(player_id):
    if 'user_id' not in session:
        return redirect("/")
    
    jogador = players.read(player_id)
    
    if not jogador:
        return "Jogador não encontrado", 404
    
    stats, total_pontos = players.get_player_stats(player_id)
    
    total_golos = sum(stat.golos_marcados for stat in stats)
    total_assistencias = sum(stat.assistencias for stat in stats)
    
    return render_template(
        'player_details.html',
        jogador=jogador,
        stats=stats,
        total_pontos=total_pontos,
        total_golos=total_golos,
        total_assistencias=total_assistencias
    )


@app.route("/jogos")
def jogos_list():
    if 'user_id' not in session:
        return redirect("/")
    page = int(request.args.get("page", 1))
    per_page = 10

    matches, total = list_paginated_matches(page, per_page)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "jogos.html",
        match=matches,
        page=page,
        total_pages=total_pages
    )


@app.route("/jogos/<match_id>")
def match_details(match_id):
    if 'user_id' not in session:
        return redirect("/")
    
    match = read_match(match_id)

    if match:
        return render_template("jogos_details.html", match=match)
    else:
        return "Jogo não encontrado", 404

@app.route("/liga/<id_liga>/equipa/<id_equipa>")
def ver_equipa_liga(id_liga, id_equipa):
    """
    Rota para ver a equipa de outro participante na liga.
    """
    if 'user_id' not in session:
        return redirect("/")
    
    try:
        # Verificar se o utilizador pertence à liga
        user_id = session['user_id']
        
        if not verificar_participacao_liga(user_id, id_liga):
            return "Não tens permissão para ver esta equipa.", 403
        
        # Obter detalhes da equipa
        dados_equipa = obter_detalhes_equipa_para_visualizacao(id_equipa)
        
        # Obter informações da liga para o breadcrumb
        liga = obter_liga_por_id(id_liga)
        
        if not liga:
            return "Liga não encontrada", 404
        
        # Verificar se é a equipa do próprio utilizador
        is_minha_equipa = False
        minha_equipa = obter_equipa_por_utilizador(user_id)
        if minha_equipa and str(minha_equipa.id) == str(id_equipa):
            is_minha_equipa = True
        
        # Calcular pontuação atual se houver jornada atual
        
        jornada_atual = obter_jornada_atual()
        pontuacao_atual = 0
        
        if jornada_atual:
            try:
                pontuacao_atual = calcular_pontuacao_equipa(id_equipa, jornada_atual['id'])
            except:
                pass  # Ignora erros no cálculo
        
        return render_template("ver_equipa_liga.html",
                             liga=liga,
                             dados_equipa=dados_equipa,
                             pontuacao_atual=pontuacao_atual,
                             is_minha_equipa=is_minha_equipa,
                             jornada_atual=jornada_atual)
        
    except Exception as e:
        print(f"Erro ao ver equipa da liga: {e}")
        return render_template("error.html",
                             message="Erro ao carregar equipa",
                             details=str(e)), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")