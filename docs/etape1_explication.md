# Étape 1 expliquée pas à pas — données, dérive simulée et versionnage

> 25/11/2026 · Lamine CAMARA · support pour le point mentor
> Décisions détaillées : [fiche de suivi, étape 1](fiche_taches_projet15.md#étape-1--données-et-versionnage-semaine-1-6-h)

**Objectif de l'étape :** préparer des données qui racontent une histoire. D'abord un modèle qui
fonctionne, puis un monde qui change, puis un modèle qui se dégrade. Tout le reste du projet
(détection de dérive, réentraînement, promotion) repose sur ces données.

---

## Pas 1 — Récupérer les données

**Ce qui a été fait :** copie de `application_train.csv` (307 511 demandes de crédit, 166 Mo)
depuis le Projet 6 vers `data/raw/`.

**Pourquoi ce fichier seul :** au P6, le modèle utilisait 804 features construites à partir de
8 tables jointes (3,5 Go). Un réentraînement aurait été trop lent pour une boucle que l'on veut
rejouer plusieurs fois. Le cadrage a donc réduit le périmètre à la table principale.

> **À retenir :** le sujet n'est pas d'améliorer le modèle, c'est de construire la boucle autour
> de lui. Un réentraînement doit prendre quelques secondes.

---

## Pas 2 — Choisir les features (décision D1)

**Le problème découvert :** le cadrage prévoyait de reprendre les 30 features surveillées au P8.
En vérifiant, 13 d'entre elles viennent des tables jointes (historique bancaire, anciennes
demandes) et n'existent pas dans `application_train`.

**Les 21 features retenues :**

| Groupe | Features | Transformation |
|---|---|---|
| 14 colonnes numériques brutes | `EXT_SOURCE_1/2/3` (scores externes, les plus prédictifs), montants (`AMT_*`), âge (`DAYS_BIRTH`), ancienneté (`DAYS_EMPLOYED`), etc. | `DAYS_EMPLOYED = 365243` (valeur sentinelle « sans emploi ») remplacée par une valeur manquante, comme au P6 |
| 3 colonnes texte | `CODE_GENDER_F`, `EDUCATION_LEVEL`, `NAME_FAMILY_STATUS_Married` | sexe → 1/0 ; niveau d'études → 0 à 4 dans l'ordre ; marié → 1/0 |
| 4 ratios métier du P6 | `CREDIT_TERM`, `ANNUITY_INCOME_PERCENT`, `CREDIT_INCOME_PERCENT`, `DAYS_EMPLOYED_PERCENT` | durée du crédit, taux d'effort, endettement, part de la vie en emploi |

**Pourquoi tout en nombres :** l'API recevra directement des nombres et n'aura aucun encodage à
faire. Il y a donc moins de risque d'écart entre l'entraînement et la production.

**Conséquence :** le modèle du P8 attend 804 features. Il ne peut pas servir de modèle de départ :
un nouveau modèle sera entraîné sur les 21 features.

> **À retenir :** l'audit de l'existant a révélé une incohérence dans le cadrage. Elle a été
> corrigée et la décision documentée (axe « auditer la solution existante »).

---

## Pas 3 — Simuler le temps qui passe

**Le problème :** il n'y a pas de vraie production, seulement un fichier figé.

**La solution :** mélanger les lignes au hasard, avec une graine fixe (42) pour que le résultat
soit reproductible, puis découper :

```
[ Référence : 100 000 ] [ Lot 1 ] [ Lot 2 ] ... [ Lot 8 ]   (25 000 demandes chacun)
```

- **La référence** est le passé connu. Elle sert à entraîner le premier modèle et de point de
  comparaison pour détecter la dérive.
- **Les 8 lots** sont 8 « semaines » de nouvelles demandes.

300 000 lignes sur 307 511 sont utilisées. Le taux de défaut reste proche de 8 % dans chaque lot.

---

## Pas 4 — Les labels arrivent en retard

**Le réalisme :** quand un client demande un crédit, on ne sait pas tout de suite s'il
remboursera. Au P8, il n'y avait d'ailleurs aucun label en production.

**La solution :** chaque lot est enregistré en deux fichiers.

| Fichier | Contenu | Qui le lit |
|---|---|---|
| `data/batches/batch_03.parquet` | Les demandes, sans la réponse | L'API |
| `data/batches/labels_03.parquet` | La réponse (défaut ou non) | La boucle, à partir du lot 4 |

La fonction `load_labels(3, current_batch=3)` refuse de rendre les labels du lot 3 tant que l'on
est au lot 3. Ils ne sont disponibles qu'au lot 4.

> **À retenir :** un retour d'information décalé d'une semaine permet de mesurer la vraie
> performance (AUC, coût métier), et pas seulement un indicateur indirect comme au P8.

---

## Pas 5 — Injecter une dérive (décision D2)

**L'histoire métier :** à partir du lot 3, le bureau de crédit externe change sa façon de
calculer les scores `EXT_SOURCE_2` et `EXT_SOURCE_3`. En même temps, l'inflation fait monter les
montants.

| Ce qui change | Transformation | Effet attendu |
|---|---|---|
| Scores `EXT_SOURCE_2/3` | `x → x^(1 + 2 × intensité)` : 0,5 devient 0,25 à intensité maximale | Les scores baissent, mais l'ordre des clients est conservé. L'information est toujours là, c'est le modèle en place qui ne sait plus la lire : il croit les clients plus risqués |
| Montants `AMT_*` | +15 % à intensité maximale | Revenu et crédit montent ensemble, donc les ratios ne bougent pas. Des colonnes dérivent sans effet sur la performance : un témoin, car toute dérive n'est pas grave |
| Labels `TARGET` | Aucune | Seul ce que voit le modèle change |

