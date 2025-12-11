"""
Backend personalizado de email para Resend usando su API REST.

Resend no tiene SMTP disponible o Railway lo bloquea, así que usamos su API REST directamente.
"""

import json
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import os

logger = logging.getLogger(__name__)


class ResendBackend(BaseEmailBackend):
    """
    Backend de email para Resend usando su API REST.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        # Leer y limpiar la API key (quitar espacios y comillas)
        raw_key = os.getenv('RESEND_API_KEY', '')
        self.api_key = raw_key.strip().strip('"').strip("'")
        self.api_url = 'https://api.resend.com/emails'
        
        # Validar formato de API key (debe empezar con "re_")
        if self.api_key and not self.api_key.startswith('re_'):
            logger.warning(f"⚠️ RESEND_API_KEY no tiene el formato esperado (debe empezar con 're_')")
            logger.warning(f"   Longitud: {len(self.api_key)} caracteres")
            logger.warning(f"   Primeros 5 caracteres: {self.api_key[:5] if len(self.api_key) >= 5 else 'N/A'}")
        
        # Logging de diagnóstico (sin mostrar la key completa)
        if self.api_key:
            masked_key = f"{self.api_key[:5]}...{self.api_key[-4:]}" if len(self.api_key) > 9 else "***"
            logger.info(f"🔑 Resend API Key detectada: {masked_key} (longitud: {len(self.api_key)})")
        else:
            logger.error("❌ RESEND_API_KEY no está configurada o está vacía")
    
    def send_messages(self, email_messages):
        """
        Envía uno o más mensajes de email usando la API REST de Resend.
        """
        if not email_messages:
            return 0
        
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY no está configurado")
            logger.error("❌ RESEND_API_KEY no está configurado")
            return 0
        
        num_sent = 0
        
        for message in email_messages:
            try:
                # Extraer información del mensaje
                from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
                to_emails = message.to
                subject = message.subject
                body = message.body
                
                # Si el mensaje tiene alternativas HTML, usar la primera
                html_content = None
                if hasattr(message, 'alternatives') and message.alternatives:
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            html_content = content
                            break
                
                # Preparar payload para Resend API
                payload = {
                    'from': from_email,
                    'to': to_emails,
                    'subject': subject,
                }
                
                # Agregar contenido (HTML tiene prioridad)
                if html_content:
                    payload['html'] = html_content
                    payload['text'] = body  # Texto plano como fallback
                else:
                    payload['text'] = body
                
                # Enviar request a Resend API
                import urllib.request
                import urllib.parse
                
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    self.api_url,
                    data=data,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json',
                    }
                )
                
                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        response_data = json.loads(response.read().decode('utf-8'))
                        if response.status == 200:
                            logger.info(f"✅ Email enviado exitosamente a {to_emails} (Resend ID: {response_data.get('id', 'N/A')})")
                            num_sent += 1
                        else:
                            error_msg = response_data.get('message', 'Error desconocido')
                            logger.error(f"❌ Error enviando email a {to_emails}: {error_msg}")
                            if not self.fail_silently:
                                raise Exception(f"Resend API error: {error_msg}")
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode('utf-8')
                    try:
                        error_data = json.loads(error_body)
                        error_msg = error_data.get('message', str(e))
                    except:
                        error_msg = str(e)
                    
                    # Manejar error específico de API key inválida
                    if 'api key is invalid' in error_msg.lower() or 'invalid api key' in error_msg.lower():
                        logger.error(f"❌ Resend API Key inválida o incorrecta")
                        logger.error(f"   Verifica en Railway que RESEND_API_KEY esté configurada correctamente:")
                        logger.error(f"   1. Ve a Railway Dashboard → Tu proyecto → Variables")
                        logger.error(f"   2. Busca RESEND_API_KEY")
                        logger.error(f"   3. Asegúrate de que:")
                        logger.error(f"      - No tenga comillas alrededor (debe ser: re_xxxxx, NO: \"re_xxxxx\")")
                        logger.error(f"      - No tenga espacios al inicio o final")
                        logger.error(f"      - Empiece con 're_'")
                        logger.error(f"   4. Obtén una nueva API key en: https://resend.com/api-keys")
                        logger.error(f"   5. Copia la key completa y pégala en Railway")
                        if not self.fail_silently:
                            raise Exception(f"Resend API HTTP error: {error_msg}")
                    # Manejar error específico de Resend sobre dominio no verificado
                    elif 'only send testing emails to your own email address' in error_msg.lower():
                        logger.error(f"❌ Resend: Solo puedes enviar emails de prueba a tu propia dirección.")
                        logger.error(f"   Para enviar a otros destinatarios, verifica tu dominio en Resend:")
                        logger.error(f"   1. Ve a: https://resend.com/domains")
                        logger.error(f"   2. Click 'Add Domain' y agrega 'teomanager.com'")
                        logger.error(f"   3. Agrega los registros DNS en Cloudflare")
                        logger.error(f"   4. Una vez verificado, actualiza DEFAULT_FROM_EMAIL en Railway")
                        logger.error(f"   5. Temporalmente, solo puedes enviar a: ariadna.pamela01@gmail.com")
                        # No lanzar excepción para que la app no falle, pero loguear el problema
                        if not self.fail_silently:
                            logger.warning(f"⚠️ Email no enviado a {to_emails} - Dominio no verificado en Resend")
                    else:
                        logger.error(f"❌ Error HTTP enviando email a {to_emails}: {error_msg}")
                        logger.error(f"   Código HTTP: {e.code}")
                        logger.error(f"   Respuesta completa: {error_body[:200]}")
                        if not self.fail_silently:
                            raise Exception(f"Resend API HTTP error: {error_msg}")
                except Exception as e:
                    logger.error(f"❌ Error enviando email a {to_emails}: {str(e)}", exc_info=True)
                    if not self.fail_silently:
                        raise
                        
            except Exception as e:
                logger.error(f"❌ Error procesando mensaje de email: {str(e)}", exc_info=True)
                if not self.fail_silently:
                    raise
        
        return num_sent

