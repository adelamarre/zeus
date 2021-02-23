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
	@kill $$(ps aux | grep '[a]ws_bastion' | awk '{print $$2}')

awsbastion:
	cd resources/ssh && ssh -F config aws_bastion

aminodel:
	cd resources/ssh && ssh -F config ami_node_L

spotify:
	cd resources/ssh && ssh -F config spotify

kill-register:
	@kill $$(ps aux | grep '[r]egister' | awk '{print $$2}')

kill-listener:
	@kill $$(ps aux | grep '[l]istener' | awk '{print $$2}')
