# ChatServer API documentation

This document describes the HTTP routes currently mounted by `chatserver/urls.py`.

## Conventions

- Base URL: replace `<base-url>` with the host running this Django project.
- Protected endpoints require `Authorization: Bearer <access_token>`.
- Requests use `application/json`, except RAG file uploads and profile avatar uploads, which use `multipart/form-data`.
- UUID placeholders such as `<conversation_id>` and `<message_id>` are UUID strings. User IDs are integers.
- Date/time values returned by the API are ISO 8601 timestamps unless stated otherwise.

## Endpoint summary

| Endpoint | Method | Authentication | Purpose |
|---|---|---:|---|
| `/api/v1/users/register` | POST | No | Register by email and send an OTP |
| `/api/v1/users/verify-otp` | POST | No | Verify registration OTP and obtain JWTs |
| `/api/v1/users/resend-otp` | POST | No | Send a replacement OTP |
| `/api/v1/users/users/search?q=` | GET | No* | Search users by username/email |
| `/api/v1/authentication/auth/login` | POST | No | Log in with email/password and reCAPTCHA |
| `/api/v1/authentication/auth/login/refresh` | POST | No | Refresh an access token |
| `/api/v1/authentication/auth/{provider}` | GET | No | Get a social-login authorization URL |
| `/api/v1/authentication/{provider}/login/callback` | GET | No | OAuth provider callback |
| `/api/v1/contacts/` | GET, POST | Yes | List or create contacts |
| `/api/v1/conversations/` | GET | Yes | List conversations |
| `/api/v1/conversations/create/` | POST | Yes | Create/retrieve a direct conversation |
| `/api/v1/conversations/direct/` | POST | Yes | Alias of conversation creation |
| `/api/v1/conversations/<conversation_id>/messages/` | GET | Yes | List messages |
| `/api/v1/conversations/<conversation_id>/messages/send/` | POST | Yes | Send a message |
| `/api/v1/conversations/<conversation_id>/read/` | POST | Yes | Mark a conversation read |
| `/api/v1/users/search/?q=` | GET | Yes | Search by first/last name |
| `/api/v1/rag/store-vector` | PUT | No | Queue a RAG source for storage |
| `/api/webhook` | POST | No | Receive a webhook payload |

`/api/v1/chat/` exposes the same chat routes as `/api/v1/`. It also exposes legacy duplicate aliases under `/api/v1/api/...` and `/api/v1/chat/api/...`.

\* The account search view does not enforce authentication in its current implementation, although it still accesses `request.user.id`.

## Account and JWT authentication

### Register

`POST /api/v1/users/register`

Payload:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "confirm_password": "StrongPassword123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "whatsapp_number": "+15551234567"
}
```

`email`, `password`, and `confirm_password` are required; first name, last name, and WhatsApp number are optional.

Success response — `201 Created`:

```json
{"message": "Check your email for the OTP."}
```

Validation failure — `400 Bad Request`:

```json
{"message": "Email is already registered."}
```

### Verify OTP

`POST /api/v1/users/verify-otp`

Payload:

```json
{"email": "user@example.com", "otp": "123456"}
```

Success response — `200 OK`:

```json
{
  "message": "OTP verified successfully.",
  "data": {"access_token": "<jwt>", "refresh_token": "<jwt>"}
}
```

Expired or invalid OTP responses use `400 Bad Request` and contain a `message`.

### Resend OTP

`POST /api/v1/users/resend-otp`

Payload:

```json
{"email": "user@example.com"}
```

Success response — `200 OK`:

```json
{"message": "A new OTP has been sent to your email."}
```

Unknown users receive `404 Not Found`; an omitted email receives `400 Bad Request`.

### Email/password login

`POST /api/v1/authentication/auth/login`

Payload:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "recaptcha_token": "<reCAPTCHA-token>"
}
```

Success response — `200 OK`:

```json
{
  "refresh": "<jwt>",
  "access": "<jwt>",
  "user_id": 42,
  "email": "user@example.com"
}
```

