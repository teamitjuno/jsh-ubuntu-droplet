def convertCurrency(currency):
    main_currency, fractional_currency = currency.split(".")[0], currency.split(".")[1]
    new_main_currency = main_currency.replace(",", ".")
    currency = new_main_currency + "," + fractional_currency
    return currency


def printFloat(fl):
    return "%.*f" % (2, fl)
