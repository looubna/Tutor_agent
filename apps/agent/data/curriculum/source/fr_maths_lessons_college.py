# -*- coding: utf-8 -*-
"""Les leçons du programme français de mathématiques — collège (6e à 3e).

La liste des chapitres suit celle de maths-et-tiques.fr (Yvan Monka, Académie de
Strasbourg), et le découpage en leçons suit le découpage de ses cours : un
chapitre trop long pour une séance est publié en « Partie 1 », « Partie 2 », et
c'est exactement la frontière de leçon dont ce pipeline a besoin.

Les objectifs sont écrits à la première personne, comme du côté des langues, et
en français : c'est un programme français, et un élève de 6e ne lit pas
d'anglais dans son cours de maths.

Format : {unit_id: [(titre, [objectifs...]), ...]}
"""

SIXIEME = {
 "fr.sixieme.nombres-entiers-et-decimaux": [
  ("Lire et écrire les nombres entiers", [
   "Je sais lire et écrire un nombre entier en chiffres et en lettres.",
   "Je connais la valeur de chaque chiffre selon sa position."]),
  ("Les nombres décimaux", [
   "Je sais lire, écrire et décomposer un nombre décimal.",
   "Je sais placer un nombre décimal sur une demi-droite graduée."]),
  ("Comparer et ranger les décimaux", [
   "Je sais comparer deux nombres décimaux.",
   "Je sais ranger une liste de décimaux dans l'ordre croissant ou décroissant.",
   "Je sais encadrer et arrondir un nombre décimal."]),
 ],
 "fr.sixieme.addition-soustraction-multiplication": [
  ("Addition et soustraction", [
   "Je sais poser et effectuer une addition et une soustraction de décimaux.",
   "Je sais calculer un ordre de grandeur pour vérifier mon résultat."]),
  ("Multiplication", [
   "Je sais poser et effectuer une multiplication de décimaux.",
   "Je sais placer la virgule dans le produit.",
   "Je sais multiplier par 10, 100, 1 000 et par 0,1 ; 0,01."]),
 ],
 "fr.sixieme.division-durees": [
  ("La division euclidienne", [
   "Je sais poser une division euclidienne et interpréter le quotient et le reste.",
   "Je connais les critères de divisibilité par 2, 3, 5, 9 et 10."]),
  ("La division décimale", [
   "Je sais effectuer une division décimale et donner un quotient approché."]),
  ("Les durées", [
   "Je sais convertir des heures, minutes et secondes.",
   "Je sais additionner et soustraire des durées."]),
 ],
 "fr.sixieme.fractions": [
  ("Écriture fractionnaire (Partie 1)", [
   "Je sais lire et écrire une fraction et nommer numérateur et dénominateur.",
   "Je sais qu'une fraction est un quotient.",
   "Je sais placer une fraction sur une demi-droite graduée."]),
  ("Fractions et décimaux (Partie 2)", [
   "Je sais donner l'écriture décimale d'une fraction.",
   "Je sais reconnaître des fractions égales et simplifier.",
   "Je sais prendre une fraction d'une quantité."]),
 ],
 "fr.sixieme.calcul-mental": [
  ("Techniques de calcul mental", [
   "Je sais calculer mentalement des sommes et des différences.",
   "Je connais les tables de multiplication.",
   "Je sais multiplier et diviser par 10, 100, 1 000."]),
 ],
 "fr.sixieme.proportionnalite": [
  ("Reconnaître la proportionnalité", [
   "Je sais reconnaître une situation de proportionnalité.",
   "Je sais reconnaître un tableau de proportionnalité."]),
  ("Calculer dans un tableau de proportionnalité", [
   "Je sais utiliser le coefficient de proportionnalité.",
   "Je sais utiliser la linéarité et le passage à l'unité.",
   "Je sais calculer une quatrième proportionnelle."]),
  ("Échelles et vitesses", [
   "Je sais utiliser une échelle sur un plan ou une carte.",
   "Je sais calculer une vitesse moyenne."]),
 ],
 "fr.sixieme.pourcentages": [
  ("Appliquer un pourcentage", [
   "Je sais calculer un pourcentage d'une quantité.",
   "Je sais qu'un pourcentage est une proportion sur 100."]),
  ("Calculer un pourcentage", [
   "Je sais exprimer une proportion en pourcentage."]),
 ],
 "fr.sixieme.gestion-de-donnees-probabilites": [
  ("Lire et construire des tableaux", [
   "Je sais lire et compléter un tableau à double entrée.",
   "Je sais organiser des données dans un tableau."]),
  ("Diagrammes et graphiques", [
   "Je sais lire un diagramme en bâtons et un diagramme circulaire.",
   "Je sais construire un diagramme adapté à des données."]),
  ("Premières probabilités", [
   "Je sais reconnaître une expérience aléatoire.",
   "Je sais dire si un événement est certain, possible ou impossible."]),
 ],
 "fr.sixieme.paralleles-et-perpendiculaires-rappels": [
  ("Points, droites, segments", [
   "Je connais le vocabulaire : point, droite, demi-droite, segment.",
   "Je sais utiliser les notations et coder une figure."]),
  ("Droites parallèles et perpendiculaires", [
   "Je sais tracer la perpendiculaire à une droite passant par un point.",
   "Je sais tracer la parallèle à une droite passant par un point.",
   "Je connais les propriétés reliant parallèles et perpendiculaires."]),
 ],
 "fr.sixieme.distances-et-cercles": [
  ("Distance et milieu", [
   "Je sais mesurer une distance entre deux points.",
   "Je sais construire le milieu d'un segment.",
   "Je sais calculer la distance d'un point à une droite."]),
  ("Le cercle", [
   "Je connais le vocabulaire : centre, rayon, diamètre, corde, arc.",
   "Je sais construire un cercle et reporter une longueur au compas."]),
 ],
 "fr.sixieme.angles": [
  ("Reconnaître et nommer un angle", [
   "Je sais nommer un angle et reconnaître sa nature.",
   "Je sais reconnaître un angle aigu, droit, obtus ou plat."]),
  ("Mesurer et construire un angle", [
   "Je sais mesurer un angle avec un rapporteur.",
   "Je sais construire un angle de mesure donnée.",
   "Je sais construire la bissectrice d'un angle."]),
 ],
 "fr.sixieme.triangles": [
  ("Construire des triangles", [
   "Je sais construire un triangle connaissant ses trois côtés.",
   "Je sais construire un triangle connaissant deux côtés et un angle."]),
  ("Triangles particuliers", [
   "Je sais reconnaître un triangle isocèle, équilatéral ou rectangle.",
   "Je connais leurs propriétés et leurs axes de symétrie."]),
 ],
 "fr.sixieme.quadrilateres-rappels": [
  ("Reconnaître les quadrilatères", [
   "Je sais reconnaître un carré, un rectangle, un losange et un parallélogramme.",
   "Je connais leurs propriétés de côtés, d'angles et de diagonales."]),
  ("Construire des quadrilatères", [
   "Je sais construire un rectangle, un carré et un losange.",
   "Je sais coder une figure pour indiquer ses propriétés."]),
 ],
 "fr.sixieme.symetrie-axiale": [
  ("Construire un symétrique", [
   "Je sais construire le symétrique d'un point par rapport à une droite.",
   "Je sais construire le symétrique d'une figure."]),
  ("Propriétés et axes de symétrie", [
   "Je sais que la symétrie axiale conserve les longueurs et les angles.",
   "Je sais reconnaître les axes de symétrie d'une figure."]),
 ],
 "fr.sixieme.perimetres": [
  ("Périmètre des figures usuelles", [
   "Je sais calculer le périmètre d'un carré, d'un rectangle et d'un triangle.",
   "Je sais convertir des unités de longueur."]),
  ("Le périmètre du cercle", [
   "Je sais calculer la longueur d'un cercle avec la formule $P = 2\\pi r$."]),
 ],
 "fr.sixieme.aires": [
  ("Aire des figures usuelles", [
   "Je sais calculer l'aire d'un carré, d'un rectangle et d'un triangle.",
   "Je sais convertir des unités d'aire."]),
  ("Aire du disque et figures composées", [
   "Je sais calculer l'aire d'un disque avec la formule $A = \\pi r^2$.",
   "Je sais calculer l'aire d'une figure composée."]),
 ],
 "fr.sixieme.solides-et-volumes": [
  ("Reconnaître les solides", [
   "Je sais reconnaître un cube, un pavé droit, un prisme, un cylindre.",
   "Je sais reconnaître et construire un patron."]),
  ("Calculer un volume", [
   "Je sais calculer le volume d'un cube et d'un pavé droit.",
   "Je sais convertir des unités de volume et de contenance."]),
 ],
}


