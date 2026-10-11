# MON SALAIRE V6 — Version Windows

Cette version reprend le projet MON SALAIRE V6 et ajoute les fichiers nécessaires pour créer une application Windows `.exe` avec PyInstaller.

## Méthode recommandée

1. Installer Python 3.11 ou 3.12 sur Windows et cocher **Add Python to PATH**.
2. Extraire ce dossier.
3. Double-cliquer sur **CREER_EXE.bat**.
4. Le script crée automatiquement un environnement `.venv`, installe Kivy + PyInstaller et construit l'application.
5. Le programme final se trouve dans :

`dist\\MON SALAIRE\\MON SALAIRE.exe`

## Version en un seul fichier

`CREER_EXE_UN_SEUL.bat` crée `dist\\MON SALAIRE.exe`.

La version dossier (`CREER_EXE.bat`) est recommandée pour une meilleure fiabilité avec Kivy.

## Important

- La base SQLite est locale à Windows.
- Les données de l'application Android ne sont pas automatiquement transférées vers Windows.
- La version Windows utilise le même `main.py` et conserve les fonctions de salaire, budget, alimentation, dépenses, scolarité, prêts, 13e mois et historique.
