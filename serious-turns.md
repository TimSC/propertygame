# Serious Monopoly: validation worksheet

**Video:** *Monopoly, But SERIOUS* (No Rolls Barred). https://www.youtube.com/watch?v=cDmxXT2o9sE
**Replayed by:** `CheckSeriousGameplay` in `test.py`. Its row numbers match the `#` column below.

## Setup

- **Board:** UK (`property-board-uk.txt`) with the modern UK card decks. The flavour text on the cards is new, but they behave like the standard cards (see *Cards* below).
- **Players:** three, numbered 1–3 in turn order. Player 3 rolled the 9 and starts. A dealer acts as banker and doesn't take turns.
- **Starting money:** 1500 each. The replay confirms this: every balance matches.
- **Dice:** where only a total was visible (rows 7, 10, 14, 30, 84), the replay uses a pair that isn't a double.

## Game turns

| # | Time | Player | Dice | Lands on | What happens | Notes |
|---|------|--------|------|----------|--------------|-------|
| 1 | 00:00:13 | all | 7, 8, 9 | – | Roll for first turn. Player 3 rolls the 9 | Not recorded who rolled the 7 and the 8 |
| 2 | 00:00:39 | 3 | 1,3 | 4 Income Tax | Pays 200 | |
| 3 | 00:01:03 | 1 | 1,5 | 6 The Angel Islington | Buys for 100 | |
| 4 | 00:01:16 | 2 | 4,2 | 6 The Angel Islington | Pays player 1 rent of 6 | |
| 5 | 00:02:22 | 3 | 6,1 | 11 Pall Mall | Buys for 140 | |
| 6 | 00:02:22 | 1 | 6,2 | 14 Northumberland Avenue | Buys for 160 | |
| 7 | 00:02:46 | 2 | 7 | 13 Whitehall | Declines; auction won by player 2 for 145 | |
| 8 | 00:04:51 | 3 | 5,6 | 22 Chance | Get Out of Jail Free, kept for later | |
| 9 | 00:05:29 | 1 | 5,4 | 23 Fleet Street | Buys for 220 | |
| 10 | 00:05:59 | 2 | 8 | 21 Strand | Buys for 220 | |
| 11 | 00:06:16 | 3 | 6,4 | 32 Oxford Street | Buys for 300 | |
| 12 | 00:06:56 | 1 | 6,3 | 32 Oxford Street | Pays player 3 rent of 26 | |
| 13 | 00:07:26 | 2 | 1,2 | 24 Trafalgar Square | Buys for 240 | |
| 14 | 00:07:55 | 3 | 11 | 3 Whitechapel Road | Passes Go (+200), buys for 60 | |
| 15 | 00:08:19 | 1 | 1,4 | 37 Park Lane | Buys for 350 | |
| 16 | 00:09:08 | 2 ↔ 1 | – | – | **Trade:** player 2 gives Whitehall + 50; player 1 gives Fleet Street | Player 2 completes the reds |
| 17 | ~00:10:50 | 2 | – | – | Buys 1 house on the reds (150), placed on 24 Trafalgar Square | Row 37's rent confirms the placement |
| 18 | 00:11:18 | 2 | 5,1 | 30 Go To Jail | Goes to jail | |
| 19 | 00:11:48 | 3 | 6,2 | 11 Pall Mall | Own property | |
| 20 | 00:11:48 | 1 | 1,3 | 1 Old Kent Road | Passes Go (+200), buys for 60 | |
| 21 | 00:12:44 | 2 | 2,2 | 14 Northumberland Avenue | Rolls a double to leave jail; pays player 1 rent of 12 | No second roll after leaving jail on a double, which is correct |
| 22 | 00:13:18 | 3 | 1,1 then 6,1 | 13 Whitehall, then 20 Free Parking | Pays player 1 rent of 10; rolls again for the double | Single rent: pink isn't complete, as player 3 owns Pall Mall |
| 23 | 00:13:54 | 1 | 1,2 | 4 Income Tax | Pays 200 | |
| 24 | 00:14:41 | 2 | 6,4 | 24 Trafalgar Square | Own property | |
| 25 | 00:14:41 | 3 | 1,1 then 6,1 | 22 Chance → 11 Pall Mall, then 18 Marlborough Street | Chance: advance to Pall Mall, passing Go (+200). Rolls again for the double; buys Marlborough Street for 180 | Doubles still give another roll after a card move |
| 26 | 00:15:21 | 1 | 1,2 | 7 Chance → 39 Mayfair | Chance: advance to Mayfair; buys for 400 | Player 1 completes the dark blues |
| 27 | 00:16:21 | 2 | 5,4 | 33 Community Chest | "Helped your neighbours after a storm": +200 | Bank error card |
| 28 | 00:16:42 | 3 | 6,3 | 27 Coventry Street | Buys for 260 | |
| 29 | 00:17:01 | 1 | 6,2 | 7 Chance | Passes Go (+200). Chance: building loan matures (+150) | |
| 30 | 00:17:39 | 2 | 6 | 39 Mayfair | Pays player 1 rent of 100 | Double rent: unimproved in a full set |
| 31 | 00:18:12 | 3 | 5,2 | 34 Bond Street | Buys for 320 | |
| 32 | 00:18:46 | 1 | 4,1 | 12 Electric Company | Buys for 150 | |
| 33 | 00:19:08 | 2 | 6,4 | 9 Pentonville Road | Passes Go (+200), buys for 120 | |
| 34 | 00:19:41 | 3 | 1,3 | 38 Super Tax | Pays 100 | |
| 35 | 00:19:58 | 1 → 3 | – | – | **Trade proposed**, counter-offered, rejected | No effect |
| 36 | ~00:21 | 1 | – | – | Buys 1 house on the dark blues (200), placed on 39 Mayfair | |
| 37 | 00:21:53 | 1 | 6,4 | 22 Chance → 24 Trafalgar Square | Chance: advance to Trafalgar Square; pays player 2 rent of 100 | Doesn't pass Go. Rent for 1 house |
| 38 | ~00:22 | 2 | – | – | Buys a second red house (150), placed on 23 Fleet Street | |
| 39 | 00:23:26 | 2 | 4,4 then 6,4 | 17 Community Chest, then 27 Coventry Street | "Helped your neighbour with her shopping": +20. Rolls again for the double; pays player 3 rent of 22 | Income tax refund card |
| 40 | 00:24:15 | 3 | 6,5 | 9 Pentonville Road | Passes Go (+200); pays player 2 rent of 8 | |
| 41 | 00:25:06 | 1 | 6,3 | 33 Community Chest → 0 Go | "Sponsored run": advance to Go (+200) | 200 is paid once only, not also for landing |
| 42 | 00:26:02 | 2 | 6,3 | 36 Chance | Chairperson of the board: pays each player 50 | |
| 43 | 00:26:45 | 3 | 3,2 | 14 Northumberland Avenue | Pays player 1 rent of 12 | The transcript's "24. No. 12." was right to settle on 12: the set isn't complete |
| 44 | 00:27:00 | 1 | 6,4 | 10 Just Visiting | | |
| 45 | 00:27:30 | 2 | 6,2 | 4 Income Tax | Passes Go (+200), pays 200 | |
| 46 | 00:27:57 | 3 | 4,3 | 21 Strand | Pays player 2 rent of 36 | Double rent: unimproved in a full set, even though Fleet Street and Trafalgar Square have houses |
| 47 | 00:28:24 | 1 | 4,2 | 16 Bow Street | Declines; auction won by player 3 for 193 | |
| 48 | 00:30:47 | 2 | 4,2 | 10 Just Visiting | | |
| 49 | 00:31:00 | 3 | 4,1 | 26 Leicester Square | Buys for 260 | |
| 50 | 00:31:19 | 1 | 4,2 | 22 Chance → 19 Vine Street | Chance: go back 3 spaces; buys Vine Street for 200 | |
| 51 | 00:32:12 | 2 | 6,2 | 18 Marlborough Street | Pays player 3 rent of 14 | |
| 52 | 00:32:33 | 1 ↔ 3 | – | – | **Trade:** player 1 gives Vine Street; player 3 gives Pall Mall | Player 3 completes orange, player 1 completes pink. |
| 53 | 00:33:50 | 3 | 6,2 | 34 Bond Street | Own property | |
| 54 | 00:34:33 | 1 | 5,1 | 25 Fenchurch Street Station | Buys for 200 | |
| 55 | 00:35:04 | 2 | 5,1 | 24 Trafalgar Square | Own property | |
| 56 | 00:35:04 | 3 | 5,3 | 2 Community Chest | Passes Go (+200). "Blasting music late at night": go to jail | |
| 57 | 00:35:14 | 3 | – | – | Buys 2 houses on orange (200), placed on 16 Bow Street and 19 Vine Street | Legal, but not the engine's choice, so the test moves one house marker by hand |
| 58 | 00:36:01 | 1 | 5,1 | 31 Regent Street | Can't afford 300, so it goes to auction | Deliberate rule deviation: no sale. Replay: nobody bids, and it stays unowned |
| 59 | 00:37:53 | 2 | 2,4 | 30 Go To Jail | Goes to jail | |
| 60 | 00:37:53 | 3 | 6,3 | 10 → 19 Vine Street | Uses Get Out of Jail Free; own property | The video uses the card when sent to jail. Under the rules it's used at the start of the next turn, which gives the same result. The card goes back to the Chance deck |
| 61 | 00:37:53 | 1 | 5,1 | 37 Park Lane | Own property | |
| 62 | 00:39:12 | 2 | 6,6 | 22 Chance | Rolls a double to leave jail. "You fought a swan and lost": pays 15 | Speeding fine card. No extra roll |
| 63 | 00:40:03 | 3 | 6,2 | 27 Coventry Street | Own property | |
| 64 | 00:40:20 | 1 | 5,1 | 3 Whitechapel Road | Passes Go (+200); pays player 3 rent of 4 | |
| 65 | 00:40:20 | 2 | 5,3 | 30 Go To Jail | Goes to jail | |
| 66 | 00:41:20 | 3 | 5,3 | 35 Liverpool Street Station | Can't afford 200; auction won by player 1 for 160 | Player 2 may bid from jail |
| 67 | 00:43:18 | 1 | 4,2 | 9 Pentonville Road | Pays player 2 rent of 8 | Owners in jail still collect rent |
| 68 | 00:43:52 | 2 | 5,6 | (in jail) | First failed roll | |
| 69 | 00:44:38 | 3 | 1,2 | 38 Super Tax | Pays 100 | |
| 70 | 00:45:19 | 1 | 6,3 | 18 Marlborough Street | Pays player 3 rent of 28 | Double rent: Marlborough has no house, which confirms row 57's placement |
| 71 | 00:45:58 | 2 | 6,4 | (in jail) | Second failed roll | |
| 72 | 00:46:35 | 3 | 6,6 then 4,2 | 10 Just Visiting, then 16 Bow Street | Passes Go (+200); own property | |
| 73 | 00:46:35 | 3 | – | – | Buys 2 houses on orange (200) | The video goes to Bow 2 / Marlborough 0 / Vine 2, which is uneven. Replay: Bow 1 / Marlborough 1 / Vine 2. **Orange rents differ from here on** |
| 74 | 00:47:12 | 1 | 5,3 | 26 Leicester Square | Pays player 3 rent of 22 | |
| 75 | 00:47:29 | 2 | 1,2 | (in jail) | Third failed roll: pays 50 and is released | The video doesn't move them. Under the rules they'd move 3 to 13 Whitehall and pay player 1 rent of 20 (full pink set). The replay follows the video |
| 76 | 00:48:35 | 3 | 6,6 then 6,1 | 28 Water Works, then 35 Liverpool Street Station | Can't afford Water Works (goes to auction); rolls again for the double; pays player 1 rent of 50 (2 stations) | Deliberate rule deviation, no sale. Replay: nobody bids |
| 77 | 00:53:11 | 1 | 5,4 | 35 Liverpool Street Station | Own property | |
| 78 | 00:53:55 | 2 | 4,2 | 16 Bow Street | Pays player 3 rent | (wrong rent due to invalid placement) Video: 2 houses, 200. Replay: 1 house, **70** |
| 79 | 00:53:55 | 3 | 6,3 | 4 Income Tax | Passes Go (+200), pays 200 | |
| 80 | 00:54:34 | 1 | 5,2 | 2 Community Chest | Passes Go (+200). "Street party": 10 from each player | Birthday card |
| 81 | 00:54:50 | 2 | 2,1 | 19 Vine Street | Pays player 3 rent of 220 | 2 houses in both the video and the replay |
| 82 | 00:55:00 | 3 | – | – | Buys 4 more buildings on orange (400) | Video: 2 houses on Bow, then a hotel on Bow, then 1 house on Marlborough. A hotel needs 4 houses on every property in the group. Replay: Bow 2 / Marlborough 3 / Vine 3, and player 3 is **topped up by 83** because the replay's rents were lower. Player 3 forgets to take a turn. |
| 84 | 00:57:10 | 1 | 7 | 9 Pentonville Road | Pays player 2 rent of 8 | |
| 85 | 01:00:23 | 2 | 3,2 | 24 Trafalgar Square | Own property | |
| 86 | 01:00:23 | 2 | – | – | Buys a third red house (150), placed on 21 Strand | |
| 87 | 01:00:23 | 3 | 4,2 | 10 Just Visiting | | |
| 88 | 01:00:23 | 1 | 6,4 | 19 Vine Street | Pays player 3 rent | (wrong rent due to invalid placement) Video: 2 houses, 220. Replay: 3 houses, **600**, with player 1 **topped up by 236** so they can pay |
| 89 | 01:00:23 | 2 | 3,4 | 31 Regent Street | Eliminated | Deliberate rule deviation, player 2 eliminated. Replay: Regent Street is unowned and nobody bids, then player 2 goes bankrupt to the bank and their property goes unsold |
| 90 | 01:04:12 | 3 | 6,1 | 17 Community Chest | "You helped a puppy": Get Out of Jail Free | |
| 91 | 01:04:12 | 3 | – | – | Buys 2 more houses on orange (200) | (invalid placement) Video: both on Vine Street. Replay: Bow 3 / Marlborough 3 / Vine 4 |
| 92 | 01:05:20 | 1 | 5,3 | 27 Coventry Street | Pays player 3 rent of 22 | Player 1 is **topped up by 22**, having been emptied at row 88. |

