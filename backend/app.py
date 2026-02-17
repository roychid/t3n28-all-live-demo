from flask import Flask, jsonify, send_from_directory, request
import os
import logging
import re
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set frontend folder
FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), '../frontend')

app = Flask(
    __name__,
    static_folder=FRONTEND_FOLDER,
    template_folder=FRONTEND_FOLDER
)

# ==================== LIVESCORE API WRAPPER ====================
class LiveScoreAPI:
    """LiveScore API wrapper - FIXED score extraction"""
    
    def __init__(self):
        self.api_key = os.getenv("LIVESCORE_API_KEY")
        self.api_secret = os.getenv("LIVESCORE_API_SECRET")
        self.base_url = "https://livescore-api.com/api-client"
        self.session = requests.Session()
        
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Base request method"""
        if params is None:
            params = {}
        
        params.update({
            "key": self.api_key,
            "secret": self.api_secret
        })
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_live_scores(self, competition_id: int = None) -> list:
        """Get all live matches - FIXED score extraction"""
        params = {}
        if competition_id:
            params["competition_id"] = competition_id
        
        data = self._get("/scores/live.json", params)
        if data.get("success"):
            matches = data.get("data", {}).get("match", [])
            
            processed_matches = []
            for match in matches:
                processed = self._extract_match_data(match)
                
                # Only include matches that are actually LIVE
                status = processed.get('status', '')
                minute = processed.get('minute', '0')
                
                if status not in ['FINISHED', 'FT', 'FULL_TIME', 'NS', 'Not Started']:
                    if minute not in ['0', 'NS', ''] or status in ['IN PLAY', 'ADDED TIME']:
                        processed_matches.append(processed)
            
            return processed_matches
        return []
    
    def _extract_match_data(self, match: dict) -> dict:
        """Extract match data - CRITICAL: scores from 'score' string field"""
        processed = match.copy() if isinstance(match, dict) else {}
        
        if not isinstance(processed, dict):
            return {}
        
        # ===== SCORE EXTRACTION - FIXED =====
        home_score = 0
        away_score = 0
        
        # Method 1: Parse from 'score' field (THIS IS WHERE THE REAL SCORE IS!)
        score_str = processed.get('score', '')
        if score_str and isinstance(score_str, str):
            # Handle formats: "2-0", "2 - 0", "2 -0", etc.
            parts = re.split(r'\s*-\s*', score_str)
            if len(parts) == 2:
                home_score = int(parts[0]) if parts[0].isdigit() else 0
                away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        # Method 2: Parse from 'ft_score' for finished matches
        if home_score == 0 and away_score == 0:
            ft_score = processed.get('ft_score', '')
            if ft_score and isinstance(ft_score, str):
                parts = re.split(r'\s*-\s*', ft_score)
                if len(parts) == 2:
                    home_score = int(parts[0]) if parts[0].isdigit() else 0
                    away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        # Method 3: Parse from 'ht_score' for half-time
        if home_score == 0 and away_score == 0:
            ht_score = processed.get('ht_score', '')
            if ht_score and isinstance(ht_score, str):
                parts = re.split(r'\s*-\s*', ht_score)
                if len(parts) == 2:
                    home_score = int(parts[0]) if parts[0].isdigit() else 0
                    away_score = int(parts[1]) if parts[1].isdigit() else 0
        
        processed['home_score'] = home_score
        processed['away_score'] = away_score
        processed['scores'] = [home_score, away_score]  # Add as array for frontend
        
        # ===== Minute formatting =====
        minute = processed.get('time', processed.get('minute', '0'))
        if isinstance(minute, str):
            minute = minute.replace('\u200e', '').strip()
        else:
            minute = str(minute)
        
        if minute in ['NS', 'Not Started', '']:
            minute = '0\''
        elif minute == 'HT':
            minute = '45\''
        elif minute == 'FT':
            minute = 'FT'
        elif minute.isdigit():
            minute = f"{minute}'"
        
        processed['minute'] = minute
        processed['time'] = minute
        
        # ===== Team name normalization =====
        if 'home_name' not in processed and 'home' in processed:
            home = processed.get('home', {})
            if isinstance(home, dict):
                processed['home_name'] = home.get('name', 'Home')
                processed['home_id'] = home.get('id')
        
        if 'away_name' not in processed and 'away' in processed:
            away = processed.get('away', {})
            if isinstance(away, dict):
                processed['away_name'] = away.get('name', 'Away')
                processed['away_id'] = away.get('id')
        
        # ===== Competition info =====
        if 'competition_name' not in processed and 'competition' in processed:
            comp = processed.get('competition', {})
            if isinstance(comp, dict):
                processed['competition_name'] = comp.get('name', 'Unknown League')
                processed['competition_id'] = comp.get('id')
        
        # ===== Status =====
        if 'status' not in processed:
            if minute == '0\'':
                processed['status'] = 'NS'
            elif minute == '45\'':
                processed['status'] = 'HT'
            elif minute == 'FT':
                processed['status'] = 'FT'
            else:
                processed['status'] = 'LIVE'
        
        return processed
    
    def get_fixtures(self, competition_id: int = None) -> list:
        """Get fixtures from all competitions"""
        if competition_id:
            # Get fixtures for specific competition
            params = {"competition_id": competition_id}
            data = self._get("/fixtures/matches.json", params)
            if data.get("success"):
                fixtures = data.get("data", [])
                processed_fixtures = []
                for fixture in fixtures:
                    processed = self._extract_fixture_data(fixture)
                    if competition_id:
                        comp_info = EUROPEAN_COMPETITIONS.get(competition_id, {})
                        processed['competition_name'] = comp_info.get("name", processed.get('competition_name', 'Unknown'))
                    processed_fixtures.append(processed)
                return processed_fixtures
            return []
        else:
            # Get fixtures from multiple major leagues
            league_ids = [2, 3, 4, 1, 5, 244, 245]  # PL, LaLiga, Serie A, Bundesliga, Ligue 1, UCL, UEL
            all_fixtures = []
            
            for league_id in league_ids:
                params = {"competition_id": league_id}
                data = self._get("/fixtures/matches.json", params)
                if data.get("success"):
                    fixtures = data.get("data", [])
                    comp_info = EUROPEAN_COMPETITIONS.get(league_id, {})
                    
                    for fixture in fixtures:
                        processed = self._extract_fixture_data(fixture)
                        processed['competition_name'] = comp_info.get("name", processed.get('competition_name', 'Unknown'))
                        processed['competition_flag'] = comp_info.get("flag", "⚽")
                        all_fixtures.append(processed)
            
            # Sort by date
            all_fixtures.sort(key=lambda x: x.get('date', ''))
            return all_fixtures
    
    def _extract_fixture_data(self, fixture: dict) -> dict:
        """Extract fixture data"""
        processed = fixture.copy() if isinstance(fixture, dict) else {}
        
        # Handle nested team objects
        if 'home' in processed and isinstance(processed['home'], dict):
            processed['home_name'] = processed['home'].get('name', 'Home')
            processed['home_id'] = processed['home'].get('id')
        
        if 'away' in processed and isinstance(processed['away'], dict):
            processed['away_name'] = processed['away'].get('name', 'Away')
            processed['away_id'] = processed['away'].get('id')
        
        # Handle competition info
        if 'competition' in processed and isinstance(processed['competition'], dict):
            processed['competition_name'] = processed['competition'].get('name', 'Unknown League')
            processed['competition_id'] = processed['competition'].get('id')
        
        # Format date if needed
        if 'date' in processed and processed['date']:
            try:
                date_obj = datetime.strptime(processed['date'], '%Y-%m-%d')
                processed['date_formatted'] = date_obj.strftime('%d %b %Y')
                
                # Add relative date
                today = datetime.now().date()
                fixture_date = date_obj.date()
                
                if fixture_date == today:
                    processed['date_relative'] = 'Today'
                elif fixture_date == today + timedelta(days=1):
                    processed['date_relative'] = 'Tomorrow'
                else:
                    processed['date_relative'] = date_obj.strftime('%d %b')
            except:
                processed['date_formatted'] = processed['date']
                processed['date_relative'] = processed['date']
        
        return processed
    
    def get_standings(self, competition_id: int = None) -> list:
        """Get league standings from all competitions"""
        if competition_id:
            # Get standings for specific competition
            params = {"competition_id": competition_id}
            data = self._get("/leagues/table.json", params)
            standings_list = []
            
            if data.get("success"):
                table_data = data.get("data", {})
                comp_info = EUROPEAN_COMPETITIONS.get(competition_id, {})
                
                if "table" in table_data:
                    standings = table_data.get("table", [])
                    standings_list.append({
                        "competition": comp_info.get("name", f"League {competition_id}"),
                        "competition_id": competition_id,
                        "competition_flag": comp_info.get("flag", "⚽"),
                        "table": standings
                    })
                else:
                    # Handle grouped standings
                    stages = table_data.get("stages", [])
                    for stage in stages:
                        groups = stage.get("groups", [])
                        for group in groups:
                            standings = group.get("standings", [])
                            group_name = group.get("group_name", stage.get("stage_name", "Group"))
                            standings_list.append({
                                "competition": f"{comp_info.get('name', 'League')} - {group_name}",
                                "competition_id": competition_id,
                                "competition_flag": comp_info.get("flag", "⚽"),
                                "table": standings
                            })
            return standings_list
        else:
            # Get standings from multiple major leagues
            league_ids = [2, 3, 4, 1, 5]  # PL, LaLiga, Serie A, Bundesliga, Ligue 1
            all_standings = []
            
            for league_id in league_ids:
                params = {"competition_id": league_id}
                data = self._get("/leagues/table.json", params)
                
                if data.get("success"):
                    table_data = data.get("data", {})
                    comp_info = EUROPEAN_COMPETITIONS.get(league_id, {})
                    
                    if "table" in table_data:
                        standings = table_data.get("table", [])
                        if standings:  # Only add if there are standings
                            all_standings.append({
                                "competition": comp_info.get("name", f"League {league_id}"),
                                "competition_id": league_id,
                                "competition_flag": comp_info.get("flag", "⚽"),
                                "table": standings
                            })
                    else:
                        # Handle grouped standings
                        stages = table_data.get("stages", [])
                        for stage in stages:
                            groups = stage.get("groups", [])
                            for group in groups:
                                standings = group.get("standings", [])
                                if standings:
                                    group_name = group.get("group_name", stage.get("stage_name", "Group"))
                                    all_standings.append({
                                        "competition": f"{comp_info.get('name', 'League')} - {group_name}",
                                        "competition_id": league_id,
                                        "competition_flag": comp_info.get("flag", "⚽"),
                                        "table": standings
                                    })
            
            return all_standings
    
    def test_connection(self) -> dict:
        """Test API connection"""
        try:
            data = self._get("/scores/live.json", {"limit": 1})
            if data.get("success"):
                matches = data.get("data", {}).get("match", [])
                return {
                    "success": True,
                    "message": "API connected",
                    "live_matches": len(matches)
                }
            return {"success": False, "message": "API error"}
        except Exception as e:
            return {"success": False, "message": str(e)}


# ==================== INITIALIZE API ====================
livescore_api = LiveScoreAPI()

# Test connection on startup
connection_test = livescore_api.test_connection()
logger.info(f"LiveScore API Connection: {connection_test}")

# ==================== EUROPEAN COMPETITIONS ====================
EUROPEAN_COMPETITIONS = {
    2: {"name": "Premier League", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    3: {"name": "LaLiga", "country": "Spain", "flag": "🇪🇸"},
    1: {"name": "Bundesliga", "country": "Germany", "flag": "🇩🇪"},
    4: {"name": "Serie A", "country": "Italy", "flag": "🇮🇹"},
    5: {"name": "Ligue 1", "country": "France", "flag": "🇫🇷"},
    244: {"name": "UEFA Champions League", "country": "Europe", "flag": "🇪🇺"},
    245: {"name": "UEFA Europa League", "country": "Europe", "flag": "🇪🇺"},
    446: {"name": "UEFA Conference League", "country": "Europe", "flag": "🇪🇺"},
}

# ==================== ROUTES ====================

# Serve CSS, JS, assets
@app.route('/src/<path:filename>')
def serve_src(filename):
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'src'), filename)

# Serve images/videos if needed
@app.route('/src/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'src', 'assets'), filename)

# Serve root HTML
@app.route('/')
def index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

# Page routes
@app.route('/live')
def live():
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'pages'), 'live.html')

@app.route('/fixtures')
def fixtures():
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'pages'), 'fixtures.html')

@app.route('/tables')
def tables():
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'pages'), 'tables.html')

@app.route('/news')
def news():
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'pages'), 'news.html')

@app.route('/videos')
def videos():
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'pages'), 'videos.html')

@app.route('/creator-dashboard')
def creator_dashboard():
    return send_from_directory(os.path.join(FRONTEND_FOLDER, 'pages'), 'creator-dashboard.html')

# ==================== API ENDPOINTS ====================

@app.route('/api/status')
def api_status():
    """Check API connection status"""
    status = livescore_api.test_connection()
    status["timestamp"] = datetime.now().isoformat()
    return jsonify(status)


@app.route('/api/live')
def api_live():
    """Get all live matches - FIXED score mapping"""
    competition_id = request.args.get('competition_id', type=int)
    matches = livescore_api.get_live_scores(competition_id)
    
    formatted_matches = []
    for match in matches[:100]:  # Limit to 100 matches
        comp_id = match.get('competition_id')
        comp_info = EUROPEAN_COMPETITIONS.get(comp_id, {})
        
        home_score = match.get('home_score', 0)
        away_score = match.get('away_score', 0)
        home_name = match.get('home_name', 'Home')
        away_name = match.get('away_name', 'Away')
        minute = match.get('minute', '0\'')
        
        is_live = minute not in ['0\'', 'NS', 'FT'] and minute != '90\''
        
        formatted_matches.append({
            "id": match.get('id', match.get('fixture_id')),
            "competition_id": comp_id,
            "competition_name": comp_info.get("name", match.get('competition_name', 'Live Match')),
            "competition_flag": comp_info.get("flag", "⚽"),
            "home_name": home_name,
            "away_name": away_name,
            "scores": [home_score, away_score],
            "home_score": home_score,
            "away_score": away_score,
            "minute": minute,
            "time": minute,
            "is_live": is_live,
            "status": match.get('status', 'LIVE' if is_live else 'NS'),
            "score_display": f"{home_score} - {away_score}"
        })
    
    return jsonify({
        "success": True,
        "data": formatted_matches,
        "count": len(formatted_matches)
    })


@app.route('/api/fixtures')
def api_fixtures():
    """Get fixtures from all competitions"""
    competition_id = request.args.get('competition_id', type=int)
    
    try:
        fixtures = livescore_api.get_fixtures(competition_id)
        
        formatted_fixtures = []
        for fixture in fixtures[:100]:  # Limit to 100 fixtures
            # Get competition info
            comp_id = fixture.get('competition_id')
            comp_info = EUROPEAN_COMPETITIONS.get(comp_id, {})
            
            # Format date
            date_str = fixture.get('date', '')
            date_formatted = fixture.get('date_relative', 'TBD')
            time_str = fixture.get('time', 'TBD')
            if time_str and len(time_str) >= 5:
                time_str = time_str[:5]  # Get HH:MM format
            
            formatted_fixtures.append({
                "id": fixture.get('id', fixture.get('fixture_id')),
                "competition_id": comp_id,
                "competition_name": comp_info.get("name", fixture.get('competition_name', 'Upcoming Match')),
                "competition_flag": comp_info.get("flag", "⚽"),
                "home_name": fixture.get('home_name', 'Home'),
                "away_name": fixture.get('away_name', 'Away'),
                "date": date_str,
                "date_formatted": date_formatted,
                "time": time_str,
                "venue": fixture.get('venue', 'Stadium TBD'),
                "status": fixture.get('status', 'NS')
            })
        
        # Sort by date
        formatted_fixtures.sort(key=lambda x: (x['date'], x['time']))
        
        return jsonify({
            "success": True,
            "data": formatted_fixtures,
            "count": len(formatted_fixtures)
        })
    except Exception as e:
        logger.error(f"Error in fixtures endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        })


@app.route('/api/tables')
def api_tables():
    """Get league tables from all competitions"""
    competition_id = request.args.get('competition_id', type=int)
    
    try:
        standings_list = livescore_api.get_standings(competition_id)
        
        formatted_standings_list = []
        for standings in standings_list:
            competition_name = standings.get("competition", "Unknown League")
            competition_flag = standings.get("competition_flag", "⚽")
            table = standings.get("table", [])
            
            formatted_table = []
            for position, team in enumerate(table, 1):
                # Handle different field names and structures
                team_name = team.get('name', 'Unknown')
                
                # Extract stats - handle both flat and nested structures
                if 'overall' in team and isinstance(team['overall'], dict):
                    overall = team.get('overall', {})
                    played = overall.get('games_played', 0)
                    won = overall.get('won', 0)
                    drawn = overall.get('draw', 0)
                    lost = overall.get('lost', 0)
                    goals_for = overall.get('goals_for', 0)
                    goals_against = overall.get('goals_against', 0)
                else:
                    played = team.get('played', team.get('games_played', 0))
                    won = team.get('won', 0)
                    drawn = team.get('drawn', team.get('draw', 0))
                    lost = team.get('lost', 0)
                    goals_for = team.get('goals_for', 0)
                    goals_against = team.get('goals_against', 0)
                
                points = team.get('points', 0)
                goals_diff = goals_for - goals_against
                
                # Handle potential string values
                try:
                    played = int(played) if played else 0
                except:
                    played = 0
                try:
                    won = int(won) if won else 0
                except:
                    won = 0
                try:
                    drawn = int(drawn) if drawn else 0
                except:
                    drawn = 0
                try:
                    lost = int(lost) if lost else 0
                except:
                    lost = 0
                try:
                    goals_for = int(goals_for) if goals_for else 0
                except:
                    goals_for = 0
                try:
                    goals_against = int(goals_against) if goals_against else 0
                except:
                    goals_against = 0
                try:
                    points = int(points) if points else 0
                except:
                    points = 0
                
                goals_diff = goals_for - goals_against
                
                formatted_table.append({
                    "position": position,
                    "name": team_name,
                    "played": played,
                    "won": won,
                    "drawn": drawn,
                    "lost": lost,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "goals_diff": goals_diff,
                    "points": points,
                    "form": team.get('form', '')
                })
            
            # Sort by position
            formatted_table.sort(key=lambda x: x['position'])
            
            if formatted_table:  # Only add if there are standings
                formatted_standings_list.append({
                    "competition": competition_name,
                    "competition_flag": competition_flag,
                    "table": formatted_table
                })
        
        return jsonify({
            "success": True,
            "data": formatted_standings_list,
            "count": len(formatted_standings_list)
        })
    except Exception as e:
        logger.error(f"Error in tables endpoint: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        })


@app.route('/api/debug/live')
def debug_live():
    """Debug endpoint to see raw API response"""
    competition_id = request.args.get('competition_id', type=int)
    params = {}
    if competition_id:
        params["competition_id"] = competition_id
    
    # Make raw API call
    url = f"{livescore_api.base_url}/scores/live.json"
    params.update({
        "key": livescore_api.api_key,
        "secret": livescore_api.api_secret
    })
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # Show sample of raw data
        matches = data.get("data", {}).get("match", [])
        samples = []
        for match in matches[:3]:
            samples.append({
                "home": match.get("home_name"),
                "away": match.get("away_name"),
                "score_field": match.get("score"),
                "ft_score": match.get("ft_score"),
                "ht_score": match.get("ht_score"),
                "time": match.get("time"),
                "status": match.get("status")
            })
        
        return jsonify({
            "success": data.get("success"),
            "total_matches": len(matches),
            "samples": samples,
            "raw_response": data
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/debug/fixtures')
def debug_fixtures():
    """Debug endpoint to see raw fixtures API response"""
    competition_id = request.args.get('competition_id', 2)  # Default to PL
    
    params = {
        "key": livescore_api.api_key,
        "secret": livescore_api.api_secret,
        "competition_id": competition_id
    }
    
    url = f"{livescore_api.base_url}/fixtures/matches.json"
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        fixtures = data.get("data", [])
        samples = []
        for fixture in fixtures[:3]:
            samples.append({
                "id": fixture.get("id"),
                "home": fixture.get("home", {}).get("name") if isinstance(fixture.get("home"), dict) else fixture.get("home"),
                "away": fixture.get("away", {}).get("name") if isinstance(fixture.get("away"), dict) else fixture.get("away"),
                "date": fixture.get("date"),
                "time": fixture.get("time"),
                "competition": fixture.get("competition", {}).get("name") if isinstance(fixture.get("competition"), dict) else fixture.get("competition")
            })
        
        return jsonify({
            "success": data.get("success"),
            "total_fixtures": len(fixtures),
            "samples": samples,
            "raw_response": data
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/debug/tables')
def debug_tables():
    """Debug endpoint to see raw tables API response"""
    competition_id = request.args.get('competition_id', 2)  # Default to PL
    
    params = {
        "key": livescore_api.api_key,
        "secret": livescore_api.api_secret,
        "competition_id": competition_id
    }
    
    url = f"{livescore_api.base_url}/leagues/table.json"
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        table_data = data.get("data", {})
        
        return jsonify({
            "success": data.get("success"),
            "raw_response": data
        })
    except Exception as e:
        return jsonify({"error": str(e)})


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return send_from_directory(FRONTEND_FOLDER, 'index.html')


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== RUN APP ====================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print("\n" + "=" * 60)
    print("🚀 T3N28 FOOTBALL DASHBOARD")
    print("=" * 60)
    
    # Test API connection
    status = livescore_api.test_connection()
    if status.get("success"):
        print(f"✅ LiveScore API: Connected ({status.get('live_matches', 0)} live matches)")
    else:
        print(f"❌ LiveScore API: {status.get('message', 'Connection failed')}")
    
    print("=" * 60)
    print(f"🌐 Server: http://localhost:{port}")
    print("📊 Endpoints:")
    print("   - /api/live - Live scores")
    print("   - /api/fixtures - Upcoming fixtures")
    print("   - /api/tables - League tables")
    print("   - /api/debug/live - Debug live scores")
    print("   - /api/debug/fixtures - Debug fixtures")
    print("   - /api/debug/tables - Debug tables")
    print("=" * 60)
    
    app.run(debug=debug, host='0.0.0.0', port=port)