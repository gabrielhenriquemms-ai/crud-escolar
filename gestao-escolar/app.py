from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path

app = Flask(__name__)
app.secret_key = "gestao-escolar-local"

ARQUIVO = Path(__file__).with_name("dados.txt")


def ler_alunos():
    alunos = []
    if not ARQUIVO.exists():
        return alunos

    with ARQUIVO.open("r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue

            partes = linha.split("|")
            if len(partes) != 5:
                continue

            id_reg, nome, nota1, nota2, frequencia = partes
            try:
                alunos.append({
                    "id": int(id_reg),
                    "nome": nome,
                    "nota1": float(nota1),
                    "nota2": float(nota2),
                    "frequencia": int(frequencia),
                })
            except ValueError:
                # Ignora linhas inválidas sem interromper o site.
                continue

    return alunos


def salvar_alunos(alunos):
    with ARQUIVO.open("w", encoding="utf-8") as arquivo:
        for aluno in alunos:
            arquivo.write(
                f"{aluno['id']}|{aluno['nome']}|{aluno['nota1']}|"
                f"{aluno['nota2']}|{aluno['frequencia']}\n"
            )


def proximo_id(alunos):
    return max((aluno["id"] for aluno in alunos), default=0) + 1


def validar_dados(form):
    nome = form.get("nome", "").strip()
    if not nome:
        raise ValueError("Informe o nome do aluno.")
    if "|" in nome or "\n" in nome:
        raise ValueError("O nome não pode conter o caractere | ou quebra de linha.")

    try:
        nota1 = float(form.get("nota1", "").replace(",", "."))
        nota2 = float(form.get("nota2", "").replace(",", "."))
        frequencia = int(form.get("frequencia", ""))
    except ValueError:
        raise ValueError("Informe notas numéricas e uma frequência inteira.")

    if not 0 <= nota1 <= 10 or not 0 <= nota2 <= 10:
        raise ValueError("As notas devem estar entre 0 e 10.")
    if not 0 <= frequencia <= 100:
        raise ValueError("A frequência deve estar entre 0% e 100%.")

    return nome, nota1, nota2, frequencia


@app.route("/")
def index():
    alunos = sorted(ler_alunos(), key=lambda aluno: aluno["id"])
    media_geral = (
        sum((aluno["nota1"] + aluno["nota2"]) / 2 for aluno in alunos) / len(alunos)
        if alunos else None
    )
    frequencia_media = (
        sum(aluno["frequencia"] for aluno in alunos) / len(alunos)
        if alunos else None
    )
    return render_template(
        "index.html",
        alunos=alunos,
        media_geral=media_geral,
        frequencia_media=frequencia_media,
    )


@app.route("/criar", methods=["POST"])
def criar():
    try:
        nome, nota1, nota2, frequencia = validar_dados(request.form)
        alunos = ler_alunos()
        alunos.append({
            "id": proximo_id(alunos),
            "nome": nome,
            "nota1": nota1,
            "nota2": nota2,
            "frequencia": frequencia,
        })
        salvar_alunos(alunos)
        flash("Aluno cadastrado com sucesso!", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("index"))


@app.route("/atualizar/<int:id_reg>", methods=["POST"])
def atualizar(id_reg):
    try:
        nome, nota1, nota2, frequencia = validar_dados(request.form)
        alunos = ler_alunos()
        aluno_encontrado = False

        for aluno in alunos:
            if aluno["id"] == id_reg:
                aluno.update({
                    "nome": nome,
                    "nota1": nota1,
                    "nota2": nota2,
                    "frequencia": frequencia,
                })
                aluno_encontrado = True
                break

        if not aluno_encontrado:
            flash("ID não encontrado.", "erro")
        else:
            salvar_alunos(alunos)
            flash("Registro atualizado com sucesso!", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")

    return redirect(url_for("index"))


@app.route("/deletar/<int:id_reg>", methods=["POST"])
def deletar(id_reg):
    alunos = ler_alunos()
    atualizados = [aluno for aluno in alunos if aluno["id"] != id_reg]

    if len(atualizados) == len(alunos):
        flash("ID não encontrado.", "erro")
    else:
        salvar_alunos(atualizados)
        flash("Registro removido com sucesso!", "sucesso")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
