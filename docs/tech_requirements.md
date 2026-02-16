# dekomposit - Gain new lexicon -> revise -> repeat.


## Why?
A usual all-in-one learning vocab service with an unusual approach.
When you learn new words it's good to use several ways, like listening,
reading, speaking, writing. To make it easier, dekomposit
provides you with different tools and methods to learn -
from hand-writing to watching short animations and reading dialogues.

dekomposit is available as a **Telegram AI agent** and a **web platform**.
The Telegram bot is the primary interface for quick, conversational learning
on the go. The web platform provides a richer experience for reading,
vocabulary management, and extended learning sessions.


## Platforms

### Telegram AI Agent
The Telegram bot is the core interface for dekomposit. It acts as a personal
language coach that users interact with conversationally. Key capabilities:
- Translate words and phrases on demand
- Deliver daily vocabulary packs via scheduled messages
- Run interactive dialogue exercises in chat
- Quiz users on saved vocabulary
- Send reminders and track streaks
- Provide instant definitions, examples, and corrections

The bot personality and behavior are defined in `dekomposit/llm/base_prompts/SOUL.md`.

### Web Platform
The web platform extends the Telegram experience with features that benefit
from a full browser interface:
- Reading section with inline translation
- Vocabulary dashboard and progress tracking
- Paper library (Trusted Authors)
- Extended learning method sessions
- Account management and settings


## Features
### 1. Translation
There must be a translator tool which translates user input to the target language.
The translation must be decomposed into pieces for better readability and user experience.
Decomposed pieces are either phrases or single words. Decomposition must preserve idioms,
citations, and phrasal verbs as single pieces.
Translation will have three main sections:
1. Translation
2. Definitions
3. Examples

Users will have an option to choose another translation method (ReversoContext, ChatGPT etc. Next: Method).
Paid Methods are included in Dekomposer Pack (See in next sections), note that not all Methods are paid.

Along the translation there will be a pixel-art picture that is associated with word meaning.
Not all translations will have pictures.

If user's input contains mistakes, it is corrected by dekomposer and user can see a corrected version.

**Telegram**: User sends a word/phrase, bot replies with decomposed translation.
**Web**: Translation page with full layout (definitions, examples, pixel-art).

### 2. Examples
User will have access to example sentences/texts/dialogues (next Example) etc. for a specific word/phrase/topic (next: unit).
Examples will have three sections:
1. Dialogue that contains the unit
2. Texts that contain the unit (if needed)
3. Sentences with translation that contain the unit

In each Example user will have a feature to translate that Example
sentence by sentence.

**Telegram**: Bot sends examples inline after translation or on request.
**Web**: Dedicated examples panel on the translation page.

### 3. Vocabulary
User will have a vocabulary storage (next Vocab). Vocab is used to practice new lexicon
via Learning Method (see in next sections). Also dekomposer decides which examples are used
based on your language level and Vocab.

User will be able to add the word to the Vocab.

**Telegram**: Tap to save a word, use commands to review saved words.
**Web**: Full vocabulary dashboard with filters, search, and export.

### 4. Learning Method
To practice Vocab dekomposit uses this Learning Method:
1. Memorize the unit/s with translations or associated pictures (units can be grouped by a topic)
2. Start reading text/dialogue with those units (you can listen to it as well). Text/dialogue is decided by
the system randomly.
3. Write examples on your own
4. Repeat for the next portion of units or select an option to practice this portion more
5. Take a challenging test (optional)

The system can force the user to write down words in input and on paper as well.

**Telegram**: Bot guides user through steps interactively in chat.
**Web**: Structured learning session page with progress indicators.

### Today's Pack of Memorizing
It is a feature that generates 10 to 20 new units that are absent from the
user's Vocab. This pack is updated every day at 12:00 AM UTC. The pack's lexicon
topic may vary from current events like New Year, Christmas, Easter etc... but if
there are no important global events then topic may be chosen in two different
ways:
1. Randomly, according to user's Vocab
2. Most important topics that are absent in user's Vocab

The algorithm prioritizes: 1) Current Events, 2) Most important topics for your Vocab, 3) Random selection (for B2-C1 users).

**Telegram**: Daily push notification with the pack. User learns directly in chat.
**Web**: Displayed on the dashboard homepage.

### Reading
There will be a section/page in dekomposit service where users can read
books, articles, stories (next Papers) published by the Trusted Authors (See in the next sections).
Users with Dekomposer Pack may add their own Papers that won't be published and will
be stored only in user's Reading Storage.

Note: We may add a feature that user cannot copy anything from Papers so that he would type
the needed units manually for better memorization. In this case, the inline translation
tool will be absent, user will need to type the unit in a translation input above the text.

**Telegram**: Not available (web-only feature due to rich UI requirements).
**Web**: Full reading experience with inline translation.

### Reading Storage
A storage for keeping track of all read Papers and status (like Paper "Harry Potter" - 40% read, Paper N - 12% read)
Users can store their own Papers in their Reading Storage. Reading Storage is never shared across the other users
until user shares his Paper with others.

Note that when a user shares some Papers, only those Papers
will be shared. By shared it is meant getting a link which
will be available to all who have it. Users who have this link
can open the Paper.

### Inline Translator
It is a tool that is present on every Paper of the dekomposit service. It highlights
the units that can be translated into Target Language (see next sections)
by hovering on them. By pressing on the unit, the user sees the translation of the unit.

