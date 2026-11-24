# Boucle MLOps fermée — scoring crédit Prêt à Dépenser

Projet 15 du parcours **AI Engineer** (OpenClassrooms) — *« Réalisez le portfolio d'AI Engineer »*.

Le monitoring du Projet 8 détecte la dérive du modèle de scoring, mais ne réagit pas. Ce projet ferme la boucle :
la dérive et la baisse de performance déclenchent un **réentraînement**. Le nouveau modèle (challenger) est comparé
au modèle en place (champion). S'il fait mieux, il est **promu dans le MLflow Model Registry** et l'API le recharge
sans redéploiement. Les données sont versionnées avec **DVC**.

> Cadrage : [`docs/fiche_cadrage_projet15.md`](docs/fiche_cadrage_projet15.md)
> · Suivi : [`docs/fiche_taches_projet15.md`](docs/fiche_taches_projet15.md)
> · Portfolio : <https://formation-ai-engineer.github.io/realisez-le-portfolio-d-AI-engineer/> (sources dans `portfolio/`)

## Architecture

```
lot k ──► API FastAPI (@champion) ──► journal Postgres (+ labels du lot k-1)
                ▲                              │
                │                              ▼
     rechargement à chaud           Evidently : dérive, AUC, coût métier
                │                              │
   MLflow Model Registry ◄── promotion ◄── réentraînement (challenger) si dérive et baisse
   (alias @champion)        si meilleur
```

## Structure du dépôt

```
.
├── docs/        # Fiche de cadrage, suivi des tâches, rapport de conduite de projet
├── mlops/       # Boucle MLOps : données et lots, dérive, entraînement, registre
├── app/         # API FastAPI qui sert le modèle @champion
├── dashboard/   # Dashboard Streamlit (versions, performance, dérive, décisions)
├── scripts/     # Scripts CLI (rejouer un lot ou tout le scénario)
├── tests/       # Tests unitaires
├── data/        # Référence et lots — versionnés par DVC, pas par Git
└── livrables/   # Fichiers nommés pour le dépôt OpenClassrooms
```

## Installation

Prérequis : **Python 3.10–3.12**, [`uv`](https://docs.astral.sh/uv/) et Docker.

```bash
uv sync --extra dev --extra monitoring
cp .env.example .env.local
uv run pytest
```

*(Les commandes de lancement — MLflow, API, pipeline, dashboard — seront ajoutées au fil des étapes.)*
