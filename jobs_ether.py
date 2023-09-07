import os
import sys
import time
import warnings
import Correo
import requests
import datetime
import json
import filter_json
import fluent_driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# Obtener env de entorno
from dotenv import load_dotenv
load_dotenv()
# Seteo timeout global
selenium_timeout = 5
pageSize = 100
timeWait= 2
folder_data="info/"
xpath_google = '//*[@id="view_container"]/div/div/div[2]/div/div[2]/div/div[1]/div/div/button/span'
xpath_ether = '//*[@id="ext-element-48"]'
class AccessException(Exception):
    def __init__(self, message):
        super().__init__(message)

# Revisa URL despues de usuario/contraseña para validar siguiente accion
def validar_caso(driver):
  message = ''
  timeout = selenium_timeout
  url = driver.current_url
  if 'google.com' in url:
    print('- Google access')
    [driver, error_code] = verificar(driver)
    if error_code == -1:
      message="Google page error"
  elif "platform.bbva.com" in url:
    print('- Second authentication factor')
    [driver, error_code] = verificar_segundo_factor(driver)
    if error_code == -1:
      message="Second factor error"
  elif "bbva-ether-console" in url:
    print('- Ether direct access')
    time.sleep(timeout)
  return [driver,error_code,message]  

# Verificación de tipo de autenticación QR o OTP
def verificar_segundo_factor(driver):
   timeout = selenium_timeout
   error_code = 0
   #if ("Está intentando acceder a los sistemas de BBVA" in driver.page_source or
   #    "You are trying to access BBVA systems" in driver.page_source):
   if ("MySecurity" in driver.page_source or
       "Captura este codigo QR" in driver.page_source):
      try:
         element_bbva=EC.presence_of_element_located((By.XPATH,"//label"))
         WebDriverWait(driver, timeout).until(element_bbva)
         button = driver.find_element(By.XPATH,"//label")
         action = ActionChains(driver)
         action.move_to_element(button).click().perform()
      except Exception as e:
         print("Error click in other option: " + str(e))
         error_code = -1
         return [driver,error_code]
      try:
        element_bbva=EC.presence_of_element_located((By.ID, 'presentMail'))
        WebDriverWait(driver, timeout).until(element_bbva)
      except TimeoutException as e:
        print("Error reading other option QR access " + str(e))
        error_code = -1
        return [driver,error_code]
   # Caso de que sea acceso sin biometria
   print('- OTP check')
   [driver, error_code] = segundo_factor(driver)
   return [driver, error_code]

#Operaciones para validar OTP   
def segundo_factor(driver):
  timeout = selenium_timeout
  method1='segundo_factor'
  error_code = 0
  if ("Está intentando acceder a los sistemas de BBVA" in driver.page_source or
      "You are trying to access BBVA systems" in driver.page_source):
      #print(driver.find_element(By.TAG_NAME,'body').text)
      radio_mail = driver.find_element(By.ID, 'presentMail')
      radio_mail.click()
      btn_enviar= driver.find_element(By.NAME,'_eventId_proceed')
      btn_enviar.click()
      try:
        element_bbva=EC.presence_of_element_located((By.ID, 'otp_mail'))
        WebDriverWait(driver, timeout).until(element_bbva)
      except TimeoutException as e:
        print("Timed out waiting for page to load " + format(str(e)))
        error_code = -1
        return [driver,error_code]         
      except Exception as e:
        print("Other exception waiting for page to load " + format(str(e)))
        error_code = -1
        return [driver,error_code]
      time.sleep(timeWait * timeout)
      cod_verificacion = Correo.consultarCorreo(os.getenv("CORREO"),os.getenv("IMAP"))
      otp_mail = driver.find_element(By.ID, 'otp_mail')
      otp_mail.send_keys(cod_verificacion)
      otp_mail.send_keys(Keys.RETURN)
      time.sleep(timeout)
      # Validar google
      try:
        element_body: EC
        element_body = lambda driver: driver.find_element(By.XPATH,xpath_google)or driver.find_element(By.XPATH,xpath_ether)
        WebDriverWait(driver, timeout).until(element_body)
      except TimeoutException as e:
        print("Timed out waiting for page to load " + method1 + format(str(e)))
        error_code = -1
        return [driver,error_code]         
      except Exception as e:
        print("Other exception for page to load " + method1 + format(str(e)))
        error_code = -1
        return [driver,error_code]
      if "google.com" in driver.current_url:
         [driver,error_code] = verificar(driver)
      elif "platform.bbva.com" in driver.current_url:
        print (" - Second factor error \n")
        error_code = -1
        print(str(driver.find_element(By.TAG_NAME,'body').text))
        return [driver,error_code]
      return [driver,error_code]

