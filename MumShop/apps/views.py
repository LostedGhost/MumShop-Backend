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
from apps.utils import is_logged_in, is_admin, is_seller, is_moderator, is_customer, is_delivery, is_not_customer, is_not_customer_or_delivery, createNotification
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

    try:
        createNotification(user, 'Bienvenue', 'Votre compte a été créé avec succès')
    except Exception:
        pass

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

    try:
        createNotification(user, 'Supermarché créé', f'Votre supermarché "{supermarket.name}" a été créé avec succès', obj='supermarket', obj_slug=supermarket.slug)
    except Exception:
        pass
    try:
        admins = User.objects.filter(role=ROLES[0])  # 'admin' role
        for admin in admins:
            createNotification(admin, 'Supermarché créé', f'L\'utilisateur {user.full_name} a créé le supermarché nommé "{supermarket.name}"', obj='supermarket', obj_slug=supermarket.slug)
    except Exception:
        pass
    
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

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def list_products(request):
    products = Product.objects.all()
    products_data = [prod.as_dict(include_related=True) for prod in products]
    return JsonResponse({'products': products_data, 'nb': products.count()}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
@is_seller
def add_product(request):

    name = request.POST.get('name', None)
    description = request.POST.get('description', '')
    price = request.POST.get('price', None)
    category_slug = request.POST.get('category_slug', None)
    supermarket_slug = request.POST.get('supermarket_slug', None)
    
    indispendable_fields = [name, price, category_slug, supermarket_slug]
    if not all(indispendable_fields):
        return JsonResponse({'error': 'Champs indispensables requis'}, status=400)
    
    try:
        price = float(price)
    except ValueError:
        return JsonResponse({'error': 'Prix invalide'}, status=400)
    
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Catégorie non trouvée'}, status=404)
    
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug, owner=request.user)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé ou accès refusé'}, status=404)
    
    product = Product(
        name=name,
        description=description,
        price=price,
        category=category,
        supermarket=supermarket
    )
    product.save()

    try:
        createNotification(request.user, 'Produit ajouté', f'Le produit "{product.name}" a été ajouté au supermarché "{supermarket.name}"', obj='product', obj_slug=product.slug)
    except Exception:
        pass
    
    return JsonResponse({'message': 'Produit ajouté avec succès', 'product': product.as_dict(include_related=True)}, status=201)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def get_product(request, product_slug):
    try:
        product = Product.objects.get(slug=product_slug)
        return JsonResponse({'product': product.as_dict(include_related=True)}, status=200)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Produit non trouvé'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_seller
