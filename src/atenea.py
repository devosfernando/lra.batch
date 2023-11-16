
import time



import os
import json
import logging
import warnings
import mysql.connector
from selenium import webdriver
from datetime import datetime
from datetime import date, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Librerias
from src.lib.Correo import consultarCorreo
from src.lib.sincronizar import Sincronizar


def fechas():
    logging.info("  -> Calculo de fechas ")
    # Calculo de Fechas
    # Fecha Desde 
    date_sql = selectSql()
    date_sql = datetime.strptime(str(date_sql), "(datetime.date(%Y, %m, %d),)").date()
    datefrom = date_sql + timedelta(days=-1)
    logging.info("  ->   Fecha From:             "+str(datefrom))
    # Fecha Hasta 
    limite = date.today()
    limite = limite + timedelta(days=-1)
    logging.info("  ->   Fecha to:               "+str(limite))
    numdays = (limite - datefrom).days 
    logging.info("  ->   Number days pendientes: "+str(numdays))
    return datefrom, limite, numdays
        

def conexion():
    logging.info ("   ---Conection Database---")
    db = mysql.connector.connect(host=os.getenv("HOST"),
                                    port=os.getenv("PORT_MYSQL"),
                                    user=os.getenv("USER_MYSQL"), 
                                    password=os.getenv("PASSWORD_MYSQL"), 
                                    database=os.getenv("DATABASE"),
                                    auth_plugin=os.getenv("ATH_MYSQL"))
    return db  


def selectSql():
    logging.info("  -> Consulta de fechas en BD")
    conn = conexion()
    cursor = conn.cursor()
    select_stmt =( "SELECT max(exec_fecha) FROM planbackend.executions WHERE exec_canal='ETHER' AND exec_tx='ATEN' ")
    try:
        cursor.execute(select_stmt)
        fecha = cursor.fetchone()
        cursor.close() 
        conn.close()
        return fecha
    except: 
        logging.info("  ---> ERROR: SELECT ")  


