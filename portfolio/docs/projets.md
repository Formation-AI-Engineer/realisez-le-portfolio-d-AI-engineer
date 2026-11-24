# Projets du parcours

Treize projets, chacun traité comme une mission pour un client fictif : un besoin métier, une
solution livrée, un résultat mesuré. Chaque fiche renvoie au code du projet sur GitHub.

<div class="grid cards" markdown>

-   **Machine learning**

    ---

    [P2 Segmentation de vêtements](#p2) · [P3 Énergie des bâtiments](#p3) ·
    [P4 Attrition RH](#p4) · [P6 Scoring crédit](#p6) · [P10 IRM semi-supervisé](#p10) ·
    [P11 Agent RL](#p11)

-   **MLOps et données**

    ---

    [P5 Déploiement d'un modèle](#p5) · [P8 Monitoring et dérive](#p8) ·
    [P12 Pipeline ETL multimodal](#p12)

-   **LLM et agents**

    ---

    [P7 Système RAG](#p7) · [P13 Agent IA](#p13) · [P14 Fine-tuning de LLM](#p14)

-   **Cadrage**

    ---

    [P9 Cadrage d'un projet IA](#p9)

</div>

---

## P2 — Requêtez des services d'IA { #p2 }

**Client : Fashion Trend Intelligence.** Segmenter automatiquement les vêtements portés sur des
photos d'influenceurs, sans entraîner de modèle.

- Appel du modèle SegFormer B3 (segmentation vestimentaire) par l'API d'inférence Hugging Face.
- Évaluation des masques prédits contre 50 masques annotés à la main.

<span class="tag">Python</span><span class="tag">Hugging Face</span><span class="tag">SegFormer</span><span class="tag">Jupyter</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/requetez-services-IA){ .md-button }

## P3 — Prédisez la consommation d'énergie des bâtiments { #p3 }

**Client : ville de Seattle.** Prédire la consommation d'énergie des bâtiments non résidentiels à
partir de leurs caractéristiques, pour éviter des relevés coûteux.

- Nettoyage, feature engineering, comparaison de modèles de régression avec validation croisée.
- Optimisation des hyperparamètres orientée vers la réduction du surapprentissage.

**Résultat :** une forêt aléatoire retenue, R² de 0,62 en validation croisée. Le surapprentissage
initial (écart de 0,34 entre entraînement et test) est réduit à 0,25.

<span class="tag">pandas</span><span class="tag">scikit-learn</span><span class="tag">régression</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/predisez-la-consommation-d-energie-des-batiments){ .md-button }

## P4 — Classifiez automatiquement des informations { #p4 }

**Client : TechNova Partners (ESN).** Identifier les causes de démission et prédire l'attrition à
partir de trois sources RH (SIRH, évaluations, sondage).

- Jointure et analyse exploratoire des trois sources.
- Classification sur des classes déséquilibrées (84 % des salariés restent) : choix de métriques
  adaptées plutôt que l'accuracy, interprétation des causes principales.

<span class="tag">pandas</span><span class="tag">scikit-learn</span><span class="tag">classification</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/classifiez-automatiquement-des-informations){ .md-button }

## P5 — Déployez un modèle de machine learning { #p5 }

**Client : Futurisys.** Mettre le modèle d'attrition du P4 en production.

- API FastAPI, journalisation des échanges dans PostgreSQL, suite de tests pytest.
- CI/CD GitHub Actions et déploiement automatique sur Hugging Face Spaces.

<span class="tag">FastAPI</span><span class="tag">PostgreSQL</span><span class="tag">pytest</span><span class="tag">GitHub Actions</span><span class="tag">CatBoost</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/deployez-un-modele-de-machine-learning){ .md-button }
[:material-rocket-launch: Démo](https://huggingface.co/spaces/lcamara/deployMLModel){ .md-button }

## P6 — Initiez-vous au MLOps : scoring crédit { #p6 }

**Client : Prêt à Dépenser.** Prédire le risque de défaut de paiement d'un client à partir du
jeu de données Home Credit (8 tables, environ 8 % de défauts).

- Feature engineering sur les 8 tables (804 variables), LightGBM.
- **Score métier** qui pénalise un faux négatif 10 fois plus qu'un faux positif, et qui fixe le
  seuil de décision.
- Suivi des expériences avec MLflow.

**Résultat :** AUC de 0,77 en validation croisée, seuil métier fixé à 0,49.

<span class="tag">LightGBM</span><span class="tag">MLflow</span><span class="tag">coût métier</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/initiez-vous-au-MLOps-1){ .md-button }

## P7 — Concevez et déployez un système RAG { #p7 }

**Client : Puls-Events.** Un assistant qui répond en langage naturel aux questions sur les
événements culturels à venir.

- Collecte par l'API Open Agenda, découpage, embeddings multilingues, index FAISS.
- Chaîne LangChain avec génération par Mistral, seuil de pertinence pour répondre « je ne sais
  pas » plutôt qu'inventer.
- Évaluation avec Ragas sur un jeu de questions annotées, API FastAPI, Docker.

<span class="tag">LangChain</span><span class="tag">FAISS</span><span class="tag">Mistral</span><span class="tag">Ragas</span><span class="tag">FastAPI</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/concevez-et-deployez-un-systeme-rag){ .md-button }

## P8 — Déployez et monitorez votre modèle { #p8 }

**Client : Prêt à Dépenser.** Mettre en production le modèle du P6 et surveiller sa dérive.

- API FastAPI conteneurisée, CI/CD, démo Gradio.
- Chaque prédiction est journalisée dans PostgreSQL ; Evidently compare le trafic à la référence.
- Dashboard Streamlit (indicateurs et dérive), optimisation de l'inférence (export ONNX).

<span class="tag">FastAPI</span><span class="tag">Docker</span><span class="tag">Evidently</span><span class="tag">PostgreSQL</span><span class="tag">Streamlit</span><span class="tag">ONNX</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/confirmez-vos-competences-en-MLOps-partie-2-2){ .md-button }
[:material-rocket-launch: API](https://huggingface.co/spaces/lcamara/scoring-credit-pret-a-depenser){ .md-button }
[:material-monitor-dashboard: Dashboard](https://huggingface.co/spaces/lcamara/scoring-credit-stream){ .md-button }

## P9 — Réalisez le cadrage d'un projet IA { #p9 }

**Client : Fashion-Insta.** Cadrer une application mobile qui recommande des vêtements à partir
de photos, et obtenir du COMEX le feu vert pour un POC.

- Périmètre du POC, architecture (system design), planning.
- Staffing, coûts cloud et LLM, calcul du retour sur investissement, conformité RGPD.
- Présentation destinée au COMEX.

<span class="tag">cadrage</span><span class="tag">system design</span><span class="tag">ROI</span><span class="tag">RGPD</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/realisez-le-cadrage-d-un-projet-ia){ .md-button }

## P10 — Approches semi-supervisées en traitement d'images { #p10 }

**Client : CurelyticsIA (e-santé).** Détecter des tumeurs cérébrales sur IRM alors que seule une
petite partie des images est annotée par des radiologues.

- Extraction de features par un ResNet pré-entraîné, clustering (K-Means, DBSCAN), labels faibles
  contrôlés par le score ARI.
- CNN entraîné sur labels faibles puis forts, comparé au supervisé seul. Métriques choisies pour
  le médical : le faux négatif est l'erreur la plus grave.

**Résultat :** le F1 passe de 0,906 à 0,929 avec le semi-supervisé. Mais sur un jeu de test
indépendant, le recall tombe à 0,62 : plus d'un cancer sur trois serait manqué. La
recommandation au client en tient compte.

<span class="tag">PyTorch</span><span class="tag">ResNet</span><span class="tag">clustering</span><span class="tag">semi-supervisé</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/labellisez-et-appliquez-des-approches-semi-supervisees-en-traitement-d-images){ .md-button }

## P11 — Entraînez votre agent RL { #p11 }

**Client : AstroDynamics.** Un pilote automatique qui pose en douceur un module lunaire simulé.

- Exercices progressifs : agent aléatoire, Q-Learning tabulaire, DQN écrit à la main puis avec
  Stable-Baselines3.
- Mission : agent DQN / PPO sur `LunarLander-v3`, API FastAPI, interface et tableau de bord
  Streamlit.

**Résultat :** score moyen de 247,6 ± 27,1 (contre −172 pour un agent aléatoire), 98 % des
épisodes au-dessus du seuil de réussite de 200, aucun épisode négatif.

<span class="tag">Gymnasium</span><span class="tag">Stable-Baselines3</span><span class="tag">PyTorch</span><span class="tag">FastAPI</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/entrainez-votre-agent-RL){ .md-button }

