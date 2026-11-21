# Explication du plan · scénario S-half-scouts seed 10

| | Glouton | Notre plan |
| --- | ---: | ---: |
| Valide | oui | oui |
| Score | 274.3 | 522.2 |
| Points servis | 546.0 | 1251.0 |
| Énergie (Wh) | 263.4 | 677.5 |
| Drones d'action consommés | 14 | 39 |
| Contacts servis | 13 | 18 |

Coût d'1 Wh = 0.5 pt · coût d'un drone d'action = 10 pts.

## Stratégie du planificateur

Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes touchées, environ 3 fois plus d'essais par seconde) ; relances par petites variations autour du meilleur ordre de contacts trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de 38 s ; deux routages selon la taille de la flotte, filet de sécurité (Mahmoud) et routage (Youcef) intégrés. Chaque plan construit est revalidé par le scorer du kit ; au final, on écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est).

Résultat sur ce scénario : **+90 %** par rapport au glouton (274.3 → 522.2 pts).

Gagnés par rapport au glouton : C01, C05, C06, C07, C19, C29, C32, C36, C37, C41, C47, C49 · perdus : C34, C46, C54, C59, C61, C63, C69.

## Ressources

| Type | Disponibles | Utilisés | Restants |
| --- | ---: | ---: | ---: |
| effector (heavy) | 35 | 4 | 31 |
| effector (light) | 50 | 35 | 15 |
| scout | 7 | 7 | 0 |

Drones au sol : H01, H02, H03, H05, H06, H07, H08, H09, H10, H11, H12, H13, H14, H15, H16, H17, H18, H19, H20, H21, H23, H24, H25, H26, H28, H29, H31, H32, H33, H34, H35, L03, L07, L10, L12, L15, L19, L22, L28, L29, L31, L33, L34, L35, L38, L40.

## Affectations, drone par drone

### H04 · effector (heavy)

Distance 4.60 km · énergie 13.2 Wh sur 51.0 Wh utilisables · coût 6.6 pts.

- t = 604 s · engage **C06** (hostile, 61 pts, fenêtre 424–652 s)

### H22 · effector (heavy)

Distance 6.99 km · énergie 15.8 Wh sur 46.4 Wh utilisables · coût 7.9 pts.

- t = 433 s · engage **C49** (hostile, 71 pts, fenêtre 373–706 s)

### H27 · effector (heavy)

Distance 6.44 km · énergie 21.3 Wh sur 47.5 Wh utilisables · coût 10.7 pts.

- t = 633 s · engage **C05** (hostile, 55 pts, fenêtre 427–749 s)

### H30 · effector (heavy)

Distance 6.65 km · énergie 19.8 Wh sur 57.7 Wh utilisables · coût 9.9 pts.

- t = 582 s · engage **C35** (hostile, 70 pts, fenêtre 344–654 s)

### L01 · effector (light)

Distance 4.21 km · énergie 8.2 Wh sur 32.9 Wh utilisables · coût 4.1 pts.

- t = 332 s · engage **C42** (hostile, 76 pts, fenêtre 162–343 s)

### L02 · effector (light)

Distance 6.26 km · énergie 9.8 Wh sur 52.7 Wh utilisables · coût 4.9 pts.

- t = 600 s · engage **C47** (hostile, 70 pts, fenêtre 398–650 s)

### L04 · effector (light)

Distance 7.24 km · énergie 11.7 Wh sur 46.6 Wh utilisables · coût 5.8 pts.

- t = 515 s · engage **C41** (hostile, 75 pts, fenêtre 243–600 s)

### L05 · effector (light)

Distance 7.11 km · énergie 12.0 Wh sur 38.3 Wh utilisables · coût 6.0 pts.

- t = 504 s · engage **C37** (hostile, 60 pts, fenêtre 466–745 s)

### L06 · effector (light)

Distance 6.27 km · énergie 11.6 Wh sur 37.4 Wh utilisables · coût 5.8 pts.

