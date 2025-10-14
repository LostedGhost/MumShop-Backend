# 🧩 **Projet : MumShop– Plateforme de gestion complète de commerce**

### **1.1. Présentation générale**

**Nom du projet :** MumShop  
**Objectif :** Développer une plateforme web et mobile de gestion de commerce (type supermarché ou boutique) permettant aux commerçants de gérer leurs stocks, leurs ventes, leurs livraisons, et d’offrir aux clients une interface intuitive pour passer des commandes et se faire livrer rapidement.  
**Contexte :**  
Dans le contexte béninois, de nombreux commerçants manquent d’outils numériques efficaces pour la gestion quotidienne de leurs activités. MumShop vient répondre à ce besoin avec une solution **locale, intuitive, multicanal et intégrée**.

---

### **1.2. Enjeux et objectifs**

#### **Objectifs principaux :**

- Digitaliser la gestion des commerces physiques et des supermarchés.
  
- Faciliter la commande et la livraison des produits par les clients.
  
- Offrir une traçabilité des opérations (commandes, stocks, paiements, livraisons).
  
- Permettre la gestion multi-boutiques et multi-utilisateurs.
  
- Garantir la rentabilité à la commerçante par une marge gérée automatiquement.
  

#### **Objectifs secondaires :**

- Proposer des statistiques de ventes et de performance.
  
- Optimiser la gestion des stocks avec alertes automatiques.
  
- Intégrer les solutions de paiement locales (Mobile Money, carte bancaire).
  
- Simplifier les interactions entre commerçant, livreurs, clients et modérateurs.
  

---

### **1.3. Description fonctionnelle**

#### **1.3.1. Profils d’utilisateurs**

| Rôle | Description | Accès |
| --- | --- | --- |
| **Administrateur système** | Supervise l’ensemble de la plateforme, gère les rôles et configurations globales. | Accès complet à tous les modules. |
| **Commanditaire / Commerçante principale** | Propriétaire de la boutique principale. Gère le stock, les ventes, les marges et les paiements. | Tableau de bord de gestion, supervision. |
| **Modérateurs (assistants)** | Gèrent les commandes, la clientèle, les livraisons, et assistent la commerçante. | Accès partiel (commandes, produits, clients). |
| **Clients** | Passent leurs commandes, consultent les produits, paient en ligne ou à la livraison. | Interface e-commerce simplifiée. |
| **Livreurs** | Prennent en charge les livraisons, gèrent les statuts des livraisons, confirment la réception. | Application mobile dédiée. |

---

#### **1.3.2. Modules fonctionnels**

1. **Module d’authentification**
  
  - Inscription / Connexion (Email, Téléphone, Réseaux sociaux, OTP).
    
  - Authentification sécurisée (OAuth2, JWT).
    
  - Gestion des rôles et permissions.
    
  - Réinitialisation du mot de passe (mail ou SMS).
    
2. **Module de gestion des produits**
  
  - Création, édition et suppression de produits.
    
  - Classification par catégorie (alimentaire, boissons, hygiène…).
    
  - Gestion des prix, promotions et marges.
    
  - Gestion des stocks avec alertes sur rupture.
    
  - Importation massive via fichier Excel/CSV.
    
  - Gestion d’images produits (galerie).
    
3. **Module de gestion des commandes**
  
  - Passage de commande (en ligne ou physique).
    
  - Paiement immédiat ou à la livraison.
    
  - Suivi du statut : *en attente*, *en préparation*, *en livraison*, *livré*.
    
  - Notifications automatiques (SMS / email / push).
    
  - Facturation automatique (PDF).
    
4. **Module de gestion des livraisons**
  
  - Attribution automatique ou manuelle des livreurs.
    
  - Géolocalisation du livreur (via GPS mobile).
    
  - Calcul des frais de livraison (distance + volume).
    
  - Signature électronique du client à la réception.
    
5. **Module de gestion des utilisateurs**
  
  - Création de comptes par rôle.
    
  - Suspension, réinitialisation ou suppression de compte.
    
  - Historique des activités.
    
6. **Module de gestion des paiements**
  
  - Intégration Mobile Money (MTN, Moov).
    
  - Intégration carte bancaire (Visa/MasterCard via PayGate, PayDunya, CinetPay).
    
  - Gestion des paiements internes (crédits clients).
    
  - Suivi des transactions et états de paiement.
    
7. **Module de reporting / statistiques**
  
  - Statistiques des ventes journalières, hebdomadaires, mensuelles.
    
  - Suivi des produits les plus vendus.
    
  - Suivi de performance des livreurs.
    
  - Marge bénéficiaire automatique par commande.
    
  - Tableau de bord analytique interactif.
    
8. **Module de communication**
  
  - Chat interne entre commerçante, modérateurs et livreurs.
    
  - Notifications push pour les statuts de commande.
    
  - Système de ticket d’assistance client.
    
9. **Module de gestion du supermarché**
  
  - Gestion multi-rayons et multi-caisses.
    
  - Enregistrement des ventes physiques (via code-barres).
    
  - Synchronisation entre vente physique et stock en ligne.
    
10. **Module d’administration système**
  
  - Gestion des paramètres globaux (TVA, devise, taux de marge).
    
  - Sauvegarde et restauration des données.
    
  - Journalisation des actions.
    
  - Gestion des mises à jour et sécurité.
    

---

### **1.4. Exigences techniques**

#### **1.4.1. Architecture**

- Architecture **modulaire** basée sur microservices.
  
