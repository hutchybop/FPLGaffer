### 4. Create a `.env` File

Create a `.env` file in the project root and add the following (see included `.envexample`):

```bash
FPL_TEAM_ID=YOUR_FPL_TEAM_ID
GROQ_API_KEY_FREE=YOUR_FREE_GROQ_API_KEY
GROQ_API_KEY_PAID=YOUR_PAID_GROQ_API_KEY
```

Both keys are optional, but the app will use them as follows:

- If **both** keys are present → it will **use the free key by default** and **automatically fall back** to the paid key if the free tier’s limits are exceeded.  
- If only the **free key** is provided → it will only use the free tier (some large or complex requests may fail).  
- If only the **paid key** is provided → all requests will be processed using your paid account (billed per token).  
- If **neither** key is provided → AI features will be disabled.

---

#### 🔍 How to find your `FPL_TEAM_ID`
1. Log in to your FPL account.  
2. Go to **"Points"** or your team page.  
3. Look at the URL — your ID is the number shown here:  
   ```
   https://fantasy.premierleague.com/entry/<team_id>/event/7
   ```

---

#### 🧠 Get your Groq API keys
Sign up and generate API keys at:  
👉 [https://console.groq.com/keys](https://console.groq.com/keys)

You can create two separate Groq accounts:
- one for **Free Tier** usage, and  
- one for **Developer (Pay-as-you-go)** usage.  

Use their respective API keys for `GROQ_API_KEY_FREE` and `GROQ_API_KEY_PAID`.

> **Note:** The paid (Developer) tier is billed per token used, but you can cancel anytime. (Always check GROQ's website)
> The app will always try to use your free tier first before switching to the paid one when needed (e.g., for large prompts or heavy requests).  
