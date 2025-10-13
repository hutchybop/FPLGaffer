# 🧠 FPLGaffer

**FPLGaffer** is a Python-based Fantasy Premier League (FPL) assistant that helps you rate all players, review your current team, and discover the best transfer replacements — all with optional AI-powered suggestions using **Groq** and the **Qwen3-32B** model.

---

## ⚽ Features

✅ **Rate All FPL Players**  
- Computes a normalized performance rating (0–100) for every player in the FPL database.  

✅ **Display Current Team**  
- Fetches your FPL team and prints it in an easy-to-read table view.

✅ **Suggest Best Replacements**  
- For a user-specified number of team players (up to 6), suggests **4 top replacements** based on normalized ratings and stats.  

✅ **AI Transfer Recommendations (Optional)**  
- Uses **Groq’s Qwen3-32B** model to provide intelligent transfer advice based on player data and team balance.

✅ **Game Week report text file creatation**  
- As well as printing to the terminal, a game week report is created in the current directory. (See included Example_GW_report.txt) 

---

## ⚙️ Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/FPLGaffer.git
cd FPLGaffer
```

### 2. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Update required global packages (recommended)
pip install --upgrade pip setuptools wheel
# Installed required app packages
pip install -r requirements.txt
```

### 4. Create a `.env` File
Create a `.env` file in the project root and add the following (See included .envexample):

```bash
FPL_TEAM_ID=YOUR_FPL_TEAM_ID
GROQ_API_KEY=YOUR_GROQ_API_KEY
```

#### How to find your `FPL_TEAM_ID`
1. Log in to your FPL account.  
2. Go to **"Points"** or your team page.  
3. Look at the URL — your ID is the number shown here:  
   ```
   https://fantasy.premierleague.com/entry/<team_id>/event/7
   ```

#### Get a Groq API key
Sign up and generate an API key at:  
👉 [https://console.groq.com/keys](https://console.groq.com/keys)

**N.B. to receive AI input for Wildcard Mode, a subscription may be required.**

---

## 🚀 Run the Script
Once your `.env` is configured:
```bash
python3 FPLGaffer.py.py
```

You’ll be prompted to:
- Choose how many players to replace (up to 6)  

---

## 🧩 Example Output

```
============================================================
POSITIONAL MIN AND MAX RATINGS
============================================================
GKP: MAX=57.22, MIN=11.81
DEF: MAX=62.54, MIN=0.0
MID: MAX=81.09, MIN=4.09
FWD: MAX=100.0, MIN=5.32


============================================================
FPL TEAM ASSESSMENT
============================================================
Players sorted by performance score (lowest to highest)
BANK: £6.5m

+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Name       |   Rating | Pos   | Cost   |   Form |   Exp Pts |   Pts |   Mins |   Pts/m | Owned   | Chance of PLaying   | News   |
+============+==========+=======+========+========+===========+=======+========+=========+=========+=====================+========+
| Baleba     |    19.52 | MID   | £4.8m  |    0.8 |       0.3 |     8 |    352 |    1.67 | 2.3%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Verbruggen |    24.81 | GKP   | £4.4m  |    1.5 |       1   |    11 |    630 |    2.5  | 4.4%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| King       |    25.24 | MID   | £4.5m  |    1.5 |       1   |    12 |    467 |    2.67 | 4.0%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Konsa      |    26.85 | DEF   | £4.5m  |    3   |       3   |    16 |    515 |    3.56 | 10.4%   | 100%                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Watkins    |    35.85 | FWD   | £8.7m  |    3.5 |       3.5 |    20 |    598 |    2.3  | 9.2%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Wood       |    38.24 | FWD   | £7.4m  |    1.8 |       1.3 |    24 |    522 |    3.24 | 12.0%   | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Pickford   |    41.15 | GKP   | £5.5m  |    3   |       2.5 |    30 |    630 |    5.45 | 10.5%   | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Cullen     |    41.85 | MID   | £5.0m  |    4.2 |       4.2 |    37 |    590 |    7.4  | 2.0%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Iwobi      |    43.49 | MID   | £6.5m  |    5   |       4.5 |    30 |    541 |    4.62 | 1.6%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Mitchell   |    44.87 | DEF   | £5.0m  |    4.8 |       4.8 |    35 |    630 |    7    | 2.5%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Muñoz      |    49.22 | DEF   | £5.6m  |    4.2 |       4.2 |    36 |    630 |    6.43 | 12.6%   | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Senesi     |    52.24 | DEF   | £5.0m  |    5.2 |       5.2 |    46 |    617 |    9.2  | 25.1%   | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Alderete   |    52.44 | DEF   | £4.1m  |    7.5 |       7   |    39 |    577 |    9.51 | 6.9%    | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Semenyo    |    81.09 | MID   | £7.9m  |   10.8 |      10.8 |    66 |    630 |    8.35 | 59.7%   | High                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Haaland    |   100    | FWD   | £14.5m |   11.5 |      12   |    70 |    593 |    4.83 | 61.3%   | 100%                |        |
+------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+


============================================================
REPLACEMENT SUGGESTIONS FOR 1 PLAYERS
============================================================

============================================================
REPLACEMENT OPTIONS FOR: Baleba (MID, £4.8m, Rating: 19.52)
============================================================
+-------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Name        |   Rating | Pos   | Cost   |   Form |   Exp Pts |   Pts |   Mins |   Pts/m | Owned   | Chance of PLaying   | News   |
+=============+==========+=======+========+========+===========+=======+========+=========+=========+=====================+========+
| Sarr        |    54.18 | MID   | £6.5m  |    4.5 |       4.5 |    36 |    432 |    5.54 | 6.4%    | 100%                |        |
+-------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Ndiaye      |    54.07 | MID   | £6.5m  |    5   |       4.5 |    37 |    588 |    5.69 | 10.7%   | 100%                |        |
+-------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Gravenberch |    53.14 | MID   | £5.7m  |    7   |       8   |    37 |    540 |    6.49 | 6.0%    | 100%                |        |
+-------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
| Tonali      |    48.58 | MID   | £5.4m  |    3.8 |       4.3 |    23 |    605 |    4.26 | 1.4%    | 100%                |        |
+-------------+----------+-------+--------+--------+-----------+-------+--------+---------+---------+---------------------+--------+
1. Sarr - £1.7m more (Rating: 54.2)
2. Ndiaye - £1.7m more (Rating: 54.1)
3. Gravenberch - £0.9m more (Rating: 53.1)
4. Tonali - £0.6m more (Rating: 48.6)

============================================================
AI Response
============================================================
Baleba → Gravenberch (Liverpool, £5.7m) — higher form (7.0) and ep_next (8.0) with easier fixture difficulty (3) and
strong Liverpool support.
```

---

## 🧭 Future Plans

- 🌐 **Web-based Interface:** Interactive GUI for easier team management.  
- 🃏 **Wildcard Optimizer:** Automatically build your best squad when using the wildcard chip.  

---

## 🧰 Tech Stack

- **Python 3**
- **Groq API** (`qwen/qwen3-32b`)
- **dotenv** for environment management
- **PrettyTable / tabulate** for clean console output
- **requests / FPL API** for player and team data

---

## 🏆 Credits

Developed by hutchyBop  
Data sourced from the [Official Fantasy Premier League API](https://fantasy.premierleague.com/api/)

---

### 💬 Feedback & Contributions

Pull requests and feature suggestions are welcome!  
If you’ve got ideas for improvements or new AI features, open an issue on GitHub.

---

**"Every manager needs a good Gaffer."** 🧤  
