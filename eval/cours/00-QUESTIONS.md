# questions / réponses

**remarque préliminaire** à propos du vocabulaire:

room = group = channel = discussion = conversation = topic = forum  
**tous ces mots sont synonymes** dans le contexte de ce projet

---

### Q

> J'ai ajouté plusieurs issues en cours au projet que je continuerai demain. En particulier, j'aimerai ajouter une fonctionnalité pour ajouter une room et pour le rejoindre ou quitter mais je ne sais pas comment gérer la gestion des rooms avec le websocket et SQLdatabase. 
Je me demandais aussi comment faire pour afficher qui sont les utilisateurs en ligne sur dans une room. 

### A

une façon naïve de traiter ce sujet consiste à concevoir 4 tables dans la base de données:
- une table `users` qui contient les utilisateurs
- une table `rooms` qui contient les groupes
- une table `subscriptions` qui contient les abonnements des utilisateurs aux groupes
- une table `messages` qui contient les messages écrits par les utilisateurs dans les groupes

au dessus de quoi vous pouvez créer une API pour ajouter/enlever des éléments de ces 4 types

du coups si nécessaire vous pouvez créer un endpoint dans l'API pour afficher les utilisateurs en ligne dans une room (ce n'est pas demandé hein)

les websockets vont nous être utiles uniquement pour faire du 'push' de messages: lorsqu'un utilisateur écrit un message dans un groupe, on veut que les autres utilisateurs présents dans ce groupe reçoivent ce message sans avoir à rafraîchir la page; on peut se contenter d'utiliser les websockets pour cette fonctionnalité-là

---

### Q

> Je me demandais comment je pouvais séparer proprement les modèles SQL (User, Group, Message) des modèles UserCreate, GroupCreate et MessageCreate ?

### A

ce qu'on fait souvent, pour ne pas avoir à se répéter (on déteste se répéter parce que lorsqu'il y a une modification à faire, on oublie une fois sur deux de la reporter dans la copie, et du coup on se retrouve avec des bugs):

```
class UserCreate(SQLModel):
    name: str = Field(description="Username")

class User(UserCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

de cette façon:
- dans `UserCreate` a un seul champ `name`
- comme `User` hérite de `UserCreate`, il a aussi un champ `name` (le même)
- mais `User` a aussi un champ `id` qui lui est propre, et qui est généré automatiquement par la base de données

donc c'est un code équivalent à ceci, mais qui évite la répétition du champ `name` (et dans la vraie vie il y aurait sans doute d'autres champs que `name`)

```
class UserCreate(SQLModel):
    name: str = Field(description="Username")

class User(SQLModel, table=True):
    name: str = Field(description="Username")
    id: int | None = Field(default=None, primary_key=True)