CINQUIEME = {
 "fr.cinquieme.regles-de-calcul": [
  ("Priorités opératoires", [
   "Je connais les priorités entre les opérations.",
   "Je sais calculer une expression avec des parenthèses."]),
  ("Distributivité", [
   "Je sais développer un produit avec la simple distributivité.",
   "Je sais factoriser une somme."]),
 ],
 "fr.cinquieme.fractions": [
  ("Comparer et simplifier", [
   "Je sais simplifier une fraction.",
   "Je sais comparer deux fractions.",
   "Je sais mettre deux fractions au même dénominateur."]),
  ("Additionner et soustraire", [
   "Je sais additionner et soustraire deux fractions."]),
  ("Multiplier des fractions", [
   "Je sais multiplier deux fractions.",
   "Je sais prendre une fraction d'une fraction."]),
 ],
 "fr.cinquieme.divisibilite": [
  ("Multiples et diviseurs", [
   "Je connais le vocabulaire multiple, diviseur, divisible.",
   "Je connais les critères de divisibilité."]),
  ("Nombres premiers", [
   "Je sais reconnaître un nombre premier.",
   "Je sais rendre une fraction irréductible."]),
 ],
 "fr.cinquieme.calculs-avec-les-nombres-relatifs": [
  ("Additionner des relatifs", [
   "Je sais additionner deux nombres relatifs.",
   "Je sais utiliser la règle des signes pour une somme."]),
  ("Soustraire des relatifs", [
   "Je sais soustraire un nombre relatif.",
   "Je sais simplifier une expression avec des relatifs."]),
 ],
 "fr.cinquieme.calcul-litteral": [
  ("Introduire une lettre", [
   "Je sais écrire une expression littérale à partir d'un énoncé.",
   "Je connais les conventions d'écriture."]),
  ("Réduire et substituer", [
   "Je sais réduire une expression littérale.",
   "Je sais calculer la valeur d'une expression pour une valeur donnée."]),
 ],
 "fr.cinquieme.equations": [
  ("Tester une égalité", [
   "Je sais tester si un nombre est solution d'une équation."]),
  ("Résoudre une équation simple", [
   "Je sais résoudre une équation du type $x + a = b$ et $ax = b$."]),
 ],
 "fr.cinquieme.proportionnalite": [
  ("Reconnaître et calculer", [
   "Je sais reconnaître une situation de proportionnalité.",
   "Je sais compléter un tableau de proportionnalité."]),
  ("Pourcentages et échelles", [
   "Je sais appliquer et calculer un pourcentage.",
   "Je sais utiliser une échelle."]),
 ],
 "fr.cinquieme.statistiques-et-probabilites": [
  ("Effectifs et fréquences", [
   "Je sais calculer un effectif et une fréquence.",
   "Je sais lire et construire un diagramme."]),
  ("Moyenne", [
   "Je sais calculer une moyenne, éventuellement pondérée."]),
  ("Probabilités", [
   "Je sais calculer la probabilité d'un événement simple.",
   "Je sais qu'une probabilité est comprise entre 0 et 1."]),
 ],
 "fr.cinquieme.nombres-relatifs-et-reperage": [
  ("Les nombres relatifs", [
   "Je sais lire, écrire, comparer et ranger des nombres relatifs.",
   "Je sais placer un relatif sur une droite graduée."]),
  ("Repérage dans le plan", [
   "Je sais lire et placer les coordonnées d'un point dans un repère."]),
 ],
 "fr.cinquieme.triangles": [
  ("Somme des angles", [
   "Je sais que la somme des angles d'un triangle vaut 180°.",
   "Je sais calculer un angle manquant."]),
  ("Inégalité triangulaire", [
   "Je sais dire si un triangle est constructible.",
   "Je sais construire un triangle et sa hauteur."]),
 ],
 "fr.cinquieme.angles": [
  ("Angles et parallèles", [
   "Je sais reconnaître des angles alternes-internes et correspondants.",
   "Je sais utiliser les angles pour prouver que deux droites sont parallèles."]),
 ],
 "fr.cinquieme.symetries": [
  ("Symétrie centrale", [
   "Je sais construire le symétrique d'un point par rapport à un point.",
   "Je sais construire le symétrique d'une figure."]),
  ("Propriétés et centres de symétrie", [
   "Je sais que la symétrie centrale conserve longueurs et angles.",
   "Je sais reconnaître un centre de symétrie."]),
 ],
 "fr.cinquieme.parallelogrammes": [
  ("Propriétés du parallélogramme", [
   "Je connais les propriétés des côtés, angles et diagonales.",
   "Je sais construire un parallélogramme."]),
  ("Parallélogrammes particuliers", [
   "Je sais reconnaître un rectangle, un losange et un carré.",
   "Je sais démontrer la nature d'un quadrilatère."]),
 ],
 "fr.cinquieme.aires": [
  ("Aires des figures usuelles", [
   "Je sais calculer l'aire d'un parallélogramme et d'un triangle.",
   "Je sais calculer l'aire d'un disque."]),
 ],
 "fr.cinquieme.solides-et-volumes": [
  ("Prismes et cylindres", [
   "Je sais reconnaître et représenter un prisme droit et un cylindre.",
   "Je sais construire leur patron."]),
  ("Volumes", [
   "Je sais calculer le volume d'un prisme droit et d'un cylindre."]),
 ],
}

