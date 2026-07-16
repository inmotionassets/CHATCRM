import "dotenv/config";
import {
  ChannelType,
  Client,
  GatewayIntentBits,
  PermissionFlagsBits,
  PermissionsBitField
} from "discord.js";
import { setupConfig } from "./config.js";

const args = new Set(process.argv.slice(2));
const isDryRun = args.has("--dry-run") || !args.has("--setup");
const shouldSetup = args.has("--setup");
const syncExistingPermissions = process.env.SYNC_EXISTING_PERMISSIONS !== "false";
const createPinnedMessages = process.env.CREATE_PINNED_MESSAGES !== "false";

const summary = {
  rolesCreated: [],
  rolesReused: [],
  categoriesCreated: [],
  categoriesReused: [],
  channelsCreated: [],
  channelsReused: [],
  permissionsApplied: [],
  pinnedMessagesCreated: [],
  pinnedMessagesReused: [],
  skipped: []
};

if (isDryRun && shouldSetup) {
  throw new Error("Use either --dry-run or --setup, not both.");
}

if (isDryRun) {
  printDryRun();
  process.exit(0);
}

const token = process.env.DISCORD_BOT_TOKEN;
const guildId = process.env.DISCORD_GUILD_ID;

if (!token || !guildId) {
  throw new Error("Missing DISCORD_BOT_TOKEN or DISCORD_GUILD_ID. Copy .env.example to .env and fill both values.");
}

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages]
});

client.once("ready", async () => {
  try {
    const guild = await client.guilds.fetch(guildId);
    await guild.roles.fetch();
    await guild.channels.fetch();

    console.log(`Connected to ${guild.name}.`);
    console.log("Creating or reusing ChatCRM roles, categories, channels, permissions, and pinned messages...");

    const rolesByName = await ensureRoles(guild);
    await orderRoles(rolesByName);
    await ensureCategoriesAndChannels(guild, rolesByName);

    printSummary(summary);
    console.log("Discord setup complete. The bot will now stop.");
  } catch (error) {
    console.error("Discord setup failed:");
    console.error(error);
    process.exitCode = 1;
  } finally {
    client.destroy();
  }
});

await client.login(token);

function printDryRun() {
  console.log("CHATCRM DISCORD SETUP DRY RUN");
  console.log("No Discord connection will be made. Nothing will be created or changed.");
  console.log("");
  console.log(`Server Name: ${setupConfig.serverName}`);
  console.log(`Tagline: ${setupConfig.tagline}`);
  console.log("");

  console.log("ROLES TO ENSURE");
  for (const role of setupConfig.roles) {
    const permissions = role.permissions.length ? role.permissions.join(", ") : "No special Discord permissions";
    console.log(`- ${role.name}: ${permissions}`);
  }
  console.log("");

  console.log("CATEGORIES, CHANNELS, PERMISSIONS, AND PINNED MESSAGES TO ENSURE");
  for (const category of setupConfig.categories) {
    const categoryProfile = getPermissionProfile(category.permissionProfile);
    console.log(`\n[Category] ${category.name}`);
    console.log(`  Permissions: ${formatProfile(categoryProfile)}`);
    for (const channel of category.channels) {
      const profile = getPermissionProfile(channel.permissionProfile || category.permissionProfile);
      const pinList = channel.pinnedMessages?.length ? channel.pinnedMessages.join(", ") : "none";
      console.log(`  - ${channel.type}: ${channel.name}`);
      console.log(`    Permissions: ${formatProfile(profile)}`);
      console.log(`    Pinned messages: ${pinList}`);
      for (const messageKey of channel.pinnedMessages || []) {
        console.log(indent(resolveMessage(messageKey), 6));
      }
    }
  }
  console.log("\nDry run complete. Run npm run setup when ready.");
}

async function ensureRoles(guild) {
  const rolesByName = new Map();
  const cachedRoles = await guild.roles.fetch();

  for (const roleConfig of setupConfig.roles) {
    const existing = cachedRoles.find((role) => role.name === roleConfig.name);
    if (existing) {
      rolesByName.set(roleConfig.name, existing);
      summary.rolesReused.push(roleConfig.name);
      continue;
    }

    const created = await guild.roles.create({
      name: roleConfig.name,
      color: roleConfig.color,
      permissions: resolveRolePermissions(roleConfig.permissions),
      reason: `ChatCRM setup: ${roleConfig.reason}`
    });
    rolesByName.set(roleConfig.name, created);
    summary.rolesCreated.push(roleConfig.name);
  }

  return rolesByName;
}

async function orderRoles(rolesByName) {
  const lowToHigh = [...setupConfig.roles].reverse();
  for (let index = 0; index < lowToHigh.length; index += 1) {
    const role = rolesByName.get(lowToHigh[index].name);
    if (!role || role.managed) continue;
    try {
      await role.setPosition(index + 1, "ChatCRM setup role hierarchy");
    } catch (error) {
      summary.skipped.push(`Could not move role ${role.name}: ${error.message}`);
    }
  }
}

async function ensureCategoriesAndChannels(guild, rolesByName) {
  for (const categoryConfig of setupConfig.categories) {
    const categoryProfile = getPermissionProfile(categoryConfig.permissionProfile);
    let category = findChannel(guild, categoryConfig.name, ChannelType.GuildCategory);
    const categoryOverwrites = buildPermissionOverwrites(guild, rolesByName, categoryProfile, "category");

    if (!category) {
      category = await guild.channels.create({
        name: categoryConfig.name,
        type: ChannelType.GuildCategory,
        permissionOverwrites: categoryOverwrites,
        reason: "ChatCRM setup category"
      });
      summary.categoriesCreated.push(categoryConfig.name);
    } else {
      summary.categoriesReused.push(categoryConfig.name);
      if (syncExistingPermissions) {
        await category.permissionOverwrites.set(categoryOverwrites, "ChatCRM setup category permissions");
        summary.permissionsApplied.push(`${categoryConfig.name} category`);
      }
    }

    for (const channelConfig of categoryConfig.channels) {
      await ensureChannel(guild, rolesByName, category, categoryConfig, channelConfig);
    }
  }
}