## P12 — Extrayez des données multimodales de sites web { #p12 }

**Client : CheckIt.AI.** Constituer un jeu de données texte + image pour entraîner un détecteur de
fausses informations.

- Extraction depuis trois sources (NewsData.io, Google Fact Check, Global Voices), nettoyage,
  chargement dans PostgreSQL sécurisé (rôles, chiffrement).
- Orchestration quotidienne avec Airflow 3, contrôle qualité et tableau de bord des indicateurs.

**Résultat :** collecte incrémentale automatique, 659 publications chargées en 4 lots.

<span class="tag">Airflow</span><span class="tag">PostgreSQL</span><span class="tag">ETL</span><span class="tag">Streamlit</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/extrayez-des-donnees-multimodales-de-sites-web){ .md-button }

## P13 — Mettez en place un agent IA { #p13 }

**Client : Fédération française des échecs.** Un agent conversationnel qui aide les jeunes
joueurs à apprendre les ouvertures.

- Agent LangGraph avec outils : base d'ouvertures Lichess, RAG sur des articles Wikichess (Milvus),
  vidéos YouTube, évaluation Stockfish hors théorie.
- Interface Angular avec échiquier, API FastAPI, cache MongoDB, LLM interchangeable (Groq,
  Gemini, Ollama).

<span class="tag">LangGraph</span><span class="tag">Milvus</span><span class="tag">FastAPI</span><span class="tag">Angular</span><span class="tag">Docker Compose</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/mettez-en-place-un-agent-IA){ .md-button }

## P14 — Fine-tunez votre propre LLM { #p14 }

**Client : CHSA (urgences hospitalières).** Un agent qui aide l'infirmier ou l'infirmière
d'accueil à prioriser les patients selon l'échelle FRENCH. La décision reste humaine.

- Qwen3-1.7B fine-tuné par SFT avec LoRA, puis aligné par DPO, servi par vLLM derrière FastAPI.
- Trois garde-fous qui peuvent relever le niveau de priorité, jamais le baisser.
- Déploiement sur Modal, RGPD, décision go / no-go documentée.

**Résultat :** POC limité à la démonstration sur des cas fictifs, après une décision go / no-go
argumentée.

<span class="tag">LoRA</span><span class="tag">DPO</span><span class="tag">vLLM</span><span class="tag">Modal</span><span class="tag">FastAPI</span>

[:fontawesome-brands-github: Code](https://github.com/Formation-AI-Engineer/finetunez-votre-propre-llm){ .md-button }
