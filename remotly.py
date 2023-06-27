# -*- coding: utf-8 -*-
# pip install webdriver-manager, pip install selenium
import os
import time
import json
#import pandas as pd
#import numpy as np
import openpyxl   #pip install openpyxl
import shutil
from datetime import datetime, date, timedelta

#Servicio python
import asyncio
from flask import Flask,jsonify,request

# Database (sudo apt-get install sqlite3 libsqlite3-dev  )
import mysql.connector  #pip install mysql-connector-python
import sqlite3  

# Manejo de warning
import warnings

# Importamos el sincronizzador de la tabla history
import sincronizar as sincronizar

#importamos el conector de jira
import jira as jira

#importamos el conector de atenea
import mainAtenea as atenea

# Obtener env de entorno
from dotenv import load_dotenv


# Importamos el sincronizzador de la tabla history
import googleDrive as googleDrive


# Creamos log de eventos por registro de tarea automatica 
import logging

# Configuración básica del logger
logging.basicConfig(filename='logRemotly.log', level=logging.INFO)

# Cargar las variables de entorno del archivo .env
load_dotenv()
    
user=os.getenv('USER_MYSQL')
password=os.getenv('PASSWORD_MYSQL')
port=os.getenv('PORT_MYSQL')
host=os.getenv('HOST')
database=os.getenv('DATABASE')

#Variable de entorno del servicio
app = Flask("__name__")
app.config['TIMEOUT']=3600


class Run:
    def __init__(self, trx, ejec, channel, mipsm, trpta):
        self.trx = trx
        self.ejec = ejec 
        self.channel = channel
        self.mipsm = round(mipsm, 2)
        self.trpta = round(trpta, 2)
        return


class Executions:
    def __init__(fecha=None, run=None):
        self.fecha = fecha 
        self.run = run
        return
    
@app.route('/',methods=['GET'])
def enpoint():
    main()
    response = {
        'message': 'Ejecución completa'
    }
    return response

@app.route('/jira',methods=['GET'])
def enpointjira():
    resultado=jira.main()
    response = {
        'message': 'Ejecución completa',
        'status': resultado
    }
    return response

@app.route('/atenea',methods=['GET'])
def enpointatenea():
    resultado= atenea.main()
    response = {
        'message': 'Ejecución completa',
        'status': resultado
    }
    return response

def sendData(path_file):
    dataJson = readJson(path_file)
    date = dataJson['date']
    conn = mysql.connector.connect(host=host, port=port, user=user, password=password, database=database)
    lend = len(dataJson['executions'])
    count = 0
    fastData= []
    FastControl = 0
    deleteData(conn, date)
    for register in dataJson['executions']:
        temp=(str(date), str(register['channel']), str(register['trx']), register['ejec'], register['mipsm'], register['trpta'])
        fastData.append(temp)
        count += 1
        FastControl += 1
        if FastControl >= 100:
            multiple_insert(conn, lend, count, 'executions',("exec_fecha", "exec_canal", "exec_tx", "exec_number", "exec_mips_medio", "exec_time_mid"), fastData)
            FastControl = 0
            fastData= []
    if FastControl > 1:
        multiple_insert(conn, lend, count, 'executions',("exec_fecha", "exec_canal", "exec_tx", "exec_number", "exec_mips_medio", "exec_time_mid"), fastData)
    # date_time = date.strftime("%m/%d/%Y, %H:%M:%S")`
    print("\r           - OK: " + str(count) + "/" + str(lend) + " - " + str(date) + "                                          ")
    conn.commit()   
    conn.close()


def readJson(path_file):
    with open(path_file,  encoding='utf-8') as f:
        objetJson = json.load(f)
    return objetJson


def multiple_insert(conn, lend, count, table, cols, rows):
    try:
        cursor = conn.cursor()
        sql_insert = 'INSERT INTO %s(%s) values %s' % (
            table,
            ','.join(cols),
            ','.join('(%s, %s, %s, %s, %s, %s)' for _ in rows)
        )
        values = [_ for r in rows for _ in r]
        cursor.execute(sql_insert, values)
        print("\r    -->    OK: " + str(count) + "/" + str(lend) + " - " + str(date) + " -           ", end=' ', flush=True)
    except:
        print(" ERROR: " + str(count) + "/" + str(lend) + " - " + str(date) + " -           ")
        conn.rollback()
              

def deleteData(conn, date):
    cursor = conn.cursor()
    insert_stmt = ('DELETE FROM	executions WHERE exec_canal != "ETHER" and exec_fecha = "' + str(date) + '"')
    try:
        cursor.execute(insert_stmt)
        conn.commit() 
        print("           - Table it´s OK           ")
    except: 
        print("           - Table ERROR         ")
        conn.rollback()
                

