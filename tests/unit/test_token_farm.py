# the logic behind tests is that we wanna test every single piece of our smart contract
# all unit tests are to be done on the local network only

from brownie import network, exceptions
from scripts.deploy import deploy_token_farm_and_vianu_token, KEPT_AMOUNT
from scripts.helpful_scripts import (
    DECIMALS_FOR_PRICE_FEED,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    get_account,
    get_contract,
)
import pytest


def test_set_price_feed():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local testing.")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, dapp_token = deploy_token_farm_and_vianu_token()
    price_feed_address = get_contract("eth_usd_price_feed")
    # Act
    token_farm.setPriceFeedContract(
        dapp_token.address, price_feed_address, {"from": account}
    )
    # Assert
    assert token_farm.tokenPriceFeedMapping(dapp_token.address) == price_feed_address
    # also, asserting that a non-owner cannot call setPriceFeedContract()
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.setPriceFeedContract(
            dapp_token.address, price_feed_address, {"from": non_owner}
        )


# using the amount_staked() fixture from conftest to set the amount_staked param
def test_stake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local testing.")
    account = get_account()
    token_farm, dapp_token = deploy_token_farm_and_vianu_token()
    # Act
    # first, approving the token_farm contract to spend the account's dapp_token
    dapp_token.approve(token_farm.address, amount_staked, {"from": account})
    # second, we stake the token
    token_farm.stakeTokens(amount_staked, dapp_token.address, {"from": account})
    # Assert
    assert (
        token_farm.stakingBalance(dapp_token.address, account.address) == amount_staked
    )
    assert token_farm.uniqueTokensStaked(account.address) == 1
    assert token_farm.stakers(0) == account.address
    # returning token_farm and dapp_token to use this test in some other tests
    return token_farm, dapp_token


def test_issue_reward_tokens(amount_staked):
    # first, we need to stake some tokens, so the test for staking tokens should be writteb first
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local testing.")
    account = get_account()
    # also adding a non_owner to then assert that a non-owner cannot call issueRewardTokens()
    non_owner = get_account(index=1)
    # using test_stake_tokens to automatically apply its tested logic to the test_issue_reward_tokens test and have some tokens staked
    token_farm, dapp_token = test_stake_tokens(amount_staked)
    # setting the starting balance to then compare updated balace agaist it
    starting_balance = dapp_token.balanceOf(account.address)
    # Act
    token_farm.issueRewardTokens({"from": account})
    # Assert
    # We are staking 1 dapp_token == 1 ETH in price
    # So, we should get 2000 dapp_token in reward since the initial price of ETH is $2,000 according to deploy_mocks() in helpful_scripts.py
    assert (
        dapp_token.balanceOf(account.address)
        == starting_balance + INITIAL_PRICE_FEED_VALUE
    )
    # checking that a non-owner cannot call issueRewardTokens()
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.issueRewardTokens({"from": non_owner})


def test_unstake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local testing.")
    account = get_account()
    token_farm, dapp_token = test_stake_tokens(
        amount_staked
    )  # now, account stakes 1 dapp_token
    # Act
    token_farm.unstakeTokens(dapp_token, {"from": account})
    # Assert
    # the balance will be equal to KEPT_AMOUNT from scripts.deploy because we minted dapp_token to the account and then staked a part of that KEPT_AMOUNT in the token farm, and then unstaked it
    assert dapp_token.balanceOf(account.address) == KEPT_AMOUNT
    assert token_farm.stakingBalance(dapp_token.address, account.address) == 0
    assert token_farm.uniqueTokensStaked(account.address) == 0
    # Improvement: make the TokenFarm contract remove the account from the stakers list and also asset that action. However, now it's not an issue to leave the account in the stakers list because it will just always get zero rewards


def test_staker_total_value_with_different_tokens(amount_staked, random_erc20):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local testing.")
    account = get_account()
    token_farm, dapp_token = test_stake_tokens(amount_staked)
    # Act
    token_farm.addAllowedTokens(random_erc20.address, {"from": account})
    # setting eth_usd_price_feed for random_erc20 so that I can later assert that the total value of the account is "an X of INITIAL_PRICE_FEED_VALUE" because I use INITIAL_PRICE_FEED_VALUE as a param for MockV3Aggregator
    token_farm.setPriceFeedContract(
        random_erc20.address, get_contract("eth_usd_price_feed"), {"from": account}
    )
    # first, approving the token_farm contract to spend the account's random_erc20 tokens
    random_erc20.approve(token_farm.address, amount_staked, {"from": account})
    # second, staking random_erc20 in token_farm
    token_farm.stakeTokens(amount_staked, random_erc20.address, {"from": account})
    # Assert
    assert (
        token_farm.getStakerTotalValue(account.address) == INITIAL_PRICE_FEED_VALUE * 2
    )


def test_get_token_value():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local testing.")
    token_farm, dapp_token = deploy_token_farm_and_vianu_token()
    # Act / Assert
    assert token_farm.getTokenValue(dapp_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS_FOR_PRICE_FEED,
    )


def test_add_allowed_tokens(random_erc20):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local testing.")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, dapp_token = deploy_token_farm_and_vianu_token()
    # Act
    token_farm.addAllowedTokens(random_erc20.address, {"from": account})
    # Assert
    # random_erc20.address should be the 4th allowed token as deploy_token_farm_and_vianu_token() already added 3 allowed tokens
    assert token_farm.allowedTokens(3) == random_erc20.address
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.addAllowedTokens(random_erc20.address, {"from": non_owner})
