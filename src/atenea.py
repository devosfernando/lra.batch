import os
import time
import warnings
import src.lib.Correo
import src.lib.sincronizar
import mysql.connector
import sys
from datetime import datetime
from datetime import date
from datetime import timedelta
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from dotenv import load_dotenv

def ejecucion():
        # Obtener env de entorno
        load_dotenv()
        print("  -      Run Selenium IDE")
        warnings.simplefilter("ignore")
        options = webdriver.ChromeOptions()
        options.add_argument('log-level=0') #INFO = 0, WARNING = 1, LOG_ERROR = 2, LOG_FATAL = 3.
        options.add_experimental_option('excludeSwitches', ['enable-automation','enable-logging'])
        options.add_argument("--disable-blink-features=AutomationControlled")        
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--remote-debugging-port=9222')
        prefs = {"profile.default_content_setting_values.notifications" : 2}    
        options.add_experimental_option("prefs",prefs)
        options.add_argument("--window-size=1382,744")
        errordriver=False
        
        try:
          host='http://'+os.getenv("HOST_SELENIUM")+':4444/wd/hub'
          driver = webdriver.Remote(host,options=options) 
          print("conexión driver") 
        except WebDriverException as e:
            errordriver=True
            print("Error al ejecutar el controlador de Chrome: {}".format(str(e)))
        
        if errordriver: 
            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get('chrome://version')
            version_element = driver.find_element_by_xpath('/html/body')
            version_text = version_element.text
            version = version_text.split('\n')[0].split(' ')[2]
            print('Versión de Google Chrome:', version)
       
        #carga Datos 
        datos=CargaDatos()
        #Consultar dias pendientes en atenea
        dateSql = selectSql()
        print("dateSql:",str(dateSql))
        date_sql = datetime.strptime(str(dateSql), "(datetime.date(%Y, %m, %d),)").date()
        limite = date.today()
            
        #Actualizar desde alguna fecha
        if len(sys.argv) == 3:
            fecha_inicio = sys.argv[1] #formato "17/02/2023"
            date_limite = sys.argv[2] #formato "19/02/2023"
            #Actualizar hasta esta fecha Limite
            date_sql = datetime.strptime(fecha_inicio,"%d/%m/%Y").date()
            limite= datetime.strptime(date_limite,"%d/%m/%Y").date()
        else:
            print ('No hay argumentos')
        
        print("Date Sql", date_sql)
        today = date.today()
        print("Today date is: ", today)
        numdays = (today - date_sql).days - 1
        print("Number days pendientes: ", numdays )
        
        #Reprocese los ultimos 2 dias
        if (numdays!=0 and numdays < 3):
            date_sql = today + timedelta(days=-3)
            
        datefrom = date_sql + timedelta(days=1)
        print("datefrom ", datefrom )
        dateTo = datefrom + timedelta(days=1)
        print("dateTo ", dateTo )
        cont = 0
       
        if (numdays>0):   
            time.sleep(20)
            print("- Get data user OK")        
            driver.get("https://atenea.live-02.platform.bbva.com/public")
            driver.implicitly_wait(60)
            time.sleep(10)
            print("- login")
            
            myInput = driver.find_element(By.TAG_NAME, 'input')
            myInput.click()
            myInput.send_keys(str(datos[0]).replace("\n",""))
            time.sleep(1)
            myInput2 = driver.find_element(By.ID, 'password')
            myInput2.send_keys(str(datos[1]).replace("\n",""))
            time.sleep(3)
            print("- Click en Aceptar")
            driver.find_element(By.XPATH, '//*[@id="loginForm"]/div[2]/button[1]').click()
            time.sleep(5)
            
            if ("Está intentando acceder a los sistemas de BBVA" in driver.page_source or
                    "You are trying to access BBVA systems" in driver.page_source):
                
                print("- Inicia pantalla de correo")
                mySelect = driver.find_element(By.ID, 'presentMail') # Click para seleccionar correo
                mySelect.click()
                mybtnEnviar = driver.find_element(By.NAME, '_eventId_proceed') # Click para enviar clave
                print(type(mybtnEnviar))
                mybtnEnviar.click()
                print("- Click en recibir clave de correo")
                textClave = driver.find_element(By.ID, 'otp_mail')# Click para colocar clave
                textClave.click()
                time.sleep(10) #agregar llamado de la clase correo y colocar texto
                print(datos[0])
                print(datos[2])
                codigoVerificacion = Correo.consultarCorreo(datos[2],datos[3])
                print("codigoVerificacion:"+codigoVerificacion)
                print("- Click para validar")
                btnValidar = driver.find_element(By.ID, 'otp_mail')# Click para colocar clave
                btnValidar.send_keys(codigoVerificacion)
                mybtnEnviar = driver.find_element(By.NAME, '_eventId_proceed') # Click para enviar clave
                mybtnEnviar.click()
            
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "btn-important")))
                mybtn = driver.find_element(By.CLASS_NAME, 'btn-important')# Click en acceptar
                mybtn.click()
                
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "btn-realease-notes-close")))
                mybtn = driver.find_element(By.CLASS_NAME, 'btn-realease-notes-close') # Click para cerrar Release note
                mybtn.click()

                print("MENU")
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/application-menu/dropdown/div/button/label/span[2]')))
                mybtn = driver.find_element(By.XPATH, '/html/body/div[1]/application-menu/dropdown/div/button/label/span[2]') # Click para seleccionar metrics
                mybtn.click()
                
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dropdown"]/div[1]/input')))
                inputUUAA = driver.find_element(By.XPATH, '//*[@id="dropdown"]/div[1]/input')
                inputUUAA.send_keys("ether.co.apx.online")
                inputUUAA.send_keys(Keys.ENTER)

                print("METRICS")
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div/div[2]')))
                metrics = driver.find_element(By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div/div[2]') # Click metrics
                metrics.click()

                print("FUNCTIONAL METRICS")
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div[2]/div[1]/button[2]')))
                fmetrics = driver.find_element(By.XPATH, '//*[@id="menu-nav-bar"]/div[1]/div[2]/div[1]/button[2]') # Click functional metrics
                fmetrics.click()

                print("MENU ")
                WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dropdown-btn-pill-box"]')))
                menu = driver.find_element(By.XPATH, '//*[@id="dropdown-btn-pill-box"]') # Click en today
                menu.click()

                #reset a los valores de tiempo en 00:00:00
                print("RESET ")
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]')))
                yesterday = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]') # Click en yesterday
                yesterday.click()
                time.sleep(80)  
            
                valorMiles=0
                while (datefrom != limite):
                    print("Date from", datefrom)                
                    print("Date to", dateTo)
                    valorAnterior=valorMiles
                    
                    if (date.today()+ timedelta(days=-1)) == datefrom:
                        print("MENU ")
                        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dropdown-btn-pill-box"]')))
                        menu = driver.find_element(By.XPATH, '//*[@id="dropdown-btn-pill-box"]') # Click en today
                        menu.click()
                        
                        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]')))
                        yesterday = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div[7]/div[1]/dashboard-filter/div/div[1]/div/div/div/ul/li[4]') # Click en yesterday
                        yesterday.click()
                        print("Click en Yesterday")
                    else:
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'fromDate')))
                        fromDate1 = driver.find_element(By.ID, 'fromDate')
                        fromDate1.clear()
                        time.sleep(5)
                        fromDate1.send_keys(datefrom.strftime('%m/%d/%Y')) # tomar fecha
                        fromDate1.send_keys(Keys.ENTER)
                        
                        time.sleep(5)
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'toDate')))
                        toDate1 = driver.find_element(By.ID, 'toDate')
                        toDate1.clear()
                        time.sleep(5)
                        toDate1.send_keys(dateTo.strftime('%m/%d/%Y')) # tomar fecha
                        toDate1.send_keys(Keys.ENTER)
                        print("Set from Date and toDate")
                        
                    time.sleep(100)
                    intento = True
                    valorMiles=0
                    while intento:
                            try:
                                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mode-view-pie"]/div/div[1]/div[3]')))
                                valorM = driver.find_element(By.XPATH, '//*[@id="mode-view-pie"]/div/div[1]/div[3]').get_attribute("title")
                                if len(valorM) > 1:
                                    print(str(valorM))
                                    valorM = valorM.replace(',','').replace('M','')
                                    valorMiles = int(valorM)
                                    if valorAnterior != valorMiles:
                                        intento = False
                            except:
                                print("\r        - Sleep Charging, retry", end=' ', flush=True)

                    print("valorMiles ", valorMiles)
                    print("datefrom ", datefrom)
                    print("Antes de insertar en bd ")
                    executionSql(datefrom,valorMiles)                
                    print("-------------------------------------------------------------------------")    
                    #finalizar 
                    cont = cont+1
                    datefrom = datefrom+timedelta(days=1)
                    dateTo = datefrom+timedelta(days=1)
            
            else:
                print("Error se reelanzara ")
                time.sleep(100)
                
        driver.close()
        driver.quit()
        time.sleep(10)
        sincronizar.main()

