# Explication du plan · scénario S-battery seed 7

| | Glouton | Notre plan |
| --- | ---: | ---: |
| Valide | oui | oui |
| Score | 90.4 | 317.1 |
| Points servis | 176.0 | 558.0 |
| Énergie (Wh) | 131.1 | 321.9 |
| Drones d'action consommés | 2 | 8 |
| Contacts servis | 6 | 15 |

Coût d'1 Wh = 0.5 pt · coût d'un drone d'action = 10 pts.

## Stratégie du planificateur

Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes touchées, environ 3 fois plus d'essais par seconde) ; relances par petites variations autour du meilleur ordre de contacts trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de 38 s ; deux routages selon la taille de la flotte, filet de sécurité (Mahmoud) et routage (Youcef) intégrés. Chaque plan construit est revalidé par le scorer du kit ; au final, on écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est).

Résultat sur ce scénario : **+251 %** par rapport au glouton (90.4 → 317.1 pts).

Gagnés par rapport au glouton : C03, C19, C27, C40, C51, C53, C60, C63, C65, C66 · perdus : C57.

## Ressources

| Type | Disponibles | Utilisés | Restants |
| --- | ---: | ---: | ---: |
| effector (heavy) | 35 | 5 | 30 |
| effector (light) | 50 | 3 | 47 |
| scout | 15 | 9 | 6 |

Drones au sol : H01, H02, H03, H04, H05, H06, H07, H08, H09, H10, H11, H12, H13, H14, H15, H17, H18, H19, H21, H22, H23, H24, H25, H26, H27, H28, H30, H31, H33, H35, L01, L02, L03, L05, L06, L07, L08, L09, L10, L11, L12, L13, L14, L15, L16, L17, L18, L19, L20, L21, L22, L23, L24, L25, L26, L27, L29, L30, L31, L32, L33, L34, L35, L36, L37, L38, L39, L40, L41, L42, L43, L44, L45, L47, L48, L49, L50, S02, S05, S06, S07, S08, S11.

## Affectations, drone par drone

### H16 · effector (heavy)

Distance 4.64 km · énergie 13.1 Wh sur 35.3 Wh utilisables · coût 6.6 pts.

- t = 275 s · engage **C47** (hostile, 61 pts, fenêtre 238–463 s)

### H20 · effector (heavy)

Distance 5.61 km · énergie 16.4 Wh sur 27.4 Wh utilisables · coût 8.2 pts.

- t = 329 s · engage **C40** (hostile, 89 pts, fenêtre 30–346 s)

### H29 · effector (heavy)

Distance 5.51 km · énergie 22.6 Wh sur 44.2 Wh utilisables · coût 11.3 pts.

- t = 592 s · engage **C19** (hostile, 75 pts, fenêtre 358–616 s)

### H32 · effector (heavy)

Distance 5.53 km · énergie 23.9 Wh sur 25.9 Wh utilisables · coût 11.9 pts.

- t = 597 s · engage **C19** (hostile, 75 pts, fenêtre 358–616 s)

### H34 · effector (heavy)

Distance 4.64 km · énergie 14.6 Wh sur 32.9 Wh utilisables · coût 7.3 pts.

- t = 276 s · engage **C47** (hostile, 61 pts, fenêtre 238–463 s)

### L04 · effector (light)

Distance 5.37 km · énergie 8.5 Wh sur 32.6 Wh utilisables · coût 4.3 pts.

- t = 422 s · engage **C03** (hostile, 50 pts, fenêtre 223–480 s)

### L28 · effector (light)

Distance 5.39 km · énergie 8.3 Wh sur 26.4 Wh utilisables · coût 4.1 pts.

- t = 427 s · engage **C03** (hostile, 50 pts, fenêtre 223–480 s)

### L46 · effector (light)

Distance 5.26 km · énergie 8.5 Wh sur 27.8 Wh utilisables · coût 4.2 pts.

- t = 289 s · engage **C27** (hostile, 91 pts, fenêtre 108–391 s)

### S01 · scout

Distance 6.51 km · énergie 18.8 Wh sur 21.4 Wh utilisables · coût 9.4 pts.

