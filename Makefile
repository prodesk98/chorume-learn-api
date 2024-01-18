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
	docker compose pull && docker compose build && docker compose up -d && make firewall
	# executa o build interno da api
	sleep 15 && docker exec -it learn-api python build.py

stop:
	# derruba os apps e excluí as regras de firewall
	docker compose down
	# mongodb
	sudo iptables -A INPUT -p tcp --dport 27017 -j ACCEPT
	#
	sudo iptables -D -A INPUT -p tcp --dport 5672 -j ACCEPT
	sudo iptables -D -A INPUT -p tcp --dport 19530 -j ACCEPT
	sudo iptables -D -A INPUT -p tcp --dport 9091 -j ACCEPT
	sudo iptables -D -A INPUT -p tcp --dport 9001 -j ACCEPT
	sudo iptables -D -A INPUT -p tcp --dport 9000 -j ACCEPT
	sudo iptables -D -A INPUT -p tcp --dport 3306 -j ACCEPT
	sudo iptables -L

firewall:
	# Regras de firewall para evitar problemas de segurança
	# rabbitmq default password
	sudo iptables -A INPUT -p tcp --dport 5672 -j DROP
	#
	# mongodb
	sudo iptables -A INPUT -p tcp --dport 27017 -j DROP
	#
	# milvus
	sudo iptables -A INPUT -p tcp --dport 19530 -j DROP
	sudo iptables -A INPUT -p tcp --dport 9091 -j DROP
	sudo iptables -A INPUT -p tcp --dport 9001 -j DROP
	sudo iptables -A INPUT -p tcp --dport 9000 -j DROP
	# mysql
	sudo iptables -A INPUT -p tcp --dport 3306 -j DROP
	# rede interna loopback
	sudo iptables -A INPUT -i lo -j ACCEPT
	sudo iptables -L

