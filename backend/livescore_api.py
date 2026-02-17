import requests
import re
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("LIVESCORE_API_KEY")
API_SECRET = os.getenv("LIVESCORE_API_SECRET")
BASE_URL = "https://livescore-api.com/api-client"

def get_live_scores(competition_id=None):
    """
    Get all live matches - FIXED score extraction from your working project
    """
    params = {}
    if competition_id:
        params["competition_id"] = competition_id
    
    # Add key and secret
    params.update({
        "key": API_KEY,
        "secret": API_SECRET
    })
    
    url = f"{BASE_URL}/scores/live.json"
    
    try:
        logger.info(f"Fetching live scores from API...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"API Response received")
        
        if data.get("success"):
            matches = data.get("data", {}).get("match", [])
            logger.info(f"Found {len(matches)} matches")
            
            # Process ALL matches with correct score extraction
            processed_matches = []
            for match in matches:
                processed = extract_match_data(match)
                
                # Only include matches that are actually LIVE or IN PLAY
                status = processed.get('status', '')
                minute = processed.get('minute', '0')
                
                if status not in ['FINISHED', 'FT', 'FULL_TIME', 'NS', 'Not Started']:
                    if minute not in ['0', 'NS', ''] or status == 'IN PLAY' or status == 'ADDED TIME':
                        processed_matches.append(processed)
            
            logger.info(f"Processed {len(processed_matches)} live matches")
            return {"success": True, "data": processed_matches}
        else:
            error_msg = data.get('error', 'Unknown error')
            logger.error(f"API Error: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Exception: {str(e)}")
        return {"success": False, "error": f"Failed to fetch live scores: {str(e)}"}

def extract_match_data(match):
    """
    Extract and normalize match data - CRITICAL FIX from your working project
    Scores are in the 'score' field as a string like "2 - 0"
    NOT in home_score/away_score fields (those are always 0)
    """
    processed = match.copy() if isinstance(match, dict) else {}
    
    if not isinstance(processed, dict):
        return {}
    
    # ===== CRITICAL FIX: Extract score from 'score' STRING field =====
    home_score = 0
    away_score = 0
    
    # METHOD 1: Parse from 'score' field (THIS IS WHERE THE REAL SCORE IS!)
    score_str = processed.get('score', '')
    if score_str and isinstance(score_str, str):
        # Format is "2 - 0" or "0 - 1" or "3 - 1"
        # Handle various formats: "2-0", "2 - 0", "2 -0", etc.
        parts = re.split(r'\s*-\s*', score_str)
        if len(parts) == 2:
            home_score = int(parts[0]) if parts[0].isdigit() else 0
            away_score = int(parts[1]) if parts[1].isdigit() else 0
    
    # METHOD 2: Parse from 'ft_score' for finished matches
    if home_score == 0 and away_score == 0:
        ft_score = processed.get('ft_score', '')
        if ft_score and isinstance(ft_score, str):
            parts = re.split(r'\s*-\s*', ft_score)
            if len(parts) == 2:
                home_score = int(parts[0]) if parts[0].isdigit() else 0
                away_score = int(parts[1]) if parts[1].isdigit() else 0
    
    # METHOD 3: Parse from 'ht_score' for half-time
    if home_score == 0 and away_score == 0:
        ht_score = processed.get('ht_score', '')
        if ht_score and isinstance(ht_score, str):
            parts = re.split(r'\s*-\s*', ht_score)
            if len(parts) == 2:
                home_score = int(parts[0]) if parts[0].isdigit() else 0
                away_score = int(parts[1]) if parts[1].isdigit() else 0
    
    # METHOD 4: Try direct home_score/away_score fields (sometimes they exist)
    if home_score == 0 and away_score == 0:
        home_score = processed.get('home_score', 0)
        away_score = processed.get('away_score', 0)
        if isinstance(home_score, str):
            home_score = int(home_score) if home_score.isdigit() else 0
        if isinstance(away_score, str):
            away_score = int(away_score) if away_score.isdigit() else 0
    
    processed['home_score'] = home_score
    processed['away_score'] = away_score
    processed['scores'] = [home_score, away_score]  # Add as array for your frontend
    processed['score_display'] = score_str
    
    # ===== Minute formatting - clean up special characters =====
    minute = processed.get('time', processed.get('minute', '0'))
    if isinstance(minute, str):
        # Remove any special characters like \u200e
        minute = minute.replace('\u200e', '').strip()
    elif isinstance(minute, (int, float)):
        minute = str(minute)
    
    # Clean up minute display
    if minute in ['NS', 'Not Started', '']:
        minute = '0'
    elif minute == 'HT':
        minute = '45'
    elif minute == 'FT':
        minute = '90'
    elif minute == 'LIVE':
        minute = '0'
    elif minute == 'FINISHED':
        minute = '90'
    
    processed['minute'] = minute
    processed['time'] = minute
    processed['status_display'] = minute if minute != '0' else 'NS'
    
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
    
    # If competition_name is still missing, try to get from league
    if 'competition_name' not in processed or not processed['competition_name']:
        if 'league' in processed:
            league = processed.get('league', {})
            if isinstance(league, dict):
                processed['competition_name'] = league.get('name', 'Unknown League')
    
    # ===== Status =====
    if 'status' not in processed:
        if minute == '0':
            processed['status'] = 'NS'
        elif minute == '45':
            processed['status'] = 'HT'
        elif minute == '90':
            processed['status'] = 'FT'
        else:
            processed['status'] = 'LIVE'
    
    return processed

def get_fixtures(competition_id=None):
    """Get fixtures"""
    params = {}
    if competition_id:
        params["competition_id"] = competition_id
    
    params.update({
        "key": API_KEY,
        "secret": API_SECRET
    })
    
    url = f"{BASE_URL}/fixtures/matches.json"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            fixtures = data.get("data", [])
            
            processed_fixtures = []
            for fixture in fixtures:
                processed = extract_fixture_data(fixture)
                processed_fixtures.append(processed)
            
            return {"success": True, "data": processed_fixtures}
        else:
            return {"success": False, "error": data.get('error', 'Unknown error')}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Failed to fetch fixtures: {str(e)}"}

def extract_fixture_data(fixture):
    """Extract fixture data"""
    processed = fixture.copy() if isinstance(fixture, dict) else {}
    
    if 'home_name' not in processed and 'home' in processed:
        home = processed.get('home', {})
        if isinstance(home, dict):
            processed['home_name'] = home.get('name', 'Home')
    
    if 'away_name' not in processed and 'away' in processed:
        away = processed.get('away', {})
        if isinstance(away, dict):
            processed['away_name'] = away.get('name', 'Away')
    
    if 'competition_name' not in processed and 'competition' in processed:
        comp = processed.get('competition', {})
        if isinstance(comp, dict):
            processed['competition_name'] = comp.get('name', 'Unknown League')
    
    return processed

def get_standings(competition_id=None):
    """Get league standings"""
    params = {}
    if competition_id:
        params["competition_id"] = competition_id
    
    params.update({
        "key": API_KEY,
        "secret": API_SECRET
    })
    
    url = f"{BASE_URL}/leagues/table.json"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            table_data = data.get("data", {})
            
            # Handle different response formats
            if "table" in table_data:
                standings = table_data.get("table", [])
                competition_name = table_data.get("competition", {}).get("name", "Unknown League")
                
                processed_standings = [{
                    "competition": competition_name,
                    "table": standings
                }]
            else:
                # Multiple leagues format
                processed_standings = []
                stages = table_data.get("stages", [])
                for stage in stages:
                    groups = stage.get("groups", [])
                    for group in groups:
                        standings = group.get("standings", [])
                        comp_name = group.get("group_name", stage.get("stage_name", "Unknown League"))
                        processed_standings.append({
                            "competition": comp_name,
                            "table": standings
                        })
            
            return {"success": True, "data": processed_standings}
        else:
            return {"success": False, "error": data.get('error', 'Unknown error')}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Failed to fetch standings: {str(e)}"}

def test_api_connection():
    """Test if API credentials are working"""
    try:
        params = {
            "key": API_KEY,
            "secret": API_SECRET
        }
        url = f"{BASE_URL}/scores/live.json"
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("success"):
            matches = data.get("data", {}).get("match", [])
            
            # Test score extraction
            sample_match = None
            sample_score = "N/A"
            if matches and len(matches) > 0:
                test_match = extract_match_data(matches[0])
                home_score = test_match.get('home_score', 0)
                away_score = test_match.get('away_score', 0)
                sample_score = f"{home_score} - {away_score}"
                sample_match = test_match.get('home_name', 'Team') + " vs " + test_match.get('away_name', 'Team')
            
            return {
                "status": "ok",
                "message": "API connection successful",
                "live_matches": len(matches),
                "sample_match": sample_match,
                "sample_score": sample_score
            }
        else:
            return {
                "status": "error",
                "message": data.get("error", "Unknown error"),
                "live_matches": 0
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "live_matches": 0
        }

# Run test if script is executed directly
if __name__ == "__main__":
    print("Testing LiveScore API connection...")
    result = test_api_connection()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Live matches: {result.get('live_matches', 0)}")
    if result.get('sample_match'):
        print(f"Sample match: {result['sample_match']} - Score: {result['sample_score']}")