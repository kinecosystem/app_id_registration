# app_id_registration

To register an app to kin ecosystem, example request:
```curl -X POST \
  'http://app-registration.developers.kinecosystem.com/register?email=EMAIL_ADDRESS&name=NAME&app_name=APP_NAME&public_wallet=PUBLIC_WALLET_ADDRESS' \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: yc7lzFjnjOadnDtLjf3848SaBW62PG&QAJtHvpbZtDZSnT'```
  
  The following params are required for each contact details:
  EMAIL_ADDRESS = contact's email address, needs validation, must be unique
  NAME = contact's name
  APP_NAME = application's name 
  PUBLIC_WALLET_ADDRESS = a kin's valid wallet address, needs validation, must be uniqu