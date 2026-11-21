# Explication du plan · scénario S-battery seed 17

| | Glouton | Notre plan |
| --- | ---: | ---: |
| Valide | oui | oui |
| Score | 164.8 | 407.0 |
| Points servis | 346.0 | 736.0 |
| Énergie (Wh) | 202.3 | 418.0 |
| Drones d'action consommés | 8 | 12 |
| Contacts servis | 8 | 17 |

Coût d'1 Wh = 0.5 pt · coût d'un drone d'action = 10 pts.

## Stratégie du planificateur

Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes touchées, environ 3 fois plus d'essais par seconde) ; relances par petites variations autour du meilleur ordre de contacts trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de 38 s ; deux routages selon la taille de la flotte, filet de sécurité (Mahmoud) et routage (Youcef) intégrés. Chaque plan construit est revalidé par le scorer du kit ; au final, on écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est).

Résultat sur ce scénario : **+147 %** par rapport au glouton (164.8 → 407.0 pts).

Gagnés par rapport au glouton : C11, C35, C38, C39, C52, C53, C55, C59, C60, C69 · perdus : C50.

## Ressources

| Type | Disponibles | Utilisés | Restants |
| --- | ---: | ---: | ---: |
| effector (heavy) | 35 | 5 | 30 |
| effector (light) | 50 | 7 | 43 |
| scout | 15 | 10 | 5 |

Drones au sol : H01, H02, H03, H04, H05, H06, H07, H08, H09, H10, H11, H14, H15, H16, H17, H18, H19, H20, H21, H22, H23, H25, H26, H27, H28, H29, H32, H33, H34, H35, L01, L02, L03, L04, L06, L07, L08, L09, L10, L11, L12, L13, L14, L15, L17, L18, L19, L20, L22, L23, L24, L25, L26, L27, L28, L29, L30, L31, L32, L33, L34, L35, L36, L37, L38, L39, L43, L44, L45, L46, L47, L48, L50, S02, S03, S09, S14, S15.

## Affectations, drone par drone

### H12 · effector (heavy)

Distance 5.91 km · énergie 17.4 Wh sur 45.6 Wh utilisables · coût 8.7 pts.

- t = 388 s · engage **C31** (hostile, 91 pts, fenêtre 172–447 s)

### H13 · effector (heavy)

Distance 6.42 km · énergie 17.5 Wh sur 39.5 Wh utilisables · coût 8.7 pts.

- t = 438 s · engage **C11** (hostile, 77 pts, fenêtre 400–646 s)

### H24 · effector (heavy)

Distance 6.37 km · énergie 18.5 Wh sur 48.4 Wh utilisables · coût 9.2 pts.

- t = 383 s · engage **C39** (hostile, 65 pts, fenêtre 238–526 s)

### H30 · effector (heavy)

Distance 6.59 km · énergie 18.5 Wh sur 40.7 Wh utilisables · coût 9.3 pts.

- t = 513 s · engage **C35** (hostile, 88 pts, fenêtre 481–720 s)

### H31 · effector (heavy)

Distance 5.91 km · énergie 18.1 Wh sur 44.8 Wh utilisables · coût 9.0 pts.

- t = 387 s · engage **C31** (hostile, 91 pts, fenêtre 172–447 s)

### L05 · effector (light)

Distance 5.99 km · énergie 10.2 Wh sur 22.2 Wh utilisables · coût 5.1 pts.

- t = 518 s · engage **C38** (hostile, 69 pts, fenêtre 486–716 s)

### L16 · effector (light)

Distance 5.98 km · énergie 10.3 Wh sur 24.8 Wh utilisables · coût 5.1 pts.

- t = 430 s · engage **C27** (hostile, 67 pts, fenêtre 286–573 s)

### L21 · effector (light)

Distance 5.90 km · énergie 10.0 Wh sur 35.8 Wh utilisables · coût 5.0 pts.

- t = 420 s · engage **C30** (hostile, 69 pts, fenêtre 351–656 s)

### L40 · effector (light)

Distance 5.89 km · énergie 8.7 Wh sur 24.8 Wh utilisables · coût 4.4 pts.

- t = 392 s · engage **C31** (hostile, 91 pts, fenêtre 172–447 s)

### L41 · effector (light)

Distance 6.00 km · énergie 12.0 Wh sur 20.3 Wh utilisables · coût 6.0 pts.

- t = 528 s · engage **C38** (hostile, 69 pts, fenêtre 486–716 s)

### L42 · effector (light)

Distance 5.99 km · énergie 8.8 Wh sur 28.1 Wh utilisables · coût 4.4 pts.

