import os
import time
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient import http as googleapiclient
from dotenv import load_dotenv


# Cargar las variables de entorno del archivo .env
load_dotenv()



def autenticar_google_drive():

    # Crear el objeto credentials a partir del archivo JSON
    credenciales = service_account.Credentials.from_service_account_info(
        {
        "type": os.getenv('TYPE'),
        "project_id": os.getenv('PROJECT_ID'),
        "private_key_id": os.getenv('PRIVATE_KEY_ID'),
        "private_key": os.getenv('PRIVATE_KEY'),
        "client_email": os.getenv('CLIENT_EMAIL'),
        "client_id": os.getenv('CLIENT_ID'),
        "auth_uri": os.getenv('AUTH_URI'),
        "token_uri": os.getenv('TOKEN_URI'),
        "auth_provider_x509_cert_url": os.getenv('AUTH_PROVIDER_X509_CERT_URL'),
        "client_x509_cert_url": os.getenv('CLIENT_X509_CERT_URL'),
        "universe_domain": os.getenv('UNIVERSE_DOMAIN')
        },
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    # Construir el servicio de Google Drive
    drive_service = build('drive', 'v3', credentials=credenciales)
    return drive_service

def descargar_archivos_de_google_drive():

    # Ejemplo de uso
    service = autenticar_google_drive()
    carpeta_id = obtener_id_carpeta()
    ruta_destino = os.getenv('RUTA_DESCARGA')

    # Obtener la lista de archivos de la carpeta en Google Drive
    response = service.files().list(
        q=f"'{carpeta_id}' in parents and trashed=false",
        fields="files(name, id)"
    ).execute()
    archivos = response.get('files', [])

    # Descargar los archivos a la ruta de destino
    for archivo in archivos:
        nombre_archivo = archivo['name']
        archivo_id = archivo['id']
        ruta_archivo = os.path.join(ruta_destino, nombre_archivo)
        request = service.files().get_media(fileId=archivo_id)
        fh = open(ruta_archivo, "wb")
        downloader = googleapiclient.MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Descargando archivo: {nombre_archivo} - {int(status.progress() * 100)}% completado")
        fh.close()
        print(f"Archivo {nombre_archivo} descargado correctamente.")

    print("Descarga de archivos completada.")

def subir_archivo_a_google_drive():

    # Ejemplo de uso
    service = autenticar_google_drive()
    carpeta_id = os.getenv('CARPETA_ID_CARGA')
    ruta_archivo = os.getenv('RUTA_ARCHICO')

    nombre_archivo = os.path.basename(ruta_archivo)
    archivos_existentes = service.files().list(q=f"name='{nombre_archivo}' and '{carpeta_id}' in parents").execute()
    if archivos_existentes.get('files'):
        archivo_existente = archivos_existentes['files'][0]
        archivo_id = archivo_existente['id']
        metadata = {'name': nombre_archivo}
        media = googleapiclient.MediaFileUpload(ruta_archivo, resumable=True)
        archivo_actualizado = service.files().update(fileId=archivo_id, body=metadata, media_body=media).execute()
        print(f"Archivo {nombre_archivo} actualizado correctamente")
    else:
        metadata = {'name': nombre_archivo, 'parents': [carpeta_id]}
        media = googleapiclient.MediaFileUpload(ruta_archivo, resumable=True)
        archivo_nuevo = service.files().create(body=metadata, media_body=media, fields='id').execute()
        print(f"Archivo {nombre_archivo} subido correctamente con ID: {archivo_nuevo['id']}")

def obtener_id_carpeta():

    # Ejemplo de uso
    service = autenticar_google_drive()
    nombre_carpeta = os.getenv('RUTA_DESCARGA')
    carpeta_padre_id= os.getenv('CARPETA_ID_CARGA')

    # Realizar la consulta para obtener el ID de la carpeta con el nombre dado
    response = service.files().list(q=f"name='{nombre_carpeta}' and mimeType='application/vnd.google-apps.folder' and '{carpeta_padre_id}' in parents",
                                    fields="files(id)").execute()
    carpetas = response.get('files', [])

    if carpetas:
        # Retornar el ID de la primera coincidencia encontrada
        return carpetas[0]['id']
    else:
        return None

def crear_o_reemplazar_carpeta():

    # Ejemplo de uso
    service = autenticar_google_drive()
    nombre_carpeta = os.getenv('RUTA_DESCARGA')
    carpeta_padre_id= os.getenv('CARPETA_ID_CARGA')

    # Verificar si ya existe una carpeta con el mismo nombre
    carpeta_id = obtener_id_carpeta()

    if carpeta_id:
        # La carpeta ya existe, se procede a eliminarla
        service.files().delete(fileId=carpeta_id).execute()
        print(f"Carpeta '{nombre_carpeta}' existente eliminada.")

    # Crear la nueva carpeta
    metadata = {
        'name': nombre_carpeta,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [carpeta_padre_id]
    }
    carpeta = service.files().create(body=metadata, fields='id').execute()
    print(f"Carpeta '{nombre_carpeta}' creada dentro de la carpeta padre con ID: {carpeta_padre_id}")