Login, reCAPTCHA, and credential failures currently return `400 Bad Request` with a `message`.

### Refresh JWT

`POST /api/v1/authentication/auth/login/refresh`

Payload:

```json
{"refresh": "<jwt>"}
```

Success response — `200 OK`:

```json
{"access": "<new-jwt>", "refresh": "<rotated-jwt>"}
```

The `refresh` field is returned when token rotation is enabled (as it is in the project settings).

### Account user search

`GET /api/v1/users/users/search?q=<query>`

No JSON payload. `q` is an optional query parameter; an empty value returns `[]`.

Success response — `200 OK`:

```json
[
  {"id": 42, "name": "janedoe", "email": "jane@example.com", "avatar": "JA"}
]
```

### Social login

All social routes are unauthenticated. Replace `{provider}` with `google`, `github`, `x`, `facebook`, or `linkedin`.

| Provider | Start endpoint | Start response | Callback endpoint |
|---|---|---|---|
| Google | `GET /api/v1/authentication/auth/google` | `{"url": "<authorization-url>"}` | `GET /api/v1/authentication/google/login/callback?code=<code>` |
| GitHub | `GET /api/v1/authentication/auth/github` | `{"url": "<authorization-url>"}` | `GET /api/v1/authentication/github/login/callback?code=<code>` |
| X | `GET /api/v1/authentication/auth/x` | `{"url": "<authorization-url>"}` | `GET /api/v1/authentication/x/login/callback?code=<code>&state=<state>` |
| Facebook | `GET /api/v1/authentication/auth/facebook` | `{"auth_url": "<authorization-url>"}` | `GET /api/v1/authentication/facebook/login/callback?code=<code>` |
| LinkedIn | `GET /api/v1/authentication/auth/linkedin` | `{"auth_url": "<authorization-url>"}` | `GET /api/v1/authentication/linkedin/login/callback?code=<code>` |

Callbacks exchange the provider code, create or retrieve the user, and redirect to `FRONTEND_URL`. Successful redirects contain JWT query parameters; exact names vary by provider (`access`/`refresh` for Google, GitHub, X, Facebook; `access_token`/`refresh_token` for LinkedIn). Failure redirects contain an `error` parameter.

## Chat APIs

The canonical endpoints below begin with `/api/v1/`. Prefix any one with `/api/v1/chat/` instead to use its equivalent alias.

### Contacts

`GET /api/v1/contacts/?search=<term>`

Payload: none. `search` is optional and matches display name, nickname, first name, last name, or email.

Success response — `200 OK`:

```json
{
  "message": "Contacts fetched successfully.",
  "data": [
    {
      "id": "<uuid>",
      "contact_user": {"id": 42, "first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"},
      "display_name": "Jane Doe",
      "nickname": "Jane",
      "notes": "",
      "favorite": false,
      "archived": false,
      "created_at": "2026-08-19T10:00:00Z",
      "updated_at": "2026-08-19T10:00:00Z"
    }
  ]
}
```

`POST /api/v1/contacts/`

Payload:

```json
{
  "contact_user_id": 42,
  "display_name": "Jane Doe",
  "nickname": "Jane",
  "notes": "Met at work"
}
```

Only `contact_user_id` is required. Success is `201 Created` with `{"message": "Contact created successfully.", "data": <contact>}`. An existing contact returns `200 OK`; invalid input returns `400 Bad Request`; an unknown user returns `404 Not Found`.

### Conversations

`GET /api/v1/conversations/`

Payload: none. Success — `200 OK`:

```json
{"message": "Conversations fetched successfully.", "data": [<conversation>]}
```

`POST /api/v1/conversations/create/` and `POST /api/v1/conversations/direct/`

Payload (either field name is accepted):

```json
{"participant_id": 42}
```

Success is `201 Created` for a new conversation, or `200 OK` when a matching direct conversation already exists:

```json
{"message": "Conversation created successfully.", "data": <conversation>}
```

`<conversation>` contains `id`, `type`, `name`, `image`, `description`, `created_by`, `participants`, `last_message`, `last_message_at`, `unread_count`, `created_at`, and `updated_at`. A participant has `id`, `user`, `role`, `joined_at`, `pinned`, and `muted_until`.

### Messages

`GET /api/v1/conversations/<conversation_id>/messages/?cursor=<ISO-8601>&page_size=<n>`

Payload: none. Both query parameters are optional; the default page size is 40. `cursor` is the `sent_at` timestamp of the oldest message from the previous page.

Success response — `200 OK`:

```json
{
  "message": "Messages fetched successfully.",
  "next_cursor": "2026-08-19T10:00:00+00:00",
  "data": [<message>]
}
```

`POST /api/v1/conversations/<conversation_id>/messages/send/`

Payload:

```json
{
  "content": "Hello!",
  "type": "text",
  "reply_to": null
}
```

`content` is required. `type` defaults to `text`; permitted values are `text`, `image`, `video`, `file`, `audio`, `voice`, `gif`, `location`, `contact`, and `sticker`. `reply_to` is optional.

Success response — `201 Created`:

```json
{"message": "Message sent successfully.", "data": <message>}
```

`<message>` contains `id`, `conversation`, `sender`, `type`, `content`, `reply_to`, `forward_from`, `edited`, `edited_at`, `deleted_for_everyone`, `sent_at`, `sent_at_formatted`, and `attachments`. An attachment contains `id`, `url`, `filename`, `mime_type`, `size`, `width`, `height`, and `duration`.

Both message endpoints return `404 Not Found` when the conversation is absent or the caller is not a participant. Sending with an invalid request returns `400 Bad Request`; an invalid `reply_to` returns `404 Not Found`.

### Mark read

`POST /api/v1/conversations/<conversation_id>/read/`

Payload: an empty JSON object is accepted.

Success response — `200 OK`:

```json
{"message": "Conversation marked as read.", "last_read_message_id": "<uuid>"}
```

When no message from another participant exists, `last_read_message_id` is `null`. A non-participant receives `404 Not Found`.

### User search

`GET /api/v1/users/search/?q=<keyword>`

Payload: none. `q` is required and must not be empty. It searches first and last names, excludes the caller, and returns at most 20 users.

Success response — `200 OK`:

```json
{
  "message": "Users fetched successfully.",
  "data": [{"id": 42, "first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"}]
}
```

## RAG storage

`PUT /api/v1/rag/store-vector`

Send exactly one source field: `text_content`, `file_content`, or `url_content`. `title` and `type` are required. Valid `type` values are `PDF`, `DOCX`, `TXT`, `CSV`, and `URL`.

Text example:

```json
{
  "title": "Product guide",
  "type": "TXT",
  "text_content": "Knowledge to index"
}
```

File upload example (`multipart/form-data`):

```text
title=Product guide
type=PDF
file_content=@guide.pdf
```

Success response — `200 OK`:

```json
{
  "message": "The rag storage is initiated successfully.",
  "data": {"title": "Product guide", "type": "TXT", "status": "PENDING"}
}
```

Validation errors return `400 Bad Request`; internal task/storage errors return `500 Internal Server Error`.

## Webhook

`POST /api/webhook`

Payload: any JSON object. No authentication or mandatory request fields are enforced. The endpoint reads the optional `x-enviroment` request header but returns the same response either way.

Success response — `200 OK`:

```json
{
  "success": true,
  "message": "Webhook received successfully",
  "received_data": {"event": "example"}
}
```

## Not currently mounted

- `ai_models/urls.py` defines `POST /huggingface`, but `ai_models.urls` is not included by the project URL configuration, so no public endpoint exists for it.
- `authentication/register_urls/auth.py` defines an alternative `/auth/...` API set, but it is not included by the project URL configuration, so those routes are not publicly reachable.