- Backend : **Django / Django REST Framework** ou **Spring Boot**.
  
- Frontend : **ReactJS / Next.js** pour le web, **React Native** pour mobile.
  
- Base de données : **PostgreSQL** (principale), **Redis** (cache), **MongoDB** (logs et historiques).
  
- Hébergement cloud : **AWS**, **DigitalOcean**, ou **OVH**.
  
- Sécurité : HTTPS, CSRF, JWT, chiffrement AES-256 pour données sensibles.
  
- Sauvegarde automatique des données tous les jours.
  

#### **1.4.2. Accessibilité**

- Responsive design (ordinateur, tablette, smartphone).
  
- Interface légère adaptée aux connexions faibles (optimisée pour le Bénin).
  
- Multilingue : Français (par défaut), Anglais, Fon (option).
  

#### **1.4.3. Ergonomie**

- Interface épurée et intuitive.
  
- Système de navigation simplifié (menu latéral + raccourcis).
  
- Tableau de bord dynamique et visuel.
  

---

### **1.5. Exigences non fonctionnelles**

- **Performance :** Temps de chargement < 3 secondes.
  
- **Sécurité :** Données encryptées, journalisation complète, rôles hiérarchisés.
  
- **Fiabilité :** Disponibilité > 99 %.
  
- **Évolutivité :** Possibilité d’ajouter d’autres commerces et partenaires.
  
- **Compatibilité :** Android 6+, iOS 12+, navigateurs modernes.
  

---

### **1.6. Livrables attendus**

- Étude de conception (UML, maquettes Figma).
  
- API REST documentée (Swagger / Postman).
  
- Interface web et mobile complète.
  
- Manuel utilisateur + manuel d’administration.
  
- Tests unitaires, d’intégration et de charge.
  
- Documentation technique.
  

---

### **1.7. Planning prévisionnel**

| Phase | Description | Durée estimée |
| --- | --- | --- |
| Étude & conception | Analyse, maquettes, spécifications | 3 semaines |
| Développement backend | API, modèles, sécurité | 6 semaines |
| Développement frontend | Web + Mobile | 6 semaines |
| Intégration & tests | QA, corrections | 3 semaines |
| Déploiement & formation | Mise en ligne, formation | 2 semaines |

---

### **1.8. Budget estimatif**

- Développement : ~ 6 000 000 FCFA
  
- Hébergement & maintenance annuelle : ~ 700 000 FCFA
  
- Formation & documentation : ~ 300 000 FCFA
  

---

## ⚙️ **2. Règles de gestion du projet MumShop**

---

### **2.1. Règles générales**

- Chaque utilisateur doit disposer d’un **profil unique**.
  
- L’accès aux fonctionnalités dépend strictement du **rôle**.
  
- Toute opération sensible (paiement, suppression, mise à jour) est **journalisée**.
  
- Le système doit pouvoir fonctionner même en cas de coupure de réseau (mode offline partiel).
  

---

### **2.2. Règles de gestion par rôle**

#### **Administrateur système**

- En tant qu’administrateur système, je peux :
  
  - Créer, modifier ou supprimer des comptes utilisateurs.
    
  - Gérer les permissions et les rôles.
    
  - Configurer les paramètres globaux (TVA, frais, devise, marges).
    
  - Superviser les statistiques générales et la santé du système.
    
  - Intervenir sur les paiements et transactions.
    

#### **Commerçante (commanditaire)**

- En tant que commerçante, je peux :
  
  - Ajouter, modifier, ou supprimer mes produits.
    
  - Fixer mes prix, marges et promotions.
    
  - Gérer mon stock et recevoir des alertes de rupture.
    
  - Consulter l’historique de mes ventes et mes revenus.
    
  - Gérer les modérateurs et livreurs liés à mon commerce.
    
  - Approuver ou refuser une commande avant traitement.
    

#### **Modérateurs**

- En tant que modérateur, je peux :
  
  - Gérer les produits (ajout, modification, suppression).
    
  - Valider et suivre les commandes des clients.
    
  - Communiquer avec les clients pour assistance.
    
  - Assigner un livreur à une commande.
    
  - Accéder aux rapports partiels de ventes.
    

#### **Clients**

- En tant que client, je peux :
  
  - Créer un compte et me connecter facilement.
    
  - Parcourir les produits et filtrer par catégorie.
    
  - Ajouter des produits au panier et passer une commande.
    
  - Choisir mon mode de paiement (Mobile Money, carte, à la livraison).
    
  - Suivre l’état de ma commande en temps réel.
    
  - Évaluer le service et déposer un avis.
    

#### **Livreurs**

- En tant que livreur, je peux :
  
  - Voir les commandes qui me sont attribuées.
    
  - Confirmer la prise en charge d’une livraison.
    
  - Mettre à jour le statut (en route, livré).
    
  - Enregistrer la signature ou la confirmation du client.
    
  - Visualiser mon historique de livraisons et mes gains.
    

---

### **2.3. Règles spécifiques**

- Une commande ne peut être annulée **qu’avant** le statut “en préparation”.
  
- Le stock d’un produit est décrémenté **uniquement** après confirmation de paiement.
  
- Une livraison est considérée comme terminée **uniquement après signature du client**.
  
- Les promotions doivent avoir une **date de début et de fin**.
  
- Le système calcule automatiquement la **marge bénéficiaire** sur chaque vente.
  
- En cas d’échec de paiement, la commande reste **en attente** pendant 24h.
  
- Les notifications sont envoyées automatiquement à chaque changement de statut.
  

---