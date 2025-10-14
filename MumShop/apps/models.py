from datetime import date, datetime, timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.config import *

# Create your models here.
class SoftQuerySet(models.QuerySet):
    def delete(self):
        # Au lieu de supprimer physiquement → update is_active=False
        return super().update(is_active=False, deleted_at=timezone.now())

    def hard_delete(self):
        # Suppression réelle en base si vraiment nécessaire
        return super().delete()

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)
    def all_with_deleted(self):
        return self.all()
    def deleted(self):
        return self.filter(is_active=False)
    
class SoftManager(models.Manager):
    def get_queryset(self):
        return SoftQuerySet(self.model, using=self._db).filter(is_active=True)

    def all_with_deleted(self):
        return SoftQuerySet(self.model, using=self._db)

    def deleted(self):
        return SoftQuerySet(self.model, using=self._db).filter(is_active=False)
    
    def active(self):
        return self.get_queryset().filter(is_active=True)
    def inactive(self):
        return self.get_queryset().filter(is_active=False)


class BaseModel(models.Model):
    # id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftManager()

    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate random unique string for slug
            import uuid
            self.slug = str(uuid.uuid4())[:16]  # Use first 8 characters of UUID as slug
            # Ensure slug is unique
            while self.__class__.objects.filter(slug='obj-'+self.slug).exists():
                self.slug = str(uuid.uuid4())[:16]
            self.slug = 'obj-' + self.slug  # Prefix slug with 'obj-'
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        # Soft delete individuel
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        # Hard delete optionnel
        super().delete(using=using, keep_parents=keep_parents)
    
    def as_dict(self, include_related=False, exclude=None):
        """
        Retourne un dict de l'objet.
        - include_related=True : inclut les FK (id par défaut sinon dict si possible)
        - exclude=["champ1", "champ2"] : permet d'exclure certains champs
        """
        data = {}
        exclude = exclude or []

        for field in self._meta.get_fields():
            field_name = field.name

            if field_name in exclude:
                continue

            if hasattr(field, "attname"):
                value = getattr(self, field_name, None)

                # Dates
                if isinstance(value, (datetime, date)):
                    data[field_name] = value.isoformat() if value else None
                # ForeignKey
                elif field.is_relation and not field.many_to_many and not field.one_to_many:
                    if include_related and hasattr(value, "as_dict"):
                        data[field_name] = value.as_dict()
                    else:
                        data[field_name] = value.pk if value else None
                # Fichiers (ImageField, FileField, etc.)
                elif isinstance(field, (models.FileField, models.ImageField)):
                    if value and hasattr(value, "url"):
                        # Précède l'URL du serveur de façon dynamique
                        request = getattr(self, '_request', None)
                        if request:
                            data[field_name] = request.build_absolute_uri(value.url)
                        else:
                            data[field_name] = settings.MEDIA_URL + value.name if value and value.name else None
                    else:
                        data[field_name] = None
                    
                elif isinstance(value, (str, int, float, bool)):
                    data[field_name] = value
                else:
                    data[field_name] = None

        return data

class Location(BaseModel):
    longitude = models.FloatField()
    latitude = models.FloatField()
    
    def __str__(self):
        return f"Location({self.latitude}, {self.longitude})"

class User(BaseModel):
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    role = models.CharField(max_length=10, choices=ROLES_CHOICES, default='customer')
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=15, unique=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True, default=None)
    delivery_place = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname} <{self.email}>"
    
    def as_dict(self, include_related=False, exclude=["password"]):
        return super().as_dict(include_related, exclude)
    
    def save(self, *args, **kwargs):
        # Hash password before saving if it's not already hashed
        if not self.password.startswith('pbkdf2_'):
            from django.contrib.auth.hashers import make_password
            self.password = make_password(self.password)
        return super().save(*args, **kwargs)
    
    def check_password(self, password):
        from django.contrib.auth.hashers import check_password
        return check_password(password, self.password)
    
    def full_name(self):
        return f"{self.firstname} {self.lastname}"
    
