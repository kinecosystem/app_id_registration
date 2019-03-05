# app_id_registration

To register an app to kin ecosystem, example request:
```curl -X POST \
  'http://app-registration.developers.kinecosystem.com/register?email=EMAIL_ADDRESS&name=NAME&app_name=APP_NAME&public_wallet=PUBLIC_WALLET_ADDRESS' \
  -H 'x-api-key: yc7lzFjnjOadnDtLjf3848SaBW62PG&QAJtHvpbZtDZSnT'```
  
  Request params:
  EMAIL_ADDRESS = contact's email address, needs validation, must be unique
  NAME = contact's name
  APP_NAME = application's name 
  PUBLIC_WALLET_ADDRESS = a kin's valid wallet address (optional)
  
  Expected response:
  XXXX => 4 uppercase or lowercase and numbers
  
  'bad request' => One of the required field is missing or in incorrect format.
  
  '<title>401 Unauthorized</title>' => The API-key is invalid.
