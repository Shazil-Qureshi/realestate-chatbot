# n8n workflow: lead → Google Sheet → email

`bella-lead-workflow.json` is the workflow. Import it into n8n running on
your laptop (`npx n8n`, then <http://localhost:5678>).

```
Receive lead ──▶ Add row to Leads sheet ──▶ Tell backend it is saved ──▶ Email the agent
 (webhook)        (Google Sheets, RAW)       (HTTP 200)                  (Gmail)
```

The order matters:

- **The row is written first.** The backend only hears "saved" after the
  sheet accepted it. If Google Sheets fails, the backend gets an error and
  keeps the lead in `backend/leads/pending.jsonl`, so nothing is lost.
- **The email is sent last.** A failed email never costs you a lead.
- **Values are written RAW**, exactly as received. Google's default mode would
  turn `03001234567` into the number `3001234567`, and would run a name
  beginning with `=` as a formula.

Do the parts below in order. Each ends with a check.

---

## Part 1 · Create the Leads sheet (2 min)

1. Go to <https://sheets.new> **while signed in to your own personal Google
   account**, the one you'll also use in Part 2. Use your personal account,
   not a work one, for the same reason n8n runs on your own laptop.
2. Name the spreadsheet **Bella Real Estate Leads**.
3. Click cell **A1** and paste this line. The gaps are tabs, so it fills
   A1 to H1:

   ```
   lead_id	received_at	name	phone	email	property_ref	message	source
   ```

   The names must match exactly: lower case, with underscores.

**Check:** row 1 shows eight headings, `lead_id` in A1 and `source` in H1.

---

## Part 2 · Let your n8n use your Google account (15–20 min)

Google needs you to register your own n8n as an "app". This creates a
**Client ID** and a **Client Secret**.

> **The Client Secret is a password.** Paste it only into n8n. Never into a
> file in this project, a screenshot or a chat message. If it leaks, delete
> it in Google Cloud and create a new one, exactly as with the Gemini key on
> 16 November.

### 2a. Create a project
1. Open <https://console.cloud.google.com>, signed in to the **same personal
   account** as Part 1.
2. Click the project dropdown at the top, then **New project**. Name it
   `bella-n8n`, then **Create**.
3. Check the dropdown now shows **bella-n8n**. Everything after this happens
   inside it.

### 2b. Switch on three Google APIs
**APIs & Services → Library.** Search for each of these, open it and click
**Enable**:
- **Google Sheets API**
- **Google Drive API** (n8n uses it to list your spreadsheets)
- **Gmail API**

### 2c. Consent screen
1. **APIs & Services → OAuth consent screen → Get started.**
2. App name: `Bella n8n`. User support email: yours. **Next.**
3. Audience: **External.** **Next.**
4. Contact email: yours. **Next**, tick the User Data Policy box,
   **Continue → Create.**
5. Go to **Audience** (or **Test users**) and click **Add users**. Add **your
   own Gmail address**. Without this you'll get "access denied" later.

Leave it in **Testing**. That means only you can sign in, and the connection
expires **every 7 days**. When n8n later says a Google credential has
expired, open it and click **Sign in with Google** again.

### 2d. Create the OAuth client
1. In n8n first: **Overview → Credentials** (or **Create → Credential**).
   Search for **Google Sheets OAuth2 API** and open it. **Copy the OAuth
   Redirect URL** it shows. It should be
   `http://localhost:5678/rest/oauth2-credential/callback`. Leave this tab
   open.
2. In Google Cloud: **APIs & Services → Credentials → + Create credentials →
   OAuth client ID.**
3. Application type: **Web application**. Name: `n8n on my laptop`.
4. **Authorized redirect URIs → + Add URI**, then paste the address from
   step 1. Don't type it.
5. **Create.** A box shows the **Client ID** and **Client Secret**. Keep it
   open.

### 2e. Finish in n8n (do this twice)
In the **Google Sheets OAuth2 API** credential:
1. Paste the **Client ID** and **Client Secret**. Watch for stray spaces.
2. **Sign in with Google**, choose your personal account, and allow access.
   You may see "Google hasn't verified this app". That's expected for your own
   test app: click **Continue**.
3. **Save.**

Then create a **Gmail OAuth2 API** credential and repeat 1–3 with **the same
Client ID and Secret**.

**Check:** both credentials show as connected, with no red warning.

| If you see | It means | Fix |
|---|---|---|
| `redirect_uri_mismatch` | The address in Google doesn't exactly match n8n's | Copy it again from n8n into 2d step 4 |
| "Access denied" | Your account isn't a test user | 2c step 5 |
| `invalid_client` | The ID or secret was pasted wrongly | Copy both again |

---

## Part 3 · Import the workflow and connect it (5 min)

1. In n8n: **Overview → Create workflow**, then the **⋯** menu at the top
   right, **Import from File…**, and choose `n8n/bella-lead-workflow.json`
   from this project.
2. Open **Add row to Leads sheet**:
   - Credential: your Google Sheets credential.
   - Document: **Bella Real Estate Leads**. Sheet: **Sheet1**.
   - The eight columns appear, already mapped. Leave them as they are.
3. Open **Email the agent**:
   - Credential: your Gmail credential.
   - **To:** replace `REPLACE_WITH_YOUR_EMAIL@example.com` with the address
     where you want lead alerts.
4. **Save** the workflow.

**Check:** no node has a red warning triangle.

---

## Part 4 · Test it inside n8n (5 min)

1. Open **Receive lead** and click **Listen for test event**. n8n shows a
   *Test URL* ending in `/webhook-test/bella-lead`.
2. In a PowerShell window, send a fake lead to it:

   ```powershell
   $lead = @{ lead_id="test00000001"; received_at="2026-11-17T09:00:00+00:00"; name="Test Lead"; phone="03001234567"; email=""; property_ref="BRE-R-202"; message="Sent from PowerShell"; source="manual test" } | ConvertTo-Json
   Invoke-RestMethod -Method Post -Uri "http://localhost:5678/webhook-test/bella-lead" -ContentType "application/json" -Body $lead
   ```

**Check, all four:**
- PowerShell prints `ok : True` and `lead_id : test00000001`.
- The sheet has a new row, with phone **03001234567** including the leading 0.
- Your inbox has "New lead: Test Lead — BRE-R-202".
- In n8n, all four nodes have green ticks.

Then send screenshots of the sheet row and the PowerShell output.

The live connection to the backend (Publish, then `N8N_WEBHOOK_URL`) comes
after this works.