class SuperMarket(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='supermarket_logos/', null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supermarkets')
    
    def __str__(self):
        return f"{self.name} owned by {self.owner.full_name()} at {self.address}"
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class Product(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    supermarket = models.ForeignKey(SuperMarket, on_delete=models.CASCADE, related_name='products')
    
    def __str__(self):
        return f"{self.name} - {self.supermarket.name}"
    
    def as_dict(self, include_related=True, exclude=None):
        p = super().as_dict(include_related, exclude)
        if include_related:
            p['category'] = self.category.as_dict() if self.category else None
            p['supermarket'] = self.supermarket.as_dict() if self.supermarket else None
            p['images'] = [img.as_dict() for img in self.images.all()]
        return p

class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class Order(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    supermarket = models.ForeignKey(SuperMarket, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=15, choices=ORDERS_STATUS_CHOICES, default='pending')
    
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_canceled = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    is_refunded = models.BooleanField(default=False)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Order #{self.id} by {self.customer.full_name()} at {self.supermarket.name}"
    
    def paid(self):
        self.is_paid = True
        self.paid_at = timezone.now()
        self.status = 'paid'
        self.save(update_fields=['is_paid', 'paid_at', 'status'])
        
    def delivered(self):
        self.is_delivered = True
        self.delivered_at = timezone.now()
        self.status = 'delivered'
        self.save(update_fields=['is_delivered', 'delivered_at', 'status'])
    
    def canceled(self):
        self.is_canceled = True
        self.canceled_at = timezone.now()
        self.status = 'canceled'
        self.save(update_fields=['is_canceled', 'canceled_at', 'status'])
    
    def refunded(self):
        self.is_refunded = True
        self.refunded_at = timezone.now()
        self.status = 'refunded'
        self.save(update_fields=['is_refunded', 'refunded_at', 'status'])
    
    def total_amount_calculate(self):
        total = sum(item.quantity * item.product.price for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total
    
    def as_dict(self, include_related=True, exclude=None):
        o = super().as_dict(include_related, exclude)
        if include_related:
            o['items'] = [item.as_dict() for item in self.items.all()]
        o['total_items'] = self.items.count()
        o['total_amount'] = float(self.total_amount_calculate())
        o['payment'] = self.payment.as_dict() if hasattr(self, 'payment') else None
        return o

class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of order
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} for Order #{self.order.id}"
    
    def price_calculate(self):
        self.price = self.quantity * self.product.price
        self.save(update_fields=['price'])
        return self.price
    
    def as_dict(self, include_related=True, exclude=None):
        oi= super().as_dict(include_related, exclude)
        oi['price'] = float(self.price_calculate())
        return oi

class Payment(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.amount} via {self.payment_method}"
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class Delivery(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'delivery'})
    pickup_time = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    delivery_address = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Delivery for Order #{self.order.id} - Status: {self.status}"
    
    def pick_up(self):
        self.status = 'in_transit'
        self.pickup_time = timezone.now()
        self.save(update_fields=['status', 'pickup_time'])
    
    def deliver(self):
        self.status = 'delivered'
        self.delivery_time = timezone.now()
        self.order.delivered()  # Mark order as delivered
        self.save(update_fields=['status', 'delivery_time'])
    
    def cancel(self):
        self.status = 'canceled'
        self.order.canceled()  # Mark order as canceled
        self.save(update_fields=['status'])
    
    def as_dict(self, include_related=True, exclude=None):
        dl = super().as_dict(include_related, exclude)
        if include_related:
            dl['delivery_person'] = self.delivery_person.as_dict() if self.delivery_person else None
            dl['order'] = self.order.as_dict() if self.order else None
            dl['delivery_address'] = self.delivery_address.as_dict() if self.delivery_address else None
            dl['notes'] = [note.as_dict() for note in self.notes.all()]
        return dl

class DeliveryNote(BaseModel):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='notes')
    note = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])  # e.g., rating out of 5
    comment = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Note for Delivery #{self.delivery.id} by {self.created_by.full_name() if self.created_by else 'Unknown'}"
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class RefreshToken(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"RefreshToken for {self.user.full_name()} - Expires at {self.expires_at}"
    
    def is_expired(self):
        return timezone.now() >= self.expires_at
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)
    
    def save(self, *args, **kwargs):
        if not self.token:
            import uuid
            token = str(uuid.uuid4()).replace('-', '')  # Generate a unique token
            while self.__class__.objects.filter(token=token).exists():
                token = str(uuid.uuid4()).replace('-', '')
            self.token = token
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)  # Default 7 days validity
        return super().save(*args, **kwargs)

class NewsletterSubscription(models.Model):
    email = models.EmailField(max_length=254, unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"NewsletterSubscription <{self.email}> - {'Active' if self.is_active else 'Inactive'}"
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.user.full_name()} - {'Read' if self.is_read else 'Unread'}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Conversation #{self.id} with {self.participants.count()} participants"
    
    def as_dict(self, include_related=True, exclude=None):
        c = super().as_dict(include_related, exclude)
        if include_related:
            c['participants'] = [p.as_dict() for p in self.participants.all()]
            c['messages'] = [m.as_dict() for m in self.messages.all()]
        return c

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return f"Message from {self.sender.full_name()} at {self.sent_at}"
    
    def is_read_by_participant(self, user):
        return self.read_receipts.filter(user=user).exists()
    
    def is_read_by_all(self):
        participant_ids = set(self.conversation.participants.values_list('id', flat=True))
        read_user_ids = set(self.read_receipts.values_list('user_id', flat=True))
        return participant_ids.issubset(read_user_ids)
    
    def as_dict(self, include_related=True, exclude=None):
        m = super().as_dict(include_related, exclude)
        if include_related:
            m['sender'] = self.sender.as_dict() if self.sender else None
            m['attachments'] = [att.as_dict() for att in self.attachments.all()]
            m['read_receipts'] = [rr.as_dict() for rr in self.read_receipts.all()]
            m['is_read_by_all'] = self.is_read_by_all()
            m['total_reactions'] = self.reactions.count()
            m['reactions'] = [reaction.as_dict() for reaction in self.reactions.all()]
        return m

class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment for Message #{self.message.id}"
    
    def as_dict(self, include_related=False, exclude=None):
        ma = super().as_dict(include_related, exclude)
        if self.file and hasattr(self.file, "url"):
            request = getattr(self, '_request', None)
            if request:
                ma['file_url'] = request.build_absolute_uri(self.file.url)
            else:
                ma['file_url'] = settings.MEDIA_URL + self.file.name if self.file and self.file.name else None
        else:
            ma['file_url'] = None
        return ma

class MessageReadReceipt(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_receipts')
    read_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"ReadReceipt for Message #{self.message.id} by {self.user.full_name()}"
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    reaction_type = models.CharField(max_length=50, choices=MESSAGE_REACTIONS_CHOICES, default='like')  # e.g., 'like', 'love', 'laugh', etc.
    reacted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Reaction '{self.reaction_type}' for Message #{self.message.id} by {self.user.full_name()}"
    
    def as_dict(self, include_related=False, exclude=None):
        return super().as_dict(include_related, exclude)

