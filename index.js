import 'dotenv/config';
import { Client, GatewayIntentBits } from 'discord.js';
import Groq from 'groq-sdk';

const { DISCORD_TOKEN, GROQ_API_KEY, GROQ_MODEL } = process.env;

if (!DISCORD_TOKEN) {
  throw new Error('Missing DISCORD_TOKEN in environment variables.');
}

if (!GROQ_API_KEY) {
  throw new Error('Missing GROQ_API_KEY in environment variables.');
}

const groq = new Groq({
  apiKey: GROQ_API_KEY,
});

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

client.once('ready', () => {
  console.log(`Logged in as ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  const isMentioned = message.mentions.has(client.user);
  const hasPrefix = message.content.startsWith('!ask ');

  if (!isMentioned && !hasPrefix) return;

  const prompt = hasPrefix
    ? message.content.slice('!ask '.length).trim()
    : message.content.replace(`<@${client.user.id}>`, '').replace(`<@!${client.user.id}>`, '').trim();

  if (!prompt) {
    await message.reply('Ask me something after mentioning me or using `!ask`.');
    return;
  }

  try {
    await message.channel.sendTyping();

    const completion = await groq.chat.completions.create({
      model: GROQ_MODEL || 'llama-3.1-8b-instant',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful Discord bot. Keep replies concise and friendly.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 800,
    });

    const reply = completion.choices[0]?.message?.content?.trim() || 'No response from Groq.';
    await message.reply(reply.slice(0, 2000));
  } catch (error) {
    console.error(error);
    await message.reply('Sorry, I could not get a response from Groq.');
  }
});

client.login(DISCORD_TOKEN);
