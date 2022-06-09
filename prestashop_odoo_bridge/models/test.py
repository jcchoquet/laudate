url = "https://www.laudate.fr/api"
key = "MD2HJUGLBFK5R6CV4P2HK9VXWDLS1VRP"

import json
from prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError

prestashop = PrestaShopWebServiceDict(url, key, debug=1)
print("================= Product Data ==========")
print(prestashop.get("products", 1238))

print("================= Combination Data ========")
print(prestashop.get("combinations", 7465))