def test_submit_sell(cow_anywhere, user, gno, dai):
    cow_anywhere.submitMarketSell(gno, dai, 100e18)