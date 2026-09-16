# Craigslist post (browser) + login hook + Gmail acceptance

**Surface:** craigslist.com (public classifieds). **Not** Clawslist/clawslist.net. **Not** create/post via [pp-craigslist](sand-workflow:pp-craigslist) — that CLI is **read-only**; use it only to verify a listing is live after post.

**Sources:** this skill + live craigslist.com UI. Do not invent a successful post, post URL, or Gmail message.

## Inputs (required before posting)

From the user (or HI-LLC handoff), collect:

- `site` (e.g. `sfbay`)
- `category` path for for-sale (e.g. general for sale / auto parts — match UI)
- `title`, `price`, `description`, `location` / neighborhood / zip as the form asks
- `photos[]` — absolute paths on a registered PC or box paths already scrubbed of EXIF/GPS
- `contact email` for the listing (must be the Gmail the connector can read for acceptance)

Never put passwords, OTP codes, or API secrets in this skill or in chat.

## Flow

### 1) Prep photos

If photos may contain GPS/EXIF: strip **all** metadata (esp. GPS) before upload; verify `exiftool -GPS:all` is empty. Prefer scrubbed copies.

### 2) Open create flow (browser)

Delegate to a box `computerUse` / browser subagent. Prefer a direct create URL when known for the site (e.g. sfbay post entry). Goal: reach the Craigslist “create posting” / account gate with a fresh snapshot.

### 3) Login hook (human)

When Craigslist requires human login (password, OTP, captcha, account chooser):

1. Take a **fresh snapshot** of the login page.
2. Follow [in-chat-forms](sand-workflow:in-chat-forms): prefer `request_user_form` when fields are fillable targets; otherwise `request_box_help`.
3. **Stop** automation until the handback/resume. Do not guess credentials. Do not paste secrets into chat.
4. After resume: fresh snapshot → continue only if logged in. If still blocked, hand off again (do not loop doomed forms).

Record for the report: `login_hook` = `form` | `box_help` | `already_logged_in` | `not_reached`.

### 4) Create the listing

Fill title, price, body, location, upload photos from the prepared paths, submit through Craigslist’s own UI.

Stop for any payment, phone verify, or captcha the form cannot express → `request_box_help`.

Capture: confirmation page text, and any **post URL** / posting ID shown. If none, say so — do not invent.

### 5) Optional live verify (read-only)

If useful and rate limits allow:

```bash
craigslist-pp-cli search '<distinctive title words>' --site <site> --category <cat> --agent
```

or open the post URL in the browser. Treat HTTP 429 as inconclusive, not FAIL by itself.

### 6) Acceptance — Gmail confirmation email

Using the **user-Gmail** connector (`search_threads` / `get_message`):

- Query recent mail from Craigslist about this post, e.g. `from:craigslist.org newer_than:1d` plus distinctive title words or posting id.
- **PASS** only if a real message is found whose **from/subject** is Craigslist and content matches this post (title or posting id).
- Record `gmail_message_id` and `subject`. If no matching email: **FAIL** / **BLOCKED** (waiting), never invent an id.

### 7) Report (HI-LLC or requesting room)

Short PASS/FAIL with:

- `login_hook` behavior
- `post_url` if any (else none)
- `gmail_message_id` + `subject` if PASS
- blockers if any

## Acceptance: PASS criteria

All required:

1. Login hook used correctly when login appeared (or `already_logged_in` documented).
2. A real post URL or posting-id from Craigslist UI (or explicit FAIL if post did not complete).
3. Matching Craigslist confirmation email found via Gmail connector with real message id + subject.

Also run [Workflow acceptance test](sand-workflow:workflow-acceptance-test) when signing off this skill itself (screenshot + checklist).

## Out of scope

- Clawslist / clawslist.net
- Mutating posts via craigslist-pp-cli
- Inventing PASS evidence
