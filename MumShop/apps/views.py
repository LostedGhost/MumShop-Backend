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
from apps.utils import is_logged_in, is_admin, is_seller, is_moderator, is_customer, is_delivery, is_not_customer
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

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def get_connected_user(request):
    user = request.user
    if not user:
        return JsonResponse({'error': 'Utilisateur non connecté'}, status=401)
    return JsonResponse({'user': user.as_dict(exclude=['password'])}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
@is_logged_in
def logout_user(request):
    user = request.user
    token = request.headers.get('Authorization', None)
    token = token.split(' ')[1] if token and ' ' in token else token
    if not user or not token:
        return JsonResponse({'error': 'Utilisateur non connecté'}, status=401)
    try:
        refresh_token = RefreshToken.objects.get(user=user, token=token)
        refresh_token.delete()
        return JsonResponse({'message': 'Déconnexion réussie'}, status=200)
    except RefreshToken.DoesNotExist:
        return JsonResponse({'error': 'Token invalide'}, status=401)

@csrf_exempt
@require_http_methods(["POST"])
@is_logged_in
def update_user(request):
    user = request.user
    if not user:
        return JsonResponse({'error': 'Utilisateur non connecté'}, status=401)
    
    firstname = request.POST.get('firstname', None)
    lastname = request.POST.get('lastname', None)
    phone = request.POST.get('phone', None)
    photo_data = request.FILES.get('photo', None)
    delivery_long = request.POST.get('delivery_long', None)
    delivery_lat = request.POST.get('delivery_lat', None)
    
    if firstname:
        user.firstname = firstname
    if lastname:
        user.lastname = lastname
    if phone:
        if User.objects.filter(phone=phone).exclude(id=user.id).exists():
            return JsonResponse({'error': 'Numéro de téléphone déjà utilisé'}, status=400)
        user.phone = phone
    if photo_data:
        user.photo = photo_data
    if delivery_long and delivery_lat:
        try:
            delivery_long = float(delivery_long)
            delivery_lat = float(delivery_lat)
            if user.delivery_place:
                user.delivery_place.longitude = delivery_long
                user.delivery_place.latitude = delivery_lat
                user.delivery_place.save()
            else:
                location = Location.objects.create(longitude=delivery_long, latitude=delivery_lat)
                user.delivery_place = location
        except ValueError:
            return JsonResponse({'error': 'Coordonnées de livraison de base invalides'}, status=400)
    
    user.save()
    return JsonResponse({'message': 'Utilisateur mis à jour avec succès', 'user': user.as_dict(exclude=['password'])}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
@is_seller
def create_supermarket(request):
    user = request.user
    name = request.POST.get('name', None)
    address = request.POST.get('address', None)
    longitude = request.POST.get('longitude', None)
    latitude = request.POST.get('latitude', None)
    photo_data = request.FILES.get('photo', None)
    
    indispendable_fields = [name, address, longitude, latitude]
    if not all(indispendable_fields):
        return JsonResponse({'error': 'Champs indispensables requis'}, status=400)
    
    try:
        longitude = float(longitude)
        latitude = float(latitude)
    except ValueError:
        return JsonResponse({'error': 'Coordonnées invalides'}, status=400)
    
    location = Location.objects.create(longitude=longitude, latitude=latitude)
    
    supermarket = SuperMarket(
        name=name,
        address=address,
        location=location,
        owner=user,
        logo=photo_data
    )
    supermarket.save()
    
    return JsonResponse({'message': 'Supermarché créé avec succès', 'supermarket': supermarket.as_dict()}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
@is_seller
def alter_supermarket(request, supermarket_slug):
    user = request.user
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug, owner=user)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé ou accès refusé'}, status=404)
    
    name = request.POST.get('name', None)
    address = request.POST.get('address', None)
    longitude = request.POST.get('longitude', None)
    latitude = request.POST.get('latitude', None)
    photo_data = request.FILES.get('photo', None)
    
    if name:
        supermarket.name = name
    if address:
        supermarket.address = address
    if longitude and latitude:
        try:
            longitude = float(longitude)
            latitude = float(latitude)
            if supermarket.location:
                supermarket.location.longitude = longitude
                supermarket.location.latitude = latitude
                supermarket.location.save()
            else:
                location = Location.objects.create(longitude=longitude, latitude=latitude)
                supermarket.location = location
        except ValueError:
            return JsonResponse({'error': 'Coordonnées invalides'}, status=400)
    if photo_data:
        supermarket.logo = photo_data
    
    supermarket.save()
    return JsonResponse({'message': 'Supermarché modifié avec succès', 'supermarket': supermarket.as_dict()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def get_supermarket(request, supermarket_slug):
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug)
        return JsonResponse({'supermarket': supermarket.as_dict(include_related=True)}, status=200)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé ou accès refusé'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def list_supermarkets(request):
    supermarkets = SuperMarket.objects.all()
    supermarkets_data = [sm.as_dict(include_related=True) for sm in supermarkets]
    return JsonResponse({'supermarkets': supermarkets_data, 'nb': supermarkets.count()}, status=200)

@csrf_exempt
@require_http_methods(["DELETE"])
@is_seller
def delete_supermarket(request, supermarket_slug):
    user = request.user
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug, owner=user)
        supermarket.delete()
        return JsonResponse({'message': 'Supermarché supprimé avec succès'}, status=200)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé ou accès refusé'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_not_customer
def add_category(request):
    name = request.POST.get('name', None)
    description = request.POST.get('description', '')
    
    if not name:
        return JsonResponse({'error': 'Le nom de la catégorie est requis'}, status=400)
    
    if Category.objects.filter(name=name).exists():
        return JsonResponse({'error': 'Une catégorie avec ce nom existe déjà'}, status=400)
    
    category = Category(
        name=name,
        description=description,
    )
    category.save()
    
    return JsonResponse({'message': 'Catégorie ajoutée avec succès', 'category': category.as_dict()}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
@is_not_customer
def alter_category(request, category_slug):
    user = request.user
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Catégorie non trouvée'}, status=404)
    
    name = request.POST.get('name', None)
    description = request.POST.get('description', None)
    
    if name:
        if Category.objects.filter(name=name).exclude(id=category.id).exists():
            return JsonResponse({'error': 'Une catégorie avec ce nom existe déjà'}, status=400)
        category.name = name
    if description is not None:
        category.description = description
    
    category.save()
    return JsonResponse({'message': 'Catégorie modifiée avec succès', 'category': category.as_dict()}, status=200)

@csrf_exempt
@require_http_methods(["DELETE"])
@is_admin
def delete_category(request, category_slug):
    user = request.user
    try:
        category = Category.objects.get(slug=category_slug)
        category.delete()
        return JsonResponse({'message': 'Catégorie supprimée avec succès'}, status=200)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Catégorie non trouvée'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def list_categories(request):
    categories = Category.objects.all()
    categories_data = [cat.as_dict() for cat in categories]
    return JsonResponse({'categories': categories_data, 'nb': categories.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def get_category(request, category_slug):
    try:
        category = Category.objects.get(slug=category_slug)
        return JsonResponse({'category': category.as_dict()}, status=200)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Catégorie non trouvée'}, status=404)