- t = 274 s · observe **C59** (unknown, 20 pts, fenêtre 234–544 s)
- t = 382 s · observe **C63** (unknown, 14 pts, fenêtre 382–632 s)

### S03 · scout

Distance 10.44 km · énergie 25.8 Wh sur 26.3 Wh utilisables · coût 12.9 pts.

- t = 257 s · observe **C27** (hostile, 91 pts, fenêtre 108–391 s)

### S04 · scout

Distance 9.53 km · énergie 25.0 Wh sur 25.1 Wh utilisables · coût 12.5 pts.

- t = 238 s · observe **C47** (hostile, 61 pts, fenêtre 238–463 s)
- t = 297 s · observe **C65** (unknown, 24 pts, fenêtre 76–380 s)

### S09 · scout

Distance 7.17 km · énergie 21.3 Wh sur 21.8 Wh utilisables · coût 10.6 pts.

- t = 366 s · observe **C67** (unknown, 22 pts, fenêtre 362–614 s)
- t = 468 s · observe **C64** (unknown, 19 pts, fenêtre 388–734 s)

### S10 · scout

Distance 6.63 km · énergie 19.1 Wh sur 19.7 Wh utilisables · coût 9.6 pts.

- t = 189 s · observe **C53** (unknown, 14 pts, fenêtre 34–311 s)

### S12 · scout

Distance 8.52 km · énergie 21.0 Wh sur 24.9 Wh utilisables · coût 10.5 pts.

- t = 451 s · observe **C68** (unknown, 25 pts, fenêtre 447–650 s)

### S13 · scout

Distance 11.37 km · énergie 26.6 Wh sur 27.1 Wh utilisables · coût 13.3 pts.

- t = 298 s · observe **C40** (hostile, 89 pts, fenêtre 30–346 s)
- t = 345 s · observe **C51** (unknown, 13 pts, fenêtre 230–500 s)

### S14 · scout

Distance 10.96 km · énergie 27.9 Wh sur 30.0 Wh utilisables · coût 13.9 pts.

- t = 358 s · observe **C19** (hostile, 75 pts, fenêtre 358–616 s)
- t = 383 s · observe **C03** (hostile, 50 pts, fenêtre 223–480 s)
- t = 449 s · observe **C60** (unknown, 29 pts, fenêtre 208–529 s)

### S15 · scout

Distance 7.09 km · énergie 20.4 Wh sur 22.9 Wh utilisables · coût 10.2 pts.

- t = 199 s · observe **C66** (unknown, 12 pts, fenêtre 76–333 s)

## Contacts non servis

