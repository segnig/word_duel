# Word Duel — Game Design Document

## 1. Overview

**Word Duel** is a two-player word-guessing game played in a Telegram group chat.

Each player secretly picks a word of an agreed length (default: 5 letters). Neither
player knows the other's word. Players then take turns guessing the *opponent's*
word. After each guess, the guesser receives Wordle-style feedback (per-letter
color hints) about how close the guess is. The first player to correctly guess
the opponent's word wins.

This is effectively "Wordle, but your opponent set the puzzle" — played
head-to-head instead of against a fixed daily word.

## 2. Core Rules

1. **Setup phase**
   - Both players agree on (or are assigned) a word length — default **5 letters**.
   - Each player privately submits a secret word of that exact length via a
     direct/private message to the bot (never posted in the group), so the
     opponent cannot see it.
   - The game does not start until both secret words are submitted.

2. **Guessing phase**
   - Turn order alternates strictly: Player A guesses, then Player B, then
     Player A, and so on.
   - On their turn, a player submits a guess word of the same length, targeting
     the *opponent's* secret word.
   - The bot evaluates the guess against the opponent's secret word and returns
     per-letter feedback to the whole group (the guess and its feedback are
     public — only the secret words stay hidden).

3. **Feedback (Wordle-style)**
   For each letter in the guess, compared to the opponent's secret word:
   - 🟩 **Green** — letter is correct and in the correct position.
   - 🟨 **Yellow** — letter exists in the secret word but in a different position.
   - ⬜ **Gray** — letter does not appear in the secret word (or all its
     occurrences are already accounted for — see 2a below).

   **2a. Duplicate-letter handling** (standard Wordle rule): if a letter
   appears more times in the guess than in the secret word, only that many
   occurrences are marked green/yellow; the rest are gray. Greens are resolved
   first, then yellows are assigned to remaining letter counts.

4. **Winning**
   - Players always get the **same number of guesses**. If player A finds the
     word first, player B still gets one more guess to match that count.
   - If only one player has the word after equal guesses, that player wins.
   - If both find the word in the same number of guesses, it is a **draw**.
   - If both use all guesses (default 10 each) with no correct word, it is a
     **draw**, and both secret words are revealed.
   - Each player may ask for a **hint** at most **twice**. A hint privately
     reveals one still-unknown letter of the opponent's word.

## 3. Game Flow (State Machine)

```
IDLE
  │  /newduel
  ▼
SETUP (waiting for both secret words, via private message to bot)
  │  both secret words submitted
  ▼
IN_PROGRESS (alternating guesses, public feedback in group)
  │
  ├─ exact match on a guess → FINISHED (winner declared)
  ├─ max rounds reached, no winner → FINISHED (draw, words revealed)
  └─ a player quits/times out → FINISHED (forfeit)
```

| State         | Description                                                        |
|---------------|---------------------------------------------------------------------|
| `IDLE`        | No active game in this chat.                                       |
| `SETUP`       | Game created; waiting on one or both secret words.                 |
| `IN_PROGRESS` | Both words set; players alternate guesses.                         |
| `FINISHED`    | Win, draw, or forfeit reached; words revealed; game can be restarted.|

## 4. Word Validation Rules

- Secret words and guesses must be exactly the agreed length (letters only,
  no digits/symbols).
- Recommend validating against a dictionary word list to prevent nonsense
  strings (e.g. "ZZZZZ") — both for secret word submission and for guesses.
  This should be configurable (strict dictionary vs. "anything goes") since
  strict validation needs a word list for the target length.
- Case-insensitive matching (normalize to uppercase internally).
- A player cannot change their secret word once submitted and the opponent
  has also submitted (i.e., once the game enters `IN_PROGRESS`).

## 5. Telegram Bot Interaction Design

Because secret words must stay hidden from the opponent, this game **needs
private messages**, unlike the group-only Tic-Tac-Toe bot. Recommended flow:

| Step | Where | Action |
|---|---|---|
| 1 | Group chat | Player runs `/newduel` — bot posts an invite with a "Join" button. |
| 2 | Group chat | Second player taps "Join". |
| 3 | Bot → both players (DM) | Bot messages each player privately: "Send me your secret 5-letter word." *(Requires the player to have started a private chat with the bot at least once — Telegram bots cannot DM a user who hasn't initiated contact.)* |
| 4 | Private chat | Each player sends their secret word directly to the bot. |
| 5 | Group chat | Once both are in, bot announces the game has started and whose turn it is. |
| 6 | Group chat | Active player sends their guess (as a message or via `/guess WORD`). |
| 7 | Group chat | Bot posts the guess with color-coded feedback, then announces the next player's turn. |
| 8 | Group chat | Repeat until a win, draw, or forfeit. Bot reveals both secret words at the end. |

**Fallback for step 3:** if a player hasn't messaged the bot privately before,
the bot can't initiate a DM. In that case, the bot posts a message in the
group with a deep link (`t.me/<botusername>?start=duel_<game_id>`) prompting
the player to tap it, which opens a private chat and lets the bot proceed.

## 6. Data Model (per active game)

```
Game {
  chat_id
  status: SETUP | IN_PROGRESS | FINISHED
  word_length: int (default 5)
  max_rounds: int (default 10)
  players: {
    A: { user_id, name, secret_word, guesses_made: int },
    B: { user_id, name, secret_word, guesses_made: int }
  }
  turn: "A" | "B"
  history: [ { player, guess, feedback } ]   # feedback = list of "green"/"yellow"/"gray"
  winner: "A" | "B" | "draw" | null
}
```

## 7. Example Round (5-letter words)

- Player A's secret word (hidden): `CRANE`
- Player B's secret word (hidden): `MOUSE`

Turn 1 — Player A guesses `HOUSE` (targeting B's word `MOUSE`):
```
H O U S E
⬜🟩🟩🟩🟩
```
(H is not in MOUSE; O, U, S, E all correct position.)

Turn 2 — Player B guesses `CRATE` (targeting A's word `CRANE`):
```
C R A T E
🟩🟩🟩⬜🟩
```
(T is not in CRANE; everything else matches.)

Play continues until someone guesses the exact word.

## 8. Open Design Questions (for you to decide before implementation)

- **Word length:** always 5, or configurable per game (e.g. `/newduel 6`)?
- **Dictionary enforcement:** strict valid-word-only, or allow any letter string?
- **Guess visibility:** should past guesses/feedback stay visible in the group
  as a running log (recommended), or should the bot delete/edit older ones?
- **Timeouts:** what happens if a player goes silent mid-game — auto-forfeit
  after N minutes?
- **Rematch:** offer a "Play again" button reusing the same two players?

## 9. Next Step

Once you confirm the open questions in Section 8, I'll implement this as a
Python (python-telegram-bot) bot, following the same structure as the
Tic-Tac-Toe bot but adding private-message handling for secret word
submission.
