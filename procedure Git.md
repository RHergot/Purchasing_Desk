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