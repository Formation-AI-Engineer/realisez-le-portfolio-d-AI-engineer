"""Point d'entrée FastAPI (étape 2).

À implémenter, en reprenant l'API du Projet 8 :
- charger ``models:/<MODEL_NAME>@<MODEL_ALIAS>`` au démarrage ;
- ``POST /predict`` : prédiction + journalisation dans Postgres ;
- ``POST /admin/reload`` : recharger le modèle après une promotion, sans redéploiement ;
- ``GET /health`` et ``GET /model/info`` (version servie).
"""
