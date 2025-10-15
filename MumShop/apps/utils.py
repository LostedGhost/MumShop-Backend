from django.http import JsonResponse
from apps.models import User, RefreshToken
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.config import CODE_VALIDITY_MINUTES

def is_logged_in(view_func):
    def wrapper(request, *args, **kwargs):
        token = request.headers.get('Authorization', None)
        token = token.split(' ')[1] if token and ' ' in token else token
        if token:
            try:
                user_connect = RefreshToken.objects.get(token=token)
                if user_connect.user.is_blocked:
                    return JsonResponse({'error': 'Utilisateur blocké'}, status=403)
                request.user = user_connect.user
                return view_func(request, *args, **kwargs)
            except RefreshToken.DoesNotExist:
                return JsonResponse({'error': 'Token invalide'}, status=401)
        else:
            return JsonResponse({'error': 'Aucun utilisateur connecté'}, status=401)
    return wrapper

def is_admin(view_func):
    @is_logged_in
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'error': 'Cette action requiert un administrateur'}, status=403)
    return wrapper

def is_seller(view_func):
    @is_logged_in
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.role == 'seller':
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'error': 'Cette action requiert la commerçante'}, status=403)
    return wrapper

def is_moderator(view_func):
    @is_logged_in
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.role == 'moderator':
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'error': 'Cette action requiert un modérateur'}, status=403)
    return wrapper

def is_customer(view_func):
    @is_logged_in
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.role == 'customer':
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'error': 'Cette action est réservée aux clients'}, status=403)
    return wrapper

def is_delivery(view_func):
    @is_logged_in
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.role == 'delivery':
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'error': 'Cette action requiert un livreur'}, status=403)
    return wrapper

def is_not_customer(view_func):
    @is_logged_in
    def wrapper(request, *args, **kwargs):
        if hasattr(request, 'user') and request.user.role != 'customer':
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'error': 'Cette action concerne tout utilisateur qui n\'est pas un client'}, status=403)
    return wrapper

def send_verify_account_mail(user, code):
    subject = "Vérification de compte"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]
    
    text_content = f"Votre code de vérification est : {code}. Ne le partagez pas."
    
    html_content  = render_to_string('emails/verify_account.html', {'user': user, 'code': code, 'validity_minutes': CODE_VALIDITY_MINUTES, 'email_host': settings.EMAIL_HOST_USER})
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def send_2FA_mail_with_template(user, code):
    subject = "Votre code de vérification 2FA"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]
    
    text_content = f"Votre code de vérification est : {code}. Ne le partagez pas."
    
    html_content  = render_to_string('emails/2fa_code.html', {'user': user, 'code': code, 'validity_minutes': CODE_VALIDITY_MINUTES, 'email_host': settings.EMAIL_HOST_USER})
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    

def send_reset_password_mail_with_template(user, token):
    subject = "Réinitialisation de votre mot de passe"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]
    reset_link = f"{settings.FRONTEND_URL}/auth/reset-password/?token={token}"
    
    text_content = f"Pour réinitialiser votre mot de passe, cliquez sur le lien suivant : {reset_link}. Ce lien est valable pendant {CODE_VALIDITY_MINUTES} minutes."
    
    html_content = render_to_string('emails/reset_password.html', {'user': user, 'reset_link': reset_link, 'validity_minutes': CODE_VALIDITY_MINUTES, 'email_host': settings.EMAIL_HOST_USER})
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    