build:
	# primeiro passo para subir o app, construir o banco vetorial + dependências
	docker compose build

pull:
	# atualiza os arquivos usando o repositório e atualiza os apps usando o docker
	git pull && docker compose pull

install_docker:
	# instala o docker + compose na máquina
	curl -fsSL https://get.docker.com -o get-docker.sh
	sh get-docker.sh
	rm -rf get-docker.sh

start:
	# atualiza os apps, constrói os containers, sobe os apps e gera as regras de firewall
	docker compose pull && docker compose build && docker compose up -d
	# executa o build interno da api
	sleep 10 && docker exec -it learn-api python build.py

stop:
	# derruba os apps e excluí as regras de firewall
	docker compose down