QUATRIEME = {
 "fr.quatrieme.divisibilite-et-nombres-premiers": [
  ("Décomposition en facteurs premiers", [
   "Je sais décomposer un entier en produit de facteurs premiers.",
   "Je sais rendre une fraction irréductible."]),
 ],
 "fr.quatrieme.nombres-relatifs": [
  ("Multiplier et diviser des relatifs", [
   "Je connais la règle des signes pour un produit et un quotient.",
   "Je sais calculer une expression avec des relatifs."]),
 ],
 "fr.quatrieme.fractions": [
  ("Opérations sur les fractions", [
   "Je sais additionner, soustraire et multiplier des fractions."]),
  ("Diviser des fractions", [
   "Je sais diviser par une fraction en multipliant par son inverse."]),
 ],
 "fr.quatrieme.puissances": [
  ("Puissances d'un nombre", [
   "Je sais calculer une puissance à exposant entier.",
   "Je connais les puissances de 10."]),
  ("Règles de calcul et notation scientifique", [
   "Je connais les règles sur les puissances.",
   "Je sais écrire un nombre en notation scientifique."]),
 ],
 "fr.quatrieme.calcul-litteral": [
  ("Développer", [
   "Je sais développer avec la simple et la double distributivité."]),
  ("Factoriser et réduire", [
   "Je sais factoriser une expression.",
   "Je sais réduire une expression littérale."]),
 ],
 "fr.quatrieme.equations": [
  ("Résoudre une équation du premier degré", [
   "Je sais résoudre une équation du type $ax + b = cx + d$.",
   "Je sais vérifier une solution."]),
  ("Mettre en équation un problème", [
   "Je sais traduire un énoncé par une équation et le résoudre."]),
 ],
 "fr.quatrieme.proportionnalite": [
  ("Proportionnalité et pourcentages", [
   "Je sais calculer une quatrième proportionnelle.",
   "Je sais calculer un pourcentage d'évolution."]),
  ("Vitesses et grandeurs composées", [
   "Je sais calculer une vitesse moyenne et convertir des unités."]),
 ],
 "fr.quatrieme.probabilites": [
  ("Calculer une probabilité", [
   "Je sais calculer la probabilité d'un événement.",
   "Je sais utiliser un arbre ou un tableau."]),
 ],
 "fr.quatrieme.statistiques": [
  ("Moyenne et médiane", [
   "Je sais calculer une moyenne pondérée.",
   "Je sais déterminer une médiane et une étendue."]),
 ],
 "fr.quatrieme.theoreme-de-pythagore": [
  ("Calculer une longueur", [
   "Je connais le théorème de Pythagore.",
   "Je sais calculer la longueur d'un côté d'un triangle rectangle."]),
  ("La réciproque", [
   "Je sais utiliser la réciproque pour prouver qu'un triangle est rectangle."]),
 ],
 "fr.quatrieme.theoreme-de-thales": [
  ("Le théorème de Thalès", [
   "Je connais la configuration de Thalès.",
   "Je sais calculer une longueur manquante."]),
 ],
 "fr.quatrieme.cosinus": [
  ("Cosinus d'un angle aigu", [
   "Je connais la définition du cosinus dans un triangle rectangle.",
   "Je sais calculer une longueur ou un angle avec le cosinus."]),
 ],
 "fr.quatrieme.translation": [
  ("Construire une image par translation", [
   "Je sais construire l'image d'une figure par une translation.",
   "Je connais les propriétés conservées."]),
 ],
 "fr.quatrieme.espace": [
  ("Pyramides et cônes", [
   "Je sais reconnaître et représenter une pyramide et un cône.",
   "Je sais calculer leur volume."]),
 ],
}

