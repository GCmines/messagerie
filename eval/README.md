# Mini WhatsApp - Evaluation project
Projet d'Adrien Mounier & Gaspard Chupin

Suite à plusieurs problèmes de commits (impossible pour l'un de nous deux d'accéder "proprement" au repo de l'autre), on a dû faire un peu de bricolage à ce niveau là en créant de nouveaux repo pour se partager le code avant de le recopier dans ce repo "eval"

## Description
Petit projet de chat en temps réel utilisant FastAPI, WebSockets et SQLite.  
Les utilisateurs et les rooms sont créés via des requêtes HTTP (ligne de commande ou HTTP client). Les utilisateurs peuvent s'abonner à des rooms, puis se connecter via WebSocket pour envoyer/recevoir des messages.

## Structure
eval/
├─ `main.py` : application FastAPI (REST + WebSocket).
├─ `database.py` : configuration SQLite / SQLAlchemy.
├─ `models.py` : modèles ORM (User, Room, Subscription, Message).
├─ `schemas.py` : schémas Pydantic.
├─ `manager.py` : gestion des connexions WebSocket par room.
├─ `requirements.txt` : dépendances.
├─ `README.md` : le présent fichier
└─ `static/` : frontend minimal.
   ├─ index.html
   └─ chat.html


## Ports usuels
8000


## Rejoindre nos discussions étape par étape

### Installer ce qu'il faut
Ouvrir un bash puis copier cette ligne : pip install -r requirements.txt
(le fichier requirements.txt comprend tout ce qui est nécessaire pour le bon fonctionnement du code)

### Ouvrir le client
Toujours dans le bash, rentrer dans le repo et exécuter cette ligne : python main.py
Puis : uvicorn main:app --reload --host 127.0.0.1 --port 8000
Pour lancer le serveur sur le port 8000
Accédez à http://127.0.0.1:8000/static/index.html sur un navigateur

### Créer un username
À l'ouverture, l’interface demande un nom d’utilisateur.
Saisissez un pseudo unique et validez. Le pseudo est stocké en session via localStorage.

### Voir la liste des rooms
La page principale affiche les rooms disponibles et le nombre de participants en ligne.

### Rejoindre une room existante
Rentrez votre pseudo dans le champ approprié, sélectionnez la room via la liste, n'oubliez pas de d'abord cliquer sur "susbscribe" avant de rentrer dans la room!

### Créer une nouvelle room
Utilisez le champ Créer une room, entrez un nom et validez. La room apparaît dans la liste et vous y êtes automatiquement ajouté.

### Envoyer un message
Tapez votre message dans la zone de saisie et cliquez sur Envoyer (Send).
Les messages sont diffusés en temps réel à tous les participants via WebSocket.

### Recevoir des messages
Les nouveaux messages s’affichent instantanément  (sans besoin de rafraichir manuellement la page). Chaque message montre l’auteur, l’horodatage, et le contenu.

### Quitter une room
Cliquez sur Quitter (Leave) ou fermez l’onglet. La présence est mise à jour côté serveur et les autres participants sont notifiés.


## Dépannage rapide
Problèmes qui sont arrivés lors du dev et façon de les résoudre : 
Client qui ne se connecte pas : vérifier que le serveur WebSocket tourne et que l’URL/port sont corrects dans la config du client.
Nom d’utilisateur déjà pris : choisir un autre pseudo ou vérifier la validation côté serveur.
Pas d’historique de messages : vérifier la connexion à la base de données et les logs du serveur.
Logs utiles : consulter la console du serveur et la console du navigateur pour les erreurs réseau et WebSocket.
