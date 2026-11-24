# Fiche de suivi — Projet 15

**Sujet** : Réalisez le portfolio d'AI Engineer
**Projet technique** : boucle MLOps fermée sur le scoring crédit Prêt à Dépenser (suite des Projets 6 et 8)
**Cadrage** : [`fiche_cadrage_projet15.md`](fiche_cadrage_projet15.md)
**Charge** : environ 60 h sur 3 semaines pour le palier 1, + 4 à 5 h pour le palier 2, + 6 à 8 h pour le palier 3 (contrainte de délai forte : le périmètre reste minimal)

## Paliers de livraison

| Palier | Contenu | Statut |
|--------|---------|--------|
| 1 — Local | Boucle complète avec `docker compose`, démo en direct et vidéo | Obligatoire |
| 2 — Vitrine en ligne | Space Hugging Face qui rejoue le scénario (résultats exportés, sans données brutes) | Conseillé |
| 3 — Boucle en ligne | DagsHub (MLflow + DVC), Neon, Hugging Face, GitHub Actions | Seulement s'il reste du temps |

Règle : on n'attaque un palier que lorsque le précédent est terminé et présentable.

## Livrables (énoncé)

Un seul dépôt sur la plateforme : un zip `Titre_du_projet_CAMARA_Lamine` contenant `CAMARA_Lamine_1_portfolio_mmaaaa`. Ce livrable est un lien vers un portfolio en ligne ou un PDF. Il inclut :

- le rapport de conduite de projet data ;
- le lien vers le projet technique.