```

---

### Q

> Bonjour Monsieur,
Ma question concerne la façon dont un utilisateur doit etre notifié de l'arrivée d'une réponse et doit pouvoir y répondre. Comment créer des groupes whats'app? Pour savoir qui est en ligne il faut que les utilisateurs s'identifient en arrivant? 

### A

- pour les notifications, l'utilisateur n'a rien à faire d'autre que d'ouvir la page du groupe

- l'énoncé ne demande pas de faire des pages d'admin; on crée un groupe par la ligne de commande  
voyez la section "create users and rooms" dans l'énoncé

- effectivement l'utilisateur qui se présente pour la première fois choisit un nom d'utilisateur dans la liste des utilisateurs connus  
  on ne demande pas
  - de faire une page de 'signup' (enregistrement),
  - ni de faire de l'authentification avec mot de passe  
  ce serait du bonus

  on ne demande pas non plus de s'assurer qu'un nom d'utilisateur n'est utilisé que par un seul client à la fois, car ça dans la vraie vie on ne le fait pas non plus, une personne peut très bien utiliser en même temps son ordi et son télephone

---

### Q

> Ma question correspond à la manière de créer une conversation, je ne sais pas comment créer une conversation que peuvent rejoindre les différents utilisateurs ni comment faire pour qu'ils aient accès à l'historique de cette conversation.

### A

Pareil, voyez l'énoncé, section "create users and rooms" pour la création de groupes (conversations)

---

### Q

> Comment peut on faire pour ajouter des gens à des groupes ou lancer des discussions simplement avec leur pseudo, et pas leur numéro de téléphone si on a bien vérifié qu’il n’y avait pas de doublons?

### A 

le workflow dans l'esprit est le suivant:

- l'administrateur a accès au terminal et peut créer:
  - des utilisateurs - chaque utilisateur a un nom unique; si vous voulez ajouter des infos comme email et téléphone c'est possible mais c'est du bonus
  - des groupes - essentiellement un groupe c'est juste un nom unique
  
- lorsqu'un utilisateur se connecte à l'application:
  - il choisit une fois pour toutes un utilisateur dans la liste
  - il a ensuite accès à une page lui affichant les groupes, à partir de quoi il peut:
    - s'abonner ou se désabonner
    - et 'entrer' dans un groupe, ce qui le fait accéder à une page dédiée à ce groupe
- et dans la page dédiée au groupe on lui affiche les messages diffusés dans ce groupe
  - il peut lui aussi y écrire des messages
  - et les messages écrits par lui ou les autres utilisateurs sont affichés au fur et à mesure de leur envoi

---

### Q

> 1. Pour la connexion WebSocket, je n'ai pas géré le cas où un même utilisateur ouvre plusieurs onglets en même temps. Dans mon broadcaster chaque nouvelle connexion écrase la précédente, du coup le premier onglet ne reçoit plus les messages. Est-ce que c'était attendu de gérer ça ou c'est acceptable de le laisser comme ça ?

### A

je n'ai pas la réponse il faudra que je voie votre code de plus près  
en théorie, deux onglets différents se présentent comme deux clients différents et normalement ne devraient pas interférer l'un avec l'autre; sauf lorsqu'on utilise un cookie (auquel cas les deux onglets vont avoir le même cookie)  
mais bon de manière générale on va dire à notre niveau que si le seul défaut de votre app c'est ça, ce n'est pas grave du tout :-)

---

### Q

> Pourquoi est-il préférable d'utiliser une fonction lifespan pour créer les tables de la base de données plutôt que de le faire directement au lancement du script ?

### A

l'idée est de pouvoir retarder au maximum l'operation; bien souvent en effet, au moment où on exécute le script lui même, on est en pleine initialisation de l'aplication, et on peut ne pas être prêt à faire des opérations de ce type; avec cette technique l'opération au dernier moment, i.e. juste avant de traiter la première requête, ce qui est plus sûr.

---

### Q

> Je n'ai pas bien compris la différence entre le server side rendering utilisé au chargement de la page et le client side rendering

### A

concrètement dans l'appli de notes:

- le server-side rendering est le code dans le template, qui produit la 'boite' correspondant à chaque note  
  https://github.com/ue22-p25/backend-fastapi-notes-steps/blob/main/templates/notes.html.j2#L24-L33
- le client-side rendering est le code dans le fichier `static/js/notes.js` qui produit la 'boite' correspondant à chaque note  
  https://github.com/ue22-p25/backend-fastapi-notes-steps/blob/main/static/js/clientside-rendering.js#L1-L13

vous pouvez vous convaincre que les deux produisent exactement la même chose, à savoir une 'boite' correspondant à une note, mais que dans le premier cas c'est le serveur qui produit le code HTML de cette boite, alors que dans le second cas c'est le client qui produit ce code HTML

---

### Q

> Pourquoi utilise-t-on WebSocket pour mettre à jour la liste des notes au lieu de demander simplement au navigateur de rafraîchir la page toutes les 5 secondes ?

### A

effectivement on pourrait faire comme ça, mais:

- imaginez le nombre de messages inutiles que ça créerait: pendant tout le temps où les applis sont "idle" - c'est-à-dire la majorité du temps - elles seraient en train de faire des requêtes pour rien, ce qui serait une perte de ressources considérable
- vous utilisez sans doute quotidiennement une appli genre what's app; quel est le temps de réaction qui vous semble 'supportable' ? accepteriez-vous de devoir attendre 5 secondes pour voir le message que votre interlocuteur vient de vous envoyer ? pour la plupart des gens, la réponse est non (enfin, c'est oui mais pas pour tous les types d'interaction...); pour passer à 1s, cela reviendrait à multiplier par 5 le nombre de messages inutiles...

bref c'est une question de performance et d'expérience utilisateur

---

### Q

> Pourquoi la bonne pratique est de créer des classes différentes comme Note create au lieu d'utiliser uniquement la classe Note pour toutes les opérations de l'API ?

### A

le cas d'usage le plus évident, c'est le mot de passe des utilisateurs; quand on crée un utilisateur on fournit un mot de passe; par contre quand on lit un utilisateur, on ne veut pas exposer sont mot de passe

autre cas d'usage, le champ `id` des objets, qui est un champ qu'on ne peut plus modifier une fois l'objet créé; du coup, on le mentionnerait dans NoteRead, mais pas dans NoteUpdate; aussi il ne fait typiquement pas partie de NoteCreate puisque c'est la base de données qui va le générer

dans le cas de relations entre objets également: lorsque vous créez un message, vous allez juste fournir un `user_id`; maintenant peut-être que lorsqu'on lit un message on va préférer exposer un champ `user` qui contient **toutes les infos de l'utilisateur** plutôt que juste son id - pour éviter à l'appelant de devoir reposter immédiatement une seconde requête pour y accéder; ce sont des compromis qu'on fait en fonction des besoins de l'application et de la logique métier

---

### Q

> Pendant que je faisais le sujet, j’ai eu un problème que je n’ai pas bien compris. Dans le sujet, la commande pour créer un utilisateur (même chose pour les rooms), c’est http POST localhost:8000/users name=alice mais ça ne marche pas avec mon code, la commande qui marche avec ce que j’ai fait, c’est http POST localhost:8000/users?name=alice 

### A

cette question résonne avec les différents types de paramètres qu'on peut passer en HTTP:

https://backend.info-mines.paris/fastapi-basics/#more-kinds-of-parameters

en fait en temps que développeur de l'API on a le choix:

- Body parameters: on décide qu'il faut passer les paramètres dans le corps de la requête, auquel cas on s'attend à ce que l'appelant fasse `http POST localhost:8000/users name=alice` (mon approche)
- Query parameters: on décide qu'il faut passer les paramètres dans la query string, auquel cas on s'attend à ce que l'appelant fasse `http POST localhost:8000/users?name=alice` (votre approche)

les deux fonctionnent en pratique; MAIS la "bonne pratique" est la première...  
c'est une question de convention et de logique métier; notamment c'est compliqué de passer des objets complexes dans la query (je veux dire: imbriqués, ou avec des espaces ou des caractères spéciaux)

cett section du cours devrait vous aider pour changer le mode de passage des paramètres

https://backend.info-mines.paris/fastapi-basics/#capturing-parameters-in-the-fastapi-route-handler

---

### Q

> 2. Quand on supprime un salon j'ai choisi de supprimer aussi tous les messages associés. Mais pour la suppression d'un utilisateur j'ai gardé ses messages dans la base. Est-ce qu'il y avait une approche préférée ?

### A

à nouveau on est dans le domaine du bonus et du second ordre  
dans la vraie vie on aurait sans doutes des contraintes légales; il semble que ce serait mieux de ne rien supprimer du tout (mais juste marquer `disabled`) de manière à être capable de récrire l'histoire en cas de besoin  
mais bon, pour notre projet, les deux approches me vont

