from brownie import TokenFarm, VianuToken, config, network
from scripts.helpful_scripts import get_account, get_contract
from web3 import Web3

# initial ERC20 token supply
INITIAL_SUPPLY = Web3.toWei(1000000000, "ether")
# reserve of the ERC20 token
KEPT_AMOUNT = Web3.toWei(1000000, "ether")


def deploy_token_farm_and_vianu_token():
    account = get_account()
    dapp_token = VianuToken.deploy(
        INITIAL_SUPPLY,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    token_farm = TokenFarm.deploy(
        dapp_token.address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    # need to transfer some VIT to the farm contract for future rewards
    # transferring a bit less than TS
    reward_transfer_tx = dapp_token.transfer(
        token_farm.address, dapp_token.totalSupply() - KEPT_AMOUNT, {"from": account}
    )
    reward_transfer_tx.wait(1)
    # need to add tokens allowed for staking and give them an associated price feed contract
    # setting dapp_token to be associated with the DAI/USD price feed
    weth_token = get_contract("weth_token")
    fau_token = get_contract("fau_token")
    dict_of_allowed_tokens = {
        dapp_token: get_contract("dai_usd_price_feed"),
        fau_token: get_contract("dai_usd_price_feed"),
        weth_token: get_contract("eth_usd_price_feed"),
    }
    add_allowed_tokens(token_farm, dict_of_allowed_tokens, account)
    # returning token_farm and dapp_token to use the deploy script in our tests
    return token_farm, dapp_token


# taking token_farm to call its functions
# e.g. we wanna allow Vianu token, weth, fau(faucet token which is, for example, DAI)
def add_allowed_tokens(token_farm, dict_of_allowed_tokens, account):
    # looping through the dictionary to add its keys' addresses as allowed tokens to our contract
    # also, setting the price feeds (dict values) for those allowed tokens
    print("Adding allowed tokens to the TokenFarm contract...")
    for token in dict_of_allowed_tokens:
        add_tx = token_farm.addAllowedTokens(token.address, {"from": account})
        add_tx.wait(1)
        set_price_feed_tx = token_farm.setPriceFeedContract(
            token.address, dict_of_allowed_tokens[token], {"from": account}
        )
        set_price_feed_tx.wait(1)
    print("The allowed tokens have been added to the TokenFarm contract!")


def main():
    deploy_token_farm_and_vianu_token()
