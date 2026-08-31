# -*- coding: utf-8 -*-
"""Les leçons du programme français de mathématiques — lycée (2de à Terminale).

Même principe qu'au collège : les chapitres suivent maths-et-tiques.fr, et le
découpage en leçons suit celui des cours publiés. Les objectifs sont en français.
"""

SECONDE = {
 "fr.seconde.calcul-litteral": [
  ("Développer et factoriser", [
   "Je sais développer avec les identités remarquables.",
   "Je sais factoriser une expression du second degré simple."]),
  ("Équations et expressions", [
   "Je sais transformer une expression pour résoudre un problème."]),
 ],
 "fr.seconde.fractions-puissances-racines-carrees": [
  ("Fractions et puissances", [
   "Je sais calculer avec des fractions et des puissances entières."]),
  ("Racines carrées", [
   "Je sais simplifier une racine carrée.",
   "Je connais les règles de calcul sur les racines."]),
 ],
 "fr.seconde.nombres-reels": [
  ("Ensembles de nombres", [
   "Je connais les ensembles $\\mathbb{N}$, $\\mathbb{Z}$, $\\mathbb{D}$, $\\mathbb{Q}$, $\\mathbb{R}$.",
   "Je sais situer un nombre dans ces ensembles."]),
  ("Intervalles et valeur absolue", [
   "Je sais écrire un intervalle et le représenter.",
   "Je sais interpréter la valeur absolue comme une distance."]),
 ],
 "fr.seconde.arithmetique": [
  ("Divisibilité et nombres premiers", [
   "Je sais décomposer un entier en facteurs premiers.",
   "Je sais raisonner sur la parité et les multiples."]),
 ],
 "fr.seconde.equations-inequations": [
  ("Équations", [
   "Je sais résoudre une équation du premier degré et une équation produit nul."]),
  ("Inéquations", [
   "Je sais résoudre une inéquation du premier degré.",
   "Je sais utiliser un tableau de signes."]),
 ],
 "fr.seconde.les-vecteurs": [
  ("Notion de vecteur", [
   "Je connais la définition d'un vecteur et de l'égalité de deux vecteurs.",
   "Je sais construire la somme de deux vecteurs."]),
  ("Relation de Chasles", [
   "Je sais utiliser la relation de Chasles.",
   "Je sais multiplier un vecteur par un réel."]),
 ],
 "fr.seconde.vecteurs-et-reperage": [
  ("Coordonnées d'un vecteur", [
   "Je sais calculer les coordonnées d'un vecteur.",
   "Je sais calculer les coordonnées d'un milieu."]),
  ("Colinéarité", [
   "Je sais calculer un déterminant et tester la colinéarité.",
   "Je sais prouver que trois points sont alignés."]),
 ],
 "fr.seconde.droites-du-plan": [
  ("Équations de droites", [
   "Je sais reconnaître une équation cartésienne et une équation réduite.",
   "Je sais tracer une droite à partir de son équation."]),
  ("Déterminer une équation", [
   "Je sais déterminer l'équation d'une droite passant par deux points."]),
 ],
 "fr.seconde.systemes-d-equations-et-droites": [
  ("Résoudre un système", [
   "Je sais résoudre un système par substitution et par combinaison.",
   "Je sais interpréter géométriquement les solutions."]),
 ],
 "fr.seconde.notion-de-fonction": [
  ("Vocabulaire et représentation", [
   "Je connais le vocabulaire image, antécédent, ensemble de définition.",
   "Je sais lire un graphique."]),
  ("Résoudre graphiquement", [
   "Je sais résoudre graphiquement $f(x) = k$ et $f(x) \\leq k$."]),
 ],
 "fr.seconde.les-fonctions-de-reference": [
  ("Fonctions affines et carré", [
   "Je connais les variations et la courbe de la fonction carré.",
   "Je connais les variations d'une fonction affine."]),
  ("Fonction inverse et racine", [
   "Je connais les variations et la courbe de la fonction inverse.",
   "Je connais la fonction racine carrée et la fonction cube."]),
 ],
 "fr.seconde.variations-d-une-fonction": [
  ("Sens de variation", [
   "Je connais la définition d'une fonction croissante et décroissante.",
   "Je sais dresser un tableau de variations."]),
  ("Extremums", [
   "Je sais déterminer un maximum et un minimum sur un intervalle."]),
 ],
 "fr.seconde.information-chiffree": [
  ("Proportions et pourcentages", [
   "Je sais calculer une proportion et une proportion de proportion."]),
  ("Évolutions", [
   "Je sais calculer un taux d'évolution et un coefficient multiplicateur.",
   "Je sais calculer une évolution réciproque et des évolutions successives."]),
 ],
 "fr.seconde.statistiques": [
  ("Indicateurs de position", [
   "Je sais calculer une moyenne et une médiane.",
   "Je sais déterminer les quartiles."]),
  ("Dispersion", [
   "Je sais calculer l'écart interquartile et l'écart type.",
   "Je sais comparer deux séries statistiques."]),
 ],
 "fr.seconde.probabilites": [
  ("Modéliser une expérience aléatoire", [
   "Je sais décrire un univers et une loi de probabilité.",
   "Je sais calculer la probabilité d'un événement."]),
  ("Réunion et intersection", [
   "Je sais utiliser la formule $P(A \\cup B) = P(A) + P(B) - P(A \\cap B)$.",
   "Je sais utiliser un tableau ou un arbre."]),
 ],
}