def conexion():
    print ("---Conection Database---")
    db = mysql.connector.connect(host=os.getenv("HOST"),
                                    port=os.getenv("PORT_MYSQL"),
                                    user=os.getenv("USER_MYSQL"), 
                                    password=os.getenv("PASSWORD_MYSQL"), 
                                    database=os.getenv("DATABASE"),
                                    auth_plugin=os.getenv("ATH_MYSQL"))
    return db  

def selectSql():
    conn = conexion()
    cursor = conn.cursor()
    fecha = ""
    select_stmt =( "SELECT max(exec_fecha) FROM planbackend.executions WHERE exec_canal='ETHER' AND exec_tx='ATEN' ")
    try:
        cursor.execute(select_stmt)
        fecha = cursor.fetchone()
        print(fecha)
    except: 
        print(" ERROR: SELECT ")  
    finally:
        cursor.close() 
        conn.close()
    return fecha
    
def executionSql( date, total):
    conn = conexion()
    cursor = conn.cursor()
    print(date)
    print(total)
    insert_stmt = (
        "INSERT INTO planbackend.executions(exec_fecha, exec_canal, exec_tx, exec_number, exec_mips_medio, exec_time_mid)"
        " VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE exec_number=%s, exec_mips_medio=%s, exec_time_mid=%s"
    )
    data = (date, 'ETHER', 'ATEN', total, '0', '0', total, '0', '0')
    try:
        cursor.execute(insert_stmt, data)
        conn.commit()
        print(cursor.rowcount, "record inserted")
        print("\r    -->    OK: " +  " - " + str(date) + " - " + str(total) + "          ", end=' ', flush=True)
    except: 
        print(" ERROR: " +  "/" + " - " + str(date) + " - " + str(total) + "          ")
        conn.rollback()
    finally:
        cursor.close() 
        conn.close()