def agregateExecution(arregloJson, trx, ejec, canal, mipsm, trpta):
    if len(arregloJson) == 0:
        dato = Run(trx, ejec, canal, mipsm, trpta).__dict__
        arregloJson.append(dato)
    else:
        repeat = True
        for register in arregloJson:
            if register['trx'] == trx:
                if register['channel'] == canal:
                    repeat = False
                    ejec = int(ejec) + int(register['ejec'])
                    mips = (float(mipsm) + float(register['mipsm']))/2
                    trpta = (float(trpta) + float(register['trpta']))/2
                    register['ejec']  = round(ejec,3)
                    register['mipsm'] = round(mips,3)
                    register['trpta'] = round(trpta,3)
                    break     
        if repeat:
            dato = Run(trx, ejec, canal, mipsm, trpta).__dict__
            arregloJson.append(dato)  
    return arregloJson


def readFile(path):
    print("        File to json " + str(path))
    logging.info('File to json')
    # Head Register
    line = 10
    # Open file Executions
    wb = openpyxl.load_workbook(path)
    sheet = wb.active
    # Control Error
    validador = True
    # Object Data
    fechaJson = "" 
    objectToJson = {}
    objectToJson['executions'] = []
    # Logical program
    while(validador):
        fecha = sheet['A' + str(line)].value
        hora  = sheet['B' + str(line)].value
        cics  = sheet['C' + str(line)].value
        canal = sheet['D' + str(line)].value
        trx   = sheet['E' + str(line)].value
        ejec  = sheet['F' + str(line)].value
        mips  = sheet['G' + str(line)].value
        mipsm = sheet['H' + str(line)].value
        trpta = sheet['I' + str(line)].value
        # Validate end file
        if (trx != None ):
            objectToJson['date'] = str(fecha)[0:10]
            fechaJson = str(fecha)[0:10]
            objectToJson['executions'] = agregateExecution(objectToJson['executions'], trx, ejec, canal, mipsm, trpta)
            line = line + 1
        else:
            validador = False
        print("\r           -   OK: " + str(fecha)[0:10] + " [" + str(line)+ "] " , end=' ', flush=True)
    print("\r           - Json object Ok!                    ")
    logging.info('- Json object Ok! ')
    #Name file was processed
    nameFile = fechaJson + '.json'
    #Path creating file json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pathNewJson = os.path.join(script_dir, 'jsonSend',nameFile)

    #Path move Json file was processed
    pathOldJson = os.path.join(script_dir,'jsonBackup',str(nameFile))
    print("           - Write json Objet to file: "+ pathNewJson)
    with open(str(pathNewJson), 'w', encoding='utf-8') as file:
        json.dump(objectToJson, file, ensure_ascii=False)
    print("           - Send data to MySql")
    sendData(pathNewJson)
    print("           - Move to backup the file: "+ pathOldJson)
    ##clean path, new files json move to old path
    if not validador:
        try:
            os.remove(pathOldJson)
            print("           - Delete file previous "+ pathOldJson)
            logging.info('- Delete file previous')
        except:
            print("           - Not delete file previous "+ pathOldJson)
            logging.info('- Not delete file previous')
        shutil.move(pathNewJson, pathOldJson)
    try:
        os.remove(path)
        print("           - Delete file downloads previous "+ path)
        logging.info('- Delete file downloads previous')
    except:
        print("           - Not delete downloads file previous "+ path)
        logging.info('- Not delete downloads file previous')


def findFile():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    downloads_dir = os.path.join(script_dir, 'downloads')
    contenido = os.listdir(downloads_dir)
    for archivo in contenido:
        if 'consumo_cics_transaccion' in archivo and '~$' not in archivo:
            file_path = os.path.join(downloads_dir, archivo)
            readFile(file_path)
            sincronizar.main()
    googleDrive.crear_o_reemplazar_carpeta()  

def getDateCurrent():
    # Get date databse, current
    print ("\r        Get date on Database", end=' ', flush=True)
    conn = mysql.connector.connect(host=host, 
                                    port=port,
                                    user=user, 
                                    password=password, 
                                    database=database)
    cursor = conn.cursor()
    cursor.execute("SELECT current_date() ")
    dateCurrent = cursor.fetchone() 
    conn.close()
    return dateCurrent[0]


def getDateHistory():
    # Get date databse history
    print ("        Get date history Database")
    logging.info('Get date history Database')
    conn = mysql.connector.connect(host=host, 
                                    port=port,
                                    user=user, 
                                    password=password, 
                                    database=database)
    cursor = conn.cursor()
    cursor.execute("""SELECT executions.exec_fecha FROM executions where executions.exec_canal <> "ETHER"
                    order by executions.exec_fecha desc limit 1""")
    dateHistory = cursor.fetchone()
    return dateHistory[0]