- t = 529 s · engage **C38** (hostile, 69 pts, fenêtre 486–716 s)

### L49 · effector (light)

Distance 5.97 km · énergie 8.8 Wh sur 26.7 Wh utilisables · coût 4.4 pts.

- t = 423 s · engage **C27** (hostile, 67 pts, fenêtre 286–573 s)

### S01 · scout

Distance 12.68 km · énergie 32.4 Wh sur 32.5 Wh utilisables · coût 16.2 pts.

- t = 351 s · observe **C39** (hostile, 65 pts, fenêtre 238–526 s)
- t = 390 s · observe **C27** (hostile, 67 pts, fenêtre 286–573 s)

### S04 · scout

Distance 10.18 km · énergie 24.1 Wh sur 25.6 Wh utilisables · coût 12.1 pts.

- t = 468 s · observe **C53** (unknown, 25 pts, fenêtre 468–711 s)

### S05 · scout

Distance 4.14 km · énergie 12.1 Wh sur 18.8 Wh utilisables · coût 6.0 pts.

- t = 416 s · observe **C63** (unknown, 18 pts, fenêtre 416–727 s)

### S06 · scout

Distance 11.97 km · énergie 32.0 Wh sur 32.4 Wh utilisables · coût 16.0 pts.

- t = 486 s · observe **C38** (hostile, 69 pts, fenêtre 486–716 s)
- t = 509 s · observe **C52** (unknown, 20 pts, fenêtre 270–540 s)
- t = 576 s · observe **C60** (unknown, 14 pts, fenêtre 339–618 s)

### S07 · scout

Distance 7.56 km · énergie 20.8 Wh sur 20.9 Wh utilisables · coût 10.4 pts.

- t = 400 s · observe **C69** (unknown, 19 pts, fenêtre 125–435 s)

### S08 · scout

Distance 7.07 km · énergie 22.7 Wh sur 25.9 Wh utilisables · coût 11.4 pts.

- t = 322 s · observe **C58** (unknown, 24 pts, fenêtre 322–623 s)
- t = 426 s · observe **C51** (unknown, 23 pts, fenêtre 172–512 s)
- t = 456 s · observe **C65** (unknown, 10 pts, fenêtre 285–588 s)

### S10 · scout

Distance 11.74 km · énergie 26.6 Wh sur 27.3 Wh utilisables · coût 13.3 pts.

- t = 388 s · observe **C30** (hostile, 69 pts, fenêtre 351–656 s)

### S11 · scout

Distance 12.78 km · énergie 31.2 Wh sur 31.5 Wh utilisables · coût 15.6 pts.

- t = 350 s · observe **C31** (hostile, 91 pts, fenêtre 172–447 s)
- t = 405 s · observe **C11** (hostile, 77 pts, fenêtre 400–646 s)
- t = 485 s · observe **C55** (unknown, 29 pts, fenêtre 312–568 s)

### S12 · scout

Distance 13.15 km · énergie 34.2 Wh sur 34.3 Wh utilisables · coût 17.1 pts.

- t = 481 s · observe **C35** (hostile, 88 pts, fenêtre 481–720 s)

### S13 · scout

Distance 8.66 km · énergie 23.2 Wh sur 24.5 Wh utilisables · coût 11.6 pts.

- t = 302 s · observe **C59** (unknown, 28 pts, fenêtre 236–540 s)

## Contacts non servis

