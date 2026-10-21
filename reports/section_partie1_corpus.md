# Partie 1 : corpus

## Choix du corpus

Nous avons retenu la loi n° 2026-18 du 3 septembre 2026 portant Code du Travail
(Journal officiel du Sénégal n° 7931). Raisons du choix :

- **Public et en français**, conforme au sujet : texte officiel, sans donnée personnelle.
- **Structuré** : 462 articles numérotés, répartis en 15 titres. Cette structure permet
  un découpage naturel (un chunk par article) et des citations précises ("article 187").
- **Questions vérifiables** : délais, durées, conditions et sanctions sont écrits noir
  sur blanc, ce qui facilite la rédaction de 20 questions avec réponse de référence.
- **Cas d'échec intéressants pour l'évaluation** : la loi abroge le Code de 1997
  (loi n° 97-17). Un modèle de langage a probablement vu l'ancien code pendant son
  entraînement et peut répondre avec des règles périmées au lieu de s'appuyer sur le
  corpus : c'est un test direct de la fidélité au corpus.
- **Domaine sensible** : un conseil juridique erroné a des conséquences réelles, ce qui
  justifie des garde-fous (partie 5).

## Préparation des données

1. **Extraction** (PyMuPDF) : le PDF de 72 pages a une couche de texte, sans OCR.
   Comme la première page mêle la couverture du Journal officiel et le début de la
   loi, nous coupons sur des repères de texte et non par page.
2. **Nettoyage** : suppression de 70 en-têtes répétés et de 71 numéros de page,
   recollage de 1 063 mots coupés en fin de ligne (avec exceptions : "ceux-ci",
   "main-d'œuvre"), conservation des listes à puces.
3. **Détection des articles** : trois formats coexistent dans le PDF
   ("Article 12. -", "Article 109 -", "Art. 49. -"). Une détection naïve en perdait
   deux sur 462, sans signalement : nous vérifions donc que les numéros de 1 à 462
   sont tous présents.
4. **Découpage** : un chunk par article, les articles de plus de 1 200 caractères
   étant scindés à la fin d'une phrase ou d'une puce, avec 150 caractères de
   chevauchement. Le contexte (Titre > Chapitre > Section) et l'intitulé sont
   répétés dans chaque chunk. Résultat : 524 chunks, de 149 à 1 444 caractères
   (moyenne 770). L'article 3 (définitions, près de 15 000 caractères) donne 16 chunks.
   Nous n'avons pas regroupé les articles courts, pour garder un chunk = un article
   et des citations exactes.

## Limites

- **Un seul document** : pas de recherche entre sources différentes.
- **Intitulés tronqués** : pour certains articles (49, 109), l'intitulé se poursuit
  sur la ligne suivante, collée au texte. Le champ `titre` est donc incomplet, mais
  le texte complet est dans le chunk.
- **Recollage approximatif** : la liste d'exceptions pour les traits d'union est une
  règle empirique ; un mot composé absent de la liste peut être recollé à tort.
- **Chevauchement** : sur l'article 3, un chunk peut commencer au milieu d'une définition.
- **Longueur des chunks et modèle d'embeddings** : <À COMPLÉTER avec la décision de la
  partie 2 : le modèle par défaut tronque peut-être les textes au-delà de ~128 tokens.>
- **Pas de contrôle de licence** : texte officiel public, mais les conditions de
  réutilisation n'ont pas été vérifiées.

## Ce que nous changerions

- <À COMPLÉTER avec ce que vous voudriez améliorer : par exemple, extraire l'intitulé
  complet des articles, ajouter d'autres textes du droit du travail (décrets d'application),
  ou découper l'article 3 par définition plutôt que par taille.>