def CargaDatos():
    user = os.getenv("USUARIO")
    psswrd = os.getenv("USUARIO_PS")
    correo = os.getenv("CORREO")
    copssd = os.getenv("IMAP")
    return user, psswrd, correo, copssd


def main():
    print(" _____        _                  _                        ")
    print("|  __ \      | |            /\  | |                       ")
    print("| |  | | __ _| |_ __ _     /  \ | |_ ___ _ __   ___  __ _ ")
    print("| |  | |/ _` | __/ _` |   / /\ \| __/ _ \ '_ \ / _ \/ _` |")
    print("| |__| | (_| | || (_| |  / ____ \ ||  __/ | | |  __/ (_| |")
    print("|_____/ \__,_|\__\__,_| /_/    \_\__\___|_| |_|\___|\__,_|")
    print("                                                          ")
    print("")    
    ejecucion()
    print("- Process end succesfully")

    
def Atenea():
    print(" _____        _                  _                        ")
    print("|  __ \      | |            /\  | |                       ")
    print("| |  | | __ _| |_ __ _     /  \ | |_ ___ _ __   ___  __ _ ")
    print("| |  | |/ _` | __/ _` |   / /\ \| __/ _ \ '_ \ / _ \/ _` |")
    print("| |__| | (_| | || (_| |  / ____ \ ||  __/ | | |  __/ (_| |")
    print("|_____/ \__,_|\__\__,_| /_/    \_\__\___|_| |_|\___|\__,_|")
    print("                                                          ")
    print("")    
    ejecucion()
    print("- Process end succesfully")