def getDataChannel():
    # Get date databse history
    print ("        Get date Channel Database")
    logging.info('Get date Channel Database')
    conn = mysql.connector.connect(host=host, 
                                    port=port,
                                    user=user, 
                                    password=password, 
                                    database=database)
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM `channelExecutionsLastMonth` LIMIT 0, 1000""")

    dataChannel = cursor.fetchall()
    channels=""
    transaccion=""
    fechaInicio=""
    fechaFin=""
    sumTrx=0

    for row in dataChannel:
         channels=channels + str(row[0])+"\t|"
         sumTrx = sumTrx + int (row[1])
         transaccion=transaccion + str(row[1])+"\t|"
         fechaInicio=row[2]
         fechaFin=row[3]
    cursor.close()
    print("\r        fechaInicio: " + str(fechaInicio) + " fechaFin: " + str(fechaFin)  + " Trx: " + str(sumTrx) )
    


def initialize(head, warning, delete, json, jsonBackup):
    # Head
    if head:
        os.system('cls')
        print("                                                                     ")
        print("       ░█████╗░██╗░░░██╗████████╗░█████╗░  ██╗░░██╗██████╗░██╗       ")
        print("       ██╔══██╗██║░░░██║╚══██╔══╝██╔══██╗  ██║░██╔╝██╔══██╗██║       ")
        print("       ███████║██║░░░██║░░░██║░░░██║░░██║  █████═╝░██████╔╝██║       ")
        print("       ██╔══██║██║░░░██║░░░██║░░░██║░░██║  ██╔═██╗░██╔═══╝░██║       ")
        print("       ██║░░██║╚██████╔╝░░░██║░░░╚█████╔╝  ██║░╚██╗██║░░░░░██║       ")
        print("       ╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░░╚════╝░  ╚═╝░░╚═╝╚═╝░░░░░╚═╝       ")
        print("")
        logging.info('********************************************************** %s ' % datetime.now())
        logging.info('AUTO KPI')
    # valid jsonBackup
    if jsonBackup:
        try:
            os.mkdir('./jsonBackup')
            print("        Directory jsonBackup Create  ")
            logging.info('Directory jsonBackup Create')
        except:
            print("        jsonBackup exists")
            logging.info('jsonBackup exists')
    # valid jsonSend
    if json:
        try:
            os.mkdir('./jsonSend')
            print("        Directory jsonSend Create  ")
            logging.info('Directory jsonSend Create')
        except:
            print("        jsonSend exists")
            logging.info('jsonSend exists')
        contenido = os.listdir('./jsonSend')
        for archivo in contenido:
            os.remove('./jsonSend' + '\\' + str(archivo))
    # Clear downloads
    if delete:
        try:
            os.mkdir('./downloads')
            print("        Directory old create")
            logging.info('Directory old create')
        except:
            print("        downloads exists and delete")
            logging.info('downloads exists and delete')
        contenido = os.listdir('./downloads')
        for archivo in contenido:
            if ('consumo_cics_transaccion' in archivo and not('~$consumo_cics_transaccion' in archivo)):
                os.remove('./downloads' + '\\' + str(archivo))
    # Delet error and warning dependency
    if warning:
        warnings.simplefilter("ignore")


def request(dateHistory, dateCurrent):

    #Path creating file json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pathNewJson = os.path.join(script_dir, 'db.db')
    conn = sqlite3.connect(pathNewJson)
    print("Delete from request")
    conn.execute("DELETE FROM request")
    while  dateHistory <= dateCurrent:
        try:
            conn.execute("INSERT INTO request (status,type,date) VALUES ('INIT', 'DOWN', '" + str(dateHistory) + "')");  
            conn.commit()  
            print("        Request Day :" + str(dateHistory))
            
        except:
            print("        Request Day :" + str(dateHistory) + " in progress")
        dateHistory=dateHistory+timedelta(days=1)
    conn.close()  

 #leer y despues escribirlo en un archivo 
def readbd():
    conn = sqlite3.connect('db.db')
    cur = conn.cursor()
    for row in cur.execute("""SELECT * FROM `request` ;"""):
         status = row[0]
         type = row[1]
         date = row[2]
         print(row) 
    conn.close() 
  
def main():
    googleDrive.descargar_archivos_de_google_drive()
    initialize(True, True, False, True, False) #Procesar sin borrar archivos de downloads
    dateHistory = getDateHistory()
    dateCurrent = getDateCurrent()+timedelta(days=-1)
    print("\n        Validate file in downloads")
    logging.info('Validate file in downloads')
    findFile()
    ##dateHistory=dateHistory+timedelta(days=-1)
    print("\r        History: " + str(dateHistory) + " Current: " + str(dateCurrent), end=' ', flush=True)
    logging.info('History')
    if (dateHistory == dateCurrent):
        print("\n        Database it´s update")
        logging.info('Database it´s update')
        getDataChannel()
    elif (dateHistory > dateCurrent):
        print("        Error in database")
        logging.info('Error in database')
    else:
        request(dateHistory, dateCurrent)
        #LLAMADO AL METODO DE DRIVE QUE CARGUE EL ARCHIVO
        googleDrive.subir_archivo_a_google_drive()
    print("        Process finished\n\n\n")
    logging.info('Process finished')


if __name__=="__main__":
    app.run(host='0.0.0.0',port='900')