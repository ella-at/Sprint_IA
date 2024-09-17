from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import os
import cx_Oracle  
import requests
from datetime import datetime


app = Flask(__name__)
app.secret_key = '6acad0a12d21148a992875e2cf935d0a06c322eea013daf9' 


# Conexão com o banco de dados Oracle
dsn = cx_Oracle.makedsn("oracle.fiap.com.br", 1521, service_name="ORCL")
connection = cx_Oracle.connect(user='RM552051', password='140400', dsn=dsn)


# Local para salvar as imagens de upload
UPLOAD_FOLDER = './static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Página index 
@app.route('/')
def index():
    return render_template('index.html')

# Chave da API e URLs dos modelos do Roboflow
api_key = "pmgZQrQDbUTGDnTXIvNo"
model_endpoint_damage1 = "https://detect.roboflow.com/plants-disease-2599r/1"
model_endpoint_damage2 = "https://detect.roboflow.com/plants-final/1"
model_endpoint_pest = "https://detect.roboflow.com/pests-in-cucumber-plants-kcmdr/1"

# Análise de imagem via Roboflow (para doenças)
def analisar_imagem_roboflow_doenca(caminho_imagem):
    url_damage1 = f"{model_endpoint_damage1}?api_key={api_key}"
    url_damage2 = f"{model_endpoint_damage2}?api_key={api_key}"
    

    with open(caminho_imagem, "rb") as img_file:
        response1 = requests.post(url_damage1, files={"file": img_file})
        resultado1 = response1.json() if response1.status_code == 200 else None

    with open(caminho_imagem, "rb") as img_file:
        response2 = requests.post(url_damage2, files={"file": img_file})
        resultado2 = response2.json() if response2.status_code == 200 else None

    return resultado1, resultado2, 

# Análise de imagem via Roboflow (para pragas)
def analisar_imagem_roboflow_pragas(caminho_imagem):
    url_pest = f"{model_endpoint_pest}?api_key={api_key}"
    
    with open(caminho_imagem, "rb") as img_file:
        response_pest = requests.post(url_pest, files={"file": img_file})
        resultado_pragas = response_pest.json() if response_pest.status_code == 200 else None

    return resultado_pragas


# Rota para upload de imagem e análise de doenças 
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        if 'imagem' not in request.files:
            flash("Nenhuma imagem foi enviada.", "erro")
            return redirect(url_for('upload_page'))

        imagem = request.files['imagem']
        
        if imagem.filename == '':
            flash("Nenhuma imagem selecionada.", "erro")
            return redirect(url_for('upload_page'))

        caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], imagem.filename)
        imagem.save(caminho_imagem)

        resultado1, resultado2 = analisar_imagem_roboflow_doenca(caminho_imagem)

        return render_template('resultado.html',
                               imagem_filename=imagem.filename, 
                               resultado1=resultado1, 
                               resultado2=resultado2)

    return render_template('upload.html')


# Rota para upload de imagem e análise de pragas
@app.route('/analise_pragas', methods=['GET', 'POST'])
def analise_pragas_page():
    if request.method == 'POST':
        if 'imagem' not in request.files:
            flash("Nenhuma imagem foi enviada.", "erro")
            return redirect(url_for('analise_pragas_page'))

        imagem = request.files['imagem']
        if imagem.filename == '':
            flash("Nenhuma imagem selecionada.", "erro")
            return redirect(url_for('analise_pragas_page'))

        caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], imagem.filename)
        imagem.save(caminho_imagem)
        
         
        resultado_pragas = analisar_imagem_roboflow_pragas(caminho_imagem)

        return render_template('resultado_pragas.html', imagem_filename=imagem.filename, resultado_pragas=resultado_pragas)

    return render_template('analise_pragas.html')


# Página de resultados das doenças
@app.route('/resultado')
def resultado():
    return render_template('resultado.html')

# Página de resultados das pragas
@app.route('/resultado_pragas')
def resultado_pragas():
    return render_template('resultado_pragas.html')


#####
#####