- **C16** · hostile, 95 pts, besoin : 4 light, fenêtre 441–757 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C37** · hostile, 95 pts, besoin : 2 light, fenêtre 121–422 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C46** · hostile, 94 pts, besoin : 1 light, fenêtre 138–395 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C06** · hostile, 93 pts, besoin : 3 light, fenêtre 424–668 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C36** · hostile, 91 pts, besoin : 1 light, 1 heavy, fenêtre 201–506 s · interdit par R7 (à 167 m de C79, friendly)
- **C13** · hostile, 90 pts, besoin : 2 light, fenêtre 99–290 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C18** · hostile, 88 pts, besoin : 4 light, fenêtre 218–425 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C48** · hostile, 88 pts, besoin : 2 light, fenêtre 492–677 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C14** · hostile, 87 pts, besoin : 3 light, fenêtre 266–456 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C17** · hostile, 86 pts, besoin : 4 light, fenêtre 344–567 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C20** · hostile, 86 pts, besoin : 3 light, fenêtre 399–671 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C32** · hostile, 86 pts, besoin : 1 heavy, fenêtre 296–649 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C15** · hostile, 85 pts, besoin : 4 light, fenêtre 158–404 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C43** · hostile, 84 pts, besoin : 2 light, fenêtre 348–656 s · interdit par R7 (à 149 m de C75, friendly)
- **C04** · hostile, 83 pts, besoin : 1 light, fenêtre 228–534 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C07** · hostile, 83 pts, besoin : 4 light, fenêtre 391–654 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C34** · hostile, 83 pts, besoin : 1 light, 1 heavy, fenêtre 46–330 s · interdit par R7 (à 178 m de C76, friendly)
- **C02** · hostile, 82 pts, besoin : 4 light, fenêtre 309–557 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C11** · hostile, 82 pts, besoin : 1 light, fenêtre 24–223 s · interdit par R7 (à 160 m de C78, friendly)
- **C49** · hostile, 79 pts, besoin : 3 light, 1 heavy, fenêtre 65–289 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C31** · hostile, 78 pts, besoin : 1 light, 2 heavy, fenêtre 424–727 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C41** · hostile, 78 pts, besoin : 3 light, fenêtre 225–571 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C12** · hostile, 77 pts, besoin : 2 light, fenêtre 348–619 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C33** · hostile, 77 pts, besoin : 1 light, fenêtre 358–698 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C09** · hostile, 76 pts, besoin : 1 light, fenêtre 388–617 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C30** · hostile, 76 pts, besoin : 3 light, 1 heavy, fenêtre 353–646 s · interdit par R7 (à 165 m de C85, civilian)
- **C38** · hostile, 76 pts, besoin : 3 light, 1 heavy, fenêtre 476–774 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C22** · hostile, 74 pts, besoin : 1 light, fenêtre 472–699 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C23** · hostile, 66 pts, besoin : 3 light, fenêtre 407–682 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C10** · hostile, 64 pts, besoin : 2 light, fenêtre 308–641 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C29** · hostile, 63 pts, besoin : 2 light, fenêtre 72–307 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C39** · hostile, 62 pts, besoin : 2 light, 2 heavy, fenêtre 269–480 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C05** · hostile, 60 pts, besoin : 2 light, fenêtre 336–570 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C21** · hostile, 59 pts, besoin : 1 light, fenêtre 294–549 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C35** · hostile, 59 pts, besoin : 1 heavy, fenêtre 4–185 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C50** · hostile, 58 pts, besoin : 3 light, 1 heavy, fenêtre 489–844 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C08** · hostile, 56 pts, besoin : 1 light, fenêtre 226–476 s · interdit par R7 (à 156 m de C72, friendly)
- **C24** · hostile, 56 pts, besoin : 3 light, fenêtre 299–634 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C44** · hostile, 56 pts, besoin : 2 light, 2 heavy, fenêtre 18–317 s · interdit par R7 (à 160 m de C79, friendly)
- **C45** · hostile, 54 pts, besoin : 2 light, fenêtre 150–335 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C28** · hostile, 51 pts, besoin : 2 light, fenêtre 246–552 s · interdit par R7 (à 118 m de C79, friendly)
- **C42** · hostile, 49 pts, besoin : 1 light, fenêtre 331–565 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C01** · hostile, 44 pts, besoin : 2 light, fenêtre 421–740 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C25** · hostile, 40 pts, besoin : 4 light, fenêtre 370–559 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C26** · hostile, 40 pts, besoin : 2 heavy, fenêtre 412–721 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C57** · unknown, 29 pts, besoin : observation, fenêtre 330–535 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C55** · unknown, 25 pts, besoin : observation, fenêtre 159–390 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C61** · unknown, 25 pts, besoin : observation, fenêtre 184–365 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C62** · unknown, 25 pts, besoin : observation, fenêtre 212–523 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C56** · unknown, 24 pts, besoin : observation, fenêtre 78–274 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C58** · unknown, 23 pts, besoin : observation, fenêtre 156–464 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C69** · unknown, 23 pts, besoin : observation, fenêtre 417–672 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C54** · unknown, 12 pts, besoin : observation, fenêtre 242–436 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C52** · unknown, 11 pts, besoin : observation, fenêtre 357–570 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C70** · unknown, 10 pts, besoin : observation, fenêtre 10–348 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)

Points réellement gagnables sans toucher au plan actuel (routage réel rejoué sur chaque contact) : **142 pts**. En concurrence avec un contact déjà servi pour les mêmes drones : **0 pts** (gagnable seulement en sacrifiant un autre contact).