## Notes

**Rules the video confirmed in the engine**
- Double rent on an unimproved property when the owner has the full set, even if other properties in the set have houses (rows 30, 46, 70).
- Rent is collected by an owner who is in jail (row 67). Players in jail can bid at auction (row 66).
- Leaving jail on a double gives no second roll (rows 21, 62). This isn't a missed turn: the rules say "even though you had thrown doubles, you do not take another turn". After the third failed roll, the player must pay 50 (row 75).
- Every other double gets its extra roll (rows 22, 25, 39, 72, 76), including after a Chance move (row 25). Rows 10 and 30 only record totals (8 and 6). If either was a double (4,4 or 3,3), that extra roll was missed, and the replay can't detect it. Advance to Go pays 200 once (row 41).
- Auctions: whoever declines, or can't afford, the property, every player can still bid (rows 7, 47, 66).

**Rule deviations and how the replay handles them**

| Rows | Deviation | Replay |
|---|---|---|
| 73, 82, 91 | Uneven building on orange, including a hotel with too few houses | Legal placement, so orange rents differ (rows 78, 88) |
| 75 | Third failed jail roll: pays but doesn't move | Forced: released without moving |
| 83 | Player 3 misses a turn | Forced |
| 82, 88, 92 | – | Cash top-ups of 83, 236 and 22, to keep players in the game after the orange rents diverge |

**Engine issues this replay found:** `MortgageSpace` allowed a property to be mortgaged twice, which is now fixed. `BuildBuildings` can't take the owner's choice of placement within the even-building rule (row 57).

**Cards seen:** Get Out of Jail Free (rows 8, 90); advance to Pall Mall (25), Mayfair (26) and Trafalgar Square (37); building loan matures (29); chairperson (42); go back 3 spaces (50); go to jail (56); speeding fine (62). Community Chest: bank error (27), income tax refund (39), advance to Go (41), birthday (80).