- t = 605 s · engage **C47** (hostile, 70 pts, fenêtre 398–650 s)

### L08 · effector (light)

Distance 7.70 km · énergie 11.7 Wh sur 46.8 Wh utilisables · coût 5.9 pts.

- t = 483 s · engage **C36** (hostile, 100 pts, fenêtre 344–529 s)

### L09 · effector (light)

Distance 6.70 km · énergie 11.2 Wh sur 29.8 Wh utilisables · coût 5.6 pts.

- t = 475 s · engage **C19** (hostile, 48 pts, fenêtre 435–715 s)

### L11 · effector (light)

Distance 7.17 km · énergie 10.0 Wh sur 37.9 Wh utilisables · coût 5.0 pts.

- t = 427 s · engage **C32** (hostile, 95 pts, fenêtre 208–487 s)

### L13 · effector (light)

Distance 4.61 km · énergie 9.0 Wh sur 45.6 Wh utilisables · coût 4.5 pts.

- t = 619 s · engage **C06** (hostile, 61 pts, fenêtre 424–652 s)

### L14 · effector (light)

Distance 7.08 km · énergie 10.1 Wh sur 40.1 Wh utilisables · coût 5.0 pts.

- t = 382 s · engage **C29** (hostile, 100 pts, fenêtre 162–408 s)

### L16 · effector (light)

Distance 3.70 km · énergie 6.0 Wh sur 42.6 Wh utilisables · coût 3.0 pts.

- t = 265 s · engage **C02** (hostile, 76 pts, fenêtre 4–343 s)

### L17 · effector (light)

Distance 7.18 km · énergie 12.5 Wh sur 37.9 Wh utilisables · coût 6.3 pts.

- t = 432 s · engage **C32** (hostile, 95 pts, fenêtre 208–487 s)

### L18 · effector (light)

Distance 4.19 km · énergie 8.4 Wh sur 40.0 Wh utilisables · coût 4.2 pts.

- t = 331 s · engage **C42** (hostile, 76 pts, fenêtre 162–343 s)

### L20 · effector (light)

Distance 6.50 km · énergie 12.0 Wh sur 49.9 Wh utilisables · coût 6.0 pts.

- t = 643 s · engage **C05** (hostile, 55 pts, fenêtre 427–749 s)

### L21 · effector (light)

Distance 7.60 km · énergie 11.7 Wh sur 43.0 Wh utilisables · coût 5.9 pts.

- t = 482 s · engage **C01** (hostile, 100 pts, fenêtre 285–603 s)

### L23 · effector (light)

Distance 4.66 km · énergie 8.0 Wh sur 45.5 Wh utilisables · coût 4.0 pts.

- t = 609 s · engage **C06** (hostile, 61 pts, fenêtre 424–652 s)

### L24 · effector (light)

Distance 4.61 km · énergie 9.8 Wh sur 50.4 Wh utilisables · coût 4.9 pts.

- t = 614 s · engage **C06** (hostile, 61 pts, fenêtre 424–652 s)

### L25 · effector (light)

Distance 7.70 km · énergie 12.7 Wh sur 33.0 Wh utilisables · coût 6.3 pts.

- t = 484 s · engage **C36** (hostile, 100 pts, fenêtre 344–529 s)

### L26 · effector (light)

Distance 7.18 km · énergie 13.0 Wh sur 36.5 Wh utilisables · coût 6.5 pts.

- t = 437 s · engage **C32** (hostile, 95 pts, fenêtre 208–487 s)

### L27 · effector (light)

Distance 6.71 km · énergie 12.2 Wh sur 33.1 Wh utilisables · coût 6.1 pts.

- t = 587 s · engage **C35** (hostile, 70 pts, fenêtre 344–654 s)

### L30 · effector (light)

Distance 7.25 km · énergie 13.4 Wh sur 42.8 Wh utilisables · coût 6.7 pts.

- t = 520 s · engage **C41** (hostile, 75 pts, fenêtre 243–600 s)

### L32 · effector (light)

