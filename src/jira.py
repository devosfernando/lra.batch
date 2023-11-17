# -*- coding: utf-8 -*-
# 
import os
import time
import json
import logging
import warnings
import mysql.connector
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Librerias
from src.lib.Correo import consultarCorreo


def tiempo_transcurrido(desde):
    logging.info("  -> Evaluando tiempo")
    tiempo_limite = 3600  # 1 hora en segundos
    tiempo_actual = datetime.now()
    logging.info("  -> Tiempo en BD:    " + str(desde))
    logging.info("  -> Tiempo en local: " + str(tiempo_actual))
    tiempo_transcurrido = (tiempo_actual - desde).total_seconds()
    if tiempo_transcurrido < tiempo_limite:
        logging.info("  -> Aun en tiempo")
        return True
    else:
        logging.info("  -> Fuera de tiempo")
        return False


def conexion():
    logging.info("   --- Conection Database ---")
    db = mysql.connector.connect(host=os.getenv("HOST"),
                                    port=os.getenv("PORT_MYSQL"),
                                    user=os.getenv("USER_MYSQL"), 
                                    password=os.getenv("PASSWORD_MYSQL"), 
                                    database=os.getenv("BD_MYSQL_JIRA"))
    return db  


def updateCookie(group, name, value, fecha_actual):
    try:
        conn = conexion()
        cursor = conn.cursor()       
        logging.info("  -> Actualizando Cookies ")
        sqlite = ("""INSERT INTO cookie 
                        (cookie.`GROUP`, cookie.`NAME`, cookie.`VAL`, cookie.`DATE_END`)
                    VALUES
                        (%s, %s, %s, NOW()) 
                    ON DUPLICATE KEY UPDATE 
                        cookie.`VAL` = %s, cookie.`DATE_END` = NOW()""")
        cursor.execute(sqlite, (group, name, value, value))
        conn.commit()
        logging.info("  -> Variables de Python insertadas con exito en la tabla Jira de ejecuciones")
    except mysql.connector.Error as err:
        logging.info("  -> Failed to INSERT/UPDATE: {}".format(err))
        conn.rollback()
    finally:
        cursor.close()
        if conn:
            conn.close()


