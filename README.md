# MON SALAIRE — Android v2

Version centrée sur le salaire net réellement reçu.

Fonctions :
- saisie du salaire net ;
- répartition automatique 100 % ;
- pourcentages modifiables ;
- clic sur Alimentation pour ouvrir son budget détaillé ;
- sac de riz 50 kg séparé à 20 000 F par défaut ;
- dépenses réelles ;
- épargne ;
- aide aux parents ;
- dîme ;
- 13e mois séparé ;
- historique local SQLite ;
- logo et identité visuelle basés sur le visuel approuvé.

Les pourcentages de budget sont des paramètres personnels et non des taux légaux.

Compilation APK :
`pip install buildozer cython`
puis `buildozer android debug`.

- 🎓 Scolarité : enfant, montant, échéance et statut.
- 💳 Prêts en cours : prêteur, montant initial, taux, mensualité, date de fin et restant dû.

## Vérification V3/V4
- Syntaxe Python vérifiée.
- Correction du calcul d'épargne du tableau de bord : il utilise désormais 5 % d'épargne (index correct), et non le taux de dîme.
- Les données restent locales dans SQLite.
- Les champs scolarité et prêts acceptent montants et échéances ; le taux du prêt est conservé comme taux saisi.

- 🔄 Les provisions mensuelles de scolarité et les mensualités de prêts sont désormais automatiquement déduites du « Reste » du tableau de bord.
- La scolarité conserve séparément le montant total et la provision mensuelle.
- Le total des engagements mensuels est affiché dans « Scolarité / prêts ».
