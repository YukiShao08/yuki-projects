# Multi-Round Conversation Guide

## ✅ What Was Fixed

Your AI assistant now supports **multi-round conversations**! Here's what was changed:

### 1. **Conversation History Loading**
- The backend now loads previous messages from the database when `chat_id` is provided
- Previous user and assistant messages are included in the conversation context
- This allows the AI to remember and reference earlier parts of the conversation

### 2. **Message Storage**
- Assistant responses are now saved with role `"assistant"` (was incorrectly `"tool calls"`)
- Both user and assistant messages are properly stored in the database
- Messages are saved in chronological order

### 3. **Chat ID Tracking**
- The API now returns `chat_id` in the response
- The frontend tracks `currentChatId` and sends it with subsequent messages
- This links all messages in a conversation together

---

## 🧪 How to Test Multi-Round Conversations

### Scenario 1: Follow-up Questions
1. **First Message**: "What is the interest rate for savings accounts?"
2. **Second Message**: "What about for fixed deposits?" (AI should remember you're asking about banking)
3. **Third Message**: "Can you compare them?" (AI should remember both previous topics)

### Scenario 2: Contextual References
1. **First Message**: "I'm looking for a mortgage"
2. **Second Message**: "What documents do I need?" (AI knows you're asking about mortgage documents)
3. **Third Message**: "How long does it take?" (AI knows you're asking about mortgage processing time)

### Scenario 3: Clarification
1. **First Message**: "Tell me about loans"
2. **Second Message**: "I mean personal loans specifically" (AI should clarify based on context)
3. **Third Message**: "What's the minimum amount?" (AI knows you're asking about personal loans)

---

## 🔍 How It Works

### Flow Diagram:
```
User sends message
    ↓
Frontend checks if currentChatId exists
    ↓
If exists: Send chat_id with request
If not: Create new conversation
    ↓
Backend receives request
    ↓
If chat_id provided:
    → Load previous messages from database
    → Add to conversation context
    ↓
Add current user message
    ↓
Save user message to database
    ↓
Send to AI with full conversation history
    ↓
AI responds with context awareness
    ↓
Save assistant response to database
    ↓
Return response + chat_id to frontend
    ↓
Frontend updates currentChatId
    ↓
Next message uses same chat_id → Multi-round conversation!
```

---

## 📊 Database Structure

Messages are stored in `chatbot_db.dbo.chat_messages`:
- `chat_id`: Links messages in the same conversation
- `role`: "user" or "assistant"
- `content`: The message text
- `created_at`: Timestamp

Example:
```
chat_id: "1234567890"
Messages:
  1. role: "user", content: "What is a savings account?"
  2. role: "assistant", content: "A savings account is..."
  3. role: "user", content: "What's the interest rate?"
  4. role: "assistant", content: "The interest rate is..."
```

---

## 🎯 Key Features

### ✅ What Works Now:
- ✅ Multi-round conversations with context
- ✅ Follow-up questions
- ✅ References to previous messages
- ✅ Conversation history persistence
- ✅ Chat ID tracking across messages

### ⚠️ Limitations:
- Each conversation is independent (different `chat_id` = new conversation)
- No automatic conversation timeout/cleanup
- Maximum context length depends on AI model (typically 4K-8K tokens)

---

## 🐛 Troubleshooting

### Issue: AI doesn't remember previous messages
**Check:**
1. Is `chat_id` being sent with requests? (Check browser console)
2. Are messages being saved? (Check database)
3. Are previous messages being loaded? (Check server logs for "📜 Loading X previous messages")

### Issue: Duplicate messages
**Fixed!** Messages are now loaded before saving the current one to avoid duplicates.

### Issue: Wrong conversation context
**Check:**
1. Is `currentChatId` being maintained in the frontend?
2. Are you starting a new chat (which creates a new `chat_id`)?

---

## 📝 Code Changes Summary

### Backend (`main.py`):
1. **Load conversation history** before processing new message
2. **Save assistant responses** with role `"assistant"` (not `"tool calls"`)
3. **Return `chat_id`** in API response
4. **Filter messages** to only include "user" and "assistant" roles

### Frontend (`script.js`):
- Already tracks `currentChatId` ✅
- Already sends `chat_id` with requests ✅
- Already updates `currentChatId` from response ✅

---

## 🚀 Next Steps

Your multi-round conversation feature is now **fully functional**! 

Try it out:
1. Start a conversation
2. Ask a follow-up question
3. Reference something from earlier
4. The AI should remember and respond contextually!