Distance 7.58 km · énergie 12.1 Wh sur 36.3 Wh utilisables · coût 6.1 pts.

- t = 476 s · engage **C01** (hostile, 100 pts, fenêtre 285–603 s)

### L36 · effector (light)

Distance 3.48 km · énergie 5.9 Wh sur 35.3 Wh utilisables · coût 3.0 pts.

- t = 382 s · engage **C18** (hostile, 71 pts, fenêtre 339–651 s)

### L37 · effector (light)

Distance 7.24 km · énergie 10.1 Wh sur 36.8 Wh utilisables · coût 5.0 pts.

- t = 510 s · engage **C41** (hostile, 75 pts, fenêtre 243–600 s)

### L39 · effector (light)

Distance 7.08 km · énergie 12.8 Wh sur 37.8 Wh utilisables · coût 6.4 pts.

- t = 384 s · engage **C29** (hostile, 100 pts, fenêtre 162–408 s)

### L41 · effector (light)

Distance 7.11 km · énergie 12.0 Wh sur 43.8 Wh utilisables · coût 6.0 pts.

- t = 503 s · engage **C37** (hostile, 60 pts, fenêtre 466–745 s)

### L42 · effector (light)

Distance 7.57 km · énergie 12.2 Wh sur 44.0 Wh utilisables · coût 6.1 pts.

- t = 481 s · engage **C01** (hostile, 100 pts, fenêtre 285–603 s)

### L43 · effector (light)

Distance 3.70 km · énergie 6.1 Wh sur 32.7 Wh utilisables · coût 3.1 pts.

- t = 260 s · engage **C02** (hostile, 76 pts, fenêtre 4–343 s)

### L44 · effector (light)

Distance 7.57 km · énergie 13.0 Wh sur 42.5 Wh utilisables · coût 6.5 pts.

- t = 471 s · engage **C01** (hostile, 100 pts, fenêtre 285–603 s)

### L45 · effector (light)

Distance 7.70 km · énergie 13.1 Wh sur 31.4 Wh utilisables · coût 6.5 pts.

- t = 489 s · engage **C36** (hostile, 100 pts, fenêtre 344–529 s)

### L46 · effector (light)

Distance 7.09 km · énergie 11.8 Wh sur 38.6 Wh utilisables · coût 5.9 pts.

- t = 394 s · engage **C29** (hostile, 100 pts, fenêtre 162–408 s)

### L47 · effector (light)

Distance 6.09 km · énergie 10.5 Wh sur 43.5 Wh utilisables · coût 5.2 pts.

- t = 435 s · engage **C07** (hostile, 69 pts, fenêtre 398–672 s)

### L48 · effector (light)

Distance 6.49 km · énergie 9.3 Wh sur 38.7 Wh utilisables · coût 4.6 pts.

- t = 638 s · engage **C05** (hostile, 55 pts, fenêtre 427–749 s)

### L49 · effector (light)

Distance 6.08 km · énergie 9.6 Wh sur 50.1 Wh utilisables · coût 4.8 pts.

- t = 437 s · engage **C07** (hostile, 69 pts, fenêtre 398–672 s)

### L50 · effector (light)

Distance 4.19 km · énergie 7.3 Wh sur 50.2 Wh utilisables · coût 3.7 pts.

- t = 325 s · engage **C42** (hostile, 76 pts, fenêtre 162–343 s)

### S01 · scout

Distance 15.59 km · énergie 37.9 Wh sur 38.5 Wh utilisables · coût 19.0 pts.

- t = 348 s · observe **C29** (hostile, 100 pts, fenêtre 162–408 s)
- t = 387 s · observe **C32** (hostile, 95 pts, fenêtre 208–487 s)
- t = 435 s · observe **C36** (hostile, 100 pts, fenêtre 344–529 s)
- t = 475 s · observe **C41** (hostile, 75 pts, fenêtre 243–600 s)
- t = 568 s · observe **C47** (hostile, 70 pts, fenêtre 398–650 s)

