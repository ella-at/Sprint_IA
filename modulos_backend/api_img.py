import cx_Oracle
import requests

# Dados para conexão com o banco de dados da Oracle
dsn = cx_Oracle.makedsn("oracle.fiap.com.br", 1521, service_name="ORCL")
connection = cx_Oracle.connect(user="RM552051", password="140400", dsn=dsn)


def verificar_conexao():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM dual")
        result = cursor.fetchone()
        print("Conexão com o banco de dados bem-sucedida:", result)
    except cx_Oracle.DatabaseError as e:
        print("Erro ao conectar ao banco de dados", e)


verificar_conexao()


# Chave da API do Roboflow 
api_key = "pmgZQrQDbUTGDnTXIvNo"
model_endpoint_damage1 = "https://detect.roboflow.com/plants-disease-2599r/1"
model_endpoint_damage2 = "https://detect.roboflow.com/plants-final/1"
model_endpoint_pest = "https://detect.roboflow.com/pests-in-cucumber-plants-kcmdr/1"




# Função para análise com as três APIs (doença e pragas)
def analisar_imagem_roboflow_completa(caminho_imagem):
    # Uso de 2 APIs, uma para analisar a saúde e outra a presença de doença
    url_damage1 = f"{model_endpoint_damage1}?api_key={api_key}"
    url_damage2 = f"{model_endpoint_damage2}?api_key={api_key}"
    
    with open(caminho_imagem, "rb") as img_file:
        # 1º análise de saúde
        response1 = requests.post(url_damage1, files={"file": img_file})
        resultado1 = response1.json() if response1.status_code == 200 else None

    with open(caminho_imagem, "rb") as img_file:
        # 2º análise de doença
        response2 = requests.post(url_damage2, files={"file": img_file})
        resultado2 = response2.json() if response2.status_code == 200 else None

    # Utiliza um modelo para a Análise de pragas
    url_pest = f"{model_endpoint_pest}?api_key={api_key}"
    with open(caminho_imagem, "rb") as img_file:
        response_pest = requests.post(url_pest, files={"file": img_file})
        resultado_pragas = response_pest.json() if response_pest.status_code == 200 else None
    
    return resultado1, resultado2, resultado_pragas

#Filtro de previsão duplicada
def filtrar_previsoes_duplicadas(previsoes):
    
    melhores_previsoes = {}

    for previsao in previsoes:
        classe = previsao.get("class", "Desconhecido")
        confianca = previsao.get("confidence", 0)

       
        if classe in melhores_previsoes:
            if confianca > melhores_previsoes[classe]["confidence"]:
                melhores_previsoes[classe] = previsao
        else:
            melhores_previsoes[classe] = previsao

    # Retorna sem resposta duplicada
    return list(melhores_previsoes.values())



