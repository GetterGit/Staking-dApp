from brownie import network
import pytest
from web3 import Web3
from scripts.deploy import deploy_token_farm_and_vianu_token
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)


def test_approve_stake_issue_reward_and_unstake(amount_staked, gas_limit):
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for testing on a live testnet.")
    account = get_account()
    token_farm, dapp_token = deploy_token_farm_and_vianu_token()
    # Act
    # approving dapp_token
    dapp_token.approve(token_farm.address, amount_staked, {"from": account})
    token_farm.stakeTokens(
        amount_staked, dapp_token.address, {"from": account, "gasLimit": gas_limit}
    )
    # starting balance to then add the reward to it in the assert statement
    starting_balance = dapp_token.balanceOf(account.address)
    # now need to calculate the reward using non-contract functions to then compare the results with the results of issueRewardTokens()
    price_feed_contract = get_contract("dai_usd_price_feed")
    (_, price, _, _, _) = price_feed_contract.latestRoundData()
    # stake 1 token
    # as per INITIAL_PRICE_FEED_PRICE, 1 dapp_token = 1 DAI ~ $0,999 at the time of running this test
    # so, the account should get a reward of 2000 dapp_tokens
    amount_of_tokens_to_issue = (
        price / 10 ** price_feed_contract.decimals()
    ) * amount_staked
    issue_reward_tx = token_farm.issueRewardTokens(
        {"from": account, "gasLimit": gas_limit}
    )
    issue_reward_tx.wait(1)
    # Assert
    # doing 2 asserts to account for a potenrial price deviation since it's getting continuously updated
    assert dapp_token.balanceOf(
        account.address
    ) < starting_balance + amount_of_tokens_to_issue + Web3.toWei(0.01, "ether")
    assert dapp_token.balanceOf(
        account.address
    ) > starting_balance + amount_of_tokens_to_issue - Web3.toWei(0.01, "ether")
