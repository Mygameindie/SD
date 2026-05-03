# SD Discord Bot

A Discord bot that uses the Groq API for AI replies.

## Setup

Install dependencies:

```bash
npm install
```

Create a `.env` file:

```env
DISCORD_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

Start the bot:

```bash
npm start
```

## How to use

Mention the bot in Discord:

```text
@YourBot hello
```

Or use the command prefix:

```text
!ask hello
```

## Groq model

Recommended fast model:

```js
model: "llama-3.1-8b-instant"
```

Higher quality model:

```js
model: "llama-3.3-70b-versatile"
```
