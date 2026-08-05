# Francess Logistics Hub — Backend

Django + Django REST Framework API **and** the dashboard front-end itself
(`core/templates/core/dashboard.html`), served together from one Django
project. You open `http://127.0.0.1:8000/` and get the actual dashboard —
Django hands it the HTML template, and from then on the page talks to the
API (`/api/...`) for everything: loading data, saving a new invoice, marking
something paid, deleting, etc.

The database ships **empty**. No demo/inline records are seeded, so on a
fresh install every KPI, chart, and the notification bell reads **0** until
real data is entered — either through the dashboard itself, the API
directly, or the Django admin.

---

## 1. How the pieces fit together

```
Browser  ──────►  http://127.0.0.1:8000/
                        │
                        ▼
              core/views.py → dashboard_view()
                        │  renders
                        ▼
      core/templates/core/dashboard.html   (the whole front-end: HTML, CSS, JS)
                        │
                        │  once loaded, the page's own JavaScript calls...
                        ▼
              http://127.0.0.1:8000/api/...
                        │
                        ▼
           Django REST Framework  →  SQLite (db.sqlite3)
```

This is different from the very first drafts of `dashboard.html` you saw,
which kept everything in plain JavaScript arrays (`billingRecords`,
`crmClients`, etc.) with nothing saved anywhere. Those arrays still exist in
the code, but now they're just an **empty cache** that gets filled from the
API on page load (see `loadFromBackend()` near the top of the `<script>`
block). If the API can't be reached, the page falls back to running with
whatever's in that empty cache and shows a toast telling you it couldn't
reach the backend — the UI won't crash, it'll just be empty until the
server's running.

Practically, this means:
- **Reads** (opening the Agents page, viewing charts, etc.) pull from the database every time you load the page.
- **Writes** (New Invoice, New Agent, marking paid, deleting, restoring) call the API immediately. If that call fails, the change still happens in the page's local cache so the UI doesn't feel broken, but it won't be there next time you reload — so keep an eye out for the "couldn't reach the backend" toast.

---

## 2. What's in here

| App             | Responsible for |
|------------------|------------------|
| `core`           | Serves the dashboard HTML at `/`; global app settings (singleton: notification toggles, email provider) |
| `accounts`       | Login/logout and the signed-in user's profile (position, avatar) — see §5 |
| `billing`        | Payables & receivables ledger (`BillingRecord`) — powers Billing, Dashboard, and Reports |
| `crm`            | Agents/vendors directory (`Agent` + `Contact`) — powers the Agents tab |
| `notifications`  | Notification bell items |
| `trash`          | Soft-delete bin — deleted billing records & agents land here for 30 days before permanent purge |
| `dashboard`      | Read-only aggregation endpoints: KPI cards, charts, revenue analytics, BI reports — all computed live from `billing` |

Deleting a billing record or agent does **not** hard-delete it — it's
snapshotted into `trash` (soft delete), matching the dashboard's recoverable
Trash tab. It can be restored or permanently purged from there, and
anything left for 30+ days is purged automatically the next time the Trash
list is loaded (or via the management command in §6).

---

## 3. Setup (Windows)

```bat
:: 1. Create & activate a virtual environment
python -m venv venv
venv\Scripts\activate

:: 2. Install dependencies
pip install -r requirements.txt

:: 3. Apply migrations (creates an empty SQLite DB — db.sqlite3)
python manage.py migrate

:: 4. Create your first login (see section 5 for why this is needed)
python manage.py createsuperuser

:: 5. Run the dev server
python manage.py runserver
```

Then open **`http://127.0.0.1:8000/`** — that's the dashboard itself. Sign
in with the username/password from step 4. The Django admin is at
`http://127.0.0.1:8000/admin/` (same login works there too), and the raw
API lives under `http://127.0.0.1:8000/api/`.

If you ever close the terminal, you just need `venv\Scripts\activate` again
followed by `python manage.py runserver` — you don't need to repeat steps
2-4 unless you delete `venv/` or `db.sqlite3`.

