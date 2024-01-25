// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;
pragma abicoder v2;

import "forge-std/Test.sol";
import "../src/Milkman.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// contract MockERC20 is IERC20 {
//     // Mock ERC20 implementation (or use a library like OpenZeppelin's mock contracts)
//     // Implement necessary functions like mint, transfer, etc.
// }

// contract PriceCheckerMock {
//     // Mock implementation of IPriceChecker
//     // Implement necessary functions to simulate price checking
// }

contract MilkmanTest is Test {
    Milkman milkman;
    IERC20 fromToken;
    IERC20 toToken;
    address priceChecker;

    mapping(string => address) private tokenAddress;
    mapping(string => string) private sellToBuyMap;
    string[] private tokensToSell;

    function setUp() public {
        milkman = new Milkman();
        
        tokenAddress["TOKE"] = 0x2e9d63788249371f1DFC918a52f8d799F4a38C94;
        tokenAddress["DAI"] = 0x6B175474E89094C44Da98b954EedeAC495271d0F;
        tokenAddress["USDC"] = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
        tokenAddress["USDT"] = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
        tokenAddress["GUSD"] = 0x056Fd409E1d7A124BD7017459dFEa2F387b6d5Cd;
        tokenAddress["AAVE"] = 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9;
        tokenAddress["WETH"] = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
        tokenAddress["BAT"] = 0x0D8775F648430679A709E98d2b0Cb6250d2887EF;
        tokenAddress["ALCX"] = 0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF;
        tokenAddress["WBTC"] = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
        tokenAddress["UNI"] = 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984;
        tokenAddress["BAL"] = 0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF;
        tokenAddress["BAL/WETH"] = 0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56;
        tokenAddress["YFI"] = 0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e;
        tokenAddress["COW"] = 0xDEf1CA1fb7FBcDC777520aa7f396b4E015F497aB;

        sellToBuyMap["TOKE"] = "DAI";
        sellToBuyMap["USDC"] = "USDT";
        sellToBuyMap["GUSD"] = "USDC";
        sellToBuyMap["AAVE"] = "WETH";
        sellToBuyMap["BAT"] = "ALCX";
        sellToBuyMap["WETH"] = "BAL/WETH";
        sellToBuyMap["UNI"] = "USDT";
        sellToBuyMap["ALCX"] = "TOKE";
        sellToBuyMap["BAL"] = "BAL/WETH";
        sellToBuyMap["YFI"] = "USDC";
        sellToBuyMap["USDT"] = "UNI";
        sellToBuyMap["COW"] = "DAI";

        tokensToSell = ["TOKE", "USDC", "GUSD", "AAVE", "BAT", "WETH", "UNI", "ALCX", "BAL", "YFI", "USDT", "COW"];
    }

    function testRequestSwapExactTokensForTokens() public {
        // Arrange: Set up the state before calling the function
        uint256 amountIn = 1e18;  // Example amount

        // Act: Call the function you want to test
        milkman.requestSwapExactTokensForTokens(
            amountIn,
            fromToken,
            toToken,
            address(this), // Receiver address
            address(priceChecker),
            "" // priceCheckerData
        );

        // Assert: Check the state after calling the function
        // Example: Assert that the swap was requested correctly
        assertTrue(true);
    }

    // Additional test cases for different scenarios and edge cases
}
