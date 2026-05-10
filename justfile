up:
    docker compose up --build -d

down:
    docker compose down

shell:
    docker exec -it noodlesdb psql -U valerii -d noodlesdb