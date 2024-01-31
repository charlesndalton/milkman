// SPDX-License-Identifier: LGPL-3.0-or-later
pragma solidity ^0.7.6;

pragma abicoder v2;

import "forge-std/Test.sol";
import "forge-std/console.sol";
import {stdJson} from "forge-std/StdJson.sol";
import {Surl} from "surl/Surl.sol";
import "../src/Milkman.sol";
import "../src/pricecheckers/UniV2ExpectedOutCalculator.sol";
import "../src/pricecheckers/CurveExpectedOutCalculator.sol";
import "../src/pricecheckers/UniV3ExpectedOutCalculator.sol";
import "../src/pricecheckers/ChainlinkExpectedOutCalculator.sol";
import {SingleSidedBalancerBalWethExpectedOutCalculator} from
    "../src/pricecheckers/SingleSidedBalancerBalWethExpectedOutCalculator.sol";
import "../src/pricecheckers/MetaExpectedOutCalculator.sol";
import "../src/pricecheckers/FixedSlippageChecker.sol";
import "../src/pricecheckers/DynamicSlippageChecker.sol";
import {IPriceChecker} from "../interfaces/IPriceChecker.sol";
import {GPv2Order} from "@cow-protocol/contracts/libraries/GPv2Order.sol";
import {IERC20 as CoWIERC20} from "@cow-protocol/contracts/interfaces/IERC20.sol";
// import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeMath} from "@openzeppelin/contracts/math/SafeMath.sol";

interface IERC20Metadata {
    function decimals() external view returns (uint8);
}

