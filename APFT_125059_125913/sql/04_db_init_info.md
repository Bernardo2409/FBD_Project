# Populating Database with Real Champions League Data

## 📋 Overview

This project uses **Football-Data.org API** (used by Native Stats) - a **100% FREE** API to populate the database with real UEFA Champions League data.

## ✅ Why Football-Data.org?

- **✓ 100% FREE** - No payment required
- **✓ No daily limits** - 10 requests/minute (more than enough)
- **✓ Champions League data** - Teams, players, matches, results
- **✓ Current season** - 2024/25 data
- **✓ Official data** - Accurate and up-to-date
- **✓ Easy to use** - Simple REST API

## 🚀 Setup Instructions

### 1. Get API Key (FREE)

1. Visit [Football-Data.org Registration](https://www.football-data.org/client/register)
2. Fill in your email and choose a password
3. Verify your email
4. Log in and copy your API key from your profile

**Important**: The free tier is more than sufficient for this project!

### 2. Install Dependencies

```bash
pip install requests python-dotenv pyodbc
```

**Required packages**:
- `requests` - HTTP requests to API
- `python-dotenv` - Load environment variables from .env
- `pyodbc` - Connect to SQL Server database

### 3. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```env
   FOOTBALL_DATA_KEY=your_actual_api_key_from_football_data_org
   DB_SERVER=localhost
   DB_NAME=FantasyChamp
   DB_USER=sa
   DB_PASSWORD=your_db_password
   ```

## 🎯 Running the Script

```bash
python populate_db.py
```

### What the Script Does:

1. ✅ Connects to Football-Data.org API and your database
2. 🧹 Optionally cleans existing game data (preserves users and leagues)
3. 📥 Fetches all UEFA Champions League 2024/25 teams
4. 👥 Fetches squad/player data for each team
5. ⚽ Fetches all match results and fixtures
6. 💾 Inserts everything into your database

## 📊 Data Inserted

### Teams
- All 36 Champions League 2024/25 participating teams
- Team names, crests/logos
- Team IDs

### Players
- **All squad players** for every team
- Player names
- Positions (Goalkeeper, Defender, Midfielder, Forward)
- Auto-generated player avatars
- Random prices (3.0-15.0M€) - can be customized
- Default status: Active

### Matches
- All fixtures and results for the season
- Match scores (home/away goals)
- Matchdays and stages
- Round information

### NOT Deleted
- ✅ User accounts (preserved)
- ✅ Fantasy leagues (preserved)
- ✅ User fantasy teams (preserved)

## ⏱️ Execution Time

**Approximate time**: 10-15 minutes
- ~36 teams = 36 requests
- ~36 team squads = 36 requests
- ~1 competition info = 1 request
- ~1 all matches = 1 request
- **Total**: ~74 requests

With 10 requests/minute = ~8 minutes of API calls + processing time

## 🔧 Customization

### Change Season

Edit `populate_db.py` line 27:
```python
SEASON = 2025  # Change to 2023, 2025, etc.
```

### Adjust Player Prices

The script currently uses random prices (3.0-15.0M€). To improve this, edit the `insert_player` method in `DatabaseManager` class (around line 248):

```python
# Example: Base price on position
position_prices = {
    'Goalkeeper': (4.0, 8.0),
    'Defender': (4.0, 10.0),
    'Midfielder': (5.0, 12.0),
    'Forward': (6.0, 15.0)
}
min_price, max_price = position_prices.get(position_name, (3.0, 15.0))
price = round(random.uniform(min_price, max_price), 1)
```

### Add Player Photos

Football-Data.org doesn't provide player photos. Currently using avatar placeholders. To add real photos:

1. Use another API like TheSportsDB (free)
2. Manually scrape from team websites
3. Use a paid service

## 🆘 Troubleshooting

### "FOOTBALL_DATA_KEY not found"
- ✅ Ensure `.env` file exists in project root folder
- ✅ Check the key name is exactly `FOOTBALL_DATA_KEY` (case-sensitive)
- ✅ No spaces around the `=` sign

### "Database connection failed"
- ✅ Verify SQL Server is running
- ✅ Check credentials in `.env` are correct
- ✅ Ensure ODBC Driver 17 for SQL Server is installed
- ✅ Try using Windows Authentication instead

### "Error 403: Forbidden"
- ✅ Check API key is correct
- ✅ Verify email on Football-Data.org was confirmed

### "Error 429: Too Many Requests"
- The script handles this automatically
- Waits 60 seconds and retries
- Should rarely happen with current delay

### No Players Inserted
- Some teams might not have squad data available yet
- Check if season is current/valid
- Try an older season (e.g., 2023)

## 📝 Example Output

```
======================================================================
UEFA Champions League Data Population Script
Using Football-Data.org API (100% FREE)
======================================================================

⚠️  Clean existing game data? (y/n): y

🧹 Cleaning existing game data...
  ✓ Cleared FantasyChamp.Pertence
  ✓ Cleared FantasyChamp.Equipa
  ...
✓ Data cleanup complete

📥 Fetching Champions League information...
✓ Competition: UEFA Champions League
   Current season: 2024-09-17 to 2025-05-31

📥 Fetching Champions League teams (Season 2024)...
✓ Found 36 teams

💾 Inserting teams...
  ✓ Team: Real Madrid CF
  ✓ Team: FC Barcelona
  ...

👥 Fetching players...
[1/36] Real Madrid CF:
  ✓ Inserted 28 players
[2/36] FC Barcelona:
  ✓ Inserted 25 players
...

✓ Total players inserted: 892

⚽ Fetching matches...
✓ Found 189 matches

💾 Inserting matches...
✓ Inserted 189 matches

======================================================================
✅ DATA POPULATION COMPLETE!
======================================================================
Teams: 36
Players: 892
Matches: 189
API Requests used: 74
======================================================================
```

## 🔗 Useful Links

- [Football-Data.org Homepage](https://www.football-data.org/)
- [API Documentation](https://docs.football-data.org/)
- [Register for Free API Key](https://www.football-data.org/client/register)
- [API Coverage](https://www.football-data.org/coverage)
- [Native Stats](https://native-stats.org/) - Built on this API

## 💡 Next Steps

After populating the database:

1. ✅ Verify data in SQL Server Management Studio
2. ✅ Test your fantasy app with real data
3. ✅ Customize player prices if needed
4. ✅ Add player photos if desired
5. ✅ Set up automatic updates for match results

## 🎯 Comparison: Football-Data.org vs API-Football

| Feature | Football-Data.org | API-Football |
|---------|-------------------|--------------|
| **Price** | 100% FREE | Free tier: 100 req/day |
| **Rate Limit** | 10 requests/min | 100 requests/day |
| **Champions League** | ✅ Yes | ✅ Yes |
| **Player Photos** | ❌ No | ✅ Yes |
| **Squad Data** | ✅ Yes | ✅ Yes |
| **Match Results** | ✅ Yes | ✅ Yes |
| **Best For** | **This project!** | Apps needing photos |

**Verdict**: Football-Data.org is perfect for your academic project! 🎓
