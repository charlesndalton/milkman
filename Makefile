# include .env file and export its env vars
# (-include to ignore error if it does not exist)
-include .env

# deps
update:; forge update

# Build & test
# change ETH_RPC_URL to another one (e.g., FTM_RPC_URL) for different chains
FORK_URL := ${ETH_RPC_URL} 

.PHONY: build test test-operation test-all-operation trace test-contract trace-contract deploy test-local trace-local clean snapshot

# For deployments. Add all args without a comma
# ex: 0x316..FB5 "Name" 10
constructor-args := 

build  :; forge build
test   :; forge test -vv --fork-url ${FORK_URL} --etherscan-api-key ${ETHERSCAN_API_KEY} --ffi
test-operation :; forge test -vvv --fork-url ${FORK_URL} --etherscan-api-key ${ETHERSCAN_API_KEY} --match-test "testProfitableHarvest_AngleFarmingProfit"
test-all-operation :; forge test -vv --fork-url ${FORK_URL} --etherscan-api-key ${ETHERSCAN_API_KEY} --match-contract "StrategyOperation"
trace   :; forge test -vvv --fork-url ${FORK_URL} --etherscan-api-key ${ETHERSCAN_API_KEY}
test-contract :; forge test -vv --fork-url ${FORK_URL} --match-contract $(contract) --etherscan-api-key ${ETHERSCAN_API_KEY}
trace-contract :; forge test -vvv --fork-url ${FORK_URL} --match-contract $(contract) --etherscan-api-key ${ETHERSCAN_API_KEY}
deploy	:; forge create --rpc-url ${FORK_URL} --constructor-args ${constructor-args} --private-key ${PRIV_KEY} src/Strategy.sol:Strategy --etherscan-api-key ${ETHERSCAN_API_KEY} --verify
# local tests without fork
test-local  :; forge test
trace-local  :; forge test -vvv
clean  :; forge clean
snapshot :; forge snapshot