**Progressivité :** l'intensité vaut 0 aux lots 1 et 2, puis 1/6, 2/6… jusqu'à 1 au lot 8.

> **À retenir :** la dérive choisie est une dérive que le réentraînement *peut* corriger. Si
> l'information avait été détruite, aucun nouveau modèle n'aurait pu faire mieux et la boucle
> n'aurait rien démontré.

---

## Pas 6 — Vérifier que la dérive fonctionne (calibration)

C'était le risque n°2 du cadrage : une dérive trop faible pour être détectée. L'expérience se
rejoue avec `uv run python scripts/calibrate_drift.py` :

1. Un LightGBM est entraîné sur la référence : c'est le **champion**.
2. Sur chaque lot, on mesure :
    - l'**AUC**, c'est-à-dire la capacité à classer les bons et les mauvais clients ;
    - le **coût métier** = (10 × faux négatifs + faux positifs) / nombre de demandes, règle du P6 ;
    - un **test KS**, qui indique si la distribution des scores prédits a changé par rapport à la
      référence (p < 0,05 signale une dérive).
3. À chaque lot, un **challenger** est entraîné sur la référence et les 2 derniers lots
   labellisés.

| | Lots 1–2 | Lot 3 | Lot 8 |
|---|---|---|---|
| AUC du champion | 0,756 | 0,749 | 0,693 |
| Coût du champion | 0,537 | 0,557 | 0,766 |
| Dérive détectée (KS) | non (p ≈ 0,6) | oui | oui |
| Challenger (AUC / coût) | — | 0,758 / 0,567 | 0,749 / 0,538 |

**Lecture :**

- Aucune fausse alerte quand il n'y a pas de dérive.
- La dérive est détectée dès le lot 3.
- Le champion se dégrade : son coût augmente de 43 % entre le lot 1 et le lot 8.
- Le réentraînement récupère presque toute la performance.
- Au lot 3, le challenger est meilleur en AUC mais plus cher en coût. La règle refusera de le
  promouvoir : le refus est aussi une décision à documenter.

**Point d'attention pour l'étape 3 :** avec 25 000 lignes, le test KS est très sensible et
détecte le moindre écart. D'où la règle du cadrage : réentraîner si **dérive et baisse de
performance**, jamais sur la dérive seule.

---

## Pas 7 — Versionner avec DVC

**Le problème :** Git n'est pas fait pour stocker 166 Mo de CSV, et les données Kaggle ne doivent
pas être publiées.

**Le principe :** Git garde une petite fiche d'identité de chaque fichier (empreinte, taille), et
DVC range le fichier lui-même ailleurs.

| Élément | Rôle |
|---|---|
| `data/raw/application_train.csv.dvc` | L'empreinte du CSV, versionnée par Git (créée par `dvc add`) |
| `dvc.yaml` | La recette de l'étape `prepare` : entrées (le CSV, le code), paramètres, sorties (référence et lots) |
| `params.yaml` | Les paramètres du scénario (graine, tailles, lot de début de dérive), lus par le code **et** par DVC |
| `dvc.lock` | La photo exacte du dernier passage : empreintes des entrées, des paramètres et des sorties |
| `../dvc-storage/projet15` | Le stockage où DVC range les vrais fichiers (local, hors du dépôt), alimenté par `dvc push` |

**Ce que ça apporte :**

- `uv run dvc repro` reconstruit tout en une quinzaine de secondes, et seulement si quelque chose
  a changé (le CSV, le code ou un paramètre).
- Chaque version du modèle pourra dire précisément sur quelles données elle a été entraînée :
  c'est l'un des critères de succès du projet.

> **À retenir :** Git versionne le code et les empreintes des données, DVC versionne les données,
> `params.yaml` centralise les réglages. Le pipeline est donc toujours reproductible.

---

## Pas 8 — Configuration, tests et publication

- **`mlops/config.py`** centralise la configuration : adresse MLflow, base de données, seuil
  métier, paramètres de `params.yaml`. Passer en ligne (paliers 2 et 3) ne demandera que de
  changer des variables d'environnement.
- **`tests/test_data.py`** (12 tests) vérifie :
    - le nettoyage et l'encodage ;
    - le calcul des ratios ;
    - la progressivité de la dérive ;
    - que la dérive conserve l'ordre des scores et ne touche ni aux ratios ni aux labels ;
    - qu'aucun client n'apparaît dans deux jeux ;
    - que les labels sont refusés avant le lot suivant.

  Les tests utilisent de fausses données : ils tournent en CI sans le vrai CSV.
- **Résultat :** 13 tests verts au total, lint propre, CI GitHub verte, décisions D1 et D2
  documentées dans la fiche de suivi.

---

## En une phrase

> J'ai transformé un fichier statique en une production simulée de 8 semaines, avec des labels
> qui arrivent en retard et une dérive réaliste qui commence la semaine 3. J'ai vérifié qu'elle
> dégrade le modèle et qu'un réentraînement peut la corriger, puis j'ai tout versionné avec DVC
> pour que ce soit reproductible.

## Commandes utiles pour la démonstration

```bash
uv run dvc repro                          # reconstruire la référence et les lots
uv run python scripts/calibrate_drift.py  # rejouer la calibration de la dérive
uv run pytest                             # lancer les tests
```