# Verificar cuenta en google
def verificar(driver):
   button = driver.find_element(By.XPATH,xpath_google)
   button.click()
   return [driver,0]

# Cierra selenium webdriver   
def cerrar_driver(driver):
   driver.close()
   driver.quit()
   print('- Closed selenium WebDriver')

# Obtiene jobs de batch catalog de ether
def obtener_jobs(ether_cookies):
  page = 0 
  maxpage = sys.maxsize
  print('- Begin assembling REST request')
  print('- Default pageSize for request: '+ str(pageSize))
  etherurl='https://bbva-ether-console-front.appspot.com/c/s/blue-catalog/__api/batchcatalog/programs'
  s = requests.Session()
  domain1 = ''
  tempstring=''
  error_ether = 0
  json_string = '['
  for cookie in ether_cookies:
    key=''
    value1=''
    if('' in domain1):domain1 = cookie['domain']
    key = cookie['name']
    value1 = cookie['value']
    cookie_ob = requests.cookies.create_cookie(domain=domain1,name=key,value=value1)
    s.cookies.set_cookie(cookie_ob)
  #Se procede a realizar la consulta por servicio REST con las cookies obtenidas de ether
  while page < maxpage:
    try:
      now = int(datetime.datetime.now().timestamp())
      query = {'page': page , 'pageSize' : pageSize, 'ts': str(now) }
      response = s.get(etherurl, params=query)
      response.raise_for_status()
      datatemp=json.loads(response.text)
      if maxpage == sys.maxsize:
         print('- Total pages ether request: ' + str(datatemp['pagination']['totalPages']))
         maxpage = datatemp['pagination']['totalPages']
         print('- Total jobs registered in ether Batch Catalog: '+ str(datatemp['pagination']['totalElements']))
      page +=1
      tempstring = json.dumps(datatemp['data'],indent=2,ensure_ascii=False).replace('[','',1)[:-1]
      if page == maxpage:
        tempstring +=']'
      else:
        tempstring +=', \n'
      json_string += tempstring
    except requests.Timeout as error:
       print('Timeout error: '+str(error))
       error_ether = -1
       break
    except requests.exceptions.HTTPError as error:
       print('Http error: '+str(error))
       error_ether = -1
       break
    except Exception as error:
       print('General exception: '+str(error))
       error_ether = -1
       break
  write_file(json_string,error_ether)

def write_file(json_string,error_ether):
  if error_ether == 0:
    if not os.path.exists(folder_data):
    # If it doesn't exist, create it
      os.makedirs(folder_data)
    file_output = folder_data + 'data_ether.json'
    with open(file_output, 'w') as outfile:
      outfile.write(str(json_string))
    print('- Full data generated in file ' + file_output)
    data_simplified = folder_data + 'data_simplified.txt'
    filter_json.filtrar_ether(file_output,data_simplified)
    print('- Data generated for global and Colombia in file ' + data_simplified)
  else:
    print('- Error generating ether data') 
    
# Configuración selenium remoto
def ejecucion(url):
    print("- Run Selenium IDE")
    warnings.simplefilter("ignore")
    options = webdriver.ChromeOptions()
    options.add_argument('log-level=0')
    options.add_experimental_option('excludeSwitches', ['enable-automation','enable-logging'])
    options.add_argument("--disable-blink-features=AutomationControlled")        
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--remote-debugging-port=9222')
    prefs = {"profile.default_content_setting_values.notifications" : 2}    
    options.add_experimental_option("prefs",prefs)
    options.add_argument("--window-size=1382,744")
    # Seteo conexión servidor selenium
    try:
      host='http://'+os.getenv("HOST_SELENIUM")+':4444/wd/hub'
      driver = webdriver.Remote(host,options=options) 
      print("- Selenium remote start connection") 
    except WebDriverException as e:
        print("Error al ejecutar el controlador de Chrome: {}".format(str(e)))
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get('chrome://version')
        version_element = driver.find_element_by_xpath('/html/body')
        version_text = version_element.text
        version = version_text.split('\n')[0].split(' ')[2]
        print('Versión de Google Chrome:', version)
        return
    except Exception as e:
        print("Error executing Chrome driver: {}".format(str(e)))
        return
    ether_cookies = login_process(driver,url)
    return ether_cookies
