# ChatCRM Blueprint Summary

## Main Idea

ChatCRM is planned as an all-in-one lead intelligence CRM for real estate wholesalers, investors, agents, and acquisitions teams.

It should combine:

- Lead management
- AI parsing
- Property research
- Mapping
- Phone, SMS, and email tools
- Automations
- Document storage
- Analytics

## Core Frontend Features

- React + Vite frontend
- Secure login
- Leads dashboard
- Property detail pages
- Map views
- Kanban-style pipeline
- Mobile responsive layout
- AI assistant sidebar
- Dark/light mode
- Search and filters

## Core Backend Features

- FastAPI backend
- SQLAlchemy database layer
- JWT authentication
- SQLite first, PostgreSQL later
- PDF processing services
- AI parsing services
- Property lookup services
- Background jobs
- External API integrations

## User Roles

- Admin users
- Acquisition managers
- Cold callers
- Virtual assistants
- Team permissions
- Role-based access control

## Lead Management

- Create, edit, and delete leads
- Assign leads to users
- Track pipeline stages
- Tags and categories
- Follow-up reminders
- Notes timeline
- Deal tracking
- Lead scoring
- Duplicate detection

## PDF Import Vision

- Upload tax delinquent lists
- Upload foreclosure lists
- Upload probate records
- Upload county documents
- Extract names, addresses, APNs, phones, and emails
- Clean and format imported data
- Merge duplicates
- Review imports before saving leads

## Future Features

- Property intelligence
- Google Maps / Earth-style overlays
- Phone calling
- SMS campaigns
- Email campaigns
- AI summaries and scoring
- Workflow automations
- Document storage
- KPI dashboard
- Integrations with Twilio, OpenAI, Google Maps, DocuSign, Stripe, and real estate data providers

## Recommended Roadmap

### Phase 1

- Stabilize authentication
- Finish lead CRUD
- Add PDF uploads
- Build the first parsing system

### Phase 2

- Add maps
- Add phone and SMS tools
- Add workflow automations

### Phase 3

- Add AI systems
- Add predictive analytics
- Add advanced property intelligence
- Expand into a full acquisitions platform

## Priority HIGH - Call Activity Tracking & Anti-Duplicate Calling System

Add a proper call activity log so team members do not double-call the same lead at the same time.

Every lead call/update should record:

- Lead ID
- User ID
- User full name or username
- Action type
- Call outcome
- Notes
- Timestamp
- Follow-up date if added

Create or update a LeadActivity / CallLog model with:

- id
- lead_id
- user_id
- user_name_snapshot
- action_type
- call_outcome
- notes
- created_at
- follow_up_date

Action types:

- called
- call_started
- note_added
- status_changed
- follow_up_set
- hot_lead_marked
- not_interested
- voicemail
- wrong_number

Frontend requirements:

- Show an activity timeline on the Lead Detail page.
- Each activity displays user name, action, outcome, note, and timestamp.
- Add Last Contacted By and Last Contacted At to the lead list.
- Warn if another user contacted the lead within the last 10 minutes.
- Add a soft lead lock when a user opens/calls a lead.
- Lock expires automatically after 10 minutes.
- Admin can override.

Backend requirements:

- Create a LeadActivity row when a user updates call outcome.
- Create a LeadActivity row when status/stage changes.
- Create a LeadActivity row when notes are added.
- Create a call_started row when a call button is clicked.
- Return activity history from GET /leads/{lead_id}/activity.

Admin dashboard:

- Add recent team activity feed.
- Add daily team call count by user.

Manual tests:

- User A calls lead, activity shows User A and timestamp.
- User B opens same lead within 10 minutes, warning appears.
- Admin can see all users' call activity.
- Acquisition users only see activity related to leads they can access.
- Last Contacted By/At updates after call outcome.
