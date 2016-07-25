Command list for BotDooder. Note that spaces will separate arguments, so to prevent strings with spaces from being split incorrectly, enclose them in quotation marks (ex. `!playtime "DOTA 2"`)

**General**
`!help`: Display this message.

**Game Tracker**

`!playtime <user_or_game> [since_date] [until_date]`: Display the playtime for a user or particular game, optionally from `since_date` to `until_date`.

**Dice Roller**

`!roll <max>`: Roll a `max`-sided dice. (Default: max=100)
`!roll <max>x<dice>`: Roll `dice` number of `max`-sided dice.

**Dota Casino**

`!livegames`: Display the currently-airing live league games.
`!bet <amount> <team_name>`: Bet `amount` of imaginary currency on `team_name` to win their match. FP is awarded or deducted upon the match's conclusion. Once a bet has been made, you cannot bet on the opposing team or lower your bet amount.
`!fp`: Display your current amount of currency.
`!leaderboard`: Display the leaderboard for the server.