async function ensureChannel(guild, rolesByName, category, categoryConfig, channelConfig) {
  const channelType = channelConfig.type === "voice" ? ChannelType.GuildVoice : ChannelType.GuildText;
  const channelProfile = getPermissionProfile(channelConfig.permissionProfile || categoryConfig.permissionProfile);
  const overwrites = buildPermissionOverwrites(guild, rolesByName, channelProfile, channelConfig.type);
  let channel = findChannel(guild, channelConfig.name, channelType);

  if (!channel) {
    channel = await guild.channels.create({
      name: channelConfig.name,
      type: channelType,
      parent: category.id,
      permissionOverwrites: overwrites,
      reason: "ChatCRM setup channel"
    });
    summary.channelsCreated.push(`${categoryConfig.name} / ${channelConfig.name}`);
  } else {
    summary.channelsReused.push(`${categoryConfig.name} / ${channelConfig.name}`);
    if (syncExistingPermissions) {
      await channel.permissionOverwrites.set(overwrites, "ChatCRM setup channel permissions");
      summary.permissionsApplied.push(`${categoryConfig.name} / ${channelConfig.name}`);
    }
  }

  if (channelType === ChannelType.GuildText && createPinnedMessages) {
    for (const messageKey of channelConfig.pinnedMessages || []) {
      await ensurePinnedMessage(channel, messageKey);
      await wait(600);
    }
  }
}

async function ensurePinnedMessage(channel, messageKey) {
  const content = resolveMessage(messageKey);
  const pins = await channel.messages.fetchPinned().catch(() => null);
  const alreadyPinned = pins?.some((message) => normalizeMessage(message.content) === normalizeMessage(content));

  if (alreadyPinned) {
    summary.pinnedMessagesReused.push(`${channel.name}: ${messageKey}`);
    return;
  }

  const sent = await channel.send(content);
  await sent.pin("ChatCRM setup pinned message");
  summary.pinnedMessagesCreated.push(`${channel.name}: ${messageKey}`);
}

function findChannel(guild, name, type) {
  return guild.channels.cache.find((channel) => channel.name === name && channel.type === type);
}

function getPermissionProfile(name) {
  const profile = setupConfig.permissionProfiles[name];
  if (!profile) throw new Error(`Missing permission profile: ${name}`);
  return profile;
}

function buildPermissionOverwrites(guild, rolesByName, profile, channelKind) {
  const everyoneDeny = channelKind === "voice"
    ? [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.Connect, PermissionFlagsBits.Speak]
    : [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.SendMessages, PermissionFlagsBits.CreatePublicThreads, PermissionFlagsBits.SendMessagesInThreads];

  const overwrites = [
    {
      id: guild.roles.everyone.id,
      deny: everyoneDeny
    }
  ];

  for (const roleName of profile.view) {
    const role = rolesByName.get(roleName);
    if (!role) continue;
    const canSend = profile.send.includes(roleName);
    const allow = channelKind === "voice"
      ? [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.Connect, ...(canSend ? [PermissionFlagsBits.Speak] : [])]
      : [
          PermissionFlagsBits.ViewChannel,
          PermissionFlagsBits.ReadMessageHistory,
          ...(canSend ? [PermissionFlagsBits.SendMessages, PermissionFlagsBits.CreatePublicThreads, PermissionFlagsBits.SendMessagesInThreads, PermissionFlagsBits.AddReactions] : [])
        ];
    const deny = channelKind === "voice"
      ? canSend ? [] : [PermissionFlagsBits.Speak]
      : canSend ? [] : [PermissionFlagsBits.SendMessages, PermissionFlagsBits.CreatePublicThreads, PermissionFlagsBits.SendMessagesInThreads];

    overwrites.push({ id: role.id, allow, deny });
  }

  return overwrites;
}

function resolveRolePermissions(permissionNames) {
  const flags = permissionNames.map((name) => PermissionFlagsBits[name]).filter(Boolean);
  return new PermissionsBitField(flags);
}

function resolveMessage(messageKey) {
  const value = setupConfig.messages[messageKey];
  if (!value) throw new Error(`Missing pinned message: ${messageKey}`);
  if (typeof value === "function") {
    return value({
      trainingDate: process.env.TRAINING_DATE,
      trainingTime: process.env.TRAINING_TIME,
      trainingLink: process.env.TRAINING_LINK
    });
  }
  return value;
}

function normalizeMessage(value) {
  return String(value || "").replace(/\r\n/g, "\n").trim();
}

function formatProfile(profile) {
  return `view=[${profile.view.join(", ")}] send=[${profile.send.join(", ")}]`;
}

function indent(value, spaces) {
  const pad = " ".repeat(spaces);
  return String(value).split("\n").map((line) => `${pad}${line}`).join("\n");
}

function printSummary(result) {
  console.log("\nCHATCRM DISCORD SETUP SUMMARY");
  for (const [key, values] of Object.entries(result)) {
    console.log(`\n${key}: ${values.length}`);
    for (const value of values) console.log(`- ${value}`);
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