Soutenance de 30 min : 15 min de présentation (de 10 à 20 min), 10 min de discussion (l'évaluateur joue Charlotte), 5 min de débrief.

## Compétences évaluées (les 5 axes de Myriam)

| Axe | Où il est démontré |
|-----|--------------------|
| Collecter les besoins métier et analyser le contexte | Fiche de cadrage §Contexte, rapport §1 |
| Auditer la solution data existante | Audit du P8 (fiche de cadrage, rapport §2) |
| Identifier une solution technique | Architecture de la boucle, choix de la stack |
| Apporter un appui stratégique pour la décision | Règles champion/challenger, dashboard des décisions |
| Contrôler délais, coûts, livrables, performance | Ce suivi, planning réel vs prévu, critères de succès |

## Étape 0 — Cadrage (semaine 1, 5 h)

- [x] Lire les PDF de la mission et analyser les projets du parcours
- [x] Rédiger la fiche de cadrage
- [x] Faire valider le sujet par le mentor (validé le 24/11/2026)
- [x] Choisir le support du portfolio : **GitHub Pages** (24/11/2026)
- [x] Créer le dépôt GitHub (`Formation-AI-Engineer/realisez-le-portfolio-d-AI-engineer`)

## Étape 1 — Données et versionnage (semaine 1, 6 h)

- [x] Copier `application_train.csv` dans `data/raw/` (non versionné par Git, suivi par DVC)
- [x] Choisir les features : 21 features (voir décision D1)
- [x] Découper en référence + 8 lots, injecter une dérive progressive dès le lot 3 (`mlops/data.py`)
- [x] Calibrer l'amplitude de la dérive (voir décision D2)
- [x] Initialiser DVC (stockage distant local `../dvc-storage/projet15`), pipeline `dvc.yaml` (étape `prepare`) et paramètres dans `params.yaml`
- [x] Tests `tests/test_data.py` (13 tests au total, verts)

**D1 — Features (24/11/2026).** Sur les 30 features surveillées au P8, 13 viennent des tables jointes (`bureau`, `previous_application`, etc.) et n'existent pas dans `application_train`. Retenues : 14 colonnes numériques brutes (dont `EXT_SOURCE_1/2/3`, montants, `DAYS_*`), 3 colonnes catégorielles encodées en nombres (`CODE_GENDER_F`, `EDUCATION_LEVEL`, `NAME_FAMILY_STATUS_Married`) et 4 ratios métier du P6 (`CREDIT_TERM`, `ANNUITY_INCOME_PERCENT`, `CREDIT_INCOME_PERCENT`, `DAYS_EMPLOYED_PERCENT`). Toutes numériques : l'API n'a pas d'encodage à faire. Conséquence : le modèle du P8 (804 features) ne peut pas servir de champion initial, un nouveau modèle de départ est entraîné sur la référence.

**D2 — Scénario de dérive (24/11/2026).** Scénario métier : le bureau de crédit externe change sa méthode de calcul de `EXT_SOURCE_2` et `EXT_SOURCE_3` (transformation `x ** (1 + 2 × intensité)`), et les montants suivent une inflation de 15 % à intensité maximale. L'intensité croît de 1/6 au lot 3 à 1 au lot 8. Les labels ne sont pas modifiés. Découpage : référence de 100 000 lignes, 8 lots de 25 000.

Calibration (LightGBM entraîné sur la référence, challenger = référence + 2 derniers lots labellisés) :

| Lot | AUC champion | Coût champion | KS du score (p) | AUC challenger | Coût challenger |
|---|---|---|---|---|---|
| 1 | 0,756 | 0,537 | 0,54 | — | — |
| 2 | 0,757 | 0,537 | 0,66 | — | — |
| 3 | 0,749 | 0,558 | < 10⁻¹⁷⁰ | 0,759 | 0,567 |
| 4 | 0,742 | 0,606 | ≈ 0 | 0,755 | 0,547 |
| 5 | 0,724 | 0,661 | ≈ 0 | 0,744 | 0,568 |
| 6 | 0,712 | 0,700 | ≈ 0 | 0,743 | 0,559 |
| 7 | 0,715 | 0,729 | ≈ 0 | 0,759 | 0,541 |
| 8 | 0,693 | 0,766 | ≈ 0 | 0,749 | 0,538 |

Coût = (10 × FN + FP) / nombre de demandes. Lecture : aucune fausse alerte sans dérive ; dérive détectée dès le lot 3 ; le champion perd 0,06 d'AUC et 43 % de coût en plus ; le réentraînement récupère presque tout. Au lot 3, le challenger est moins bon en coût : un refus de promotion à documenter. À noter pour l'étape 3 : avec 25 000 lignes, le test KS est très sensible, d'où l'intérêt d'exiger aussi une baisse de performance pour déclencher.

## Étape 2 — Registre et API (semaine 1, 6 h)

- [ ] Lancer le serveur MLflow (backend SQLite, artefacts locaux)
- [ ] Faire passer toutes les adresses par la configuration (`MLFLOW_TRACKING_URI`, `DATABASE_URL`) pour préparer les paliers 2 et 3
- [ ] Entraîner le modèle initial, l'enregistrer et lui poser l'alias `@champion` (`mlops/training.py`, `mlops/registry.py`)
- [ ] Faire charger `models:/credit-scoring@champion` par l'API, avec un rechargement à chaud (`app/`)
- [ ] Journaliser les prédictions dans Postgres (repris du P8)

## Étape 3 — Boucle de réentraînement (semaine 2, 10 h)

- [ ] Dérive (Evidently) et performance (AUC, coût métier) par lot (`mlops/drift.py`)
- [ ] Règle de déclenchement, puis réentraînement du challenger
- [ ] Comparaison champion/challenger sur le même jeu de test, promotion ou refus
- [ ] Rafraîchir la référence de dérive après une promotion (versionnée avec DVC)
- [ ] `scripts/run_cycle.py` : rejouer un lot ou tout le scénario en une commande
- [ ] Calibrer les seuils sur les lots 1 et 2

## Étape 4 — Dashboard, tests, documentation (semaine 2, 6 h)

- [ ] Dashboard Streamlit : versions du modèle, performance par lot, dérive, réentraînements et promotions
- [ ] `docker-compose.yml` : MLflow, Postgres, API, dashboard
- [ ] Tests pytest (règles de décision, chargement par alias, promotion et retour arrière)
- [ ] CI GitHub Actions verte
- [ ] README final et courte vidéo de démo
- [ ] **Palier 1 terminé** : le scénario complet se rejoue en local en une commande

## Palier 2 — Vitrine Hugging Face (semaine 2, + 4 à 5 h, conseillé)

- [ ] Exporter les résultats du scénario (versions, performance par lot, dérive, décisions) en fichiers agrégés
- [ ] Space Streamlit qui lit ces exports (repris du `streamlit_space/` du P8)
- [ ] (Option) Space API servant le `@champion` final (repris de `deploy_hf.py` du P8)
- [ ] Vérifier qu'aucune donnée brute Home Credit n'est publiée
- [ ] Ajouter les liens au README et au portfolio

## Palier 3 — Boucle en ligne (+ 6 à 8 h, seulement s'il reste du temps)

- [ ] Vérifier les conditions de l'offre gratuite de DagsHub (dépôts privés, quotas)
- [ ] MLflow et stockage DVC sur DagsHub (données gardées privées)
- [ ] Journal des prédictions sur Neon
- [ ] API et dashboard sur Hugging Face, branchés sur DagsHub et Neon
- [ ] Workflow GitHub Actions qui lance `run_cycle.py` (bouton manuel)
- [ ] Secrets (tokens DagsHub, Hugging Face, URL Neon) dans GitHub Secrets et les Spaces, jamais commités

## Étape 5 — Rapport de conduite de projet (semaine 2, 8 h)

- [ ] Besoins et contexte, audit, solution, aide à la décision
- [ ] Bilan : planning prévu vs réel, coûts, livrables, performance obtenue

## Étape 6 — Carte mentale et portfolio (semaine 3, 14 h)

- [ ] Carte mentale (Xmind ou Mermaid `mindmap`) : projets, compétences et niveaux, réflexivité, soft skills
- [ ] Faire valider la carte mentale par le mentor
- [ ] Portfolio : profil, compétences, projets 2 à 14, projet personnel, rapport → squelette MkDocs dans `portfolio/` (24/11/2026), à relire
- [ ] Soigner l'ergonomie, l'accessibilité et la qualité visuelle

## Étape 7 — Soutenance (semaine 3, 5 h)

- [ ] Plan de présentation (15 min)
- [ ] Questions-réponses attendues : gestion de projet, choix techniques, objectif professionnel, axes d'amélioration
- [ ] Répétition chronométrée
- [ ] Zip des livrables correctement nommé
