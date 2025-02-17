from yoomoney import Authorize

Authorize(
      client_id="Клиент айди, который вы получаете на https://yoomoney.ru/myservices/new",
      redirect_uri="Редирект, который вы ввели на сайте выше =)",
      client_secret="Клиент секрет. Желательно указать на сайте выше =)",
      scope=["account-info",
             "operation-history",
             "operation-details",
             "incoming-transfers",
             "payment-p2p",
             "payment-shop",
             ]
      )