# Chave de API da Agromonitoring
API_KEY = '7172f74a4716f5cc9bc58d17ac90e471'  
BASE_URL = 'https://api.agromonitoring.com/agro/1.0/'


# Página de monitoramento 
@app.route('/monitoramento')
def monitoramento():
    return render_template('monitoramento.html')


@app.route('/definir_area', methods=['POST'])
def definir_area():
    dados = request.json
    coordenadas = dados.get('coordenadas', [])
    tipo_dado = dados.get('tipo_dado')

    if not coordenadas:
        return jsonify({"error": "Nenhuma coordenada fornecida"}), 400

    
    coords_formatted = [[p['lng'], p['lat']] for p in coordenadas]

    
    polygon_data = {
        "name": "Área de Monitoramento",
        "geo_json": {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords_formatted]
            }
        }
    }

    
    url_polygon = f'{BASE_URL}polygons?appid={API_KEY}'
    resposta = requests.post(url_polygon, json=polygon_data)

    if resposta.status_code == 200:
        polygon_id = resposta.json().get('id')

        
        if tipo_dado == 'satellite':
            url_dado = f'{BASE_URL}image/search?polyid={polygon_id}&appid={API_KEY}'
        elif tipo_dado == 'weather':
            url_dado = f'{BASE_URL}weather?polyid={polygon_id}&appid={API_KEY}'
        elif tipo_dado == 'soil_moisture':
            url_dado = f'{BASE_URL}soil?polyid={polygon_id}&appid={API_KEY}'

        
        resposta_dados = requests.get(url_dado)

        if resposta_dados.status_code == 200:
            return jsonify(resposta_dados.json()), 200
        else:
            return jsonify({"error": "Erro ao buscar os dados do tipo selecionado"}), 500
    else:
        return jsonify({"error": "Erro ao definir a área"}), 500




###########
###########

#  Página com lista do hitorico das áreas de plantio
@app.route('/areas_plantio')
def areas_plantio():
    try:
        
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id_nova_plantio, nome, tamanho_hectares, tipo_solo, rotacao, tipo_irrigacao, tecnologia, pragas
            FROM T_CFS_Nova_Area_Plantio
        """)
        areas = cursor.fetchall()
        return render_template('areas_plantio.html', areas=areas)

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Erro ao acessar o banco de dados Oracle: {error}")
        return "Erro ao acessar o banco de dados", 500
    finally:
        cursor.close()



# Página de cadastro de nova área de plantação
@app.route('/nova_area', methods=['GET', 'POST'])
def nova_area():
    if request.method == 'POST':
        nome = request.form['nome']
        tamanho = request.form['tamanho']
        tipo_solo = request.form['tipo_solo']
        irrigada = 1 if request.form['irrigada'] == 'Sim' else 0
        tipo_irrigacao = request.form['tipo_irrigacao']
        rotacao = 'S' if request.form['rotacao'] == 'Sim' else 'N'
        tecnologia = request.form['tecnologia']
        pragas = request.form['pragas'] if request.form['pragas'] else None
        
        

        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO T_CFS_Nova_Area_Plantio (id_nova_plantio, nome, tamanho_hectares, tipo_solo, irrigada, 
                                                     tipo_irrigacao, rotacao, tecnologia, pragas)
                VALUES (T_CFS_Nova_Area_Plantio_seq.NEXTVAL, :nome, :tamanho, :tipo_solo, :irrigada, 
                        :tipo_irrigacao, :rotacao, :tecnologia, :pragas)
            """, {
                'nome': nome,
                'tamanho': float(tamanho),
                'tipo_solo': tipo_solo,
                'irrigada': irrigada,
                'tipo_irrigacao': tipo_irrigacao,
                'rotacao': rotacao,
                'tecnologia': tecnologia,
                'pragas': pragas
            })
            connection.commit()
            flash("Área de plantio cadastrada com sucesso!", "sucesso")
            return redirect(url_for('areas_plantio'))
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            print(f"Erro ao inserir dados: {error}")
            return "Erro ao salvar a área de plantio", 500
        finally:
            cursor.close()

    return render_template('nova_area.html')


