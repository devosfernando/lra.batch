# -*- coding: utf-8 -*-
import os
# Nombre del equipo
import socket
# Database (sudo apt-get install sqlite3 libsqlite3-dev  )
import mysql.connector  #pip install mysql-connector-python
# Manejo de fechas
from datetime import timedelta
from dotenv import load_dotenv


# Cargar las variables de entorno del archivo .env
load_dotenv()

port = os.getenv('PORT_MYSQL')


def insertSql(usr,pas,host,info, query, value,port):
    print ("\r   " + info + "                                 ", end=' ', flush=True)
    conn = mysql.connector.connect(host=host, user=usr, password=pas, database="planbackend",port=port)
    cursor = conn.cursor()
    cursor.execute(query, value)
    conn.commit()
    conn.close()
    return cursor.rowcount


def deleteSql(usr, pas, host, info, query,port):
    print ("\r   " + info + "                                 ", end=' ', flush=True)
    conn = mysql.connector.connect(host=host, user=usr, password=pas, database="planbackend",port=port)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()
    return cursor.rowcount


def getSql(usr, pas, host, info, query,port):
    print ("\r   " + info + "                                 ", end=' ', flush=True)
    conn = mysql.connector.connect(host=host, user=usr, password=pas, database="planbackend",port=port)
    cursor = conn.cursor()
    cursor.execute(query)
    dateHistory = cursor.fetchone()
    conn.close()
    return dateHistory[0]


def queryEther(usr,pas,host,date,port):
    query = 'SELECT sum(exec_number) AS ether FROM `executions` WHERE `exec_fecha` BETWEEN `FIRST_MONTH` ("' + str(date) + '") AND "' + str(date) + '" AND exec_canal = "ETHER"'
    ether = getSql(usr,pas,host,"Get Ether", query,port)
    return(ether)


def queryAltamira(usr,pas,host,date,port):
    query1 = 'SELECT sum(exec_number) FROM executions WHERE exec_fecha BETWEEN FIRST_MONTH("' + str(date) + '") AND "' + str(date) + '" AND exec_canal != "ETHER" '
    query2 = ' AND ( exec_canal <> "Excluir" OR exec_canal = "Excluir" AND exec_tx IN ( "KAMU", "KAQU", "KAPT", "KAO1", "KAPS", "KAPR", "KANF", "KARW", "KANQ", "KAMY", '
    query3 = ' "KAQA", "KAMP", "QOSF", "KAUC", "KAPV", "KAQB", "KAPI", "KANC", "KAPX", "KAQ9", "K286", "PECY", "KAN6", "KAMS", "KAO0", "KAN7", "K2J0", "KAN4", "KAO7", '
    query4 = ' "KARA", "KANW", "KAN8", "K240", "KAPU", "KAN5", "KAOX",  "KARC", "KARB", "KAQ6", "K130", "KAPH", "KARU", "KARZ", "KANN", "KANI", "KARN", "KAP5", "KAO5", '
    query4 = ' "KAO6", "KAMK", "K230", "K131", "KAMT", "KANU", "KAPY", "KAO2", "KARJ", "KANY", "KARO", "KANE", "KAQ2", "KAOW", "KAPE", "KAMJ", "KAO8", "KAP3", "KAOA", '
    query5 = ' "KAQK", "KAQM", "KNZ1", "KAP8", "KAPN", "K136", "KAR3", "KAPJ", "KANK", "KAM6", "KANT", "KANZ", "KAMG", "KAQE", "KANJ", "K135", "KAR7", "KANV", "KAQR", '
    query6 = ' "KAP1", "KAPP", "KAM9", "KAPA", "KAQF", "KAPZ", "KAP9", "KAQV", "KAP2", "KAOY", "KAM1", "KAPB", "KAMN", "KARQ", "KAM3", "KAQ3", "KAM7", "KAQ0", "KAQ5", '
    query7 = ' "KAR1", "KAMO", "KARP", "KNF1", "KANM", "KAQ7", "KARD", "KAML", "KAQY", "KARK", "KAMX", "KAQQ", "KAMM", "KANP", "KAQN", "KARH", "KAM2", "KAMZ", "KANH", '
    query8 = ' "KAP6", "KARE", "K140", "K150" ))'
    query = query1 + query2 + query3 + query4 + query5 + query6 + query7 + query8
    altamira = getSql(usr,pas,host,"Get altamira", query,port)
    return(altamira)
     

