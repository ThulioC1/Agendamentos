from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_agendamentos():
    conn = sqlite3.connect('agendamentos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agendamentos')
    agendamentos = cursor.fetchall()
    conn.close()
    
    # Formata as datas para PT-BR
    agendamentos_formatados = []
    for agendamento in agendamentos:
        id, data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome = agendamento
        
        # Verifica se a data é uma string
        if isinstance(data, int):
            # Se data for um inteiro, converte para string
            data_formatada = datetime.fromtimestamp(data).strftime('%d/%m/%Y')
        else:
            # Converte a data de string para o formato PT-BR
            data_formatada = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        agendamentos_formatados.append((id, data_formatada, hora_inicio, hora_fim, descricao, participantes, sala_id, nome))
    
    return agendamentos_formatados

# Função para verificar se o horário está ocupado para uma sala específica
def verificar_horario_ocupado(sala_id, data, hora_inicio, hora_fim):
    conn = sqlite3.connect('agendamentos.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM agendamentos 
        WHERE sala_id = ? 
        AND data = ? 
        AND (
            (hora_inicio < ? AND hora_fim > ?) OR  -- Horário de início está dentro do intervalo
            (hora_inicio < ? AND hora_fim > ?) OR  -- Horário de fim está dentro do intervalo
            (hora_inicio >= ? AND hora_fim <= ?)   -- Intervalo está totalmente dentro de um agendamento existente
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
    sala_id = int(request.form['sala'])  # Converta para inteiro, se necessário

    # Debug: Verifique os dados recebidos
    print(f"Agendamento: nome={nome}, descricao={descricao}, participantes={participantes}, "
          f"data={data}, hora_inicio={hora_inicio}, hora_fim={hora_fim}, sala_id={sala_id}")

    # Verifica se o horário já está ocupado para a sala específica
    horario_ocupado = verificar_horario_ocupado(sala_id, data, hora_inicio, hora_fim)

    if horario_ocupado:
        return jsonify({"success": False, "message": "Horário já está ocupado para esta sala."})
    else:
        # Insere o novo agendamento
        conn = sqlite3.connect('agendamentos.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO agendamentos (data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Agendamento realizado com sucesso!"})

@app.route('/agendamentos')
def listar_agendamentos():
    conn = sqlite3.connect('agendamentos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome FROM agendamentos')
    agendamentos = cursor.fetchall()
    conn.close()

    # Formata as datas para PT-BR
    agendamentos_formatados = []
    for agendamento in agendamentos:
        id, data, hora_inicio, hora_fim, descricao, participantes, sala_id, nome = agendamento
        
        if isinstance(data, int):
            data_formatada = datetime.fromtimestamp(data).strftime('%d/%m/%Y')
        else:
            data_formatada = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        agendamentos_formatados.append((id, data_formatada, hora_inicio, hora_fim, descricao, participantes, sala_id, nome))
    
    return jsonify(agendamentos_formatados)

if __name__ == '__main__':
    app.run(debug=True)
