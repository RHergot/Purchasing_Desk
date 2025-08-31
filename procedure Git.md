Le Workflow de Mise à Jour en 3 Actes
Acte 1 : Le Développement (sur votre PC Windows)
Vous travaillez comme d'habitude : Vous modifiez votre code, ajoutez des fonctionnalités, corrigez des bugs sur votre machine Windows avec votre éditeur.
Vous testez localement : Vous utilisez python manage.py runserver et votre base de données db.sqlite3 pour vous assurer que tout fonctionne parfaitement. C'est votre bac à sable, vous pouvez tout y casser sans risque.
Acte 2 : La Synchronisation (avec GitHub)
Une fois que vous êtes satisfait de vos modifications, vous les "officialisez" en les envoyant sur GitHub.

Ouvrez un terminal à la racine de votre projet sur Windows.
Ajoutez vos modifications :
bash
git add .
Créez un "commit" (un instantané) avec un message descriptif :
bash
git commit -m "Exemple: Ajout de la page de contact"
Poussez votre code vers GitHub :
bash
git push origin main
À ce stade, votre nouveau code est en sécurité sur GitHub, mais pas encore sur le serveur.
Acte 3 : Le Déploiement (sur le serveur VPS)
C'est l'étape finale pour mettre votre site à jour.

Connectez-vous au serveur en SSH.
Allez dans le dossier du projet :
bash
cd /var/www/web_sales
Téléchargez les dernières modifications depuis GitHub :
bash
git pull origin main
Activez l'environnement virtuel :
bash
source venv/bin/activate
(Optionnel mais important) Mettez à jour si besoin :
Si vous avez modifié les modèles (
models.py
) : python manage.py migrate
Si vous avez modifié des fichiers statiques (CSS, JS, images) : python manage.py collectstatic --noinput
Redémarrez l'application pour qu'elle prenne en compte le nouveau code :
bash
Et c'est tout ! Votre site est à jour. Ce processus prend moins d'une minute une fois que vous en avez l'habitude.

clonage : pour cloner le repo sur le serveur
git clone https://github.com/RHergot/Purchasing_Desk.git
git clone https://RHergot:ghp...@github.com/RHergot/Purchasing_Desk.git
Il faut ensuite reconstituer l'environnement virtuel.

source venv/bin/activate


e vais vous guider pour configurer l'environnement virtuel sur votre serveur Ubuntu. Voici les étapes à suivre :

Mettre à jour les paquets système (en tant que root) :
bash
apt update && apt upgrade -y
Installer Python et pip (si ce n'est pas déjà fait) :
bash
apt install python3 python3-pip python3-venv -y
Aller dans le répertoire de votre projet :
bash
cd /chemin/vers/votre/projet
Créer un nouvel environnement virtuel :
bash
python3 -m venv venv
Activer l'environnement virtuel :
bash
source venv/bin/activate
Vous devriez voir (venv) au début de votre invite de commande
Installer les dépendances :
bash
pip install -r requirements.txt
Vérifier l'installation :
bash
pip list

Donner les droits rw répertoire au groupe users

e vais vous aider à configurer les permissions pour le répertoire Purchasing_Desk. Voici les commandes à exécuter sur votre serveur Ubuntu :

Définir le groupe propriétaire (remplacez /chemin/vers/Purchasing_Desk par le chemin réel) :
bash
sudo chgrp -R users /chemin/vers/Purchasing_Desk
Définir les permissions pour permettre la lecture/écriture au propriétaire et au groupe, et lecture seule aux autres :
bash
sudo chmod -R 775 /chemin/vers/Purchasing_Desk
Définir le bit setgid pour que les nouveaux fichiers et dossiers héritent du groupe parent :
bash
sudo chmod g+s /chemin/vers/Purchasing_Desk
Vérifier les permissions :
bash
ls -ld /chemin/vers/Purchasing_Desk
Explications :

chgrp -R : Change le groupe propriétaire de manière récursive
chmod 775 : Donne tous les droits au propriétaire et au groupe, lecture et exécution aux autres
g+s : Assure que les nouveaux fichiers créés auront le même groupe que le répertoire parent

## Configuration du serveur de production

### Variables d'environnement
Créez un fichier `.env` à la racine du projet avec les variables nécessaires :
```bash
cp .env.example .env  # Si vous avez un exemple
nano .env            # Éditez les variables
```

### Gestion des processus PM2
Pour faire tourner l'application en arrière-plan :
```bash
# Installation de PM2
sudo npm install -g pm2

# Démarrer l'application
pm2 start --name=purchasing_desk python -- app.py

# Activer le démarrage automatique
pm2 startup
pm2 save

# Commandes utiles
pm2 status         # Voir l'état
pm2 logs           # Voir les logs
pm2 restart all    # Redémarrer
```

## Maintenance

### Sauvegardes
```bash
# Sauvegarde de la base de données (exemple pour PostgreSQL)
pg_dump -U utilisateur -d nom_bdd > backup_$(date +%Y%m%d).sql

# Sauvegarde des fichiers importants
tar -czvf backup_$(date +%Y%m%d).tar.gz /chemin/vers/important
```

### Mises à jour de sécurité
```bash
# Mettre à jour le système
sudo apt update
sudo apt upgrade -y

# Mettre à jour les packages Python
pip list --outdated
pip install --upgrade package_name
```

## Dépannage courant

### Vérifier l'espace disque
```bash
df -h
```

### Voir les logs d'erreur
```bash
# Logs système
journalctl -u votre_service -n 50 --no-pager

# Logs PM2
pm2 logs --lines 100
```

## Sécurité

### Mettre à jour les clés SSH
```bash
# Générer une nouvelle clé SSH
ssh-keygen -t ed25519 -C "votre@email.com"

# Ajouter la clé à l'agent
ssh-add ~/.ssh/id_ed25519
```

### Renouveler les tokens d'API
Pensez à mettre à jour régulièrement :
- Tokens d'API
- Mots de passe
- Clés secrètes

## Redémarrage des services
Après certaines modifications, il peut être nécessaire de redémarrer :
```bash
# Redémarrer le serveur web
sudo systemctl restart nginx  # ou apache2

# Redémarrer PM2
pm2 restart all
```