def iteration(usr,pas,host,dateHistory, dateCurrent,port):
    while  dateHistory <= dateCurrent:
        date = dateHistory
        print("\r\n   Process: " + str(date) + "                                 ")
        # Validamos datos de ether
        query = 'SELECT count(exec_fecha) FROM executions WHERE `exec_fecha` = "' + str(date) + '" AND exec_canal = "ETHER"'
        etetherCounter = getSql(usr, pas, host, "Get etetherCounter", query,port)
        # Validamos datos de altamira
        query = 'SELECT count(exec_fecha) FROM executions WHERE `exec_fecha` = "' + str(date) + '" AND exec_canal <> "ETHER"'
        altamiraCounter = getSql(usr, pas, host, "Get altamiraCounter", query,port)
        # Si los dos tienen datos calculamos

        if etetherCounter > 0 and altamiraCounter > 0:
            # Optenemos ejecuciones de ether
            ether = queryEther(usr, pas, host, date,port)
            # Optenemos ejecuciones de altamira
            altamira = queryAltamira(usr, pas, host, date,port)
            # Optenemos el Kpi estimado
            query = 'SELECT hist_kpiEstimado FROM `history` WHERE hist_date = LAST_DAY(LAST_DAY("' + str(date) + '"))'
            kpiEstimado = getSql(usr,pas,host,"Get kpiEstimado", query,port)
            # Calculamos kpiReal
            kpiReal = (ether) / (ether +altamira)
            # Ejecutamos Delete
            query = 'DELETE FROM `history` WHERE hist_date ="' + str(date) + '"'
            delete = deleteSql(usr,pas,host,"Delete histori", query,port)
            # Ejecutamos Insert
            query = 'INSERT INTO history (hist_date, hist_EjecEther, hist_EjecHost, hist_kpiEstimado, hist_kpiReal ) VALUES (%s, %s, %s, %s, %s)'
            value = (date, ether, altamira, kpiEstimado, kpiReal)
            resultado = insertSql(usr,pas,host,"Insert database", query, value,port)

        else: 
            print("Process Stop no informations, ether " + str(etetherCounter) + " altamira "+ str(altamiraCounter))
        dateHistory=dateHistory+timedelta(days=1)


def parametros():

    print(" Ejecucion Local")
    usr = os.getenv('USER_MYSQL')
    print(f"  Usuario:  {usr}")
    pas = os.getenv('PASSWORD_MYSQL')
    print(f"  Password: {pas}")
    host= os.getenv('HOST')
    print(f"  Host:  {host}")
    port = os.getenv('PORT_MYSQL')
    print(f"  Puerto:  {port}")
    return(usr, pas, host,port)


def Sincronizar():
    print("\n")
    usr,pas,host,port=parametros()
    query = """select hist_date from history where hist_EjecHost <> 0 order by hist_date desc limit 1"""
    histQ = getSql(usr,pas,host,"Get date on Database", query,port)
    query = """SELECT executions.exec_fecha FROM executions where executions.exec_canal <> "ETHER" order by executions.exec_fecha desc limit 1"""
    etherQ = getSql(usr,pas,host,"Get date on Database", query,port)
    query = "SELECT current_date() "
    hostQ = getSql(usr, pas, host, "Get Info history Database", query,port)

    if etherQ < hostQ:
        tempQ = etherQ
    else:
        tempQ = hostQ
    print(tempQ)
    print(hostQ)
    print(histQ)
    if tempQ <= histQ:
        print("No update")
    else:
        dateHistory = histQ
        dateCurrent = tempQ
        iteration(usr, pas, host, dateHistory, dateCurrent,port)
