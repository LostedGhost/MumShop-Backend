import os
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import base64
import mimetypes
from datetime import datetime
from django.core.files.base import ContentFile
from django.http import JsonResponse
from apps.models import *
from apps.utils import is_logged_in, is_admin, is_seller, is_moderator, is_customer, is_delivery
from django.conf import settings

# Create your views here.
@csrf_exempt
@require_http_methods(["GET"])
@is_admin
def get_users(request):
    users = User.objects.all()
    users_data = [user.as_dict(exclude=['password']) for user in users]
    return JsonResponse({'users': users_data}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    firstname = request.POST.get('firstname', None)
    lastname = request.POST.get('lastname', None)
    email = request.POST.get('email', None)
    password = request.POST.get('password', None)
    phone = request.POST.get('phone', None)
    role = request.POST.get('role', 'customer')
    photo_data = request.FILES.get('photo', None)
    delivery_long = request.POST.get('delivery_long', None)
    delivery_lat = request.POST.get('delivery_lat', None)
    
    indispendable_fields = [firstname, lastname, email, password, phone, role]
    if not all(indispendable_fields):
        return JsonResponse({'error': 'Champs indispensables requis'}, status=400)
    if role not in ROLES:
        return JsonResponse({'error': 'Rôle invalide'}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Email déjà utilisé'}, status=400)
    if User.objects.filter(phone=phone).exists():
        return JsonResponse({'error': 'Numéro de téléphone déjà utilisé'}, status=400)
    delivery_place = None
    if delivery_long and delivery_lat:
        try:
            delivery_long = float(delivery_long)
            delivery_lat = float(delivery_lat)
            delivery_place = Location.objects.create(longitude=delivery_long, latitude=delivery_lat)
        except ValueError:
            return JsonResponse({'error': 'Coordonnées de livraison de base invalides'}, status=400)
    
    user = User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        phone=phone,
        role=role,
        delivery_place=delivery_place,
        password=password,
        photo = photo_data
    )
    user.save()
    return JsonResponse({'message': 'Utilisateur enregistré avec succès', 'user': user.as_dict(exclude=['password'])}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', None)
        password = data.get('password', None)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données JSON invalides'}, status=400)
    
    if not email or not password:
        return JsonResponse({'error': 'Email et mot de passe requis'}, status=400)
    
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            return JsonResponse({'error': 'Mot de passe incorrect'}, status=401)
        if user.is_blocked:
            return JsonResponse({'error': 'Utilisateur bloqué'}, status=403)
        
        # Create a refresh token
        token = base64.urlsafe_b64encode(os.urandom(30)).decode()
        refresh_token = RefreshToken(user=user, token=token)
        refresh_token.save()
        
        return JsonResponse({
            'message': 'Connexion réussie',
            'user': user.as_dict(exclude=['password']),
            'token': token
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)

