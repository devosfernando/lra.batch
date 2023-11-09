# -*- coding: utf-8 -*-
# 
import email
import imaplib
import logging
from email.header import decode_header


def consultarCorreo(username,password):
    logging.info("   --- Conection Correo ---")
    logging.info("  -> Accediendo via IMAP al correo: " + str(username))
    codverificacion="000000"
    # Crear conexión
    imap = imaplib.IMAP4_SSL("imap.gmail.com")

    # iniciar sesión
    imap.login(username, password)
    logging.info("  -> Login Completado: " + str(username))

    status, mensajes = imap.select("INBOX")
    # mensajes a recibir
    N = 3
    # cantidad total de correos
    mensajes = int(mensajes[0])

    for i in range(mensajes, mensajes - N, -1):
        # Obtener el mensaje
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
                logging.info("  ->    Subject:" + str(subject))
                #print("De:",mensaje.get("De"))
                logging.info("  ->    From:" + str(from_))
                #print("Mensaje obtenido con exito"))
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
                            logging.info("  ->     Body: " + str(body))
                            codverificacion = body[-6:]
                            logging.info("  ->     Codigo: " + str(codverificacion))                            
                        except:
                            pass
        if codverificacion != "000000":
            break
    imap.close()
    imap.logout()
    return codverificacion