PREMIERE = {
 "fr.premiere.second-degre": [
  ("Forme canonique et discriminant", [
   "Je sais déterminer la forme canonique d'un trinôme.",
   "Je sais calculer le discriminant."]),
  ("Racines et factorisation", [
   "Je sais résoudre une équation du second degré.",
   "Je sais factoriser un trinôme."]),
  ("Signe du trinôme", [
   "Je connais le signe d'un trinôme selon le discriminant.",
   "Je sais résoudre une inéquation du second degré."]),
 ],
 "fr.premiere.generalites-sur-les-suites": [
  ("Définir une suite", [
   "Je sais définir une suite explicitement et par récurrence.",
   "Je sais calculer les premiers termes."]),
  ("Variations et représentation", [
   "Je sais étudier le sens de variation d'une suite.",
   "Je sais représenter une suite."]),
 ],
 "fr.premiere.suites-arithmetiques-suites-geometriques": [
  ("Suites arithmétiques", [
   "Je sais reconnaître une suite arithmétique et calculer sa raison.",
   "Je connais la formule du terme général et de la somme."]),
  ("Suites géométriques", [
   "Je sais reconnaître une suite géométrique.",
   "Je connais la formule du terme général et de la somme."]),
 ],
 "fr.premiere.derivation": [
  ("Nombre dérivé et tangente", [
   "Je connais la définition du nombre dérivé.",
   "Je sais déterminer l'équation de la tangente."]),
  ("Fonction dérivée", [
   "Je connais les dérivées des fonctions de référence.",
   "Je connais les règles de dérivation d'une somme, d'un produit, d'un quotient."]),
  ("Dérivée et variations", [
   "Je sais utiliser le signe de la dérivée pour étudier les variations.",
   "Je sais déterminer un extremum."]),
 ],
 "fr.premiere.fonction-exponentielle": [
  ("Définition et propriétés", [
   "Je connais la définition de la fonction exponentielle.",
   "Je connais les propriétés algébriques de l'exponentielle."]),
  ("Étude de la fonction", [
   "Je connais la dérivée et les variations de l'exponentielle.",
   "Je sais résoudre une équation et une inéquation avec l'exponentielle."]),
 ],
 "fr.premiere.trigonometrie": [
  ("Cercle trigonométrique", [
   "Je sais placer un point sur le cercle trigonométrique.",
   "Je connais le radian et les mesures d'angles associées."]),
  ("Cosinus et sinus", [
   "Je connais les valeurs remarquables de cosinus et sinus.",
   "Je sais résoudre une équation trigonométrique simple."]),
 ],
 "fr.premiere.produit-scalaire": [
  ("Définitions du produit scalaire", [
   "Je connais les différentes expressions du produit scalaire.",
   "Je sais calculer un produit scalaire."]),
  ("Applications", [
   "Je sais caractériser l'orthogonalité par le produit scalaire.",
   "Je sais utiliser le théorème d'Al-Kashi."]),
 ],
 "fr.premiere.geometrie-reperee": [
  ("Droites et vecteurs normaux", [
   "Je sais déterminer une équation de droite à partir d'un vecteur normal."]),
  ("Le cercle", [
   "Je connais l'équation d'un cercle et je sais déterminer son centre et son rayon."]),
 ],
 "fr.premiere.probabilites-conditionnelles-et-independance": [
  ("Probabilités conditionnelles", [
   "Je connais la définition de $P_A(B)$.",
   "Je sais utiliser un arbre pondéré."]),
  ("Formule des probabilités totales et indépendance", [
   "Je sais utiliser la formule des probabilités totales.",
   "Je sais reconnaître deux événements indépendants."]),
 ],
 "fr.premiere.variables-aleatoires": [
  ("Loi de probabilité", [
   "Je sais déterminer la loi d'une variable aléatoire."]),
  ("Espérance, variance, écart type", [
   "Je sais calculer une espérance, une variance et un écart type.",
   "Je sais interpréter l'espérance dans un problème."]),
 ],
}

