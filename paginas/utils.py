# utils.py
import json
import os

ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_GRUPOS = "grupos_pesquisa.json"
ARQUIVO_POPS = "pops.json"
ARQUIVO_USUARIOS = "usuarios.json"

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if dados:
                    return dados
        except Exception:
            return padrao
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)