### S02 · scout

Distance 14.92 km · énergie 39.8 Wh sur 43.5 Wh utilisables · coût 19.9 pts.

- t = 433 s · observe **C01** (hostile, 100 pts, fenêtre 285–603 s)

### S03 · scout

Distance 13.15 km · énergie 33.1 Wh sur 33.4 Wh utilisables · coût 16.5 pts.

- t = 398 s · observe **C07** (hostile, 69 pts, fenêtre 398–672 s)
- t = 443 s · observe **C19** (hostile, 48 pts, fenêtre 435–715 s)

### S04 · scout

Distance 13.98 km · énergie 31.4 Wh sur 32.4 Wh utilisables · coût 15.7 pts.

- t = 466 s · observe **C37** (hostile, 60 pts, fenêtre 466–745 s)

### S05 · scout

Distance 13.12 km · énergie 33.6 Wh sur 34.9 Wh utilisables · coût 16.8 pts.

- t = 430 s · observe **C35** (hostile, 70 pts, fenêtre 344–654 s)
- t = 461 s · observe **C05** (hostile, 55 pts, fenêtre 427–749 s)

### S06 · scout

Distance 9.62 km · énergie 27.2 Wh sur 40.9 Wh utilisables · coût 13.6 pts.

- t = 230 s · observe **C02** (hostile, 76 pts, fenêtre 4–343 s)
- t = 289 s · observe **C42** (hostile, 76 pts, fenêtre 162–343 s)
- t = 350 s · observe **C18** (hostile, 71 pts, fenêtre 339–651 s)
- t = 455 s · observe **C60** (unknown, 30 pts, fenêtre 268–604 s)
- t = 576 s · observe **C64** (unknown, 24 pts, fenêtre 431–664 s)

### S07 · scout

Distance 14.21 km · énergie 33.7 Wh sur 33.9 Wh utilisables · coût 16.8 pts.

- t = 401 s · observe **C49** (hostile, 71 pts, fenêtre 373–706 s)
- t = 572 s · observe **C06** (hostile, 61 pts, fenêtre 424–652 s)

## Contacts non servis

