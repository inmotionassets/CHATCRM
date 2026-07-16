export const setupConfig = {
  serverName: "ChatCRM Team",
  tagline: "Close More. Build Wealth.",
  roles: [
    {
      name: "Founder / Admin",
      color: "#047857",
      permissions: ["Administrator"],
      reason: "Full access for Virgo Davis and Shawn McGraw."
    },
    {
      name: "Leadership",
      color: "#0f766e",
      permissions: [],
      reason: "Access to leadership, performance, hiring, strategy, and coaching channels."
    },
    {
      name: "Acquisition Caller",
      color: "#2563eb",
      permissions: [],
      reason: "Access to announcements, training, call floor, lead help, team wins, schedules, and general areas."
    },
    {
      name: "Disposition",
      color: "#7c3aed",
      permissions: [],
      reason: "Access to Buyer Network, buyer matches, deal room, contracts, disposition updates, and shared team areas."
    },
    {
      name: "VA / Support",
      color: "#0891b2",
      permissions: [],
      reason: "Access to support, training, data cleanup, imports, assigned work, and announcements."
    },
    {
      name: "Trainee",
      color: "#f59e0b",
      permissions: [],
      reason: "Read-only Start Here and Training Center access before approval."
    },
    {
      name: "Bot",
      color: "#64748b",
      permissions: [],
      reason: "Automation role only. Do not grant Administrator unless absolutely necessary."
    }
  ],
  permissionProfiles: {
    startHere: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support"]
    },
    startHereOpenPost: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"]
    },
    announcementsReadOnly: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership"]
    },
    training: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership"]
    },
    acquisitionFloor: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "VA / Support"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "VA / Support"]
    },
    acquisitionQuestions: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "VA / Support", "Trainee"]
    },
    dealJourney: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support"],
      send: ["Founder / Admin", "Leadership", "Disposition"]
    },
    hotLeadPromoted: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller"]
    },
    dispositionPrivate: {
      view: ["Founder / Admin", "Leadership", "Disposition"],
      send: ["Founder / Admin", "Leadership", "Disposition"]
    },
    teamWins: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"]
    },
    support: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"]
    },
    leadershipPrivate: {
      view: ["Founder / Admin", "Leadership"],
      send: ["Founder / Admin", "Leadership"]
    },
    foundersPrivate: {
      view: ["Founder / Admin"],
      send: ["Founder / Admin"]
    },
    voiceTraining: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support", "Trainee"]
    },
    voiceCallFloor: {
      view: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support"],
      send: ["Founder / Admin", "Leadership", "Acquisition Caller", "Disposition", "VA / Support"]
    },
    voiceLeadership: {
      view: ["Founder / Admin", "Leadership"],
      send: ["Founder / Admin", "Leadership"]
    }
  },
  categories: [
    {
      name: "START HERE",
      permissionProfile: "startHere",
      channels: [
        { name: "welcome", type: "text", permissionProfile: "startHere", pinnedMessages: ["welcome"] },
        { name: "rules-and-expectations", type: "text", permissionProfile: "startHere", pinnedMessages: ["rules"] },
        { name: "introductions", type: "text", permissionProfile: "startHereOpenPost" },
        { name: "sign-paperwork", type: "text", permissionProfile: "startHere", pinnedMessages: ["signPaperwork"] },
        { name: "training-call-info", type: "text", permissionProfile: "startHere", pinnedMessages: ["trainingCallInfo"] },
        { name: "onboarding-checklist", type: "text", permissionProfile: "startHere", pinnedMessages: ["onboardingChecklist"] }
      ]
    },
    {
      name: "ANNOUNCEMENTS",
      permissionProfile: "announcementsReadOnly",
      channels: [
        { name: "announcements", type: "text", pinnedMessages: ["announcements"] },
        { name: "schedule", type: "text" },
        { name: "important-updates", type: "text" },
        { name: "company-goals", type: "text" }
      ]
    },
    {
      name: "TRAINING CENTER",
      permissionProfile: "training",
      channels: [
        { name: "training-manual", type: "text" },
        { name: "call-script", type: "text", pinnedMessages: ["callScript"] },
        { name: "rebuttals", type: "text", pinnedMessages: ["rebuttals"] },
        { name: "voicemail-drops", type: "text" },
        { name: "property-research", type: "text" },
        { name: "chatcrm-how-to", type: "text" },
        { name: "recordings-and-examples", type: "text" },
        { name: "frequently-asked-questions", type: "text" }
      ]
    },
    {
      name: "ACQUISITION CALL FLOOR",
      permissionProfile: "acquisitionFloor",
      channels: [
        { name: "daily-check-in", type: "text", permissionProfile: "acquisitionQuestions", pinnedMessages: ["dailyCheckIn"] },
        { name: "live-call-floor", type: "text" },
        { name: "call-questions", type: "text", permissionProfile: "acquisitionQuestions" },
        { name: "property-help", type: "text" },
        { name: "lead-help", type: "text" },
        { name: "hot-leads", type: "text", pinnedMessages: ["hotLead"] },
        { name: "follow-ups", type: "text", pinnedMessages: ["followUp"] },
        { name: "call-review", type: "text" }
      ]
    },
    {
      name: "DEAL JOURNEY",
      permissionProfile: "dealJourney",
      channels: [
        { name: "hot-leads-promoted", type: "text", permissionProfile: "hotLeadPromoted", pinnedMessages: ["hotLeadPromoted"] },
        { name: "offers-in-review", type: "text" },
        { name: "offers-sent", type: "text" },
        { name: "negotiations", type: "text" },
        { name: "under-contract", type: "text", pinnedMessages: ["underContract"] },
        { name: "title-and-closing", type: "text" },
        { name: "funded-and-closed", type: "text", pinnedMessages: ["fundedAndClosed"] }
      ]
    },
    {
      name: "DISPOSITION",
      permissionProfile: "dispositionPrivate",
      channels: [
        { name: "buyer-network", type: "text" },
        { name: "builder-network", type: "text" },
        { name: "buyer-matches", type: "text" },
        { name: "deal-marketing", type: "text" },
        { name: "buyer-feedback", type: "text" },
        { name: "disposition-updates", type: "text" },
        { name: "closing-coordination", type: "text" },
        { name: "closed-deals", type: "text" }
      ]
    },
    {
      name: "TEAM WINS",
      permissionProfile: "teamWins",
      channels: [
        { name: "wins", type: "text", pinnedMessages: ["wins"] },
        { name: "leaderboard", type: "text" },
        { name: "commissions-and-bonuses", type: "text" },
        { name: "motivation", type: "text" },
        { name: "general-chat", type: "text" }
      ]
    },
    {
      name: "SUPPORT & OPERATIONS",
      permissionProfile: "support",
      channels: [
        { name: "tech-support", type: "text" },
        { name: "crm-bugs", type: "text", pinnedMessages: ["bugReport"] },
        { name: "data-issues", type: "text" },
        { name: "account-access", type: "text" },
        { name: "suggestions", type: "text" },
        { name: "system-status", type: "text" }
      ]
    },
    {
      name: "LEADERSHIP",
      permissionProfile: "leadershipPrivate",
      channels: [
        { name: "admin-chat", type: "text" },
        { name: "strategy", type: "text" },
        { name: "hiring-and-onboarding", type: "text" },
        { name: "caller-performance", type: "text" },
        { name: "coaching-notes", type: "text" },
        { name: "commissions-and-payments", type: "text" },
        { name: "priority-deals", type: "text" },
        { name: "company-roadmap", type: "text" }
      ]
    },
    {
      name: "FOUNDING TEAM",
      permissionProfile: "foundersPrivate",
      channels: [
        { name: "founders-chat", type: "text" },
        { name: "beta-testing", type: "text" },
        { name: "product-feedback", type: "text" },
        { name: "roadmap-ideas", type: "text" },
        { name: "company-vision", type: "text" }
      ]
    },
    {
      name: "VOICE CHANNELS",
      permissionProfile: "voiceCallFloor",
      channels: [
        { name: "Training Room", type: "voice", permissionProfile: "voiceTraining" },
        { name: "Call Floor 1", type: "voice", permissionProfile: "voiceCallFloor" },
        { name: "Call Floor 2", type: "voice", permissionProfile: "voiceCallFloor" },
        { name: "Call Floor 3", type: "voice", permissionProfile: "voiceCallFloor" },
        { name: "Property Help Room", type: "voice", permissionProfile: "voiceCallFloor" },
        { name: "1-on-1 Coaching", type: "voice", permissionProfile: "voiceCallFloor" },
        { name: "Leadership Room", type: "voice", permissionProfile: "voiceLeadership" }
      ]
    }
  ],
  messages: {
    welcome: `Welcome to ChatCRM.

This is where we train, communicate, track wins, support one another, and build the acquisition team.

Start here:

1. Read #rules-and-expectations.
2. Check #training-call-info.
3. Complete your ChatCRM login.
4. Enter your name and email.
5. Sign your paperwork inside ChatCRM.
6. Review #call-script and #rebuttals.
7. Introduce yourself in #introductions.
8. Post your daily calling plan in #daily-check-in.

Close More. Build Wealth.`,
    rules: `ChatCRM Team Expectations

* Protect all seller, buyer, lead, and company information.
* Do not share leads, scripts, data, recordings, screenshots, or internal training outside the company.
* Keep notes accurate and professional inside ChatCRM.
* Do not quote prices, promise offers, or guarantee closings unless leadership has approved it.
* Be respectful, professional, dependable, and coachable.
* Show up on time for training and scheduled calling blocks.
* Ask questions early. Do not guess about important seller or property information.
* Do not call the same lead when another team member is actively working it.
* Review the lead timeline before calling.
* Every call matters.`,
    signPaperwork: `Before calling live leads, every team member must complete onboarding inside ChatCRM.

Steps:

1. Log in using the account provided.
2. Enter your legal name and email.
3. Review the confidentiality and partner agreement.
4. Sign electronically.
5. Download your signed copy.
6. Wait for Admin confirmation.
7. After approval, your Discord role will be changed from Trainee to Acquisition Caller.`,
    trainingCallInfo: ({ trainingDate, trainingTime, trainingLink }) => `ChatCRM Acquisition Team Training

Date: ${trainingDate || "[ADD DATE]"}
Time: ${trainingTime || "[ADD TIME] Central"}
Meeting Link: ${trainingLink || "[ADD LINK]"}

Bring:

* Laptop or desktop
* Notebook and pen
* Quiet workspace
* Headset if available
* Positive attitude

Training will cover:

* ChatCRM vision
* Confidentiality expectations
* Acquisition workflow
* Seller qualification
* Call scripts and rebuttals
* Property research
* Notes and call outcomes
* Hot-lead process
* Deal Journey tracking
* Commission structure
* First-week expectations`,
    onboardingChecklist: `ChatCRM New Team Member Checklist

[ ] Joined Discord
[ ] Read rules
[ ] Attended training
[ ] Received ChatCRM login
[ ] Entered name and email
[ ] Signed paperwork
[ ] Reviewed call script
[ ] Reviewed rebuttals
[ ] Practiced sample call
[ ] Admin approved live access
[ ] Promoted to Acquisition Caller`,
    announcements: `Announcements are for important ChatCRM team updates.

Founder/Admin and Leadership can post here. Team members should read updates and use threads when replies are needed.`,
    callScript: `Do not make offers on the first call unless leadership has specifically approved it.

Your job is to:

* Verify ownership
* Confirm interest in selling
* Understand motivation
* Confirm timeline
* Collect accurate notes
* Set the next step
* Mark qualified opportunities correctly`,
    rebuttals: `Best default response:

"I understand. My job is simply to confirm the correct information and see whether it makes sense for our acquisitions team to review the property."`,
    dailyCheckIn: `Daily check-in format:

Name:
Calling block:
Number of calls planned:
Conversation goal:
Hot-lead goal:
Follow-ups due:
Any help needed:`,
    hotLead: `Hot Lead Submission

Property Address:
Owner Name:
Best Phone:
Caller:
Motivation:
Seller Timeline:
Price Mentioned:
Best Callback Time:
Property Concerns:
Additional Notes:
Date and Time Submitted:

Important:
Mark the lead Hot inside ChatCRM before posting here.`,
    followUp: `Property Address:
Owner:
Assigned Caller:
Reason for Follow-Up:
Follow-Up Date:
Best Time:
Last Call Result:
Important Notes:`,
    hotLeadPromoted: `HOT LEAD PROMOTED

Property:
Seller:
Original Caller:
Assigned Acquisition Manager:
Current Stage:
Next Action:
Last Updated:`,
    underContract: `UNDER CONTRACT

Property:
Original Caller:
Contract Date:
Contract Price:
Title Company:
Assigned Disposition:
Estimated Closing:
Current Status:`,
    fundedAndClosed: `FUNDED AND CLOSED

Property:
Original Caller:
Closing Date:
Assignment Fee / Company Revenue:
Caller Commission:
Payment Status:
Congratulations Message:

Do not expose private buyer contact information in shared Acquisition channels.`,
    wins: `Drop your wins here:

* Good seller conversations
* Confirmed owners
* Hot leads
* Follow-ups booked
* Offers sent
* Contracts signed
* Deals closed
* Personal improvement
* Team accomplishments

Small wins stack into big checks.

Important:
Do not post confidential seller details, full phone numbers, private buyer information, or contract documents in public team channels.`,
    bugReport: `Issue:
User:
Device:
Browser:
Page:
What happened:
What should have happened:
Screenshot:
Time of issue:`
  }
};
