# Fleet Orchestration : environnement reproductible (Python stdlib uniquement).
#
# Build (depuis fleet-kit/) :   docker build -t fleet-kit .
# Check du hand-in :            docker run --rm fleet-kit
# Une commande fleetkit :       docker run --rm fleet-kit python -m fleetkit stats L2 --seeds 0-19
# Limiter les CPU (test réaliste de la machine d'évaluation) : docker run --rm --cpus 2 fleet-kit
# Récupérer les fichiers générés (viewer, plans) dans ./out :
#   docker run --rm -v "$PWD/out:/out" fleet-kit sh -c \
#     "python -m fleetkit generate L4 3 -o /out/s.json && python handin/planner.py /out/s.json /out/plan.json && python -m fleetkit view /out/s.json /out/plan.json -o /out/view.html"
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /kit
COPY . /kit

# Par défaut : lance le hand-in comme le font les organisateurs.
CMD ["python", "handin/check_handin.py"]
