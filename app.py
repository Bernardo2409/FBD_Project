from flask import Flask, render_template
from persistence.session import create_connection
from persistence.players import list_all, read

app = Flask(__name__)

@app.route("/")
def base():
    jogadores = list_all()

    return render_template("players.html", jogadores=jogadores)

@app.route("/players/<j_id>")
def player_view(j_id):
    jogador = read(j_id)  # Agora, read retorna diretamente o objeto PlayerDetails

    if jogador:
        return render_template("player_view.html", jogador=jogador)
    else:
        return "Jogador não encontrado", 404
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