TERMINALE = {
 "fr.terminale.les-suites": [
  ("Raisonnement par récurrence", [
   "Je sais rédiger une démonstration par récurrence."]),
  ("Limites de suites", [
   "Je sais déterminer la limite d'une suite.",
   "Je connais le théorème de convergence monotone et le théorème des gendarmes."]),
 ],
 "fr.terminale.limite-des-fonctions": [
  ("Limites en l'infini et en un point", [
   "Je sais déterminer une limite en l'infini et en un réel.",
   "Je sais interpréter une asymptote."]),
  ("Opérations et formes indéterminées", [
   "Je connais les opérations sur les limites.",
   "Je sais lever une forme indéterminée."]),
 ],
 "fr.terminale.derivation": [
  ("Dérivée d'une composée", [
   "Je sais dériver une fonction composée.",
   "Je sais dériver $e^{u}$, $\\ln(u)$ et $\\sqrt{u}$."]),
 ],
 "fr.terminale.continuite-des-fonctions": [
  ("Continuité", [
   "Je connais la définition de la continuité.",
   "Je sais utiliser la continuité d'une fonction dérivable."]),
  ("Théorème des valeurs intermédiaires", [
   "Je sais appliquer le théorème des valeurs intermédiaires.",
   "Je sais déterminer un encadrement d'une solution."]),
 ],
 "fr.terminale.convexite": [
  ("Convexité et dérivée seconde", [
   "Je connais la définition d'une fonction convexe et concave.",
   "Je sais utiliser le signe de la dérivée seconde."]),
  ("Points d'inflexion", [
   "Je sais déterminer les points d'inflexion d'une courbe."]),
 ],
 "fr.terminale.fonction-logarithme-neperien": [
  ("Définition et propriétés", [
   "Je connais la définition du logarithme népérien.",
   "Je connais les propriétés algébriques du logarithme."]),
  ("Étude de la fonction", [
   "Je connais la dérivée, les limites et les variations de $\\ln$.",
   "Je sais résoudre une équation et une inéquation avec $\\ln$."]),
 ],
 "fr.terminale.fonctions-trigonometriques": [
  ("Fonctions cosinus et sinus", [
   "Je connais les variations et les courbes de cosinus et sinus.",
   "Je sais dériver $\\cos$ et $\\sin$."]),
 ],
 "fr.terminale.primitives-et-eq-differentielles": [
  ("Primitives", [
   "Je connais la définition d'une primitive.",
   "Je connais les primitives des fonctions usuelles."]),
  ("Équations différentielles", [
   "Je sais résoudre $y' = ay$ et $y' = ay + b$."]),
 ],
 "fr.terminale.calcul-integral": [
  ("Intégrale et aire", [
   "Je connais la définition de l'intégrale comme aire.",
   "Je sais calculer une intégrale avec une primitive."]),
  ("Propriétés de l'intégrale", [
   "Je connais la linéarité et la relation de Chasles.",
   "Je sais calculer une valeur moyenne."]),
 ],
 "fr.terminale.combinatoire-et-denombrement": [
  ("Dénombrer", [
   "Je sais dénombrer des listes, des permutations et des combinaisons.",
   "Je connais le coefficient binomial $\\binom{n}{k}$."]),
 ],
 "fr.terminale.vecteurs-droites-et-plans-de-l-espace": [
  ("Vecteurs de l'espace", [
   "Je sais utiliser des vecteurs coplanaires.",
   "Je sais utiliser une base et un repère de l'espace."]),
  ("Droites et plans", [
   "Je sais étudier les positions relatives de droites et de plans."]),
 ],
 "fr.terminale.orthogonalite-dans-l-espace": [
  ("Produit scalaire dans l'espace", [
   "Je sais calculer un produit scalaire dans l'espace.",
   "Je sais caractériser l'orthogonalité."]),
  ("Vecteur normal et plan", [
   "Je sais déterminer une équation cartésienne d'un plan.",
   "Je sais calculer une distance d'un point à un plan."]),
 ],
 "fr.terminale.representations-parametriques-et-equations-cartesiennes": [
  ("Représentation paramétrique d'une droite", [
   "Je sais déterminer une représentation paramétrique d'une droite."]),
  ("Intersections", [
   "Je sais déterminer l'intersection d'une droite et d'un plan."]),
 ],
 "fr.terminale.loi-binomiale": [
  ("Schéma de Bernoulli", [
   "Je sais reconnaître un schéma de Bernoulli.",
   "Je connais la loi binomiale et ses paramètres."]),
  ("Espérance et calculs", [
   "Je connais l'espérance et la variance d'une loi binomiale.",
   "Je sais calculer une probabilité avec la loi binomiale."]),
 ],
 "fr.terminale.loi-des-grands-nombres": [
  ("Inégalités de concentration", [
   "Je connais l'inégalité de Bienaymé-Tchebychev."]),
  ("Loi des grands nombres", [
   "Je connais la loi des grands nombres et je sais l'interpréter."]),
 ],
}

LYCEE = {**SECONDE, **PREMIERE, **TERMINALE}