# Página de cadastro de nova plantação 
@app.route('/nova_plantacao/<int:area_id>', methods=['GET', 'POST'])
def nova_plantacao(area_id):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_nova_plantio, nome FROM T_CFS_Nova_Area_Plantio WHERE id_nova_plantio = :area_id", {'area_id': area_id})
        area = cursor.fetchone()

        cursor.execute("SELECT id_funcionario, nome FROM T_CFS_Funcionarios")
        funcionarios = cursor.fetchall()

        if request.method == 'POST':
            nome_cultivo = request.form['nome_cultivo']
            cultura = request.form['cultura']
            data_plantio = request.form['data_plantio']
            data_colheita_prevista = request.form['data_colheita_prevista']
            funcionario_id = request.form['funcionario_id']
            fertilizacao = request.form['fertilizacao']
            pesticida = request.form['pesticida']
            frequencia_irrigacao = request.form['frequencia_irrigacao']

            cursor.execute("""
                INSERT INTO T_CFS_Novo_Cultivo (id_novo_cultivo, id_nova_plantio, nome_cultivo, cultura, data_plantio, 
                                                data_colheita_prevista, funcionario_id, fertilizacao, pesticida, frequencia_irrigacao)
                VALUES (T_CFS_Novo_Cultivo_seq.NEXTVAL, :id_nova_plantio, :nome_cultivo, :cultura, :data_plantio, 
                        :data_colheita_prevista, :funcionario_id, :fertilizacao, :pesticida, :frequencia_irrigacao)
            """, {
                'id_nova_plantio': area_id,
                'nome_cultivo': nome_cultivo,
                'cultura': cultura,
                'data_plantio': datetime.strptime(data_plantio, '%Y-%m-%d'),
                'data_colheita_prevista': datetime.strptime(data_colheita_prevista, '%Y-%m-%d') if data_colheita_prevista else None,
                'funcionario_id': funcionario_id,
                'fertilizacao': fertilizacao,
                'pesticida': pesticida,
                'frequencia_irrigacao': frequencia_irrigacao
            })
            connection.commit()

            return redirect(url_for('areas_plantio'))
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Erro ao acessar o banco de dados: {error}")
        return "Erro ao acessar o banco de dados", 500
    finally:
        cursor.close()

    return render_template('nova_plantacao.html', area=area, funcionarios=funcionarios)

# Página com a lista de plantações cadastradas
@app.route('/ver_plantacao/<int:area_id>')
def ver_plantacao(area_id):
    try:
        cursor = connection.cursor()

        
        cursor.execute("SELECT nome FROM T_CFS_Nova_Area_Plantio WHERE id_nova_plantio = :area_id", {'area_id': area_id})
        area = cursor.fetchone()
        if not area:
            return f"Erro: Área de plantio com ID {area_id} não encontrada.", 404

        
        cursor.execute("""
            SELECT nome_cultivo, cultura, data_plantio, data_colheita_prevista, fertilizacao, pesticida, frequencia_irrigacao
            FROM T_CFS_Novo_Cultivo WHERE id_nova_plantio = :area_id
        """, {'area_id': area_id})
        plantacao = cursor.fetchall()

        return render_template('ver_plantacao.html', area_nome=area[0], plantacao=plantacao)
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Erro ao acessar o banco de dados: {error}")
        return "Erro ao acessar o banco de dados", 500
    finally:
        cursor.close()


# Página para cadastrar novos funcionários
@app.route('/novo_funcionario', methods=['GET', 'POST'])
def novo_funcionario():
    if request.method == 'POST':
        nome = request.form['nome']
        cargo = request.form['cargo']

        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO T_CFS_Funcionarios (id_funcionario, nome, cargo)
                VALUES (T_CFS_Funcionarios_seq.NEXTVAL, :nome, :cargo)
            """, {'nome': nome, 'cargo': cargo})
            connection.commit()

            return redirect(url_for('areas_plantio'))
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            print(f"Erro ao inserir funcionário: {error}")
            return "Erro ao cadastrar funcionário", 500
        finally:
            cursor.close()

    return render_template('novo_funcionario.html')




if __name__ == '__main__':
        app.run(debug=True, port=8080)