**Web-only feature**.

### Trusted Authors
Trusted Authors are those who can publish Papers globally on the dekomposit Reading
section to make this Paper available for everyone who uses this section/page.

Trusted Authors are chosen by our admins. There are no strict rules for choosing
Trusted Authors. Anyone who wants to become an author can write to our support with
a "Trusted Author" subject and we will decide whether to accept you or not.

Example of Trusted Author mail: "Subject: Trusted author
                                Dekomposit profile: <Link to your profile>
                                Reason: I'd like to publish Harry Potter and some
                                other books."

If you were approved -> You will get an answer from us and you'll get
Trusted Author Mark in your profile.

By becoming a Trusted Author you agree to the following:
1. You will not publish spam or content unrelated to the platform's purpose.
2. You will not advertise yourself, third parties, or external services.
3. You will not publish prohibited information, including content related to drugs, political propaganda, or other restricted topics.
4. You will not distribute or promote forbidden materials.
5. You will not publish papers containing incorrect grammar or poor vocabulary.

Papers that violate any of the rules above will be removed.
By violating the rules above you can be deprived of Trusted Author Status. Note that we
check each Paper before publication.

### Dialogues
Dialogues are texts generated by dekomposit according to user's Vocab and Language level.
User can explore dialogues in a Translation section (Examples section). In each sentence user has a feature to
translate text into Source Language (see next sections).

Dialogues do not appear if you're logged out.

Ideally, there would be a separate interactive dialogue page with a UI/UX similar to
AI Chat Bots. There may be different tasks. Probable tasks: correct some mistakes in replica,
fill in the gaps in replica, chat to the Dialogue.

Interactive dialogues are part of the Dekomposer Pack. Note that
user has access to more and longer dialogues with Dekomposer Pack.

**Telegram**: Interactive dialogues run natively in chat - the bot plays one speaker, the user plays the other.
**Web**: Dedicated dialogue page with chat-like UI.

### Sentences
Sentences are part of the Translation page (Examples section). Each sentence
is generated by the following algorithm:
1. If user is logged in -> Generated by dekomposit
2. If user is logged out -> Fetched from Reverso Context API

### Texts
Texts are part of the Translation page (Examples section). The difference
from Sentences is that Text is longer and has context.

### Fallback
We may switch our dekomposit generation system to others in order to improve it.
Due to technical reasons we can completely shut down the generation system
for some time - we will use Reverso API as a fallback.

### Episodes
Not described yet (soon).

### Dekomposer Pack
By subscribing to our Dekomposer Pack user gets:
1. 1,000 available requests to paid Methods
2. Access to Episodes
3. Access to Interactive Dialogues
4. Higher input limits - up to 10,000 symbols
5. High quality audio
6. More and longer dialogue examples

* Respect from us

## Tech Details
### 1. Translation
- User input limit: 1,000 symbols (logged in, nonpremium)
                    500 (logged out / Telegram anonymous)
                    10,000 (logged in, premium)

### 2. Examples
- Dialogue Limit per one Translation: 3 (logged in, nonpremium)
                                      0 (logged out)
                                      15 (logged in, premium)
- Dialogue length limit: 5 replicas (logged in, nonpremium)
                         30 replicas (logged in, premium)
- Text length limit (if generated, not fetched):
                     500 symbols (logged in, nonpremium)
                     2000 symbols (logged in, premium)
- Sentence length limit (if generated, not fetched):
                     100 symbols (logged in, nonpremium)
                     300 symbols (logged in, premium)

If user is logged out -> There are no dialogues available, Texts and sentences are
fetched from Reverso API or from other sources.

### 3. Trusted Authors
File size of the Paper is limited to 100 MB.

### 4. User & Profile
User will have the following fields:
- Username
- Email
- Telegram ID (linked when user starts the bot)

User will receive an email to pass the Login/Registration on the web platform.
Telegram users authenticate by starting the bot and optionally linking their web account.

Profile:
- Source Language (Native language of the user)
- Target Language (The language user wants to learn)
- Language Level (e.g. A2, B1)
- Vocabulary storage (Stores all saved words/phrases by user)
- Reading storage (Stores all Papers that user is reading and progress of reading for each Paper)
- Actual Language Level (Defined by LLM by rating the Vocabulary storage and user's Language Level)

Important: User's Vocab is not included in the prompt, LLM decides on it's own which words or phrases
are needed and executes a tool that checks whether there is the word/phrase in the user's Vocab.
Instead of User's Vocab, we pass to the LLM it's compressed version: labels of topics that are
present in the Vocab.

### 5. Telegram Bot Architecture
- Built with aiogram (async Telegram bot framework)
- Shares the same backend services as the web platform
- Bot commands: /start, /translate, /vocab, /daily, /level, /settings, /help
- Inline mode support for quick translations in any chat
- Callback queries for interactive exercises and vocabulary saving
- Scheduled tasks for daily packs and streak reminders

### 6. Web Platform Architecture
- Backend: FastAPI
- Frontend: HTML, CSS, JavaScript (htmx)
- Database: PostgreSQL + SQLAlchemy
- Shared service layer with Telegram bot

### Costs & Profits
All costs = ~$25/mo
Subscription plan price = $5/mo
Profit in ~7 subscribed users