# Função para exibir os resultados
def extrair_dados_analise_completa(resultado_analise1, resultado_analise2, resultado_pragas):
    print("\n--- Resultados da Análise de Saúde (Modelo 1) ---")
    if resultado_analise1 and resultado_analise1["predictions"]:
        # Filtra previsões duplicadas da analise de saude
        previsoes_filtradas1 = filtrar_previsoes_duplicadas(resultado_analise1["predictions"])
        for i, previsao in enumerate(previsoes_filtradas1, 1):
            nome_objeto = previsao.get("class", "Desconhecido")
            confianca = previsao.get("confidence", 0) * 100
            print(f"{i}. {nome_objeto} com {confianca:.2f}% de confiança")
    else:
        print("Nenhuma doença detectada no Modelo 1")

    print("\n--- Resultados da Análise de Doenças (Modelo 2) ---")
    if resultado_analise2 and resultado_analise2["predictions"]:
        # Filtra previsões duplicadas da analise de doenças
        previsoes_filtradas2 = filtrar_previsoes_duplicadas(resultado_analise2["predictions"])
        for i, previsao in enumerate(previsoes_filtradas2, 1):
            nome_objeto = previsao.get("class", "Desconhecido")
            confianca = previsao.get("confidence", 0) * 100
            print(f"{i}. {nome_objeto} com {confianca:.2f}% de confiança")
    else:
        print("Nenhuma doença detectada no Modelo 2")

    # Analisa as pragas da mesma forma
    print("\n--- Resultados da Análise de Pragas ---")
    if resultado_pragas and resultado_pragas["predictions"]:
        previsoes_filtradas_pragas = filtrar_previsoes_duplicadas(resultado_pragas["predictions"])
        for i, previsao in enumerate(previsoes_filtradas_pragas, 1):
            nome_objeto = previsao.get("class", "Desconhecido")
            confianca = previsao.get("confidence", 0) * 100
            print(f"{i}. {nome_objeto} com {confianca:.2f}% de confiança")
    else:
        print("Nenhuma praga detectada")


    # Filtro para aumentar a confiabilidade do resultado entre os modelos de doenças e pragas
    melhor_previsao1 = max(resultado_analise1["predictions"], key=lambda x: x["confidence"]) if resultado_analise1 and resultado_analise1["predictions"] else None
    melhor_previsao2 = max(resultado_analise2["predictions"], key=lambda x: x["confidence"]) if resultado_analise2 and resultado_analise2["predictions"] else None
    melhor_previsao_pragas = max(resultado_pragas["predictions"], key=lambda x: x["confidence"]) if resultado_pragas and resultado_pragas["predictions"] else None

    # Prioridade: maior confiança entre os modelos de doenças, depois pragas
    if melhor_previsao1 and melhor_previsao2:
        if melhor_previsao1["confidence"] > melhor_previsao2["confidence"]:
            return melhor_previsao1.get("confidence", 0) * 100, melhor_previsao1.get("class", "Desconhecido")
        else:
            return melhor_previsao2.get("confidence", 0) * 100, melhor_previsao2.get("class", "Desconhecido")
    elif melhor_previsao1:
        return melhor_previsao1.get("confidence", 0) * 100, melhor_previsao1.get("class", "Desconhecido")
    elif melhor_previsao2:
        return melhor_previsao2.get("confidence", 0) * 100, melhor_previsao2.get("class", "Desconhecido")
    elif melhor_previsao_pragas:
        return melhor_previsao_pragas.get("confidence", 0) * 100, melhor_previsao_pragas.get("class", "Desconhecido")
    else:
        return 0, "Nenhuma doença ou praga detectada"

# Função para salvar os resultados no banco de dados
def salvar_resultado_no_banco(imagem_path, resultado_analise, probabilidade, status):
    cursor = connection.cursor()
    
    # SQL para inserir o resultado no banco de dados
    sql = """
    INSERT INTO T_CFS_ANALISE_IMAGEM_IA (
        ID_IMG_IA, ID_PLANTIO, CAMINHO_IMAGEM, RESULTADO_ANALISE, PROBABILIDADE, STATUS
    ) VALUES (
        T_CFS_Analise_Imagem_IA_seq.NEXTVAL, :id_plantio, :caminho_imagem, :resultado_analise, :probabilidade, :status
    )
    """
    
    # Inserindo dados no banco
    cursor.execute(sql, {
        "id_plantio": None,  
        "caminho_imagem": imagem_path,
        "resultado_analise": str(resultado_analise),
        "probabilidade": probabilidade,
        "status": status
    })
    
    connection.commit()
    cursor.close()
    print("Resultado salvo no banco de dados.")

# Função que realiza a análise completa
def processo_completo(caminho_imagem):
    # Analisa a imagem com as duas APIs de doenças e a API de pragas
    resultado1, resultado2, resultado_pragas = analisar_imagem_roboflow_completa(caminho_imagem)
    
    if resultado1 or resultado2 or resultado_pragas:
        # Extrai e exibe as informações detalhadas da análise
        probabilidade, status = extrair_dados_analise_completa(resultado1, resultado2, resultado_pragas)
        
        # Salvar o resultado no banco de dados
        salvar_resultado_no_banco(caminho_imagem, {"modelo1": resultado1, "modelo2": resultado2, "pragas": resultado_pragas}, probabilidade, status)
    else:
        print("Erro na análise da imagem.")

# Executa o processo completo com uma imagem de teste predefinida 
processo_completo("X:/CPA_CHALLENGE/STATIC/UPLOADS/planta.jpg")