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


tunel-start:
	cd resources/ssh && ssh -F config -f -N bastion

tunel-stop:
	@kill $$(ps aux | grep '[b]astion' | awk '{print $$2}')

nodeR1:
	cd resources/ssh && ssh -F config nodeR1

nodeLami:
	cd resources/ssh && ssh -F config nodeLami

nodeL1:
	cd resources/ssh && ssh -F config nodeL1

nodeL2:
	cd resources/ssh && ssh -F config nodeL2

spotify:
	cd resources/ssh && ssh -F config spotify

kill-register:
	@kill $$(ps aux | grep '[r]egister' | awk '{print $$2}')

kill-listener:
	@kill $$(ps aux | grep '[l]istener' | awk '{print $$2}')