- **C09** · hostile, 100 pts, besoin : 1 light, fenêtre 382–618 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C28** · hostile, 100 pts, besoin : 4 light, fenêtre 7–202 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C44** · hostile, 100 pts, besoin : 1 light, 1 heavy, fenêtre 12–323 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C33** · hostile, 97 pts, besoin : 2 light, 1 heavy, fenêtre 267–448 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C08** · hostile, 96 pts, besoin : 2 light, 2 heavy, fenêtre 222–487 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C26** · hostile, 94 pts, besoin : 1 light, 2 heavy, fenêtre 347–630 s · interdit par R7 (à 92 m de C71, friendly)
- **C29** · hostile, 91 pts, besoin : 3 light, 1 heavy, fenêtre 332–671 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C12** · hostile, 87 pts, besoin : 3 light, fenêtre 312–670 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C45** · hostile, 86 pts, besoin : 2 light, 1 heavy, fenêtre 436–766 s · interdit par R7 (à 75 m de C90, civilian)
- **C48** · hostile, 82 pts, besoin : 3 light, fenêtre 127–452 s · interdit par R7 (à 153 m de C76, friendly)
- **C10** · hostile, 81 pts, besoin : 4 light, fenêtre 254–604 s · interdit par R7 (à 166 m de C84, civilian)
- **C03** · hostile, 80 pts, besoin : 1 light, fenêtre 218–566 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C16** · hostile, 80 pts, besoin : 2 light, fenêtre 285–641 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C24** · hostile, 77 pts, besoin : 1 light, fenêtre 387–616 s · interdit par R7 (à 164 m de C79, friendly)
- **C23** · hostile, 76 pts, besoin : 1 light, fenêtre 172–447 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C36** · hostile, 76 pts, besoin : 2 light, fenêtre 280–463 s · interdit par R7 (à 117 m de C78, friendly)
- **C21** · hostile, 73 pts, besoin : 3 light, fenêtre 149–355 s · interdit par R7 (à 158 m de C83, civilian)
- **C07** · hostile, 72 pts, besoin : 2 heavy, fenêtre 179–535 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C19** · hostile, 72 pts, besoin : 2 light, fenêtre 301–656 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C25** · hostile, 72 pts, besoin : 1 light, fenêtre 52–333 s · interdit par R7 (à 183 m de C90, civilian)
- **C34** · hostile, 72 pts, besoin : 1 light, 1 heavy, fenêtre 368–691 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C02** · hostile, 71 pts, besoin : 4 light, fenêtre 426–755 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C42** · hostile, 71 pts, besoin : 1 light, 2 heavy, fenêtre 111–325 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C17** · hostile, 67 pts, besoin : 1 light, 2 heavy, fenêtre 48–240 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C13** · hostile, 66 pts, besoin : 3 light, fenêtre 245–547 s · interdit par R7 (à 138 m de C90, civilian)
- **C37** · hostile, 61 pts, besoin : 2 heavy, fenêtre 284–548 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C05** · hostile, 60 pts, besoin : 1 heavy, fenêtre 308–630 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C41** · hostile, 60 pts, besoin : 1 heavy, fenêtre 281–529 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C04** · hostile, 56 pts, besoin : 1 light, 2 heavy, fenêtre 311–638 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C49** · hostile, 55 pts, besoin : 1 light, 1 heavy, fenêtre 494–830 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C18** · hostile, 54 pts, besoin : 3 light, fenêtre 462–688 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C40** · hostile, 53 pts, besoin : 3 light, fenêtre 161–482 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C14** · hostile, 51 pts, besoin : 3 light, fenêtre 83–274 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C15** · hostile, 49 pts, besoin : 1 light, 1 heavy, fenêtre 349–589 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C32** · hostile, 48 pts, besoin : 1 light, 1 heavy, fenêtre 474–750 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C01** · hostile, 46 pts, besoin : 4 light, fenêtre 42–256 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C20** · hostile, 45 pts, besoin : 2 light, fenêtre 142–472 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C22** · hostile, 45 pts, besoin : 1 light, 2 heavy, fenêtre 237–452 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C47** · hostile, 45 pts, besoin : 1 heavy, fenêtre 152–511 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C50** · hostile, 44 pts, besoin : 2 light, fenêtre 324–676 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C43** · hostile, 43 pts, besoin : 1 light, 2 heavy, fenêtre 3–219 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C46** · hostile, 43 pts, besoin : 3 light, fenêtre 242–552 s · interdit par R7 (à 170 m de C71, friendly)
- **C06** · hostile, 41 pts, besoin : 2 heavy, fenêtre 74–390 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C61** · unknown, 30 pts, besoin : observation, fenêtre 62–270 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C54** · unknown, 20 pts, besoin : observation, fenêtre 2–281 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C56** · unknown, 17 pts, besoin : observation, fenêtre 352–602 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C64** · unknown, 16 pts, besoin : observation, fenêtre 222–488 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C70** · unknown, 15 pts, besoin : observation, fenêtre 37–308 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C62** · unknown, 13 pts, besoin : observation, fenêtre 243–603 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C66** · unknown, 12 pts, besoin : observation, fenêtre 55–350 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C67** · unknown, 11 pts, besoin : observation, fenêtre 179–454 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C57** · unknown, 10 pts, besoin : observation, fenêtre 474–668 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C68** · unknown, 10 pts, besoin : observation, fenêtre 200–522 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner

Points réellement gagnables sans toucher au plan actuel (routage réel rejoué sur chaque contact) : **232 pts**. En concurrence avec un contact déjà servi pour les mêmes drones : **0 pts** (gagnable seulement en sacrifiant un autre contact).
