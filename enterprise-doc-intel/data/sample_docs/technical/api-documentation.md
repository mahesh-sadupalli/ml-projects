# Payment Processing API Documentation

## Overview
The Payment Processing API enables merchants to process transactions, manage refunds, and retrieve payment status. Built on a RESTful architecture with JSON payloads.

## Base URL
```
Production: https://api.company.com/v2
Staging: https://api-staging.company.com/v2
```

## Authentication
All requests require an API key passed in the `Authorization` header:
```
Authorization: Bearer <api_key>
```
API keys are generated in the Merchant Dashboard. Production and staging environments use separate keys.

## Rate Limits
- Standard tier: 100 requests/minute
- Premium tier: 1,000 requests/minute
- Enterprise tier: 10,000 requests/minute
- Rate limit headers: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Endpoints

### POST /payments
Create a new payment transaction.

Request body:
- `amount` (integer, required): Amount in cents (e.g., 1000 = €10.00)
- `currency` (string, required): ISO 4217 currency code (EUR, USD, GBP)
- `merchant_id` (string, required): Your merchant identifier
- `customer_email` (string, optional): Customer email for receipt
- `metadata` (object, optional): Custom key-value pairs

Response: Returns a payment object with `id`, `status`, and `created_at`.

### GET /payments/{id}
Retrieve payment details by ID.

### POST /payments/{id}/refund
Issue a full or partial refund.

Request body:
- `amount` (integer, optional): Partial refund amount in cents. Omit for full refund.
- `reason` (string, required): One of `duplicate`, `fraudulent`, `customer_request`

### GET /payments
List payments with filtering.

Query parameters:
- `status`: Filter by status (pending, completed, failed, refunded)
- `from_date` / `to_date`: Date range (ISO 8601)
- `limit`: Results per page (default: 20, max: 100)
- `cursor`: Pagination cursor

## Webhooks
Configure webhooks in the Merchant Dashboard to receive real-time event notifications:
- `payment.completed`
- `payment.failed`
- `refund.completed`

Webhook payloads are signed with HMAC-SHA256. Verify signatures using your webhook secret.

## Error Codes
- `400`: Invalid request parameters
- `401`: Authentication failed
- `404`: Resource not found
- `429`: Rate limit exceeded
- `500`: Internal server error

## SDKs
Official SDKs available for Python, Node.js, Java, and Go. Install via pip/npm/maven/go-get.

## Support
API support: api-support@company.com
Status page: https://status.company.com