### Production notes (for later, once this is ready to actually deploy)
- Swap `SECRET_KEY`, `DEBUG=False`, and `ALLOWED_HOSTS` via environment
  variables (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`).
- SQLite is used for zero-setup convenience — swap `DATABASES` in
  `francess_backend/settings.py` for Postgres/MySQL in production.
- Lock `CORS_ALLOW_ALL_ORIGINS` down to your real front-end origin
  (`DJANGO_CORS_ALLOW_ALL=False` + add `CORS_ALLOWED_ORIGINS`).
- Schedule `python manage.py purge_trash` daily (cron / Windows Task
  Scheduler) so expired trash clears even if nobody opens the Trash tab.
- This is also the point where you'd pick a host (Render, Railway,
  PythonAnywhere, etc.) and get a real reachable URL — see the earlier
  conversation about domains if you want a recap of that.

---

## 4. API reference

All endpoints are prefixed with `/api/`. List endpoints are paginated
(`?page=`) and support `?search=` and `?ordering=` where noted.

### Core
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health/` | Health check |
| GET, PATCH | `/api/settings/` | Global settings singleton |

### Accounts (`/api/accounts/`) — see §5 for the full picture
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/accounts/ping/` | No-auth reachability check — the front-end calls this on load |
| POST | `/api/accounts/login/` | Body `{"username", "password"}` → `{"token", "name", "position", "photo"}` |
| POST | `/api/accounts/logout/` | Invalidates the current token (needs `Authorization: Token ...`) |
| POST | `/api/accounts/register/` | Creates a new login — not exposed on the sign-in screen, see §5 |
| GET, PATCH | `/api/accounts/me/` | Read/update the signed-in user's `position` and `photo` |

### Billing (`/api/billing/`)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/billing/` | List records. Filter: `?category=payable\|receivable`, `?status=paid\|outstanding\|overdue`, `?currency=PHP\|USD`. Search: `?search=`. |
| POST | `/api/billing/` | Create a record. `amount`, `due_date`, and `status` are computed server-side (see below) |
| GET/PATCH/PUT | `/api/billing/{id}/` | Retrieve / update a record |
| DELETE | `/api/billing/{id}/` | Soft-delete → moves to Trash |
| POST | `/api/billing/batch-delete/` | Body `{"ids": [1,2,3]}` — soft-delete many at once |
| POST | `/api/billing/{id}/mark-paid/` | Shortcut to flip status to `paid` |

A few fields worth knowing about on `BillingRecord`:
- **`credit_line`** (integer, days) + **`invoice_date`** together produce **`due_date`** automatically on save — nobody types a due date by hand, same as how the real invoicing workflow works. `due_date` is read-only from the API's point of view; send `credit_line` instead.
- **`shipment_scope`** is one of `local` / `import` / `export` / `international`, matching the four options on the New Invoice form (Local = city→city within PH, Import = country→city, Export = city→country, International = country→country).
- **`amount`** is always `si_amount − less_2307 + soa_amount`, and international (USD) records skip SI/LESS 2307 entirely (no VAT applies) — this is enforced in `recompute_amount()`, not just in the UI.

### CRM (`/api/crm/`)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/crm/` | List agents. Filter: `?industry=Local Agent\|International Agent`. Search: `?search=`. |
| POST | `/api/crm/` | Create an agent, with nested `contacts: [...]` |
| GET/PATCH/PUT | `/api/crm/{slug}/` | Retrieve / update (lookup by slug, e.g. `linkasia`) |
| DELETE | `/api/crm/{slug}/` | Soft-delete → moves to Trash |
| GET | `/api/crm/industries/` | Distinct industry values in use |

The dashboard's "type an agent name in New Invoice and click it" autocomplete
and the automatic PHP→USD currency switch both just read this list
client-side — there's no separate endpoint for it.

### Notifications (`/api/notifications/`)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/notifications/` | List notifications (newest first) |
| POST | `/api/notifications/` | Create a notification |
| GET | `/api/notifications/unread_count/` | `{"unread": N}` — for the bell badge |
| POST | `/api/notifications/mark-all-read/` | Mark everything read |
| POST | `/api/notifications/{id}/mark-read/` | Mark one read (the front-end also greys it out visually) |
| DELETE | `/api/notifications/clear-all/` | Wipe all notifications |

### Trash (`/api/trash/`)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/trash/` | List soft-deleted items (auto-purges anything past 30 days first) |
| POST | `/api/trash/{trash_id}/restore/` | Restore one item back to its original app |
| POST | `/api/trash/restore_batch/` | Body `{"trash_ids": [...]}` |
| POST | `/api/trash/delete_batch/` | Body `{"trash_ids": [...]}` — permanent delete |
| DELETE | `/api/trash/{trash_id}/` | Permanent delete of a single item |

### Dashboard aggregation (`/api/dashboard/`) — all read-only, live-computed
| Endpoint | Mirrors this front-end widget |
|---|---|
| `GET /api/dashboard/kpis/` | The 3 top KPI cards (outstanding payables/receivables, overdue) |
| `GET /api/dashboard/charts/bar/` | "Payables vs receivables" bar chart (last 6 months) |
| `GET /api/dashboard/charts/line/` | "Annual revenue" line chart (current year, ₱ only) |
| `GET /api/dashboard/charts/pie/` | "Invoice status" pie chart (this month, ₱ only) |
| `GET /api/dashboard/revenue-analytics/` | Revenue analytics panel (YTD, this month, avg, top client) |
| `GET /api/dashboard/this-month/` | "This month" summary card |
| `GET /api/dashboard/reports/volume/` | Reports page: monthly volume |
| `GET /api/dashboard/reports/revenue/` | Reports page: annual revenue |
| `GET /api/dashboard/reports/ontime/` | Reports page: payment timeliness (all-time status split) |
| `GET /api/dashboard/reports/vendor/` | Reports page: top 8 vendors by ₱ spend |

With an empty database, every one of these returns zeroed-out counts, empty
chart series, and `null` for things like "top client" — a fresh system
renders all KPIs/graphs/notifications at 0, on purpose.

**Note:** as of this update, the dashboard's charts (bar/line/pie on the
Dashboard page, and the 4 cards on the Reports page) are still computed
**client-side** in JavaScript from whatever's in the page's local
`billingRecords` cache, not from these `/api/dashboard/...` endpoints yet.
The endpoints exist and work (tested), but wiring the front-end charts to
call them instead of computing locally is the next integration step —
right now both approaches would give the same numbers since the cache is
loaded straight from `/api/billing/`, but the aggregation endpoints are the
more correct long-term source once there's enough data that computing
everything client-side gets slow.

