// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// stake tokens CHECK
// unstake tokens
// issue rewards CHECK
// add allowed tokens for staking CHECK
// get eth value of the staked tokens CHECK

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract TokenFarm is Ownable {
    //mapping token address -> staker address -> amount
    mapping(address => mapping(address => uint256)) public stakingBalance;
    // mapping for the num of unique tokens staked by each staker to then add them to the stakers list for subsequent reward distribution
    mapping(address => uint256) public uniqueTokensStaked;
    // mapping of tokens to their price feed addresses for getTokenValue()
    mapping(address => address) public tokenPriceFeedMapping;
    // list of the tokens allowed for staking
    address[] public allowedTokens;
    // list of stakers to loop through at issueRewardTokens() as we cannot loop through a mapping
    address[] public stakers;
    // storing the reward token as a global variable
    IERC20 public rewardToken;

    // adding the reward token address when initiating the contract
    constructor(address _rewardToken) public {
        rewardToken = IERC20(_rewardToken);
    }

    // to set the price feed contract for a chosen token
    function setPriceFeedContract(address _token, address _priceFeed)
        public
        onlyOwner
    {
        tokenPriceFeedMapping[_token] = _priceFeed;
    }

    // to issue rewards in VianuToken (VIT) for stakers
    // e.g. if a staker stakes 50 ETH and 50 DAI, we want to reward 1 VIT for each 1 DAI
    function issueRewardTokens() public onlyOwner {
        // Issue tokens to all stakers by first looping through the stakers list
        for (
            uint256 stakersIndex = 0;
            stakersIndex < stakers.length;
            stakersIndex++
        ) {
            address recipient = stakers[stakersIndex];
            // send them a token reward based on their TVL
            // first, getting the rewardToken set in the constructor
            // second, calculating the staker's TVL
            uint256 stakerTotalValue = getStakerTotalValue(recipient);
            // transferring 1 reward token for each 1 USD of the userTotalValue
            rewardToken.transfer(recipient, stakerTotalValue);
        }
    }

    // !!! it's gonna be very gas exepensive to loop through all addresses to find the staker and their TVL across all unique tokens
    // !!! so, many dApps prefer enabling Claim function to save on the gas fees
    function getStakerTotalValue(address _staker)
        public
        view
        returns (uint256)
    {
        uint256 totalValue = 0;
        require(
            uniqueTokensStaked[_staker] > 0,
            "This user doesn't staker any tokens."
        );
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ) {
            // adding the amount the staker has in a given token to totalValue
            // however, gotta know what currency we count totalValue in and convert the amount to that currency before adding to totalValue
            totalValue += getStakerSingleTokenValue(
                _staker,
                allowedTokens[allowedTokensIndex]
            );
        }
        return totalValue;
    }

    // to convert any token value to USD and then get staker's balance of that token in terms of USD
    function getStakerSingleTokenValue(address _staker, address _token)
        public
        view
        returns (uint256)
    {
        // using 'if' and not 'require' so that our getStakerTotalValue tx wouldn't revert
        if (uniqueTokensStaked[_staker] <= 0) {
            return 0;
        }
        // price of the token * stakingBalance[_token][_user]
        (uint256 price, uint256 decimals) = getTokenValue(_token);
        // e.g. (10 * 1e18) ETH * (2000 * 1e8) ETH/USD / (10**8) => getting (20000 * 1e18) USD as a result
        return ((stakingBalance[_token][_staker] * price) / (10**decimals));
    }

    // to get a USD value of a chosen token
    function getTokenValue(address _token)
        public
        view
        returns (uint256, uint256)
    {
        // priceFeedAddress
        address priceFeedAddress = tokenPriceFeedMapping[_token];
        AggregatorV3Interface priceFeed = AggregatorV3Interface(
            priceFeedAddress
        );
        // getting the token's price in USD
        (, int256 price, , , ) = priceFeed.latestRoundData();
        // we need to ensure the decimals consistency
        uint256 decimals = priceFeed.decimals();
        return (uint256(price), uint256(decimals));
    }

    function stakeTokens(uint256 _amount, address _token) public {
        require(_amount > 0, "Amount must be higher than zero.");
        // making sure the user wants to stake an allowed token
        require(
            tokenIsAllowed(_token),
            "The token is not allowed for staking."
        );
        // calling transferFrom() not transfer() because the farm contract doesn't own the tokens we want to transfer to it from the staker
        // this means the staker will firstly need to approve the farm contract to spend their tokens
        // we also need the token's ABI to call this function so we need IERC20 and then wrap _token into IERC20
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        // updating the mapping for unique tokens staked by the staker
        updateUniqueTokensStaked(msg.sender, _token);
        stakingBalance[_token][msg.sender] += _amount;
        // now, we wanna see how many unique tokens the staker stakes to then be able to send a reward for all of them
        // if the staker is already in the stakers list, we don't add them there again
        // if that's the first unique token staked by the staker, we add the staker to the stakers list for later rewards
        if (uniqueTokensStaked[msg.sender] == 1) {
            stakers.push(msg.sender);
        }
    }

    function unstakeTokens(address _token) public {
        // first, how many of the token the user has
        uint256 balance = stakingBalance[_token][msg.sender];
        require(balance > 0, "You don't stake any of this token.");
        IERC20(_token).transfer(msg.sender, balance);
        stakingBalance[_token][msg.sender] = 0;
        uniqueTokensStaked[msg.sender] -= 1;
    }

    function updateUniqueTokensStaked(address _user, address _token) internal {
        if (stakingBalance[_token][_user] <= 0) {
            uniqueTokensStaked[_user] += 1;
        }
    }

    // to update the list of allowed tokens
    function addAllowedTokens(address _token) public onlyOwner {
        allowedTokens.push(_token);
    }

    // to check if the token the user wants to stake is allowed
    function tokenIsAllowed(address _token) public returns (bool) {
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ) {
            if (allowedTokens[allowedTokensIndex] == _token) {
                return true;
            }
        }
        return false;
    }
}
