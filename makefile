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


start-bastion:
	cd resources/ssh && ssh -F config -f -N bastion

stop-bastion:
	@kill $$(ps aux | grep '[b]astion' | awk '{print $$2}')


nodeLami:
	cd resources/ssh && ssh -F config nodeLami

znodeL1:
	cd resources/ssh && ssh -F config znodeL1

spotify:
	cd resources/ssh && ssh -F config spotify

kill-register:
	@kill $$(ps aux | grep '[r]egister' | awk '{print $$2}')

kill-listener:
	@kill $$(ps aux | grep '[l]istener' | awk '{print $$2}')
