from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  


iTOKEN = '122c24fa48c34e7f031d0ea6f29525e1'

def obter_id_cidade(nome_cidade):
    iURL = f"http://apiadvisor.climatempo.com.br/api/v1/locale/city?name={nome_cidade}&token={iTOKEN}"
    try:
        iRESPONSE = requests.get(iURL)
        iRESPONSE.raise_for_status()
        iRETORNO_REQ = iRESPONSE.json()

        if not iRETORNO_REQ:
            return {"error": "Cidade não encontrada."}

        cidades = []
        for cidade in iRETORNO_REQ:
            iID = cidade['id']
            iNAME = cidade['name']
            iSTATE = cidade['state']
            iCOUNTRY = cidade['country']
            cidades.append((iID, iNAME, iSTATE, iCOUNTRY))

        if len(cidades) == 0:
            return {"error": "Nenhuma cidade encontrada."}

        if len(cidades) > 1:
            return {"cidades": cidades}

        return {"id": cidades[0][0]}

    except requests.RequestException as e:
        return {"error": str(e)}

@app.route('/consultar_clima', methods=['GET'])
def consultar_clima():
    tipo = request.args.get('tipo')
    nome_cidade = request.args.get('nome_cidade')
    cidade_id = request.args.get('cidade_id')  

    
    if cidade_id:
        if tipo == '1':  # Clima atual
            iURL = f"http://apiadvisor.climatempo.com.br/api/v1/weather/locale/{cidade_id}/current?token={iTOKEN}"
        elif tipo == '3':  # Previsão de 15 dias
            iURL = f"http://apiadvisor.climatempo.com.br/api/v1/forecast/locale/{cidade_id}/days/15?token={iTOKEN}"
        else:
            return jsonify({"error": "Tipo de consulta inválido."})

        try:
            iRESPONSE = requests.get(iURL)
            iRESPONSE.raise_for_status()
            iRETORNO_REQ = iRESPONSE.json()
            return jsonify(iRETORNO_REQ)
        except requests.RequestException as e:
            return jsonify({"error": str(e)})

   
    if nome_cidade:
        cidade_info = obter_id_cidade(nome_cidade)
        if "error" in cidade_info:
            return jsonify(cidade_info)
        if "cidades" in cidade_info:
           
            return jsonify({"message": "Escolha uma cidade pelo ID", "cidades": cidade_info["cidades"]})

    return jsonify({"error": "Nome da cidade ou ID da cidade é necessário."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)