# app_id_registration

Register
-
Returns the new app id:
```
POST '{ "email":"contact's email address",
         "name":"contact's name",
         "app_name": "application's name",
         "public_wallet": "a kin's valid wallet address (optional)" }' SERVICE_URL/register
```

Response:
- The expected response is a 4 letters of letters and numbers:
```
{ XXXX }
```

Update
-
Update the application's data, it is required to provide the current app_id and either email or public_wallet in the API:
```
PATCH '{"app_id": "required current app_id",
        "email": "required current email address",
        ...  (list of the fields to update)}' SERVICE_URL/update
```
Or
```
PATCH '{"app_id": "required current app_id",
        "public_wallet": "required current public wallet address",
        ...  (list of the fields to update)}' SERVICE_URL/update
```
Response:
- The expected response is a 4 letters of letters and numbers:
```
{ XXXX }
```

Get Application's Data:
-
Retrieve the application's data, it is required to provide the current app_id and either email or public_wallet in the API:
```
PATCH '{"app_id": "required current app_id",
        "email": "required current email address"}' SERVICE_URL/get_app
```
Or
```
PATCH '{"app_id": "required current app_id",
        "public_wallet": "required current public wallet address"}' SERVICE_URL/get_app
```
Response:
- The expected response is a 4 letters of letters and numbers:
```
{ "app_id": "current app_id",
  "app_name": "current application's name",
  "email": "curent email",
  "name": "current name",
  "public_wallet": "current public address"}
```

Remove
-
Delete all the application's data, it is required to provide the current app_id and either email or public_wallet in the API:
```
Delete '{"app_id": "required current app_id",
        "email": "required current email address"}' SERVICE_URL/remove
```
Or
```
PATCH '{"app_id": "required current app_id",
        "public_wallet": "required current public wallet address"}' SERVICE_URL/remove
```
Response:
```
{ OK }
```

---
Unexpected payload for all cases can result in the following errors:
- One of the required field is missing or in incorrect format:
```
{ bad request }
```
- The API-key is invalid:
```
{ unauthorized }
```