TROISIEME = {
 "fr.troisieme.calculs-numeriques": [
  ("Fractions et puissances", [
   "Je sais calculer avec des fractions et des puissances.",
   "Je sais utiliser la notation scientifique."]),
  ("Racines carrées", [
   "Je connais la définition de la racine carrée.",
   "Je sais simplifier une écriture avec des racines."]),
 ],
 "fr.troisieme.developpements": [
  ("Double distributivité", [
   "Je sais développer un produit de deux sommes."]),
  ("Identités remarquables", [
   "Je connais les trois identités remarquables.",
   "Je sais développer avec une identité remarquable."]),
 ],
 "fr.troisieme.factorisations": [
  ("Facteur commun", [
   "Je sais factoriser en repérant un facteur commun."]),
  ("Factoriser avec une identité remarquable", [
   "Je sais factoriser une différence de deux carrés.",
   "Je sais factoriser un carré parfait."]),
 ],
 "fr.troisieme.equations": [
  ("Équations du premier degré", [
   "Je sais résoudre une équation du premier degré."]),
  ("Équations produit nul", [
   "Je sais résoudre une équation produit nul.",
   "Je sais résoudre une équation du type $x^2 = a$."]),
 ],
 "fr.troisieme.arithmetique": [
  ("PGCD", [
   "Je sais calculer le PGCD de deux entiers.",
   "Je sais rendre une fraction irréductible avec le PGCD."]),
  ("Nombres premiers entre eux", [
   "Je sais reconnaître deux nombres premiers entre eux.",
   "Je sais résoudre un problème de partage."]),
 ],
 "fr.troisieme.notion-de-fonction": [
  ("Vocabulaire des fonctions", [
   "Je connais le vocabulaire image, antécédent.",
   "Je sais lire une image et un antécédent sur un graphique."]),
  ("Représenter une fonction", [
   "Je sais compléter un tableau de valeurs.",
   "Je sais tracer la représentation graphique d'une fonction."]),
 ],
 "fr.troisieme.fonctions-affines": [
  ("Fonctions affines et linéaires", [
   "Je sais reconnaître une fonction affine ou linéaire.",
   "Je connais le rôle du coefficient directeur et de l'ordonnée à l'origine."]),
  ("Déterminer une fonction affine", [
   "Je sais déterminer l'expression d'une fonction affine à partir de deux points."]),
 ],
 "fr.troisieme.proportionnalite": [
  ("Proportionnalité et fonctions linéaires", [
   "Je sais relier proportionnalité et fonction linéaire.",
   "Je sais calculer un pourcentage d'évolution et un coefficient multiplicateur."]),
 ],
 "fr.troisieme.probabilites": [
  ("Probabilités d'un événement", [
   "Je sais calculer la probabilité d'un événement.",
   "Je sais calculer la probabilité de l'événement contraire."]),
  ("Expériences à deux épreuves", [
   "Je sais utiliser un arbre pondéré pour une expérience à deux épreuves."]),
 ],
 "fr.troisieme.statistiques": [
  ("Indicateurs de position", [
   "Je sais calculer une moyenne et une médiane."]),
  ("Indicateurs de dispersion", [
   "Je sais calculer l'étendue et les quartiles.",
   "Je sais interpréter une série statistique."]),
 ],
 "fr.troisieme.theoreme-de-thales": [
  ("Le théorème de Thalès", [
   "Je sais calculer une longueur avec le théorème de Thalès."]),
  ("La réciproque de Thalès", [
   "Je sais prouver que deux droites sont parallèles."]),
 ],
 "fr.troisieme.triangles-semblables": [
  ("Triangles semblables", [
   "Je sais reconnaître deux triangles semblables.",
   "Je sais utiliser un rapport d'agrandissement ou de réduction."]),
 ],
 "fr.troisieme.trigonometrie": [
  ("Cosinus, sinus, tangente", [
   "Je connais les trois rapports trigonométriques.",
   "Je sais calculer une longueur dans un triangle rectangle."]),
  ("Calculer un angle", [
   "Je sais calculer la mesure d'un angle avec la trigonométrie."]),
 ],
 "fr.troisieme.transformations": [
  ("Rotation et homothétie", [
   "Je sais construire l'image d'une figure par une rotation.",
   "Je sais construire l'image d'une figure par une homothétie."]),
 ],
 "fr.troisieme.espace": [
  ("Sphère et boule", [
   "Je sais calculer l'aire d'une sphère et le volume d'une boule."]),
  ("Agrandissement et réduction", [
   "Je sais l'effet d'un agrandissement sur les aires et les volumes."]),
 ],
}

COLLEGE = {**SIXIEME, **CINQUIEME, **QUATRIEME, **TROISIEME}