- **C26** · hostile, 98 pts, besoin : 2 light, 2 heavy, fenêtre 260–469 s · interdit par R7 (à 196 m de C77, friendly)
- **C38** · hostile, 97 pts, besoin : 1 light, fenêtre 93–382 s · interdit par R7 (à 134 m de C77, friendly)
- **C23** · hostile, 94 pts, besoin : 2 light, fenêtre 267–618 s · interdit par R7 (à 133 m de C85, civilian)
- **C27** · hostile, 92 pts, besoin : 1 heavy, fenêtre 123–332 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C17** · hostile, 85 pts, besoin : 1 light, fenêtre 100–380 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C24** · hostile, 85 pts, besoin : 1 light, 2 heavy, fenêtre 218–521 s · interdit par R7 (à 132 m de C73, friendly)
- **C08** · hostile, 75 pts, besoin : 1 light, fenêtre 303–616 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C28** · hostile, 74 pts, besoin : 1 heavy, fenêtre 337–566 s · interdit par R7 (à 111 m de C81, friendly)
- **C39** · hostile, 74 pts, besoin : 1 light, fenêtre 76–294 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C22** · hostile, 73 pts, besoin : 2 light, fenêtre 6–213 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C33** · hostile, 73 pts, besoin : 2 light, fenêtre 259–531 s · interdit par R7 (à 123 m de C71, friendly)
- **C50** · hostile, 73 pts, besoin : 2 light, 1 heavy, fenêtre 154–432 s · interdit par R7 (à 174 m de C83, civilian)
- **C30** · hostile, 70 pts, besoin : 2 light, fenêtre 216–455 s · interdit par R7 (à 132 m de C80, friendly)
- **C11** · hostile, 68 pts, besoin : 2 light, 1 heavy, fenêtre 247–578 s · routable seul, mais les drones nécessaires sont déjà pris par un autre contact dans notre plan (concurrence de ressources)
- **C14** · hostile, 67 pts, besoin : 1 heavy, fenêtre 392–696 s · interdit par R7 (à 126 m de C76, friendly)
- **C44** · hostile, 67 pts, besoin : 3 light, fenêtre 288–581 s · interdit par R7 (à 127 m de C90, civilian)
- **C20** · hostile, 65 pts, besoin : 2 light, fenêtre 310–632 s · interdit par R7 (à 132 m de C82, friendly)
- **C40** · hostile, 61 pts, besoin : 2 light, fenêtre 20–313 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C04** · hostile, 59 pts, besoin : 1 light, fenêtre 425–630 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C16** · hostile, 59 pts, besoin : 2 light, fenêtre 433–642 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C31** · hostile, 59 pts, besoin : 2 light, fenêtre 110–344 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C12** · hostile, 57 pts, besoin : 3 light, fenêtre 246–441 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C03** · hostile, 54 pts, besoin : 3 light, fenêtre 226–519 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C34** · hostile, 54 pts, besoin : 3 light, fenêtre 260–528 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C46** · hostile, 52 pts, besoin : 3 light, fenêtre 212–441 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C21** · hostile, 51 pts, besoin : 1 light, 2 heavy, fenêtre 108–444 s · interdit par R7 (à 165 m de C72, friendly)
- **C45** · hostile, 51 pts, besoin : 2 heavy, fenêtre 319–677 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C25** · hostile, 49 pts, besoin : 1 heavy, fenêtre 270–513 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C48** · hostile, 48 pts, besoin : 3 light, fenêtre 249–440 s · interdit par R7 (à 148 m de C90, civilian)
- **C10** · hostile, 47 pts, besoin : 3 light, 1 heavy, fenêtre 296–490 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C09** · hostile, 46 pts, besoin : 1 heavy, fenêtre 255–457 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C13** · hostile, 44 pts, besoin : 1 light, fenêtre 424–650 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C15** · hostile, 40 pts, besoin : 1 heavy, fenêtre 488–733 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C43** · hostile, 40 pts, besoin : 1 heavy, fenêtre 307–559 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C54** · unknown, 28 pts, besoin : observation, fenêtre 486–739 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C58** · unknown, 27 pts, besoin : observation, fenêtre 382–589 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C65** · unknown, 27 pts, besoin : observation, fenêtre 30–269 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C69** · unknown, 26 pts, besoin : observation, fenêtre 276–505 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C52** · unknown, 24 pts, besoin : observation, fenêtre 54–374 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C56** · unknown, 24 pts, besoin : observation, fenêtre 245–460 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C62** · unknown, 23 pts, besoin : observation, fenêtre 247–493 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C66** · unknown, 22 pts, besoin : observation, fenêtre 360–557 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C51** · unknown, 19 pts, besoin : observation, fenêtre 346–556 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C68** · unknown, 19 pts, besoin : observation, fenêtre 58–362 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C55** · unknown, 18 pts, besoin : observation, fenêtre 77–327 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C53** · unknown, 17 pts, besoin : observation, fenêtre 106–375 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C70** · unknown, 16 pts, besoin : observation, fenêtre 111–340 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C63** · unknown, 15 pts, besoin : observation, fenêtre 181–410 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C61** · unknown, 14 pts, besoin : observation, fenêtre 445–641 s · routage réel réussi avec des drones encore au sol, sans conflit : à gagner
- **C67** · unknown, 13 pts, besoin : observation, fenêtre 378–718 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C57** · unknown, 11 pts, besoin : observation, fenêtre 11–361 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)
- **C59** · unknown, 10 pts, besoin : observation, fenêtre 475–787 s · aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)

Points réellement gagnables sans toucher au plan actuel (routage réel rejoué sur chaque contact) : **416 pts**. En concurrence avec un contact déjà servi pour les mêmes drones : **68 pts** (gagnable seulement en sacrifiant un autre contact).
