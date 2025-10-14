ROLES = (
    'admin',
    'seller',
    'moderator',
    'customer',
    'delivery',
)

ROLES_CHOICES = (
    ('admin', 'Administrateur'),
    ('seller', 'Commerçante'),
    ('moderator', 'Assistant'),
    ('customer', 'Client'),
    ('delivery', 'Livreur'),
)

ORDERS_STATUS = (
    'pending',
    'paid',
    'preparing',
    'in_delivery',
    'delivered',
    'canceled',
    'refunded',
)

ORDERS_STATUS_CHOICES = (
    ('pending', 'En attente'),
    ('paid', 'Payée'),
    ('preparing', 'En préparation'),
    ('in_delivery', 'En livraison'),
    ('delivered', 'Livrée'),
    ('canceled', 'Annulée'),
    ('refunded', 'Remboursée'),
)

DELIVERY_STATUS = (
    'pending',
    'in_transit',
    'delivered',
    'canceled',
)

DELIVERY_STATUS_CHOICES = (
    ('pending', 'En attente'),
    ('in_transit', 'En transit'),
    ('delivered', 'Livrée'),
    ('canceled', 'Annulée'),
)

MESSAGE_REACTIONS = (
    'like',
    'love',
    'laugh',
    'sad',
    'angry'
)

# Emojis: 👍 ❤️ 😂 😢 😡
MESSAGE_REACTIONS_CHOICES = (
    ('like', '👍'),
    ('love', '❤️'),
    ('laugh', '😂'),
    ('sad', '😢'),
    ('angry', '😡')
)

CODE_VALIDITY_MINUTES = 15