def ejecucion(local):
    json_data = []
    logging.info("  -> Run Selenium IDE")
    warnings.simplefilter("ignore")
    logging.info("  -> Cargta driver y opciones de selenium")
    option = webdriver.ChromeOptions()
    option.add_argument("--window-size=1382,744")
    # Adding argument to disable the AutomationControlled flag 
    option.add_argument("--disable-blink-features=AutomationControlled") 
    # Exclude the collection of enable-automation switches 
    option.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    # Turn-off userAutomationExtension 
    option.add_experimental_option("useAutomationExtension", False) 
    # INFO = 0, WARNING = 1, LOG_ERROR = 2, LOG_FATAL = 3.
    option.add_argument('log-level=0') 
    # Evitar errores
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

    # Changing the property of the navigator value for webdriver to undefined 
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 

    datefrom, limite, numdays = fechas()

    if (numdays>0):   
        logging.info("  -> Solicitando pagina de login")   
        driver.implicitly_wait(3)     
        driver.get("https://atenea.live-02.platform.bbva.com/public")
        myInput = driver.find_element(By.TAG_NAME, 'input')
        myInput.click()
        myInput.send_keys(os.getenv('USUARIO').replace("\n",""))
        myInput2 = driver.find_element(By.ID, 'password')
        myInput2.send_keys(os.getenv('USUARIO_PS').replace("\n",""))
        driver.find_element(By.XPATH, '//*[@id="loginForm"]/div[2]/button[1]').click()
        time.sleep(3)
        if ("Está intentando acceder a los sistemas de BBVA" in driver.page_source or
                "You are trying to access BBVA systems" in driver.page_source):
            logging.info("  -> Inicia pantalla de correo")
            mySelect = driver.find_element(By.ID, 'presentMail') # Click para seleccionar correo
            mySelect.click()
            mybtnEnviar = driver.find_element(By.NAME, '_eventId_proceed') # Click para enviar clave
            mybtnEnviar.click()
            logging.info("  -> Click en recibir clave de correo")
            textClave = driver.find_element(By.ID, 'otp_mail')# Click para colocar clave
            textClave.click()
            time.sleep(3)
            codigoVerificacion = consultarCorreo(os.getenv('CORREO'),os.getenv('CORREOIMAP'))
            logging.info("  -> Click para validar con el codigo: " + str(codigoVerificacion))
            btnValidar = driver.find_element(By.ID, 'otp_mail')# Click para colocar clave
            btnValidar.send_keys(codigoVerificacion)
            mybtnEnviar = driver.find_element(By.NAME, '_eventId_proceed') # Click para enviar clave
            mybtnEnviar.click()
        
            time.sleep(3)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "btn-important")))
            mybtn = driver.find_element(By.CLASS_NAME, 'btn-important')# Click en acceptar
            mybtn.click()
            
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "btn-realease-notes-close")))
            mybtn = driver.find_element(By.CLASS_NAME, 'btn-realease-notes-close') # Click para cerrar Release note
            mybtn.click()

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/application-menu/dropdown/div/button/label/span[2]')))
            mybtn = driver.find_element(By.XPATH, '/html/body/div[1]/application-menu/dropdown/div/button/label/span[2]') # Click para seleccionar metrics
            mybtn.click()
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dropdown"]/div[1]/input')))
            inputUUAA = driver.find_element(By.XPATH, '//*[@id="dropdown"]/div[1]/input')
            inputUUAA.send_keys("ether.co.apx.online")
            inputUUAA.send_keys(Keys.ENTER)
            estado = True
            while estado:
                try:
                    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div/div[2]')))
                    metrics = driver.find_element(By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div/div[2]') # Click metrics
                    metrics.click()
                    logging.info("  -> MENU de metricas")
                    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div[2]/div[1]/button[3]')))
                    fmetrics = driver.find_element(By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div[2]/div[1]/button[3]') # Click functional metrics
                    fmetrics.click()
                    logging.info("  -> MENU Funcional Metrics")
                    estado = False
                except:
                    driver.execute_script("location.reload();")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dropdown-btn-pill-box"]')))
            menu = driver.find_element(By.XPATH, '//*[@id="dropdown-btn-pill-box"]') # Click en today
            menu.click()
            #reset a los valores de tiempo en 00:00:00
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]')))
            yesterday = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]') # Click en yesterday
            yesterday.click()
            logging.info("  -> MENU de date range, dia anterior")
            while (datefrom != limite):  
                date_Temp= datefrom + timedelta(days=+1)
                if (date.today()+ timedelta(days=-1)) == datefrom:
                    logging.info("MENU ")
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dropdown-btn-pill-box"]')))
                    menu = driver.find_element(By.XPATH, '//*[@id="dropdown-btn-pill-box"]') # Click en today
                    menu.click()
                    
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]')))
                    yesterday = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]') # Click en yesterday
                    yesterday.click()
                    logging.info("Click en Yesterday")
                else:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'fromDate')))
                    fromDate1 = driver.find_element(By.ID, 'fromDate')
                    fromDate1.clear()
                    fromDate1.send_keys(datefrom.strftime('%d/%m/%Y')) # tomar fecha
                    fromDate1.send_keys(Keys.ENTER)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'toDate')))
                    toDate1 = driver.find_element(By.ID, 'toDate')
                    toDate1.clear()
                    toDate1.send_keys(date_Temp.strftime('%d/%m/%Y')) # tomar fecha
                    toDate1.send_keys(Keys.ENTER)
                    logging.info("  -> Asignando los datos de la consulta")
                intento = True
                valorM=0
                while intento:
                    try:
                        time.sleep(5)
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mode-view-pie"]/div/div[1]/div[3]')))
                        valorM = driver.find_element(By.XPATH, '//*[@id="mode-view-pie"]/div/div[1]/div[3]').get_attribute("title")
                        intento = False
                    except:
                        logging.info("\r        - Sleep Charging, retry", end=' ', flush=True)
                registro= {'datefrom': datefrom, 'valorMiles': valorM}
                logging.info("  -> Fecha: " + str(datefrom) + " Ejecuciones: " + str(valorM))
                executionSql(datefrom,valorM) 
                json_data.append(registro)
                datefrom = date_Temp
        else:
            logging.info("  -> Error se reelanzara ")
            return("  -> Error se reelanzara ")
    driver.close()
    driver.quit()
    time.sleep(10)
    return json_data

    
def executionSql(date, total):
    conn = conexion()
    cursor = conn.cursor()
    print(type(total))
    date = date.strftime('%Y-%m-%d')
    insert_stmt = (
        "INSERT INTO planbackend.executions(exec_fecha, exec_canal, exec_tx, exec_number, exec_mips_medio, exec_time_mid)"
        " VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE exec_number=%s, exec_mips_medio=%s, exec_time_mid=%s"
    )
    data = (date, 'ETHER', 'ATEN', total, '0', '0', total, '0', '0')
    #try:
    cursor.execute(insert_stmt, data)
    conn.commit()
    logging.info(cursor.rowcount, "record inserted")
    logging.info("\r    -->    OK: " +  " - " + str(date) + " - " + str(total) + "          ", end=' ', flush=True)
    #except: 
    #    logging.info(" ERROR: " +  "/" + " - " + str(date) + " - " + str(total) + "          ")
    #    conn.rollback()
    #finally:
    cursor.close() 
    conn.close()

    
def Atenea():
    logging.info("--- Inicio Atenea ---")
    local=True
    json_data = ejecucion(local)
    Sincronizar()
    logging.info("--- Fin Atenea ---")
    return json_data