def add_product_images(request, product_slug):
    user = request.user
    try:
        product = Product.objects.get(slug=product_slug, supermarket__owner=user)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Produit non trouvé ou accès refusé'}, status=404)
    
    images = request.FILES.getlist('images')
    if not images:
        return JsonResponse({'error': 'Aucune image fournie'}, status=400)
    
    for img in images:
        product_image = ProductImage(product=product, image=img)
        product_image.save()
    
    return JsonResponse({'message': 'Images ajoutées avec succès', 'product': product.as_dict(include_related=True)}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
@is_seller
def alter_product(request, product_slug):
    user = request.user
    try:
        product = Product.objects.get(slug=product_slug, supermarket__owner=user)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Produit non trouvé ou accès refusé'}, status=404)
    
    name = request.POST.get('name', None)
    description = request.POST.get('description', None)
    price = request.POST.get('price', None)
    category_slug = request.POST.get('category_slug', None)
    
    if name:
        product.name = name
    if description is not None:
        product.description = description
    if price:
        try:
            price = float(price)
            product.price = price
        except ValueError:
            return JsonResponse({'error': 'Prix invalide'}, status=400)
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            product.category = category
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Catégorie non trouvée'}, status=404)
    
    product.save()
    return JsonResponse({'message': 'Produit modifié avec succès', 'product': product.as_dict(include_related=True)}, status=200)

@csrf_exempt
@require_http_methods(["DELETE"])
@is_seller
def delete_product(request, product_slug):
    user = request.user
    try:
        product = Product.objects.get(slug=product_slug, supermarket__owner=user)
        product.delete()
        return JsonResponse({'message': 'Produit supprimé avec succès'}, status=200)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Produit non trouvé ou accès refusé'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def list_supermarket_products(request, supermarket_slug):
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé'}, status=404)
    
    products = Product.objects.filter(supermarket=supermarket)
    products_data = [prod.as_dict(include_related=True) for prod in products]
    return JsonResponse({'products': products_data, 'nb': products.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_seller
def all_orders(request):
    user = request.user
    supermarkets = SuperMarket.objects.filter(owner=user)
    orders = Order.objects.filter(supermarket__in=supermarkets)
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_seller
def all_supermarket_orders(request, supermarket_slug):
    user = request.user
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug, owner=user)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé ou accès refusé'}, status=404)
    
    orders = Order.objects.filter(supermarket=supermarket)
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_customer
def customer_orders(request):
    user = request.user
    orders = Order.objects.filter(customer=user)
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_customer
def all_customer_supermarket_orders(request, supermarket_slug):
    user = request.user
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé'}, status=404)
    
    orders = Order.objects.filter(supermarket=supermarket, customer=user)
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_not_customer_or_delivery
def all_orders_admin(request):
    orders = Order.objects.all()
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_not_customer_or_delivery
def all_supermarket_orders_admin(request, supermarket_slug):
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé'}, status=404)
    
    orders = Order.objects.filter(supermarket=supermarket)
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_delivery
def delivery_orders(request):
    user = request.user
    deliveries = Delivery.objects.filter(user=user)
    orders = Order.objects.filter(id__in=deliveries.values_list('order_id', flat=True))
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
@is_customer
def place_order(request):

    user = request.user
    supermarket_slug = request.POST.get('supermarket_slug', None)
    products_data = request.POST.get('products', None)
    delivery_address = request.POST.get('delivery_address', None)
    
    indispendable_fields = [supermarket_slug, products_data, delivery_address]
    if not all(indispendable_fields):
        return JsonResponse({'error': 'Champs indispensables requis'}, status=400)
    
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé'}, status=404)
    
    try:
        products_list = json.loads(products_data)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données de produits invalides'}, status=400)
    
    if not isinstance(products_list, list) or not products_list:
        return JsonResponse({'error': 'La liste des produits doit être non vide'}, status=400)
    
    order = Order(
        customer=user,
        supermarket=supermarket,
        delivery_address=delivery_address,
        status='pending'
    )
    order.save()
    
    total_price = 0
    for item in products_list:
        product_slug = item.get('product_slug', None)
        quantity = item.get('quantity', 1)
        if not product_slug:
            return JsonResponse({'error': 'Le slug du produit est requis pour chaque article'}, status=400)
        try:
            product = Product.objects.get(slug=product_slug, supermarket=supermarket)
            order_item = OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price * quantity
            )
            order_item.save()
            total_price += order_item.price
        except Product.DoesNotExist:
            return JsonResponse({'error': f'Produit non trouvé: {product_slug}'}, status=404)
    
    order.total_price = total_price
    order.save()

    try:
        createNotification(supermarket.owner, 'Nouvelle commande', f'Une nouvelle commande {order.slug} a été passée sur "{supermarket.name}"', obj='order', obj_slug=order.slug)
    except Exception:
        pass
    try:
        createNotification(user, 'Commande passée', f'Votre commande {order.slug} a été passée avec succès', obj='order', obj_slug=order.slug)
    except Exception:
        pass
    
    return JsonResponse({'message': 'Commande passée avec succès', 'order': order.as_dict(include_related=True)}, status=201)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def get_order(request, order_slug):
    user = request.user
    try:
        order = Order.objects.get(slug=order_slug)
        if user.role == 'customer' and order.customer != user:
            return JsonResponse({'error': 'Accès refusé à cette commande'}, status=403)
        if user.role == 'seller' and order.supermarket.owner != user:
            return JsonResponse({'error': 'Accès refusé à cette commande'}, status=403)
        return JsonResponse({'order': order.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_customer
def revoke_order(request, order_slug):

    user = request.user
    try:
        order = Order.objects.get(slug=order_slug, customer=user)
        if order.status != 'pending':
            return JsonResponse({'error': 'Seules les commandes en attente peuvent être annulées'}, status=400)
        order.canceled()
        try:
            createNotification(order.supermarket.owner, 'Commande annulée', f'La commande {order.slug} a été annulée par le client', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        try:
            createNotification(user, 'Commande annulée avec succès', f'Votre commande a bien été annulée', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        return JsonResponse({'message': 'Commande annulée avec succès'}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée ou accès refusé'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_customer
def pay_order(request, order_slug):

    user = request.user
    transaction_id = request.POST.get('transaction_id', None)
    if not transaction_id:
        return JsonResponse({'error': 'L\'identifiant de transaction est requis'}, status=400)
    try:
        order = Order.objects.get(slug=order_slug, customer=user)
        if order.status != 'pending':
            return JsonResponse({'error': 'Seules les commandes en attente peuvent être payées'}, status=400)
        # Here you would integrate with a payment gateway
        payement = Payment(
            order=order,
            payment_method = 'credit_card',
            amount=order.total_price,
            transaction_id = transaction_id
        )
        payement.save()
        order.paid()

        try:
            createNotification(order.supermarket.owner, 'Commande payée', f'La commande {order.slug} a été payée', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        try:
            createNotification(user, 'Paiement reçu', f'Le paiement pour la commande {order.slug} a été reçu', obj='order', obj_slug=order.slug)
        except Exception:
            pass

        return JsonResponse({'message': 'Commande payée avec succès', 'order': order.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée ou accès refusé'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_customer
def revoke_payment(request, order_slug):

    user = request.user
    try:
        order = Order.objects.get(slug=order_slug, customer=user)
        if not order.is_paid:
            return JsonResponse({'error': 'Seules les commandes payées peuvent être annulées'}, status=400)
        payment = Payment.objects.filter(order=order).last()
        if not payment:
            return JsonResponse({'error': 'Paiement non trouvé pour cette commande'}, status=404)
        payment.delete()
        order.status = 'pending'
        order.save()

        try:
            createNotification(order.supermarket.owner, 'Paiement annulé', f'Le paiement pour la commande {order.slug} a été annulé', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        try:
            createNotification(user, 'Paiement annulé', f'Votre paiement pour la commande {order.slug} a été annulé', obj='order', obj_slug=order.slug)
        except Exception:
            pass

        return JsonResponse({'message': 'Paiement annulé avec succès', 'order': order.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée ou accès refusé'}, status=404)
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Paiement non trouvé pour cette commande'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_moderator
def assign_delivery(request, order_slug):

    delivery_user_id = request.POST.get('delivery_user_id', None)
    delivery_address_long = request.POST.get('delivery_address_long', None)
    delivery_address_lat = request.POST.get('delivery_address_lat', None)
    if not delivery_user_id:
        return JsonResponse({'error': 'L\'identifiant de l\'utilisateur de livraison est requis'}, status=400)
    if not delivery_address_long or not delivery_address_lat:
        return JsonResponse({'error': 'Les coordonnées de l\'adresse de livraison sont requises'}, status=400)
    try:
        order = Order.objects.get(slug=order_slug)
        delivery_user = User.objects.get(id=delivery_user_id, role='delivery')
        try:
            delivery_address_long = float(delivery_address_long)
            delivery_address_lat = float(delivery_address_lat)
            delivery_location = Location(longitude=delivery_address_long, latitude=delivery_address_lat)
            delivery_location.save()
        except ValueError:
            return JsonResponse({'error': 'Coordonnées de l\'adresse de livraison invalides'}, status=400)
        delivery = Delivery(
            order=order,
            delivery_person=delivery_user,
            delivery_address=delivery_location
        )
        delivery.save()
        order.save()

        try:
            createNotification(delivery_user, 'Nouvelle livraison', f'Vous avez été assigné à la commande {order.slug}', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        try:
            createNotification(order.customer, 'Livreur assigné', f'Un livreur a été assigné à votre commande {order.slug}', obj='order', obj_slug=order.slug)
        except Exception:
            pass

        return JsonResponse({'message': 'Livreur assigné avec succès', 'order': order.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur de livraison non trouvé'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_delivery
def start_delivery(request, order_slug):

    user = request.user
    try:
        order = Order.objects.get(slug=order_slug)
        delivery = Delivery.objects.get(order=order, delivery_person=user)
        if order.status != 'paid':
            return JsonResponse({'error': 'La livraison ne peut commencer que pour les commandes payées'}, status=400)
        delivery.pick_up()
        try:
            createNotification(order.customer, 'Livraison commencée', f'La livraison de votre commande {order.slug} a commencé', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        return JsonResponse({'message': 'Livraison commencée avec succès', 'order': order.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except Delivery.DoesNotExist:
        return JsonResponse({'error': 'Accès refusé à cette livraison'}, status=403)

@csrf_exempt
@require_http_methods(["POST"])
@is_delivery
def complete_delivery(request, order_slug):

    user = request.user
    try:
        order = Order.objects.get(slug=order_slug)
        delivery = Delivery.objects.get(order=order, delivery_person=user)
        if order.status != 'in_delivery':
            return JsonResponse({'error': 'La livraison ne peut être complétée que pour les commandes en cours de livraison'}, status=400)
        delivery.deliver()
        try:
            createNotification(order.customer, 'Livraison complétée', f'Votre commande {order.slug} a été livrée', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        return JsonResponse({'message': 'Livraison complétée avec succès', 'order': order.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except Delivery.DoesNotExist:
        return JsonResponse({'error': 'Accès refusé à cette livraison'}, status=403)

@csrf_exempt
@require_http_methods(["POST"])
@is_delivery
def cancel_delivery(request, order_slug):

    user = request.user
    try:
        order = Order.objects.get(slug=order_slug)
        delivery = Delivery.objects.get(order=order, delivery_person=user)
        if order.status not in ['in_delivery', 'paid']:
            return JsonResponse({'error': 'La livraison ne peut être annulée que pour les commandes en cours de livraison ou payées'}, status=400)
        delivery.cancel()
        try:
            createNotification(order.customer, 'Livraison annulée', f'La livraison de votre commande {order.slug} a été annulée', obj='order', obj_slug=order.slug)
        except Exception:
            pass
        return JsonResponse({'message': 'Livraison annulée avec succès', 'order': order.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except Delivery.DoesNotExist:
        return JsonResponse({'error': 'Accès refusé à cette livraison'}, status=403)

@csrf_exempt
@require_http_methods(["GET"])
@is_delivery
def delivery_pending_orders(request):
    user = request.user
    deliveries = Delivery.objects.filter(delivery_person=user, status=DELIVERY_STATUS[0])
    orders = Order.objects.filter(id__in=deliveries.values_list('order_id', flat=True))
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_delivery
def delivery_in_progress_orders(request):
    user = request.user
    deliveries = Delivery.objects.filter(delivery_person=user, status=DELIVERY_STATUS[1])
    orders = Order.objects.filter(id__in=deliveries.values_list('order_id', flat=True))
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_delivery
def delivery_completed_orders(request):
    user = request.user
    deliveries = Delivery.objects.filter(delivery_person=user, status=DELIVERY_STATUS[2])
    orders = Order.objects.filter(id__in=deliveries.values_list('order_id', flat=True))
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_delivery
def delivery_canceled_orders(request):
    user = request.user
    deliveries = Delivery.objects.filter(delivery_person=user, status=DELIVERY_STATUS[3])
    orders = Order.objects.filter(id__in=deliveries.values_list('order_id', flat=True))
    orders_data = [order.as_dict(include_related=True) for order in orders]
    return JsonResponse({'orders': orders_data, 'nb': orders.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_admin
def all_deliveries(request):
    deliveries = Delivery.objects.all()
    deliveries_data = [delivery.as_dict(include_related=True) for delivery in deliveries]
    return JsonResponse({'deliveries': deliveries_data, 'nb': deliveries.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_seller
def supermarket_deliveries(request, supermarket_slug):
    user = request.user
    try:
        supermarket = SuperMarket.objects.get(slug=supermarket_slug, owner=user)
    except SuperMarket.DoesNotExist:
        return JsonResponse({'error': 'Supermarché non trouvé ou accès refusé'}, status=404)
    
    orders = Order.objects.filter(supermarket=supermarket)
    deliveries = Delivery.objects.filter(order__in=orders)
    deliveries_data = [delivery.as_dict(include_related=True) for delivery in deliveries]
    return JsonResponse({'deliveries': deliveries_data, 'nb': deliveries.count()}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
@is_seller
def seller_deliveries(request):
    user = request.user
    supermarkets = SuperMarket.objects.filter(owner=user)
    orders = Order.objects.filter(supermarket__in=supermarkets)
    deliveries = Delivery.objects.filter(order__in=orders)
    deliveries_data = [delivery.as_dict(include_related=True) for delivery in deliveries]
    return JsonResponse({'deliveries': deliveries_data, 'nb': deliveries.count()}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
@is_customer
def note_delivery(request, order_slug):

    user = request.user
    rating = request.POST.get('rating', None)
    comment = request.POST.get('comment', '')
    if not rating:
        return JsonResponse({'error': 'La note est requise'}, status=400)
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return JsonResponse({'error': 'La note doit être comprise entre 1 et 5'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Note invalide'}, status=400)
    try:
        order = Order.objects.get(slug=order_slug, customer=user)
        delivery = Delivery.objects.get(order=order)
        note_deliv = DeliveryNote.objects.filter(delivery=delivery, customer=user).first()
        if note_deliv:
            return JsonResponse({'error': 'Vous avez déjà noté cette livraison'}, status=400)
        
        note_deliv = DeliveryNote(
            delivery=delivery,
            note=rating,
            comment=comment,
            created_by=user
        )
        note_deliv.save()

        try:
            createNotification(delivery.delivery_person, 'Nouvelle note', f'Vous avez reçu une note de {rating} pour la livraison de la commande {order.slug}', obj='order', obj_slug=order.slug)
        except Exception:
            pass

        return JsonResponse({'message': 'Livraison notée avec succès', 'delivery': delivery.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée ou accès refusé'}, status=404)
    except Delivery.DoesNotExist:
        return JsonResponse({'error': 'Livraison non trouvée pour cette commande'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def get_delivery_note(request, order_slug):
    user = request.user
    try:
        order = Order.objects.get(slug=order_slug)
        delivery = Delivery.objects.get(order=order)
        note_deliv = DeliveryNote.objects.get(delivery=delivery)
        return JsonResponse({'delivery_note': note_deliv.as_dict(include_related=True)}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except Delivery.DoesNotExist:
        return JsonResponse({'error': 'Livraison non trouvée pour cette commande'}, status=404)
    except DeliveryNote.DoesNotExist:
        return JsonResponse({'error': 'Note de livraison non trouvée pour cette commande'}, status=404)

@csrf_exempt
@require_http_methods(["DELETE"])
@is_customer
def delete_delivery_note(request, order_slug):
    user = request.user
    try:
        order = Order.objects.get(slug=order_slug, customer=user)
        delivery = Delivery.objects.get(order=order)
        note_deliv = DeliveryNote.objects.get(delivery=delivery, customer=user)
        note_deliv.delete()
        return JsonResponse({'message': 'Note de livraison supprimée avec succès'}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée ou accès refusé'}, status=404)
    except Delivery.DoesNotExist:
        return JsonResponse({'error': 'Livraison non trouvée pour cette commande'}, status=404)
    except DeliveryNote.DoesNotExist:
        return JsonResponse({'error': 'Note de livraison non trouvée pour cette commande'}, status=404)
    
@csrf_exempt
@require_http_methods(["POST"])
def add_newsletter_subscriber(request):
    email = request.POST.get('email', None)
    if not email:
        return JsonResponse({'error': 'L\'email est requis'}, status=400)
    if NewsletterSubscription.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Cet email est déjà abonné à la newsletter'}, status=400)
    subscribtion = NewsletterSubscription(email=email)
    subscribtion.save()
    return JsonResponse({'message': 'Abonnement à la newsletter réussi'}, status=201)

@csrf_exempt
@require_http_methods(["DELETE"])
def remove_newsletter_subscriber(request):
    email = request.POST.get('email', None)
    if not email:
        return JsonResponse({'error': 'L\'email est requis'}, status=400)
    try:
        subscribtion = NewsletterSubscription.objects.get(email=email)
        subscribtion.delete()
        return JsonResponse({'message': 'Désabonnement de la newsletter réussi'}, status=200)
    except NewsletterSubscription.DoesNotExist:
        return JsonResponse({'error': 'Cet email n\'est pas abonné à la newsletter'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
@is_logged_in
def read_all_notifications(request):
    user = request.user
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return JsonResponse({'message': 'Notifications marquées comme lues'}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
@is_logged_in
def read_notification(request, notification_slug):
    user = request.user
    try:
        notification = Notification.objects.get(slug=notification_slug, user=user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'message': 'Notification marquée comme lue'}, status=200)
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification non trouvée'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
@is_logged_in
def list_notifications(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    notifications_data = [notif.as_dict() for notif in notifications]
    return JsonResponse({'notifications': notifications_data, 'nb': notifications.count()}, status=200)

