# Link loss : mini-simulateur, plans à marges, courbe de dimensionnement

Statut : partie OPTIONNELLE du brief, construite par nous. Le kit ne simule pas la perte de liaison et son scorer ne la note pas (README du kit : « no communication »). Le brief décrit un « banc en boîte noire » des organisateurs dont l'interface ne nous a pas été donnée : tout ce qui suit est mesuré dans NOTRE simulateur, avec NOS hypothèses. Rien ici n'est importé par `handin/planner.py` (un test le vérifie) : le plan remis ne change pas.

## Ce que le brief demande (docs/brief.pdf, page 3)
- Livrable : « une politique pour le cas de perte de liaison, passée dans un banc en boîte noire + une courbe de dimensionnement ».
- Évaluation : points encore servis après la coupure, sans violation de séparation ni de zone, moins un petit coût par message ; le scorer balaie le budget de communication (débit, portée) ; un design qui tient sur un budget serré est récompensé.

## Modèle (linkloss/sim.py)
- Le plan est valide et déterministe. À `t_cut` (par défaut 25 % de l'horizon) la liaison avec l'opérateur est perdue pour de bon.
- Après la coupure, une part des avions (30 % par défaut) vole plus lentement : retard à chaque waypoint = `ralentissement x (t - t_cut)`, ralentissement tiré dans (0, max_slow). Les trajectoires dans l'espace ne changent pas (zones et contacts intacts) : seules les règles de temps peuvent casser (R4 confirmation, R8 séparation, R9 fenêtres, R10 synchronisation, horizon, énergie).
- Score d'un run : points des contacts encore servis après la coupure (règles re-vérifiées sur les temps perturbés, aucune paire en violation de séparation parmi les avions du contact, énergie suffisante jusqu'à la dernière action) moins `cout x messages`. Le plafond est la même somme sans perturbation.
- Politiques :
  - `continue` : suivre le plan à l'aveugle, 0 message.
  - `return` : tout le monde rentre à la coupure, 0 violation, 0 point après la coupure (plancher de sécurité).
  - `adjust` : un avion en retard qui ferait échouer un de ses contacts diffuse son retard (portée limitée, débit limité à `max_msgs` diffusions espacées de `period_s`, pertes, latence) ; un équipier qui l'entend attend en vol au dernier waypoint avant son action pour garder l'équipe synchrone, seulement si le contact échouerait sinon.
- Plans à marges (linkloss/harden.py) : on donne au planificateur INCHANGÉ une copie du scénario aux règles plus strictes (séparation +20/+40/+60 m, marge de confirmation et fenêtres rétrécies de 5/10/20 s, fenêtre de synchronisation 10/6/4 s). Un plan valide pour la copie est valide pour le vrai scénario (vérifié sur chaque plan du balayage), et il garde de la marge quand les avions arrivent en retard.

## Lancer
```sh
cd fleet-kit
python3 -m unittest tests.test_linkloss            # 10 tests
python3 -m linkloss.sweep --levels L2 L3 --seeds 0-3 --draws 30 --out linkloss/results
```

## Mesures (linkloss/results, 8 scénarios L2 et L3 graines 0 à 3, 30 tirages de dérive chacun, coupure à 25 % de l'horizon)
Score attendu = score du plan - points perdus après la coupure - coût des messages (1 point par message). Moyenne sur les 8 scénarios.

| Marge du plan | Score du plan sans dérive | Attendu, continue, dérive 5 % | 10 % | 30 % | Part de tirages avec violation de séparation (10 %) |
|---|---|---|---|---|---|
| 0 (plan remis) | 387,2 | 277,4 | 239,4 | 183,1 | 40 % |
| 1 (+20 m, 5 s, sync 10 s) | 348,1 | 298,3 | 241,8 | 193,4 | 43 % |
| 2 (+40 m, 10 s, sync 6 s) | 314,9 | 288,4 | 262,4 | 210,5 | 25 % |
| 3 (+60 m, 20 s, sync 4 s) | 241,8 | 241,8 | 236,4 | 222,4 | 3 % |

Lecture (MESURÉ dans notre simulateur) :
- Sans aucune dérive, le plan de marge 0 est le meilleur (387,2 contre 241,8 pour la marge 3) : la marge coûte du score nominal. Elle ne se justifie que si la perte de liaison est probable.
- Dès 10 % de ralentissement, la marge 2 gagne +9,6 % en score attendu sur la marge 0 (262,4 contre 239,4) ; à 30 %, +15 % (210,5 contre 183,1) pour la marge 2 et +21 % (222,4) pour la marge 3. La marge 3 est la seule presque sûre (3 % de tirages avec violation de séparation, contre 40 % pour le plan remis).
- Politique `adjust` (portée 1000 m, 3 messages, sans perte) contre `continue` à marge égale : +3,2 % à 10 % de dérive sur la marge 0 (246,9 contre 239,4), +9,3 % à 30 % ; +3,1 % et +6,0 % sur la marge 2. Les messages ne réparent pas la séparation entre avions de contacts différents : l'essentiel du gain vient des marges, pas de la radio.
- Courbe de dimensionnement (sizing.svg, dérive 10 %, 3 messages) : sans portée, `adjust` coûte ses messages et fait moins bien que `continue` (235,7 contre 239,4 sur la marge 0). Le score monte avec la portée (marge 0 : 240,4 à 100 m, 246,9 à 1000 m, 266,4 à 3000 m) ; 30 % de pertes de messages n'enlèvent qu'environ 1 à 3 points. Sur la marge 2, la courbe est presque plate dès 100 m (270,2 à 100 m, 277,0 à 3000 m) : un plan à marge tient sur un budget de communication serré, un plan à marge 0 non.
- Plan de repli `return` (tout le monde rentre à la coupure) : sûr, mais perd tous les points d'après la coupure.

## Limites honnêtes
- Modèle de perturbation unique (ralentissement) : pas de vent latéral, pas de pannes d'avion, pas de messages en relais.
- Interface du banc officiel inconnue : aucune garantie de transfert des chiffres.
- L'attente en vol de `adjust` peut elle-même créer des conflits de séparation avec des tiers : le simulateur les compte.
