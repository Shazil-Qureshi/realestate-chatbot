# 02 · Requirements

| | |
|---|---|
| **Project** | AI Real Estate Customer Support Chatbot |
| **Phase** | Stage 1 – Backend and AI knowledge base |
| **Task** | 1.2 Requirements document |
| **Last updated** | 13 November 2026 |
| **Status** | Completed |

## 1. Objective

Write down exactly what the system must do, before writing any code, so that
"finished" has a clear meaning and every feature can be tested against a
numbered requirement.

## 2. Technical concepts

| Term | What it means | Why we need it | How it works | Example |
|---|---|---|---|---|
| **Functional requirement** | Something the system must *do*. | It defines the features to build. | Written as "The system shall…" so it is either true or false, never a matter of opinion. | FR-04: the chatbot shall say it does not know when the documents lack the answer. |
| **Non-functional requirement** | A quality the system must *have*: speed, cost, safety. | A feature that is correct but takes 60 seconds, or costs money we don't have, is still a failure. | Written with a number wherever possible, so it can be measured. | NFR-01: an answer shall arrive within 10 seconds. |
| **Out of scope** | Things we deliberately will not build. | Stops the project growing forever ("scope creep"). | A written list agreed in advance. | Real payments, user accounts. |
| **Acceptance criteria** | The checks that prove a requirement is met. | Turns a requirement into a test case. | Each criterion names an input and the expected result. | Ask "Do you deliver to Mars?" → the bot says it doesn't know. |
| **Traceability** | Each requirement has an ID used in code and tests. | Lets us prove every requirement was actually built and tested. | Test `test_unknown_question` refers to FR-04. | FR-04 → test case CHAT-03. |

Why this matters in practice: without written requirements, a beginner tends to
build whatever is interesting that day and calls the project done when they run
out of energy. With them, the project has a finish line.

## 3. Tools and technologies

No tools are used in this task. It is a written specification that drives every
later task.

## 4. Implementation details

### 4.1 Fictional business

| | |
|---|---|
| **Company** | Bella Real Estate |
| **Type** | Residential sales and rentals agency (fictional) |
| **Location** | Islamabad and Rawalpindi, Pakistan (fictional branches) |
| **Customers** | Buyers, renters and sellers asking about listings, prices, areas, viewings and the agency's process |

All data is invented. Nothing in this project represents a real company,
property, price or person.

### 4.2 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The system shall accept a customer question as text through a web chat widget. | Must |
| FR-02 | The system shall search the company documents and retrieve the most relevant passages for that question. | Must |
| FR-03 | The system shall generate an answer using only the retrieved passages. | Must |
| FR-04 | The system shall reply that it does not know when the retrieved passages do not contain the answer, instead of guessing. | Must |
| FR-05 | The system shall show which document each answer came from. | Must |
| FR-06 | The system shall politely decline questions unrelated to the company's business. | Must |
| FR-07 | The system shall offer to pass the customer to a human agent. | Should |
| FR-08 | The system shall ask for the customer's name and phone number only after the customer agrees to share them. | Must |
| FR-09 | The system shall validate a lead before accepting it: a non-empty name and a plausible phone number. | Must |
| FR-10 | The system shall send each accepted lead to an n8n webhook. | Must |
| FR-11 | The n8n workflow shall append each lead as a row in a Google Sheet. | Must |
| FR-12 | The n8n workflow shall email the agent when a lead arrives. | Must |
| FR-13 | The system shall tell the customer their details were received. | Must |
| FR-14 | The website shall present the agency and open the chat widget. | Must |
| FR-15 | The system shall be reachable publicly as a live demo. | Must |
| FR-16 | The system shall answer in the customer's language where it can. | Could |

### 4.3 Non-functional requirements

