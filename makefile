default:help

## Display this help dialog
help:
	@echo "${YELLOW}Usage:${NC}\n  make [command]:\n\n${YELLOW}Available commands:${NC}"
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "  ${GREEN}%-30s${NC} %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)


kill-register:
	@kill -9 $$(ps aux | grep '[r]egister' | awk '{print $$2}')

kill-listener:
	@kill -9 $$(ps aux | grep '[l]istener' | awk '{print $$2}')

kill-python:
	@kill -9 $$(ps aux | grep '[p]ython' | awk '{print $$2}')

kill-xvfb:
	@kill -9 $$(ps aux | grep '[X]vfb' | awk '{print $$2}') 

kill-chrome:
	@kill -9 $$(ps aux | grep '[c]hromedriver' | awk '{print $$2}')

purgelog:
	@rm -rf temp/*

update-venom:
	rm -rf build && rm -rf dist && pyinstaller --onefile venom.spec &&\
	sudo systemctl stop venom-service &&\
	sudo systemctl stop venom-collector &&\
	sudo rm -f /usr/bin/venom &&\
	sudo cp dist/venom /usr/bin &&\
	sudo systemctl start venom-service
	sudo systemctl start venom-collector

build-venom:
	rm -rf build && rm -rf dist && pyinstaller --onefile venom.spec


