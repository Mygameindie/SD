# SD Discord Bot

Repository: https://github.com/Mygameindie/SD

This bot uses Groq API instead of Gemini.

## Environment variables

```env
DISCORD_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key
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

## Groq API structure for Node.js

```js
import Groq from "groq-sdk";

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

const completion = await groq.chat.completions.create({
  model: "llama-3.1-8b-instant",
  messages: [
    {
      role: "system",
      content: "You are a helpful Discord bot.",
    },
    {
      role: "user",
      content: "Hello!",
    },
  ],
});

const reply = completion.choices[0].message.content;
console.log(reply);
```
