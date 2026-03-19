# Rest API MonCash — Documentation

> © 2019 Digicel. All Rights Reserved.

---

## Table des matières

- [Introduction](#introduction)
- [REST API Host](#rest-api-host)
- [MonCash Gateway Base URL](#moncash-gateway-base-url)
- [Authentication](#authentication)
- [Create Payment](#create-payment)
- [Payment Details](#payment-details)
  - [Capture by Transaction ID](#capture-payment-by-transaction-id)
  - [Capture by Order ID](#capture-payment-by-order-id)
- [Check Customer Status](#check-customer-status)
- [Prefunded / Payout](#prefundedpayout)
- [Check Prefunded Transaction Status](#check-prefunded-transaction-status)
- [Balance Prefunded](#balance-prefunded)

---

## Introduction

Use the MonCash REST API to easily and securely accept payments on your website or mobile app.

---

## REST API Host

| Environnement | Host |
|---|---|
| **Live** | `moncashbutton.digicelgroup.com/Api` |
| **Sandbox** | `sandbox.moncashbutton.digicelgroup.com/Api` |

---

## MonCash Gateway Base URL

| Environnement | Gateway Base URL |
|---|---|
| **Live** | `https://moncashbutton.digicelgroup.com/Moncash-middleware` |
| **Sandbox** | `https://sandbox.moncashbutton.digicelgroup.com/Moncash-middleware` |

---

## Authentication

To call the resources of the MonCash REST API, you must authenticate by including the bearer token in the `Authorization` header using the Bearer authentication scheme.

The value should be:
- `Bearer <Access-Token>`, or
- `Basic <client_id>:<secret>`

The `client_id` and `client_secret` can be generated from the business portal.

### Sample Authentication Basic

**`POST /oauth/token`**

**Request**
```bash
curl -X POST https://client_id:client_secret@HOST_REST_API/oauth/token \
  -H "Accept: application/json" \
  -d "scope=read,write&grant_type=client_credentials"
```

**Response**
```json
{
  "access_token": "<Access-token>",
  "token_type": "bearer",
  "expires_in": 59,
  "scope": "read,write",
  "jti": "the jti"
}
```

---

## Create Payment

To create a payment, you must send the `orderId` and `amount` as an HTTP POST request, including an Authorization Bearer Token in the header. The response will contain the parameters `success` and a redirect URL to load the Payment Gateway of MonCash Middleware.

The redirect URL to load the Payment Gateway will be:
```
GATEWAY_BASE/Payment/Redirect?token=<payment-token>
```

### Sample Create Payment

**`POST /v1/CreatePayment`**

**Request**
```bash
curl -X POST https://HOST_REST_API/v1/CreatePayment \
  -H 'accept: application/json' \
  -H 'authorization: Bearer <Access-token>' \
  -H 'content-type: application/json' \
  -d '{"amount": <amount>, "orderId": <orderId>}'
```

**Response**
```json
{
  "path": "/v1/CreatePayment",
  "payment_token": {
    "expired": "2019-05-24 12:46:55:107",
    "created": "2019-05-24 12:36:55:107",
    "token": "<payment-token>"
  },
  "timestamp": 1558715815122,
  "status": 202,
  "mode": "<sandbox or live>"
}
```

---

## Payment Details

To retrieve payment details from the return URL business script, you must send the `transactionId` or `orderId` as an HTTP POST request with an Authorization Bearer Token.

### Capture Payment by Transaction ID

**`POST /v1/RetrieveTransactionPayment`**

**Request**
```bash
curl -X POST https://HOST_REST_API/v1/RetrieveTransactionPayment \
  -H 'accept: application/json' \
  -H 'authorization: Bearer <Access-token>' \
  -H 'content-type: application/json' \
  -d '{"transactionId": <transactionId>}'
```

**Response**
```json
{
  "path": "/v1/RetrieveTransactionPayment",
  "payment": {
    "reference": "1559796839",
    "transaction_id": "12874820",
    "cost": 10,
    "message": "successful",
    "payer": "50937007294"
  },
  "timestamp": 1560029360970,
  "status": 200
}
```

---

### Capture Payment by Order ID

**`POST /v1/RetrieveOrderPayment`**

**Request**
```bash
curl -X POST http://HOST_REST_API/v1/RetrieveOrderPayment \
  -H 'accept: application/json' \
  -H 'authorization: Bearer <Access-token>' \
  -H 'content-type: application/json' \
  -d '{"orderId": <orderId>}'
```

**Response**
```json
{
  "path": "/v1/RetrieveOrderPayment",
  "payment": {
    "reference": "1559796839",
    "transaction_id": "12874820",
    "cost": 10,
    "message": "successful",
    "payer": "50937007294"
  },
  "timestamp": 1560029360970,
  "status": 200
}
```

---

## Check Customer Status

To check the customer status, you must send the `account` (the customer's account) as an HTTP POST request, including an Authorization Bearer Token.

### Sample Request for Check Customer Status

**`POST /v1/CustomerStatus`**

**Request**
```bash
curl -X POST https://HOST_REST_API/v1/CustomerStatus \
  -H 'accept: application/json' \
  -H 'authorization: Bearer <Access-token>' \
  -H 'content-type: application/json' \
  -d '{"account": <account of customer>}'
```

**Response**
```json
{
  "path": "/v1/CustomerStatus",
  "customerStatus": {
    "type": "fullkyc",
    "status": ["registered", "active"]
  },
  "timestamp": 1558715815122,
  "status": 200,
  "mode": "<sandbox or live>"
}
```

---

## Prefunded/Payout

To pay the customer, you must send the `receiver` (the customer's account), `amount`, `desc`, and `reference` (a unique value that represents your transaction) in an HTTP POST request, including an Authorization Bearer Token.

### Sample Payout Request

**`POST /v1/Transfert`**

**Request**
```bash
curl -X POST https://HOST_REST_API/v1/Transfert \
  -H 'accept: application/json' \
  -H 'authorization: Bearer <Access-token>' \
  -H 'content-type: application/json' \
  -d '{
    "amount": <amount>,
    "receiver": <Receive Account>,
    "desc": <Some description>,
    "reference": <Id that represents your transaction>
  }'
```

**Response**
```json
{
  "path": "/Api/v1/Transfert",
  "transfer": {
    "transaction_id": "Transaction id",
    "amount": 100.0,
    "receiver": "Receiver account",
    "message": "successful",
    "desc": "Test Api Transfer"
  },
  "timestamp": 1589927614388,
  "status": 200
}
```

---

## Check Prefunded Transaction Status

To check the status of a prefunded transaction, you must send the `reference` (a unique value that represents your transaction) as an HTTP POST request, including an Authorization Bearer Token.

### Sample Request for Prefunded Transaction Status

**`POST /v1/PrefundedTransactionStatus`**

**Request**
```bash
curl -X POST https://HOST_REST_API/v1/PrefundedTransactionStatus \
  -H 'accept: application/json' \
  -H 'authorization: Bearer <Access-token>' \
  -H 'content-type: application/json' \
  -d '{"reference": <Id that represents your transaction>}'
```

**Response — Succès**
```json
{
  "path": "/Api/v1/PrefundedTransactionStatus",
  "transStatus": "successful",
  "timestamp": 1732154100298,
  "status": 200
}
```

**Response — Transaction introuvable**
```json
{
  "path": "/Api/v1/PrefundedTransactionStatus",
  "error": "Not Found",
  "message": "Can't find this transaction",
  "timestamp": 1732131728381,
  "status": 404
}
```

**Response — Solde maximum atteint**
```json
{
  "path": "/Api/v1/Transfert",
  "error": "Forbidden",
  "message": "Maximum Account Balance",
  "timestamp": 1732154199606,
  "status": 403
}
```

---

## Balance Prefunded

To check the balance, you must send an HTTP GET request with an Authorization Bearer Token.

### Sample Request for Balance (Prefunded)

**`GET /v1/PrefundedBalance`**

**Request**
```bash
curl -X GET https://HOST_REST_API/v1/PrefundedBalance \
  -H 'accept: application/json' \
  -H 'authorization: Bearer <Access-token>'
```

**Response**
```json
{
  "path": "/Api/v1/PrefundedBalance",
  "balance": {
    "balance": 29814021.179999999701976776123046875,
    "message": "successful"
  },
  "timestamp": 1732205962423,
  "status": 200
}
```

---

> © 2019 Digicel. All Rights Reserved.
