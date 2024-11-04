from flask import Flask, render_template, request, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# String de conexão ao banco de dados Neon
DATABASE_URL = "postgresql://neondb_owner:HGe8o6aKVprN@ep-dark-lake-a5hkjrso.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_agendamentos():
    # Conecte-se ao banco de dados usando psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agendamentos')
    agendamentos = cursor.fetchall()
    conn.close()
    
    # Formate as datas para PT-BR
    agendamentos_formatados = []
    for agendamento in agendamentos:
        id, data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome = agendamento
        
        # Verifica o tipo de data e converte para o formato PT-BR
        if isinstance(data, datetime):
            data_formatada = data.strftime('%d/%m/%Y')
        elif isinstance(data, str):
            data_formatada = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        else:
            data_formatada = data  # Mantém como está se já estiver formatada

        agendamentos_formatados.append((id, data_formatada, hora_inicio, hora_fim, descricao, participantes, sala_id, nome))
    
    return agendamentos_formatados

# Função para verificar se o horário está ocupado para uma sala específica
def verificar_horario_ocupado(sala_id, data, hora_inicio, hora_fim):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM agendamentos 
        WHERE sala_id = %s 
        AND data = %s 
        AND (
            (hora_inicio < %s AND hora_fim > %s) OR  
            (hora_inicio < %s AND hora_fim > %s) OR  
            (hora_inicio >= %s AND hora_fim <= %s)   
        )
    ''', (sala_id, data, hora_inicio, hora_inicio, hora_fim, hora_fim, hora_inicio, hora_fim))
    
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado > 0

@app.route('/')
def index():
    agendamentos = get_agendamentos()
    return render_template('index.html', agendamentos=agendamentos)

@app.route('/agendar', methods=['POST'])
def agendar():
    nome = request.form['nome']
    descricao = request.form['descricao']
    participantes = request.form['participantes']
    data = request.form['data']
    hora_inicio = request.form['hora_inicio']
    hora_fim = request.form['hora_fim']
    sala_id = int(request.form['sala'])

    # Verifica se o horário já está ocupado para a sala específica
    horario_ocupado = verificar_horario_ocupado(sala_id, data, hora_inicio, hora_fim)

    if horario_ocupado:
        return jsonify({"success": False, "message": "Horário já está ocupado para esta sala."})
    else:
        # Insere o novo agendamento
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO agendamentos (data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Agendamento realizado com sucesso!"})

@app.route('/agendamentos')
def listar_agendamentos():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT id, data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome FROM agendamentos')
    agendamentos = cursor.fetchall()
    conn.close()

    # Formata as datas para PT-BR
    agendamentos_formatados = []
    for agendamento in agendamentos:
        id, data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome = agendamento
        
        # Verifica o tipo de data e converte para o formato PT-BR
        if isinstance(data, datetime):
            data_formatada = data.strftime('%d/%m/%Y')
        elif isinstance(data, str):
            data_formatada = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        else:
            data_formatada = data

        agendamentos_formatados.append((id, data_formatada, hora_inicio, hora_fim, descricao, participantes, sala_id, nome))
    
    return jsonify(agendamentos_formatados)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
