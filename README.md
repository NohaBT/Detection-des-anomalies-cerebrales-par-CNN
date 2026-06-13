# NeuroDetect 🧠

**NeuroDetect** est une application de bureau interactive et moderne conçue pour la détection et la classification des tumeurs cérébrales à partir d'images d'imagerie par résonance magnétique (IRM) à l'aide du Deep Learning.

L'application utilise un modèle **MobileNetV2** pour classifier les images IRM en 4 catégories :
*   **Gliome** (Glioma)
*   **Méningiome** (Meningioma)
*   **Tumeur hypophysaire** (Pituitary tumor)
*   **Sain / Aucune tumeur** (No tumor)

## 🚀 Fonctionnalités principales

L'application propose trois espaces adaptés à différents profils d'utilisateurs :

### 1. ⚕️ Espace Médecin
*   **Diagnostic par IA :** Importation d'images IRM (par glisser-déposer ou explorateur de fichiers) et classification en temps réel.
*   **Détails Cliniques :** Affichage du type de tumeur, de sa localisation type, de son grade classique, d'un indice de confiance de l'IA (en %) et de recommandations cliniques.
*   **Historique & Suivi :** Accès à l'historique complet des analyses enregistrées dans la base de données.
*   **Statistiques :** Visualisation de graphiques d'activité (nombre d'analyses par mois, répartition des types de tumeurs détectées, confiance moyenne).

### 2. 🎓 Espace Étudiant (Pédagogique)
*   **Cas Cliniques :** Consultation de cas cliniques réels anonymisés enregistrés sur la plateforme.
*   **Quiz Interactif :** Test de connaissances en neuro-oncologie et sur le modèle d'IA avec explications détaillées pour chaque réponse.
*   **Suivi de Progression :** Visualisation des statistiques d'apprentissage de l'étudiant.

### 3. 🧑‍⚕️ Espace Patient
*   **Dossier Médical :** Consultation des informations personnelles (groupe sanguin, ville, âge, etc.) et du médecin référent.
*   **Résultats d'Analyses :** Consultation sécurisée des résultats d'analyses d'IRM transmis par son médecin.

## 🛠️ Stack Technique

*   **Langage :** Python 3.x
*   **Interface Graphique (GUI) :** PySide6 (Qt pour Python) avec un design sombre moderne (Glassmorphism & animations de réseau de neurones).
*   **Base de Données :** SQLite (mode WAL activé pour des accès concurrents sécurisés).
*   **Deep Learning :** TensorFlow / Keras (Modèle MobileNetV2 pour la classification d'images).

## 📁 Structure du Projet

```text
├── app/
│   ├── assets/            # Images, icônes et ressources visuelles
│   ├── database/          # Fichiers de configuration de la DB
│   ├── ui/                # Fichiers d'interface utilisateur (Pages du Dashboard, Login, etc.)
│   ├── database.py        # Gestion de la connexion et des requêtes SQLite
│   └── main.py            # Point d'entrée de l'application
├── data/
│   └── neurodetect.db     # Base de données locale SQLite (créée automatiquement)
├── best_model.keras       # Modèle MobileNetV2 entraîné
├── label_encoder.pkl      # Encoder des labels de classification
├── .gitignore             # Fichiers exclus du contrôle de version
└── README.md              # Présentation du projet
```

## 💻 Installation et Lancement

### 1. Prérequis
Assurez-vous d'avoir Python 3.8+ installé.

### 2. Installation des dépendances
Installez les bibliothèques requbes via pip :
```bash
pip install PySide6 tensorflow pillow numpy
```

### 3. Lancement de l'application
Exécutez la commande suivante depuis la racine du projet :
```bash
python app/main.py
```

---

## 🔒 Sécurité et Données Privées
Les mots de passe des utilisateurs sont chiffrés en base de données à l'aide de l'algorithme SHA-256 combiné à un sel (salt) généré aléatoirement pour chaque compte.
