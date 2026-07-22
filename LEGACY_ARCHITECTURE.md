# LEGACY Architecture

ChatCRM is not just a CRM. ChatCRM is becoming an acquisition operations platform powered by LEGACY Market Intelligence.

The permanent product question is:

> What does LEGACY know about this property?

Every major screen should eventually be able to ask that question and receive the same trusted intelligence snapshot, shaped for the user's role.

## Platform Map

```text
ChatCRM

+-- CRM Layer
|   +-- Leads
|   +-- Buyers
|   +-- Tasks
|   +-- Users
|   +-- Agreements
|   +-- Communications
|
+-- LEGACY Market Intelligence
|   +-- Transaction Engine
|   +-- Buyer Intelligence
|   +-- Builder Intelligence
|   +-- Ownership Intelligence
|   +-- Contact Intelligence
|   +-- Permit Intelligence
|   +-- Corridor Detection
|   +-- Pricing Intelligence
|   +-- Opportunity Engine
|   +-- Market Alerts
|   +-- Prediction Engine
|
+-- Acquisition Workspace
+-- Disposition Workspace
+-- Leadership Dashboard
+-- Future APIs
```

## Core Idea

The CRM layer stores work.

LEGACY explains the market.

Acquisition, Disposition, Leadership, Buyer Network, Analytics, and future mobile apps should not each invent their own property logic. They should consume one shared Market Intelligence snapshot.

## Market Intelligence Snapshot

A property snapshot should eventually answer:

- Who owns nearby?
- Who bought nearby?
- Who is building nearby?
- Who is permitting nearby?
- Who is selling nearby?
- Who is assembling land?
- Who is buying cash?
- Who is likely to buy this deal?
- What is the opportunity score?
- Why was that score generated?

## Service Direction

The backend should move toward this shape:

```text
MarketIntelligenceService

+-- TransactionService
+-- BuyerService
+-- BuilderService
+-- OwnershipService
+-- ContactService
+-- PermitService
+-- FootprintService
+-- CorridorService
+-- MatchService
+-- PricingService
+-- OpportunityService
```

Routers should call the MarketIntelligenceService for a property snapshot. The service coordinates the modules underneath.

This keeps the frontend stable while the intelligence layer grows.

## User Views

### Acquisition

Acquisition users need a simple version of the truth:

- Is this property worth fighting for?
- Are builders active nearby?
- Are buyers already purchasing in this area?
- What should I say to the seller?
- Should this become a hot lead?

### Disposition

Disposition users need buyer and exit intelligence:

- Best buyers for this deal
- Buyer footprint
- Buyer purchase history
- Buyer demand score
- Suggested blast list
- Likely close probability

### Leadership

Leadership needs market direction:

- Where buyer activity is rising
- Where builder demand is increasing
- Which callers are creating real opportunities
- Which areas deserve more lead volume
- Which buyers are closing
- Whether top buyer recommendations are accurate

## Contact Intelligence

Do not think of this as skip tracing only.

Skip tracing is one data source. Contact Intelligence is the system.

Contact Intelligence may include:

- Business phone
- Office phone
- Public email
- Mailing address
- Registered agent
- Secretary of State records
- Company website
- Public social profiles where appropriate
- Licensed skip-trace provider data
- Previous conversations in ChatCRM
- Last contacted date
- Response rate
- Preferred contact method
- Confidence score

The UI should show what was found, where it came from, and how confident ChatCRM is.

## Source Trust

ChatCRM should always separate:

- Recorded sale
- Estimated sale
- Buyer mailing record
- Inferred builder
- Verified repeat buyer
- Public business contact
- Licensed skip-trace contact

Do not blend weak signals into verified facts.

Trust comes from showing the source.

## Opportunity Score

The Opportunity Engine should score a property from 0 to 100.

The score must be explainable.

Example score drivers:

- Buyer demand
- Builder activity
- Nearby transaction quality
- Corridor strength
- Price spread
- Parcel fit
- Tax or distress signal
- Contact quality
- Recent market velocity

Every point should have a reason.

## Buyer Prediction Goal

"We have all the buyers" should become measurable.

For every deal that enters ChatCRM, track:

- How many buyers were identified?
- How many buyers responded?
- How many made offers?
- Who bought the deal?
- Was the winning buyer in the top three recommendations?

Long-term target:

```text
Winning buyer appears in ChatCRM's top three recommendations at least 90% of the time.
```

That is the proof that LEGACY is working.

## Product Story

Short version:

```text
Open any property, and LEGACY tells you everything the market already knows about it.
```

That is the north star.