contract MilkmanTest is Test {
    using Surl for *;
    using stdJson for string;
    using GPv2Order for GPv2Order.Data;
    using SafeMath for uint256;

    Milkman milkman;
    IERC20 fromToken;
    IERC20 toToken;
    uint256 amountIn;
    address priceChecker;
    address whale;

    address chainlinkExpectedOutCalculator;
    address curveExpectedOutCalculator;
    address sushiswapExpectedOutCalculator;
    address ssbBalWethExpectedOutCalculator;
    address univ3ExpectedOutCalculator;
    address metaExpectedOutCalculator;
    address chainlinkPriceChecker;
    address curvePriceChecker;
    address sushiswapPriceChecker;
    address univ3PriceChecker;
    address metaPriceChecker;
    address ssbBalWethPriceChecker;

    bytes32 public constant APP_DATA = 0x2B8694ED30082129598720860E8E972F07AA10D9B81CAE16CA0E2CFB24743E24;
    bytes4 internal constant MAGIC_VALUE = 0x1626ba7e;
    bytes4 internal constant NON_MAGIC_VALUE = 0xffffffff;

    bytes32 public constant SWAP_REQUESTED_EVENT =
        keccak256("SwapRequested(address,address,uint256,address,address,address,address,bytes)");

    address SUSHISWAP_ROUTER = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;

    mapping(string => address) private tokenAddress;
    mapping(string => string) private sellToBuyMap;
    string[] private tokensToSell;
    mapping(string => uint256) private amounts;
    mapping(string => address) private whaleAddresses;
    mapping(string => address) private priceCheckers;

    function parseUint(string memory json, string memory key) internal pure returns (uint256) {
        bytes memory valueBytes = vm.parseJson(json, key);
        string memory valueString = abi.decode(valueBytes, (string));
        return vm.parseUint(valueString);
    }

    function setUp() public {
        milkman = new Milkman();
        chainlinkExpectedOutCalculator = address(new ChainlinkExpectedOutCalculator());
        curveExpectedOutCalculator = address(new CurveExpectedOutCalculator());

        sushiswapExpectedOutCalculator = address(
            new UniV2ExpectedOutCalculator(
                                    "SUSHI_EXPECTED_OUT_CALCULATOR",
                                    0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F // Sushi Router
                                )
        );

        ssbBalWethExpectedOutCalculator = address(new SingleSidedBalancerBalWethExpectedOutCalculator());
        univ3ExpectedOutCalculator = address(new UniV3ExpectedOutCalculator());
        metaExpectedOutCalculator = address(new MetaExpectedOutCalculator());

        chainlinkPriceChecker = address(
            new DynamicSlippageChecker(
                                    "CHAINLINK_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
                                    chainlinkExpectedOutCalculator
                                )
        );

        curvePriceChecker = address(
            new DynamicSlippageChecker(
                                    "CURVE_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
                                    curveExpectedOutCalculator
                                )
        );

        sushiswapPriceChecker = address(
            new FixedSlippageChecker(
                                    "SUSHISWAP_STATIC_500_BPS_SLIPPAGE_PRICE_CHECKER",
                                    500, // 5% slippage
                                    sushiswapExpectedOutCalculator
                                )
        );

        univ3PriceChecker = address(
            new DynamicSlippageChecker(
                                    "UNIV3_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
                                    univ3ExpectedOutCalculator
                                )
        );

        metaPriceChecker = address(
            new DynamicSlippageChecker(
                                    "META_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
                                    metaExpectedOutCalculator
                                )
        );

        ssbBalWethPriceChecker = address(
            new DynamicSlippageChecker(
                                    "SSB_BAL_WETH_DYNAMIC_SLIPPAGE_PRICE_CHECKER",
                                    ssbBalWethExpectedOutCalculator
                                )
        );

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

        amounts["TOKE"] = 80000; // 80,000 TOKE
        amounts["USDC"] = 5000000; // 5,000,000 USDC
        amounts["GUSD"] = 1000; // 1,000 GUSD
        amounts["AAVE"] = 2500; // 2,500 AAVE
        amounts["BAT"] = 280000; // 280,000 BAT
        amounts["WETH"] = 325; // 325 WETH
        amounts["UNI"] = 80000; // 80,000 UNI
        amounts["ALCX"] = 4000; // 4,000 ALCX
        amounts["BAL"] = 300000; // 300,000 BAL
        amounts["YFI"] = 3; // 3 YFI
        amounts["USDT"] = 2000000; // 2,000,000 USDT
        amounts["COW"] = 900000; // 900,000 COW

        whaleAddresses["GUSD"] = 0x5f65f7b609678448494De4C87521CdF6cEf1e932;
        // whaleAddresses["USDT"] = 0xa929022c9107643515f5c777ce9a910f0d1e490c;
        // whaleAddresses["WETH"] = 0x030ba81f1c18d280636f32af80b9aad02cf0854e;
        // whaleAddresses["WBTC"] = 0xccf4429db6322d5c611ee964527d42e5d685dd6a;
        whaleAddresses["DAI"] = 0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643;
        whaleAddresses["USDC"] = 0x0A59649758aa4d66E25f08Dd01271e891fe52199;
        whaleAddresses["LINK"] = 0x98C63b7B319dFBDF3d811530F2ab9DfE4983Af9D;
        whaleAddresses["GNO"] = 0x4f8AD938eBA0CD19155a835f617317a6E788c868;
        whaleAddresses["TOKE"] = 0x96F98Ed74639689C3A11daf38ef86E59F43417D3;
        whaleAddresses["AAVE"] = 0x4da27a545c0c5B758a6BA100e3a049001de870f5;
        whaleAddresses["BAT"] = 0x6C8c6b02E7b2BE14d4fA6022Dfd6d75921D90E4E;
        whaleAddresses["UNI"] = 0x1a9C8182C09F50C8318d769245beA52c32BE35BC;
        whaleAddresses["ALCX"] = 0x000000000000000000000000000000000000dEaD;
        whaleAddresses["BAL"] = 0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f;
        whaleAddresses["YFI"] = 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52;
        // whaleAddresses["COW"] = 0xca771eda0c70aa7d053ab1b25004559b918fe662;

        priceCheckers["TOKE"] = sushiswapPriceChecker;
        priceCheckers["USDC"] = curvePriceChecker;
        priceCheckers["GUSD"] = curvePriceChecker;
        priceCheckers["AAVE"] = chainlinkPriceChecker;
        priceCheckers["BAT"] = chainlinkPriceChecker;
        priceCheckers["YFI"] = chainlinkPriceChecker;
        priceCheckers["USDT"] = chainlinkPriceChecker;
        priceCheckers["UNI"] = univ3PriceChecker;
        priceCheckers["BAL"] = ssbBalWethPriceChecker;
        priceCheckers["WETH"] = ssbBalWethPriceChecker;
        // priceCheckers["COW"] = fixedMinOut;
        // priceCheckers["ALCX"] = validFrom;

        // tokensToSell = ["TOKE", "USDC", "GUSD", "AAVE", "BAT", "WETH", "UNI", "ALCX", "BAL", "YFI", "USDT", "COW"];
        tokensToSell = ["TOKE"];
    }

    function testRequestSwapExactTokensForTokens() public {
        for (uint8 i = 0; i < tokensToSell.length; i++) {
            {
                string memory tokenToSell = tokensToSell[i];
                string memory tokenToBuy = sellToBuyMap[tokenToSell];
                fromToken = IERC20(tokenAddress[tokenToSell]);
                toToken = IERC20(tokenAddress[tokenToBuy]);
                uint8 decimals = IERC20Metadata(address(fromToken)).decimals();
                amountIn = amounts[tokenToSell] * (10 ** decimals);
                whale = whaleAddresses[tokenToSell];
                priceChecker = priceCheckers[tokenToSell];
            }

            vm.prank(whale);
            fromToken.approve(address(milkman), amountIn);

            vm.recordLogs();

            vm.prank(whale);
            milkman.requestSwapExactTokensForTokens(
                amountIn,
                fromToken,
                toToken,
                address(this), // Receiver address
                priceChecker,
                "" // priceCheckerData
            );

            Vm.Log[] memory entries = vm.getRecordedLogs();

            assertEq(entries[3].topics[0], SWAP_REQUESTED_EVENT);

            (address orderContract,,,,,,,) =
                (abi.decode(entries[3].data, (address, address, uint256, address, address, address, address, bytes)));

            assertEq(fromToken.balanceOf(orderContract), amountIn);

            {
                bytes32 expectedSwapHash =
                    keccak256(abi.encode(whale, address(this), fromToken, toToken, amountIn, priceChecker, bytes("")));
                assertEq(Milkman(orderContract).swapHash(), expectedSwapHash);
            }

            uint256 buyAmount = 0;
            uint256 feeAmount = 0;
            {
                string[] memory headers = new string[](1);
                headers[0] = "Content-Type: application/json";

                (uint256 status, bytes memory data) = "https://api.cow.fi/mainnet/api/v1/quote".post(
                    headers,
                    string(
                        abi.encodePacked(
                            '{"sellToken": "',
                            vm.toString(address(fromToken)),
                            '", "buyToken": "',
                            vm.toString(address(toToken)),
                            '", "from": "',
                            vm.toString(whale),
                            '", "kind": "sell", "sellAmountBeforeFee": "',
                            vm.toString(amountIn),
                            '", "priceQuality": "fast", "signingScheme": "eip1271", "verificationGasLimit": 30000',
                            "}"
                        )
                    )
                );

                assertEq(status, 200);

                string memory json = string(data);

                buyAmount = parseUint(json, ".quote.buyAmount");
                feeAmount = parseUint(json, ".quote.feeAmount");
            }

            uint256 amountToSell = amountIn - feeAmount;
            assertLt(amountToSell, amountIn);

            assertTrue(
                IPriceChecker(priceChecker).checkPrice(
                    amountToSell, 
                    address(fromToken), 
                    address(toToken), 
                    feeAmount, 
                    buyAmount, 
                    bytes("")
                )
            );

            uint32 validTo = uint32(block.timestamp) + 60 * 60 * 24;

            GPv2Order.Data memory order = GPv2Order.Data({
                sellToken: CoWIERC20(address(fromToken)),
                buyToken: CoWIERC20(address(toToken)),
                receiver: address(this),
                sellAmount: amountToSell,
                feeAmount: feeAmount,
                buyAmount: buyAmount,
                partiallyFillable: false,
                kind: GPv2Order.KIND_SELL,
                sellTokenBalance: GPv2Order.BALANCE_ERC20,
                buyTokenBalance: GPv2Order.BALANCE_ERC20,
                validTo: validTo,
                appData: APP_DATA
            });

            bytes memory signatureEncodedOrder = abi.encode(order, whale, priceChecker, bytes(""));

            bytes32 orderDigest = order.hash(milkman.DOMAIN_SEPARATOR());

            {
                uint256 gasBefore = gasleft();
                bytes4 isValidSignature = Milkman(orderContract).isValidSignature(orderDigest, signatureEncodedOrder);
                uint256 gasAfter = gasleft();

                uint256 gasConsumed = gasBefore.sub(gasAfter);

                console.log("gas consumed:", gasConsumed);

                assertLt(gasConsumed, 1_000_000);

                assertEq(isValidSignature, MAGIC_VALUE);
            }
        }
    }

    // Additional test cases for different scenarios and edge cases
}
