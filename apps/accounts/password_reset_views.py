"""
Vistas personalizadas para restablecimiento de contraseña.

Estas vistas extienden las vistas de Django para hacer el envío de correos
de forma asíncrona y evitar timeouts en producción.
"""

from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
import threading
import logging

logger = logging.getLogger(__name__)


def send_password_reset_email_async(user, request):
    """
    Envía el correo de restablecimiento de contraseña de forma asíncrona.
    
    Args:
        user: Usuario al que enviar el correo
        request: Request object para obtener el dominio
    """
    def _send_email():
        try:
            # Obtener el dominio del sitio
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
            
            # Asegurar que el dominio tenga protocolo
            if not domain.startswith('http'):
                protocol = 'https' if (settings.IS_PRODUCTION or settings.IS_STAGING) else 'http'
                base_url = f'{protocol}://{domain}'
            else:
                base_url = domain
            
            # Generar token y uid
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Construir URL de reset
            from django.urls import reverse
            reset_url = f"{base_url}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
            
            # Renderizar template de email
            subject = f'Restablecimiento de contraseña en {site_name}'
            message = render_to_string('registration/password_reset_email.html', {
                'user': user,
                'domain': domain,
                'protocol': 'https' if (settings.IS_PRODUCTION or settings.IS_STAGING) else 'http',
                'uid': uid,
                'token': token,
                'site_name': site_name,
            })
            
            # Enviar email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            
            logger.info(f"Email de restablecimiento de contraseña enviado a {user.email}")
            
        except Exception as e:
            logger.error(f"Error enviando email de restablecimiento a {user.email}: {str(e)}")
    
    # Enviar en un thread separado
    try:
        thread = threading.Thread(target=_send_email)
        thread.daemon = True
        thread.start()
    except Exception as e:
        logger.error(f"Error creando thread para email de restablecimiento: {str(e)}")
        # Fallback: intentar enviar de forma síncrona
        try:
            _send_email()
        except Exception as sync_error:
            logger.error(f"Error enviando email de forma síncrona: {str(sync_error)}")


class AsyncPasswordResetForm(PasswordResetForm):
    """
    Formulario personalizado que envía emails de restablecimiento de forma asíncrona.
    """
    
    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Sobrescribe save para enviar emails de forma asíncrona.
        """
        email = self.cleaned_data["email"]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Buscar usuarios activos con ese email
        users = User.objects.filter(email__iexact=email, is_active=True)
        
        # Enviar email a cada usuario de forma asíncrona
        for user in users:
            send_password_reset_email_async(user, request)
        
        # Retornar la lista de usuarios (requerido por la vista)
        return users


class PasswordResetView(auth_views.PasswordResetView):
    """
    Vista personalizada de restablecimiento de contraseña que envía emails de forma asíncrona.
    """
    form_class = AsyncPasswordResetForm

