# pytest in brownie will automatically grab all fixtures from conftest to be used across tests

import pytest
from brownie import MockERC20
from web3 import Web3
from scripts.helpful_scripts import get_account

# we should now be able to use the amount_staked() fixture as a static variable in our tests
@pytest.fixture
def amount_staked():
    return Web3.toWei(1, "ether")


# adding erc20 fixture to get a mock erc20 token for tests
@pytest.fixture
def random_erc20():
    account = get_account()
    erc20 = MockERC20.deploy({"from": account})
    return erc20


# adding gasLimit for the integraion testing on Kovan
@pytest.fixture
def gas_limit():
    return 21000
