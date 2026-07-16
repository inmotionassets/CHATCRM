# ChatCRM Discord Setup Bot

This folder contains a one-time Discord setup bot for the ChatCRM Team server.

It creates the ChatCRM roles, categories, text channels, voice channels, permission overwrites, and pinned onboarding/training templates from the ChatCRM Discord buildout.

The script is safe by default:

- It never hardcodes your Discord token.
- It uses `DISCORD_BOT_TOKEN` from `.env`.
- It uses `DISCORD_GUILD_ID` from `.env`.
- It does not delete existing channels.
- It reuses existing roles and channels instead of duplicating them.
- It prints a summary of everything created, reused, skipped, and pinned.
- It has a dry-run mode that makes no Discord changes.

## Files

- `package.json` - Node package and commands.
- `index.js` - One-time setup bot.
- `config.js` - ChatCRM roles, categories, channels, permissions, and pinned messages.
- `.env.example` - Safe environment variable template.
- `README.md` - Setup instructions.

## 1. Create The Discord Application

1. Go to the Discord Developer Portal.
2. Click **New Application**.
3. Name it `ChatCRM Setup Bot`.
4. Open the application.

## 2. Create The Bot

1. Go to **Bot**.
2. Click **Add Bot**.
3. Copy the bot token.
4. Do not share this token with anyone.

## 3. Enable Required Intents

In the bot settings, enable:

- Server Members Intent is optional for this setup.
- Message Content Intent is not required for this setup.

The bot mainly needs guild, role, channel, message-send, and pin permissions from the invite.

## 4. Invite The Bot To Your Server

In Discord Developer Portal:

1. Go to **OAuth2**.
2. Go to **URL Generator**.
3. Select scopes:
   - `bot`
4. Select bot permissions:
   - Manage Roles
   - Manage Channels
   - View Channels
   - Send Messages
   - Manage Messages
   - Read Message History
   - Add Reactions
   - Connect
   - Speak
5. Copy the generated invite URL.
6. Open it in your browser.
7. Invite the bot to the `ChatCRM Team` server.

Important:

- Put the bot role above the roles it needs to create/manage.
- Do not give the bot Administrator unless absolutely necessary.
- If role creation fails, move the bot role higher in Discord server settings and run setup again.

## 5. Add Environment Variables

From this folder:

```powershell
Copy-Item .env.example .env
```

Then open `.env` and fill in:

```env
DISCORD_BOT_TOKEN=your-bot-token-here
DISCORD_GUILD_ID=your-server-id-here
```

To find your server ID:

1. In Discord, enable Developer Mode.
2. Right-click your server name.
3. Click **Copy Server ID**.

Optional training fields:

```env
TRAINING_DATE=Saturday, July 18, 2026
TRAINING_TIME=3:00 PM Central
TRAINING_LINK=https://your-meeting-link
```

## 6. Install Dependencies

```powershell
npm install
```

## 7. Run Dry Run First

Dry run prints the exact roles, categories, channels, permissions, and pinned messages that would be created.

It does not connect to Discord and does not change anything.

```powershell
npm run dry-run
```

## 8. Run Setup

When dry-run looks right, run:

```powershell
npm run setup
```

The bot will:

1. Connect to the server from `DISCORD_GUILD_ID`.
2. Create missing roles.
3. Reuse existing roles.
4. Create missing categories.
5. Reuse existing categories.
6. Create missing text channels.
7. Create missing voice channels.
8. Apply permission overwrites.
9. Post and pin onboarding/training/template messages.
10. Print a summary.
11. Stop when finished.

## 9. Optional: Remove The Bot After Setup

After the server is built, you may remove the bot from the server if you want.

The created roles, categories, channels, permissions, and pinned messages will remain.

## Safety Notes

- Never commit `.env`.
- Never paste your Discord bot token into ChatCRM, Discord, GitHub, or a public channel.
- Do not store ChatCRM passwords, login PDFs, API keys, tax information, or private seller/buyer data in Discord.
- Keep leadership, disposition, buyer data, payroll, and admin discussions private.
- Acquisition callers should not see Buyer Network data, disposition strategy, payroll, or leadership channels.

## Troubleshooting

If setup says it cannot manage roles:

1. Open Discord server settings.
2. Go to Roles.
3. Move the bot role above the ChatCRM roles.
4. Run `npm run setup` again.

If setup says it cannot create channels:

1. Confirm the bot has Manage Channels permission.
2. Confirm the bot is still in the correct server.
3. Confirm `DISCORD_GUILD_ID` is correct.
4. Run `npm run setup` again.

If pinned messages do not post:

1. Confirm the bot has Send Messages.
2. Confirm the bot has Manage Messages.
3. Confirm the bot has Read Message History.
4. Run `npm run setup` again.
