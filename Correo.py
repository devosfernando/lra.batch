import imaplib
import email
from email.header import decode_header
import webbrowser
import os
from getpass import getpass

#irzsbvrvjyevapri
# Datos del usuario


def consultarCorreo(user,clave):
    username = user
    password = clave

    codverificacion="000000"
    # Crear conexión
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    # iniciar sesión
    imap.login(username, password)

    status, mensajes = imap.select("INBOX")
    # print(mensajes)
    # mensajes a recibir
    N = 3
    # cantidad total de correos
    mensajes = int(mensajes[0])

    for i in range(mensajes, mensajes - N, -1):
        # print(f"vamos por el mensaje: {i}")
    #     # Obtener el mensaje
        try:
            res, mensaje = imap.fetch(str(i), "(RFC822)")
        except:
            break
        for respuesta in mensaje:
            if isinstance(respuesta, tuple):
                # Obtener el contenido
                mensaje = email.message_from_bytes(respuesta[1])
                # decodificar el contenido
                subject = decode_header(mensaje["Subject"])[0][0]
                if isinstance(subject, bytes):
                    # convertir a string
                    subject = subject.decode()
                # de donde viene el correo
                from_ = mensaje.get("From")
                print("Subject:", subject)
                #print("De:",mensaje.get("De"))
                print("From:", from_)
                #print("Mensaje obtenido con exito")
                # si el correo es html
                if mensaje.is_multipart() and from_ == "Acceso Corporativo BBVA <nauthilus-bot@bbva.com>" :
                    # Recorrer las partes del correo
                    for part in mensaje.walk():
                        # Extraer el contenido
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            # el cuerpo del correo
                            body = part.get_payload(decode=True).decode()
                            #body=part.get_content_charset()
                            print("BODY--------------------------------------------")
                            print(body)
                            codverificacion = body[-6:]
                            print("CODIGO-----------------------------------------------")
                            print(codverificacion)
                            
                        except:
                            pass
                # if content_type == "text/html":
                #     # Abrir el html en el navegador
                #     if not os.path.isdir(subject):
                #         os.mkdir(subject)
                #     nombre_archivo = f"{subject}.html"
                #     ruta_archivo = os.path.join(subject, nombre_archivo)
                #     open(ruta_archivo, "w").write(body)
                #     # abrir el navegador
                #     webbrowser.open(ruta_archivo)
    #             print("********************************")
        if codverificacion != "000000":
            break
    imap.close()
    imap.logout()
    return codverificacion