# Configuración chromedriver(ejecutable grafico)
def login_ether(url):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach",True)
    options.add_argument('--no-proxy-server')
    prefs = {"profile.default_content_setting_values.notifications" : 2}    
    options.add_experimental_option("prefs",prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              options=options)
    ether_cookies = login_process(driver,url)
    return ether_cookies

#proceso login
def login_process(driver,url):
    timeout = selenium_timeout
    error_code = 0
    method1 = 'login_process'
    print("- Begin login process")
    print("- Timeout used: "+ str(timeout)+ " seconds")
    print('- Additional time wait multiplier for second factor: '+ str(timeWait))
    try:    
      driver.get(url)
      driver.implicitly_wait(20)
    except Exception as e:
       print('Failing accessing ether url: ' + format(str(e)))
       return None
    try:
      pageloaded = EC.presence_of_element_located((By.ID,'username'))
      WebDriverWait(driver, timeout).until(pageloaded)
    except Exception as e:
      print('Timed out waiting for page to load ' + method1 + ' 1 '+ format(str(e)))
      return None
    if 'platform.bbva.com' in  driver.current_url:
      print("- BBVA login")
      usuario = driver.find_element(By.ID,'username')
      contrasenia = driver.find_element(By.ID,'password')
      usuario.clear()
      usuario.send_keys(os.getenv("USUARIO"))
      contrasenia.clear()
      contrasenia.send_keys(os.getenv("USUARIO_PS"))
      contrasenia.send_keys(Keys.RETURN)
      # Se genera un sleep para el caso de acceso por google
      time.sleep(timeout)
      '''
      Caso 1: acceso directo a ether
      Caso 2: acceso a ether x validacion de google
      Caso 3: acceso para 2 factor de autenticación
      '''
      try:
        element_body: EC
        element_body = lambda driver: driver.find_element(By.XPATH,
                            '//*[@id="form"]/div[3]/label') or driver.find_element(By.XPATH,xpath_google)or driver.find_element(By.XPATH,xpath_ether)
        WebDriverWait(driver, timeout).until(element_body)
        [driver,error_code,message]=validar_caso(driver)
        if error_code == -1:
           raise AccessException(message)
      except TimeoutException as e:
        print('Timed out waiting for page to load '+ method1 + ' 2 '+ format(str(e)))
        print("Current url: " + str(driver.current_url))
        print(str(driver.find_element(By.TAG_NAME,'body').text))
        cerrar_driver(driver)
        return None
      except Exception as e:
        print('Exception for page to load '+ method1 + ' 2 '+ format(str(e)))
        print("Current url: " + str(driver.current_url))
        print(str(driver.find_element(By.TAG_NAME,'body').text))
        cerrar_driver(driver)
        return None
      time.sleep(timeout)
      ether_cookies= driver.get_cookies()
      print('- Retrieved session cookies from ether')
      #Fin proceso
      cerrar_driver(driver)
      return ether_cookies

def ether_access(opc,url):
  global selenium_timeout
  global timeWait
  if opc is None:
     opc = '1'
  if len(sys.argv) > 2:
      timeWait = 1
  if opc == '1':
    selenium_timeout = 2
    ether_cookies = ejecucion(url)
  else:
    ether_cookies = login_ether(url)   
  return ether_cookies

def main(opc):
    now = datetime.datetime.now()
    url="https://bbva-ether-console-front.appspot.com/"
    print('- Time Started: ' + str(now))
    ether_cookies = ether_access(opc,url)
    # Generación json con información ether
    if ether_cookies is not None:
      print('- Ether cookies generated')
      obtener_jobs(ether_cookies)
    now = datetime.datetime.now()
    print('- Time Ended: ' + str(now))
    print("- Process end")
    time.sleep(2)

if __name__=="__main__":
    os.system('cls')
    opc = '1'
    if len(sys.argv) == 2:
       opc=str(sys.argv[1])
    print(' _       ____       _        _____   _     _                   ')
    print('| |     |  _ \     / \      | ____| | |_  | |__     ___   _ __ ')
    print('| |     | |_) |   / _ \     |  _|   | __| | \'_ \   / _ \ | \'__|')
    print('| |___  |  _ <   / ___ \    | |___  | |_  | | | | |  __/ | |   ')
    print('|_____| |_| \_\ /_/   \_\   |_____|  \__| |_| |_|  \___| |_|   ')
    print('                                                               ')
    print('')
    main(opc)