| ID | Requirement | How it will be measured |
|---|---|---|
| NFR-01 | An answer shall normally arrive within 10 seconds. | Timed during testing. |
| NFR-02 | The project shall run on free service tiers only. | No payment details given to any service. |
| NFR-03 | No API key, token or password shall appear in the GitHub repository. | `.env` is listed in `.gitignore`; repository searched before publishing. |
| NFR-04 | The backend shall limit how many questions one visitor can ask per hour. | A limit is enforced and tested by exceeding it. |
| NFR-05 | The chatbot shall keep answering questions even when the n8n webhook is unreachable. | Tested with a deliberately wrong webhook address. |
| NFR-06 | The vector database shall be rebuilt automatically when the server starts. | Verified after restarting the Hugging Face Space. |
| NFR-07 | The website shall state clearly that the company and its data are fictional. | Visible on the page and in the chat. |
| NFR-08 | The chat widget shall be usable on a phone screen. | Checked at 375 px width. |
| NFR-09 | Lead data shall not be committed to the repository or shown to other visitors. | Repository and responses inspected. |
| NFR-10 | A beginner shall be able to run the project from the README alone. | Followed start to finish on a clean folder. |

### 4.4 Out of scope

These are deliberately excluded, and saying so now prevents the project
expanding without end:

- Real property data or any live MLS or portal feed
- Payments, bookings or contracts
- User accounts, logins or chat history across visits
- Voice calls or speech
- A mobile app
- Multiple companies in one deployment
- Automatic retraining on new documents (documents are added by rerunning the
  ingestion script)

### 4.5 Acceptance criteria

The project is complete when all of the following are true and have been
recorded in a test report with real output:

| # | Check | Requirement |
|---|---|---|
| AC-1 | Asking "Do you have 3-bedroom houses in DHA?" returns an answer drawn from the listing documents, with the source named. | FR-02, FR-03, FR-05 |
| AC-2 | Asking "Do you sell cars?" gets a polite decline, not an invented answer. | FR-06 |
| AC-3 | Asking something plausible but absent, such as "What is your Karachi office address?", gets "I don't know" rather than a guess. | FR-04 |
| AC-4 | Agreeing to share contact details results in a new row in Google Sheets and an email to the agent. | FR-08 to FR-13 |
| AC-5 | Submitting an empty name or a phone number such as "abc" is rejected with a clear message. | FR-09 |
| AC-6 | The live demo answers questions from a public URL on both a laptop and a phone. | FR-15, NFR-08 |
| AC-7 | Pointing the webhook at a wrong address still allows normal chat. | NFR-05 |
| AC-8 | Searching the public repository finds no API key. | NFR-03 |
| AC-9 | Exceeding the rate limit returns a clear "too many requests" message. | NFR-04 |
| AC-10 | Restarting the Hugging Face Space leaves the chatbot working with no manual step. | NFR-06 |

## 5. Files created or modified

| File | Purpose |
|---|---|
| `docs/02_requirements.md` | This document |
| `PROJECT_TRACKER.md` | Task 1.2 marked complete |

## 6. Instructions

Create the file `docs/02_requirements.md` in VS Code and paste this content.
No commands are run in this task.

## 7. Testing procedure

A requirements document is reviewed, not executed. The review asks:

1. Is every requirement either true or false, with no room for opinion?
2. Can each one be tested?
3. Does every acceptance criterion map to at least one requirement?
4. Is anything in the roadmap missing from the list?

## 8. Test results

| Check | Result |
|---|---|
| All requirements stated as testable sentences | Pass (reviewed 13 Nov 2026) |
| Every acceptance criterion maps to a requirement ID | Pass |
| Every roadmap feature appears as a requirement | Pass |
| Out-of-scope list written | Pass |

No code was executed in this task, so there is nothing to run.

## 9. Problems encountered

Two gaps in the original roadmap came to light while writing this:

1. The roadmap did not say what should happen to the chatbot when n8n is down.
   Added as NFR-05: chat must keep working.
2. The roadmap did not mention off-topic questions, which is one of the first
   things a stranger will try on a public demo. Added as FR-06.

## 10. Solutions

Both are now numbered requirements with matching acceptance criteria (AC-2 and
AC-7), so neither can be quietly forgotten.

## 11. Evidence

- [ ] Screenshot: `docs/02_requirements.md` open in VS Code

## 12. Completion status

Completed and reviewed on 13 November 2026.

## 13. Next steps

Task 1.3: write the fictional Bella Real Estate documents into `data/`. These
become the chatbot's knowledge, so their quality sets a ceiling on how good the
answers can be.