---

## 5. Accounts & logging in

There's no public "create account" page — intentionally. Whoever manages
the system creates a login for each employee, one of two ways:

**Option A — Django admin (easiest for now)**
Go to `http://127.0.0.1:8000/admin/`, sign in with your superuser, add a
new **User** under "Authentication and Authorization", set a username and
password, save. A matching `Profile` (position/photo) gets created
automatically the first time that person logs into the dashboard.

**Option B — the API**
```
POST /api/accounts/register/
{ "username": "jane", "password": "at-least-6-chars", "name": "Jane Reyes", "position": "Billing Clerk" }
```

Once an account exists, that person opens `http://127.0.0.1:8000/` and
signs in with username + password on the dashboard's login screen. What
happens next:
1. The dashboard checks `/api/accounts/ping/` to see if the backend is even reachable.
2. On submit, it calls `/api/accounts/login/`. Success → it gets a token back, stores it, and shows the dashboard.
3. If the backend genuinely can't be reached at all (server not running), it falls back to a **local-only** session so you're not locked out of a demo — but it says so clearly ("Backend not reachable — signed in locally only") rather than pretending it's real.
4. Clicking the profile block (bottom-left) → **Edit profile** lets you set your display name, position, and a photo — these are separate from the username/password and just control how you appear in the sidebar. **Log out** clears the session and invalidates the token server-side.

---

## 6. Useful management commands

```bat
python manage.py purge_trash        :: permanently delete expired trash rows
python manage.py createsuperuser    :: admin + dashboard login in one step
python manage.py migrate            :: apply/reset schema
python manage.py changepassword <username>   :: reset someone's password
```

---

## 7. Where things live, if you're exploring the code

```
francess_backend/
├── francess_backend/       # project settings + root urls.py
├── core/                   # serves dashboard.html, health check, global settings
│   └── templates/core/dashboard.html   ← the entire front-end lives here
├── accounts/                # login/logout, user profiles
├── billing/                 # payables & receivables
├── crm/                     # agents/vendors + their contacts
├── notifications/           # bell items
├── trash/                   # soft-delete bin
├── dashboard/                # aggregation/reporting endpoints
├── requirements.txt
├── manage.py
└── db.sqlite3               # created after your first `migrate`
```

Every app follows the same shape: `models.py` (the table), `serializers.py`
(how it's turned into/from JSON), `views.py` (the actual endpoints,
usually a DRF `ViewSet`), `urls.py` (routes), `admin.py` (Django admin
registration). If you want to add a field to something, that's the order
to touch files in: model → migration (`makemigrations`) → serializer →
(usually nothing needed in views.py) → front-end.
