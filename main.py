# -*- coding: utf-8 -*-
# pip install -r requirements.txt && pip3 install -r requirements.txt 
# Inicio productivo gunicorn remotly:AppBatch 

import os
import mysql.connector 
from dotenv import load_dotenv
from flask import Flask
from src.remotly import Remotly
from src.jira import Jira
from src.atenea import Atenea

def connectMysql():
    conn = mysql.connector.connect(
    host=os.getenv('HOST'),
    user=os.getenv('USER_MYSQL'),
    password=os.getenv('PASSWORD_MYSQL'),
    database=os.getenv('BD_MYSQL_PB'),
    port=os.getenv('PORT_MYSQL')
    )
    return conn

# Cargado de variables de entorno
def variablesEntorno(cargador):
    conn = connectMysql()
    cursor = conn.cursor()
    cursor.execute("""SELECT parametry.`field`, parametry.`key`, parametry.`value` FROM planbackend.parametry """)
    configuraciones = cursor.fetchall()
    for field, key, value in configuraciones:
        if field in cargador:
            os.environ[key] = value
    conn.close()

# Definicion de servicios
def servicio():
    # Entorno
    app = Flask("__name__")
    app.config['TIMEOUT']=3600
    app.config['DEBUG'] = False
    app.config['ENV'] = 'production'
    #Servicios
    @app.route('/remotly',methods=['GET'])
    def enpoint():
        Remotly()
        response = {
            'message': 'Ejecución remotly completa'
        }
        return response

    @app.route('/jira',methods=['GET'])
    def enpointjira():
        resultado=Jira()
        response = {
            'message': 'Ejecución jira completa',
            'dato': resultado,
            'status': 200 if len(resultado)>3 else 203
        }
        return response

    @app.route('/atenea',methods=['GET'])
    def enpointatenea():
        resultado= Atenea()
        response = {
            'message': 'Ejecución atenea completa',
            'status': resultado
        }
        return response
    app.run(host='0.0.0.0',port='900')

# Solo para pruebas o inici
if __name__=="__main__":
    # Variables de entorno
    load_dotenv()
    variablesEntorno(os.getenv('VARIABLE_ENTORNO'))
    # Reinicio del log
    archivo = open('logRemotly.log','w')
    archivo.close() 
    # Construccion del servicio
    servicio()