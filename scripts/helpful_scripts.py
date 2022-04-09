from brownie import (
    accounts,
    network,
    config,
    Contract,
    MockDAI,
    MockWETH,
    MockV3Aggregator,
)
from web3 import Web3

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development"]
INITIAL_PRICE_FEED_VALUE = Web3.toWei(2000, "ether")
DECIMALS_FOR_PRICE_FEED = 18


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    elif id:
        return accounts.load(id)
    elif network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    # for the DAI/USD price feed we can parameratize MockV3Aggregatoar to set different initial values
    "dai_usd_price_feed": MockV3Aggregator,
    "weth_token": MockWETH,
    "fau_token": MockDAI,
}


def get_contract(contract_name):
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


# the function params are set for MockV3Aggregator
def deploy_mocks(
    decimals=DECIMALS_FOR_PRICE_FEED, initial_value=INITIAL_PRICE_FEED_VALUE
):
    account = get_account()
    print("Deploying mocks...")
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    MockWETH.deploy({"from": account})
    MockDAI.deploy({"from": account})
    print("All mocks have been deployed!")
