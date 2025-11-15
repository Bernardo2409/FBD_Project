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
    jogador_id, jogador = read(j_id)

    return render_template("player_view.html", jogador_id=jogador_id, jogador=jogador)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