def ejecucion(local):
    # Variables de entorno
    resultado='403'
    logging.info("   --- Conection Selenium ---")
    
    try:
        logging.info("  -> Cargta driver y opciones de selenium")
        option = webdriver.ChromeOptions()
        option.add_argument("--window-size=1382,744")
        # Adding argument to disable the AutomationControlled flag 
        option.add_argument("--disable-blink-features=AutomationControlled") 
        # Exclude the collection of enable-automation switches 
        option.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        # Turn-off userAutomationExtension 
        option.add_experimental_option("useAutomationExtension", False) 
        #INFO = 0, WARNING = 1, LOG_ERROR = 2, LOG_FATAL = 3.
        option.add_argument('log-level=0') 
        #Evitar errores
        option.add_experimental_option('excludeSwitches', ['enable-automation','enable-logging'])
        prefs = {"profile.default_content_setting_values.notifications" : 2}    
        option.add_experimental_option("prefs",prefs)
        if local:
            logging.info("  -> Conexion local")
            # Setting the driver path and requesting a page 
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)  
        else:
            errordriver=False
            logging.info("  -> Conexion remota de selenium")
            try:
                host='http://'+os.getenv("HOST_SELENIUM")+':4444/wd/hub'
                driver = webdriver.Remote(host,options=option) 
                logging.info("  -> Conexion a selenio iniciada")
            except WebDriverException as e:
                errordriver=True
                logging.info("  -> Error al ejecutar el controlador de Chrome: {}".format(str(e)))

            if errordriver: 
                driver = webdriver.chrome.service(ChromeDriverManager().install())
                driver.get('chrome://version')
                version_element = driver.find_element_by_xpath('/html/body')
                version_text = version_element.text
                version = version_text.split('\n')[0].split(' ')[2]
                logging.info('  -> Versión de Google Chrome:', version)
                print('  -> Versión de Google Chrome:', version)

        # Changing the property of the navigator value for webdriver to undefined 
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 

        intento=True
        logging.info("  -> Cargando Login ")
        
        contador=0
        while intento:
            try:
                driver.implicitly_wait(50)     
                driver.get("https://globaldevtools.bbva.com/jira/")
                WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH,  '//*[@id="loginForm"]/div[2]/button[1]'))).click()
                intento = False
            except:
                logging.info("\r        - Sleep Charging, retry", end=' ', flush=True)
                time.sleep(10)
                contador=contador+1
                logging.info("  -> Intento de carga numero:",contador)
                if contador == 10:
                    intento = False
                    logging.info("  -> Pagina No cargada")
                time.sleep(5)
        logging.info("  -> Login BBVA")
        myInputname = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'username')))
        myInputname.send_keys(os.getenv('USUARIO').replace("\n",""))

        myInputps = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'password')))
        myInputps.click()
        myInputps.clear()
        myInputps.send_keys(os.getenv('USUARIO_PS').replace("\n",""))
     
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="loginForm"]/div[2]/button[1]'))).click()
        
        if ("Está intentando acceder a los sistemas de BBVA" in driver.page_source or
            "You are trying to access BBVA systems" in driver.page_source):
                logging.info("  -> Validacion de Cuenta")
                # Click para seleccionar correo
                mySelect = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'presentMail')))
                mySelect.click()
                # Click para enviar clave
                mybtnEnviar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, '_eventId_proceed')))
                mybtnEnviar.click()
                logging.info("  -> Click en recibir clave de correo")
                # Click para colocar clave
                textClave = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'otp_mail')))
                textClave.click()
                time.sleep(10) #agregar llamado de la clase correo y colocar texto
                codigoVerificacion = consultarCorreo(os.getenv('CORREO'),os.getenv('CORREOIMAP'))
                # Click para colocar clave
                btnValidar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'otp_mail')))
                btnValidar.send_keys(codigoVerificacion)
                # Click para enviar clave
                mybtnEnviar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, '_eventId_proceed')))
                mybtnEnviar.click()
                logging.info("   --- Conection Selenium ---")
                logging.info("  -> Click para confirmar cuenta")
                time.sleep(5)
                logging.info("  -> Obtener Cookies")
                cokies= driver.get_cookies()
                # Recorrer el diccionario y realizar la lógica requerida
                for cookie in cokies:
                    if cookie['domain'] == 'jira.globaldevtools.bbva.com':
                        logging.info("  -> Valor a domain " + str(cookie['domain']))
                        logging.info("  -> Valor a name   " + str(cookie['name']))
                        logging.info("  -> Valor a value  " + str(cookie['value']))
                        try:
                            expiracion = datetime.utcfromtimestamp(cookie['expiry'])
                            logging.info("  -> Valor a fecha  " + str(expiracion))
                        except:
                            expiracion= datetime.min
                            logging.info("  -> Valor a fecha !" + str(expiracion))
                        if not("session-data-" in cookie['name']):
                            updateCookie(cookie['domain'], cookie['name'], cookie['value'], expiracion)
                        else:
                            logging.info("   --- Conection Database ---")
                logging.info("  -> Finaliza Correctamente")
        else:
            logging.info("  -> Error se relanzara no cargo correctamente la pagina")
            status='ERROR PAGINA'
            resultado='500'
        driver.close()
        driver.quit()
        fecha, value = selectTimeCookie()
        logging.info("  -> Finaliza")
        return value
    except Exception as e:
        driver.close()
        status='ERROR GENERAL'+ str(e[:480])
        logging.info("  -> Se produjo un error:", e)
        logging.info("  -> Error generico")
        return e


def selectTimeCookie():
    try:
        conn = conexion()
        cursor = conn.cursor()       
        logging.info("  -> Opteniendo tiempo de ultima ejecucion")
        consulta_sql = ("""SELECT cookie.DATE_END, cookie.VAL, cookie.`NAME`, cookie.`GROUP` 
                        FROM cookie 
                        WHERE cookie.`GROUP` = "jira.globaldevtools.bbva.com" 
                        ORDER BY DATE_END DESC""")
        cursor.execute(consulta_sql)
        result = cursor.fetchall()
        if result is not None:
            # Convertir los resultados a un formato JSON
            columnas = [desc[0] for desc in cursor.description]
            registros_json = []
            for registro in result:
                registro_dict = dict(zip(columnas, registro))
                # Convertir el objeto datetime a una cadena (formato ISO 8601) antes de agregar al diccionario
                temp = registro_dict['DATE_END'] = registro_dict['DATE_END'].strftime("%Y-%m-%d %H:%M:%S")
                temp = datetime.strptime(temp, "%Y-%m-%d %H:%M:%S")
                if temp > datetime.min:
                    fecha = temp
                registros_json.append(registro_dict)
            registros_json = json.dumps(registros_json)
            registros_json = json.loads(registros_json)
        else:
            value=0
            fecha=datetime.min
        logging.info("  -> Fecha en BD: " + str(fecha))
        logging.info("  -> Valor en BD: " + str(registros_json))
        return fecha, registros_json
    except mysql.connector.Error as err: 
        logging.info(" ERROR: SELECT COOKIE: {}".format(err)) 
        conn.rollback()
    finally:
        cursor.close() 
        conn.close()


def Jira():
    print("--- Inicio Jira ---")
    local=False
    fecha, value = selectTimeCookie()
    accion=tiempo_transcurrido(fecha)
    print("--- Fin Jira ---")
    return value if accion else ejecucion(local)
