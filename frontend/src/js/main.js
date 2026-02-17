// ====== main.js ======

// Wait until DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM loaded, initializing...");
  
  setupThemeToggle();
  setupMobileMenu();
  setupAuthButtons();
  setupSearchFunctionality();

  // Check current page by looking at the pathname
  const path = window.location.pathname;
  console.log("Current path:", path);
  
  if (path === '/' || path === '/index.html') {
    // Home page - load live matches in the home page container
    fetchLiveScores('live-matches-container');
    fetchNews();
    fetchVideos();
    fetchPopularLeagues();
  } else if (path === '/live') {
    // Live page
    fetchLiveScores('live-container');
    setupAutoRefresh('live');
  } else if (path === '/fixtures') {
    // Fixtures page
    fetchFixtures();
  } else if (path === '/tables') {
    // Tables page
    fetchTables();
    setupLeagueFilter();
  } else if (path === '/news') {
    // News page
    fetchNews();
  } else if (path === '/videos') {
    // Videos page
    fetchVideos();
  } else if (path === '/creator-dashboard') {
    // Creator dashboard
    initCreatorDashboard();
  }
});

// ==========================
// Theme toggle (dark/light)
// ==========================
function setupThemeToggle() {
  const toggle = document.getElementById("theme-toggle");
  if (!toggle) return;
  
  const body = document.body;
  const icon = toggle.querySelector("i");

  // Check for saved theme preference
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    body.classList.add('dark-theme');
    if (icon) {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
    }
  }

  toggle.addEventListener("click", () => {
    body.classList.toggle("dark-theme");
    
    if (body.classList.contains('dark-theme')) {
      if (icon) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
      }
      localStorage.setItem('theme', 'dark');
    } else {
      if (icon) {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
      }
      localStorage.setItem('theme', 'light');
    }
  });
}

// ==========================
// Mobile menu toggle
// ==========================
function setupMobileMenu() {
  const btn = document.getElementById("mobile-menu-btn");
  const navMenu = document.querySelector(".nav-menu");
  
  if (!btn || !navMenu) return;

  btn.addEventListener("click", () => {
    navMenu.classList.toggle("active");
    
    // Change icon based on menu state
    const icon = btn.querySelector("i");
    if (navMenu.classList.contains("active")) {
      icon.classList.remove("fa-bars");
      icon.classList.add("fa-times");
    } else {
      icon.classList.remove("fa-times");
      icon.classList.add("fa-bars");
    }
  });

  // Close menu when clicking on a link
  navMenu.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
      navMenu.classList.remove("active");
      const icon = btn.querySelector("i");
      icon.classList.remove("fa-times");
      icon.classList.add("fa-bars");
    });
  });
}

// ==========================
// Auth buttons
// ==========================
function setupAuthButtons() {
  const loginBtn = document.getElementById("login-btn");
  const registerBtn = document.getElementById("register-btn");
  
  if (loginBtn) {
    loginBtn.addEventListener('click', () => showAuthModal('login'));
  }
  
  if (registerBtn) {
    registerBtn.addEventListener('click', () => showAuthModal('register'));
  }
}

// Auth modal function
function showAuthModal(type) {
  // Create modal if it doesn't exist
  let modal = document.getElementById('auth-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'auth-modal';
    modal.className = 'modal';
    document.body.appendChild(modal);
  }

  const isLogin = type === 'login';
  modal.innerHTML = `
    <div class="modal-content">
      <span class="close-modal">&times;</span>
      <h2>${isLogin ? 'Login' : 'Register'}</h2>
      <form id="auth-form" onsubmit="return false;">
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" placeholder="Enter your email" required>
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input type="password" id="password" placeholder="Enter your password" required>
        </div>
        ${!isLogin ? `
        <div class="form-group">
          <label for="confirm-password">Confirm Password</label>
          <input type="password" id="confirm-password" placeholder="Confirm your password" required>
        </div>
        ` : ''}
        <button type="submit" class="btn-primary btn-block">
          ${isLogin ? 'Login' : 'Register'}
        </button>
      </form>
      <p class="auth-switch">
        ${isLogin ? "Don't have an account? " : "Already have an account? "}
        <a href="#" onclick="showAuthModal('${isLogin ? 'register' : 'login'}')">
          ${isLogin ? 'Register' : 'Login'}
        </a>
      </p>
    </div>
  `;

  modal.style.display = 'block';

  // Close modal functionality
  modal.querySelector('.close-modal').onclick = () => {
    modal.style.display = 'none';
  };

  window.onclick = (event) => {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  };

  // Handle form submission
  const form = document.getElementById('auth-form');
  form.onsubmit = (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    if (!isLogin) {
      const confirmPassword = document.getElementById('confirm-password').value;
      if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
      }
    }
    
    alert(`${isLogin ? 'Login' : 'Registration'} successful! (Demo mode)`);
    modal.style.display = 'none';
  };
}

// ==========================
// Search functionality
// ==========================
function setupSearchFunctionality() {
  const searchInput = document.getElementById('search-input');
  if (!searchInput) return;

  let searchTimeout;

  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();
    
    if (query.length < 2) {
      hideSearchResults();
      return;
    }

    searchTimeout = setTimeout(() => {
      performSearch(query);
    }, 500);
  });

  // Close search results when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-box')) {
      hideSearchResults();
    }
  });
}

async function performSearch(query) {
  try {
    // Show loading state
    showSearchResults([{ type: 'loading', message: 'Searching...' }]);

    // Mock search results
    const mockResults = [
      { type: 'team', name: 'Manchester United', league: 'Premier League' },
      { type: 'team', name: 'Manchester City', league: 'Premier League' },
      { type: 'team', name: 'Liverpool', league: 'Premier League' },
      { type: 'team', name: 'Arsenal', league: 'Premier League' },
      { type: 'team', name: 'Chelsea', league: 'Premier League' },
      { type: 'team', name: 'Real Madrid', league: 'La Liga' },
      { type: 'team', name: 'Barcelona', league: 'La Liga' },
      { type: 'team', name: 'Bayern Munich', league: 'Bundesliga' },
      { type: 'player', name: 'Erling Haaland', team: 'Manchester City' },
      { type: 'player', name: 'Kylian Mbappe', team: 'PSG' },
      { type: 'player', name: 'Jude Bellingham', team: 'Real Madrid' }
    ].filter(item => 
      item.name.toLowerCase().includes(query.toLowerCase())
    );

    if (mockResults.length === 0) {
      showSearchResults([{ type: 'empty', message: 'No results found' }]);
    } else {
      showSearchResults(mockResults);
    }
  } catch (error) {
    console.error('Search error:', error);
    showSearchResults([{ type: 'error', message: 'Search failed' }]);
  }
}

function showSearchResults(results) {
  let resultsDiv = document.getElementById('search-results');
  
  if (!resultsDiv) {
    resultsDiv = document.createElement('div');
    resultsDiv.id = 'search-results';
    resultsDiv.className = 'search-results';
    document.querySelector('.search-box').appendChild(resultsDiv);
  }

  if (results[0]?.type === 'loading') {
    resultsDiv.innerHTML = `<div class="search-loading"><i class="fas fa-spinner fa-spin"></i> ${results[0].message}</div>`;
  } else if (results[0]?.type === 'empty') {
    resultsDiv.innerHTML = `<div class="search-empty">${results[0].message}</div>`;
  } else if (results[0]?.type === 'error') {
    resultsDiv.innerHTML = `<div class="search-error">${results[0].message}</div>`;
  } else {
    let html = '<div class="search-results-list">';
    results.forEach(result => {
      const icon = result.type === 'team' ? 'fa-shield-alt' : 
                   result.type === 'player' ? 'fa-user' : 'fa-futbol';
      html += `
        <div class="search-result-item" onclick="handleSearchResultClick('${result.type}', '${result.name}')">
          <i class="fas ${icon}"></i>
          <div class="result-info">
            <div class="result-name">${result.name}</div>
            <div class="result-detail">${result.league || result.team || ''}</div>
          </div>
        </div>
      `;
    });
    html += '</div>';
    resultsDiv.innerHTML = html;
  }
  
  resultsDiv.style.display = 'block';
}

function hideSearchResults() {
  const resultsDiv = document.getElementById('search-results');
  if (resultsDiv) {
    resultsDiv.style.display = 'none';
  }
}

window.handleSearchResultClick = (type, name) => {
  alert(`Navigate to ${type}: ${name} (Demo mode)`);
  hideSearchResults();
};

// ==========================
// Auto-refresh functionality
// ==========================
let refreshInterval;

function setupAutoRefresh(page) {
  // Clear any existing interval
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }

  // Set up auto-refresh every 60 seconds for live scores
  refreshInterval = setInterval(() => {
    console.log(`Auto-refreshing ${page} data...`);
    if (page === 'live') {
      fetchLiveScores('live-container');
    }
  }, 60000);

  // Add refresh indicator to the page
  addRefreshIndicator();
}

function addRefreshIndicator() {
  const container = document.querySelector('.live-section .section-header');
  if (!container) return;

  // Check if indicator already exists
  if (container.querySelector('.refresh-indicator')) return;

  const indicator = document.createElement('div');
  indicator.className = 'refresh-indicator';
  indicator.innerHTML = `
    <span class="refresh-text"><i class="fas fa-sync-alt"></i> Auto-refreshing every 60s</span>
    <button class="btn-refresh" onclick="manualRefresh()"><i class="fas fa-redo"></i> Refresh Now</button>
  `;
  container.appendChild(indicator);
}

window.manualRefresh = () => {
  const path = window.location.pathname;
  if (path === '/live') {
    fetchLiveScores('live-container');
  } else if (path === '/fixtures') {
    fetchFixtures();
  } else if (path === '/tables') {
    fetchTables();
  }
  
  // Show refresh animation
  const refreshBtn = document.querySelector('.btn-refresh i');
  if (refreshBtn) {
    refreshBtn.classList.add('fa-spin');
    setTimeout(() => {
      refreshBtn.classList.remove('fa-spin');
    }, 1000);
  }
};

// ==========================
// Fetch Live Scores from all competitions
// ==========================
async function fetchLiveScores(containerId = 'live-matches-container') {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container with id '${containerId}' not found`);
    return;
  }

  console.log(`Fetching live scores for container: ${containerId}`);
  
  container.innerHTML = `<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading live scores from all leagues... (${new Date().toLocaleTimeString()})</div>`;

  try {
    const res = await fetch("/api/live");
    const response = await res.json();

    if (!response.success) {
      container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${response.error || 'Failed to load live scores'}</div>`;
      return;
    }

    const matches = response.data || [];
    console.log(`Received ${matches.length} live matches`);
    
    // Hide/show no live message
    const noLiveMsg = document.getElementById('no-live-message');
    if (noLiveMsg) {
      noLiveMsg.style.display = matches.length === 0 ? 'block' : 'none';
    }
    
    if (matches.length === 0) {
      container.innerHTML = '<div class="empty-state"><i class="far fa-futbol"></i> No live matches at the moment.</div>';
      return;
    }

    // Group matches by competition
    const matchesByLeague = matches.reduce((groups, match) => {
      const league = match.competition_name || 'Other Leagues';
      if (!groups[league]) {
        groups[league] = [];
      }
      groups[league].push(match);
      return groups;
    }, {});

    let html = '';
    let matchCount = 0;
    
    for (const [league, leagueMatches] of Object.entries(matchesByLeague)) {
      html += `<h3 class="league-heading"><i class="fas fa-trophy"></i> ${league} (${leagueMatches.length})</h3>`;
      html += '<div class="live-matches-grid">';
      
      leagueMatches.forEach(match => {
        matchCount++;
        const homeScore = match.scores ? match.scores[0] : 0;
        const awayScore = match.scores ? match.scores[1] : 0;
        const matchStatus = match.minute || match.time || '0\'';
        const isLive = match.is_live || (matchStatus.includes('\'') && !matchStatus.includes('FT') && matchStatus !== '0\'');
        
        html += `
          <div class="match-card ${isLive ? 'live-match' : ''}">
            <div class="match-header">
              <span class="match-minute ${isLive ? 'live-indicator' : ''}">${matchStatus}</span>
              <span class="match-competition">${league}</span>
            </div>
            <div class="match-teams">
              <div class="team home">
                <span class="team-name">${match.home_name || 'Home'}</span>
                <span class="team-score ${homeScore > awayScore ? 'winning' : ''}">${homeScore}</span>
              </div>
              <div class="team away">
                <span class="team-name">${match.away_name || 'Away'}</span>
                <span class="team-score ${awayScore > homeScore ? 'winning' : ''}">${awayScore}</span>
              </div>
            </div>
            ${isLive ? '<div class="live-badge"><span class="pulse"></span> LIVE</div>' : ''}
          </div>
        `;
      });
      
      html += '</div>';
    }
    
    // Update section header with match count for home page
    if (containerId === 'live-matches-container') {
      const sectionHeader = document.querySelector('.live-section .section-header h2');
      if (sectionHeader) {
        sectionHeader.innerHTML = `<i class="fas fa-bolt"></i> Live Matches (${matchCount})`;
      }
    }
    
    container.innerHTML = html;
    console.log(`Displayed ${matchCount} live matches`);

  } catch (err) {
    console.error('Live scores error:', err);
    container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> Failed to connect to server. Please refresh the page.</div>`;
  }
}

// ==========================
// Fetch Fixtures
// ==========================
async function fetchFixtures() {
  const container = document.getElementById("fixtures-container");
  if (!container) return;

  container.innerHTML = `<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading fixtures from all leagues...</div>`;

  try {
    const res = await fetch("/api/fixtures");
    const response = await res.json();

    if (!response.success) {
      container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${response.error || 'Failed to load fixtures'}</div>`;
      return;
    }

    const fixtures = response.data || [];
    
    if (fixtures.length === 0) {
      container.innerHTML = `<div class="empty-state"><i class="far fa-calendar-times"></i> No upcoming fixtures found.</div>`;
      return;
    }

    // Group fixtures by competition
    const groupedFixtures = fixtures.reduce((groups, fixture) => {
      const league = fixture.competition_name || 'Other Leagues';
      if (!groups[league]) {
        groups[league] = [];
      }
      groups[league].push(fixture);
      return groups;
    }, {});

    let html = '<div class="fixtures-wrapper">';
    
    for (const [league, leagueFixtures] of Object.entries(groupedFixtures)) {
      html += `<h2 class="league-title">${league}</h2>`;
      html += '<div class="fixtures-grid">';
      
      leagueFixtures.slice(0, 10).forEach(fixture => {
        const dateDisplay = fixture.date_formatted || fixture.date || 'TBD';
        const timeDisplay = fixture.time || 'TBD';
        
        html += `
          <div class="fixture-card">
            <div class="fixture-date-badge">${dateDisplay}</div>
            <div class="fixture-teams">
              <div class="team-info home">
                <span class="team-name">${fixture.home_name}</span>
              </div>
              <span class="fixture-vs">VS</span>
              <div class="team-info away">
                <span class="team-name">${fixture.away_name}</span>
              </div>
            </div>
            <div class="fixture-time">
              <i class="far fa-clock"></i> ${timeDisplay}
            </div>
            <div class="fixture-venue">
              <i class="fas fa-map-marker-alt"></i> ${fixture.venue || 'Stadium TBD'}
            </div>
          </div>
        `;
      });
      
      html += '</div>';
    }
    
    html += '</div>';
    container.innerHTML = html;

  } catch (err) {
    console.error('Fixtures error:', err);
    container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> Failed to load fixtures</div>`;
  }
}

// ==========================
// Fetch League Tables
// ==========================
async function fetchTables() {
  const container = document.getElementById("tables-container");
  if (!container) return;

  container.innerHTML = `<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading league tables...</div>`;

  try {
    const res = await fetch("/api/tables");
    const response = await res.json();

    if (!response.success) {
      container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${response.error || 'Failed to load league tables'}</div>`;
      return;
    }

    const leagues = response.data || [];
    
    if (leagues.length === 0) {
      container.innerHTML = `<div class="empty-state"><i class="fas fa-table"></i> No league standings available.</div>`;
      return;
    }

    let html = '<div class="tables-wrapper">';
    
    // Add league selector if multiple leagues
    if (leagues.length > 1) {
      html += '<div class="league-tabs">';
      leagues.forEach((league, index) => {
        html += `<button class="league-tab ${index === 0 ? 'active' : ''}" data-league-index="${index}">${league.competition}</button>`;
      });
      html += '</div>';
    }
    
    // Add tables for each league
    html += '<div class="tables-container">';
    leagues.forEach((league, leagueIndex) => {
      const displayStyle = leagueIndex === 0 ? 'block' : 'none';
      html += `<div class="league-table-container" data-league-index="${leagueIndex}" style="display: ${displayStyle};">`;
      html += `<h2 class="league-title">${league.competition}</h2>`;
      
      if (!league.table || league.table.length === 0) {
        html += `<p class="empty-message">No standings available for this league.</p>`;
      } else {
        html += '<div class="table-responsive"><table class="league-table">';
        html += `<thead>
                   <tr>
                     <th>#</th>
                     <th>Team</th>
                     <th>P</th>
                     <th>W</th>
                     <th>D</th>
                     <th>L</th>
                     <th>GF</th>
                     <th>GA</th>
                     <th>GD</th>
                     <th>Pts</th>
                   </tr>
                 </thead>
                 <tbody>`;

        league.table.forEach((team) => {
          // Determine if position qualifies for European competitions
          const positionClass = 
            team.position <= 4 ? 'champions-league' : 
            team.position === 5 ? 'europa-league' : '';
          
          html += `
            <tr class="${positionClass}">
              <td class="position">${team.position}</td>
              <td class="team-name-cell">
                <span class="team-badge">${team.name.substring(0, 3).toUpperCase()}</span>
                ${team.name}
              </td>
              <td>${team.played || 0}</td>
              <td>${team.won || 0}</td>
              <td>${team.drawn || 0}</td>
              <td>${team.lost || 0}</td>
              <td>${team.goals_for || 0}</td>
              <td>${team.goals_against || 0}</td>
              <td>${team.goals_diff > 0 ? '+' : ''}${team.goals_diff || 0}</td>
              <td class="points"><strong>${team.points || 0}</strong></td>
            </tr>
          `;
        });

        html += '</tbody></table></div>';
      }
      
      html += '</div>';
    });
    
    html += '</div></div>';
    container.innerHTML = html;

    // Setup tab switching if multiple leagues
    if (leagues.length > 1) {
      setupLeagueTabs();
    }

  } catch (err) {
    console.error('Tables error:', err);
    container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> Failed to load league tables</div>`;
  }
}

function setupLeagueTabs() {
  const tabs = document.querySelectorAll('.league-tab');
  const tables = document.querySelectorAll('.league-table-container');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Update active tab
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // Show corresponding table
      const index = tab.dataset.leagueIndex;
      tables.forEach(table => {
        if (table.dataset.leagueIndex === index) {
          table.style.display = 'block';
        } else {
          table.style.display = 'none';
        }
      });
    });
  });
}

function setupLeagueFilter() {
  // Additional league filtering can be added here
}

// ==========================
// Fetch News
// ==========================
async function fetchNews() {
  const container = document.getElementById("news-container");
  if (!container) return;

  container.innerHTML = `<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading latest news...</div>`;

  try {
    // Mock news data
    const newsArticles = [
      {
        id: 1,
        title: "Champions League Quarter-Final Draw: Manchester City face Real Madrid",
        excerpt: "The draw for the Champions League quarter-finals has set up a blockbuster tie between last year's finalists...",
        image: "https://via.placeholder.com/400x250/007bff/ffffff?text=UCL",
        category: "Champions League",
        date: "2024-03-15",
        author: "James Smith"
      },
      {
        id: 2,
        title: "Premier League Title Race: Arsenal maintain lead with crucial victory",
        excerpt: "Arsenal secured a vital win to maintain their position at the top of the Premier League table...",
        image: "https://via.placeholder.com/400x250/28a745/ffffff?text=PL",
        category: "Premier League",
        date: "2024-03-14",
        author: "Sarah Johnson"
      },
      {
        id: 3,
        title: "La Liga: Barcelona's lead cut after dramatic El Clasico",
        excerpt: "Real Madrid kept their title hopes alive with a stunning late victory over Barcelona...",
        image: "https://via.placeholder.com/400x250/dc3545/ffffff?text=LA+LIGA",
        category: "La Liga",
        date: "2024-03-13",
        author: "Carlos Rodriguez"
      }
    ];

    let html = '<div class="news-grid">';
    
    newsArticles.forEach(article => {
      html += `
        <article class="news-card">
          <div class="news-image-wrapper">
            <img src="${article.image}" alt="${article.title}" class="news-image" loading="lazy">
            <span class="news-category">${article.category}</span>
          </div>
          <div class="news-content">
            <h3 class="news-title">${article.title}</h3>
            <p class="news-excerpt">${article.excerpt}</p>
            <div class="news-meta">
              <span class="news-author"><i class="far fa-user"></i> ${article.author}</span>
              <span class="news-date"><i class="far fa-calendar"></i> ${formatDate(article.date)}</span>
            </div>
          </div>
        </article>
      `;
    });
    
    html += '</div>';
    container.innerHTML = html;

  } catch (err) {
    console.error('News error:', err);
    container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> Failed to load news</div>`;
  }
}

// ==========================
// Fetch Videos
// ==========================
async function fetchVideos() {
  const container = document.getElementById("video-container");
  if (!container) return;

  container.innerHTML = `<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading videos...</div>`;

  try {
    // Mock video data
    const videos = [
      {
        id: 1,
        title: "Manchester United 3-1 Liverpool | Extended Highlights",
        thumbnail: "https://via.placeholder.com/400x225/dc3545/ffffff?text=MUN+LIV",
        duration: "12:30",
        views: "1.2M",
        channel: "Premier League"
      },
      {
        id: 2,
        title: "Top 10 Goals of the Week | Champions League",
        thumbnail: "https://via.placeholder.com/400x225/007bff/ffffff?text=TOP+10",
        duration: "8:15",
        views: "892K",
        channel: "UEFA TV"
      },
      {
        id: 3,
        title: "Real Madrid 4-0 Barcelona | El Clasico Highlights",
        thumbnail: "https://via.placeholder.com/400x225/ffc107/000000?text=EL+CLASICO",
        duration: "15:45",
        views: "2.5M",
        channel: "La Liga"
      }
    ];

    let html = '<div class="videos-grid">';
    
    videos.forEach(video => {
      html += `
        <div class="video-card" onclick="playVideo(${video.id})">
          <div class="video-thumbnail">
            <img src="${video.thumbnail}" alt="${video.title}" loading="lazy">
            <span class="video-duration">${video.duration}</span>
            <div class="video-play-overlay">
              <i class="fas fa-play-circle"></i>
            </div>
          </div>
          <div class="video-info">
            <h4 class="video-title">${video.title}</h4>
            <div class="video-meta">
              <span class="video-channel"><i class="fas fa-tv"></i> ${video.channel}</span>
              <span class="video-views"><i class="far fa-eye"></i> ${video.views}</span>
            </div>
          </div>
        </div>
      `;
    });
    
    html += '</div>';
    container.innerHTML = html;

  } catch (err) {
    console.error('Videos error:', err);
    container.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> Failed to load videos</div>`;
  }
}

window.playVideo = (videoId) => {
  alert(`Playing video ${videoId} (Demo mode)`);
};

// ==========================
// Fetch Popular Leagues
// ==========================
async function fetchPopularLeagues() {
  const container = document.querySelector('.leagues-grid');
  if (!container) return;

  const leagues = [
    { name: 'Premier League', icon: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', path: '/tables?league=premier' },
    { name: 'La Liga', icon: '🇪🇸', path: '/tables?league=laliga' },
    { name: 'Serie A', icon: '🇮🇹', path: '/tables?league=seriea' },
    { name: 'Bundesliga', icon: '🇩🇪', path: '/tables?league=bundesliga' },
    { name: 'Ligue 1', icon: '🇫🇷', path: '/tables?league=ligue1' },
    { name: 'Champions League', icon: '🇪🇺', path: '/tables?league=champions' }
  ];

  let html = '';
  leagues.forEach(league => {
    html += `
      <a href="${league.path}" class="league-card">
        <span class="league-icon">${league.icon}</span>
        <span class="league-name">${league.name}</span>
      </a>
    `;
  });

  container.innerHTML = html;
}

// ==========================
// Creator Dashboard
// ==========================
function initCreatorDashboard() {
  const container = document.querySelector('.creator-content');
  if (!container) return;

  container.innerHTML = `
    <div class="creator-dashboard">
      <div class="dashboard-header">
        <h2>Creator Dashboard</h2>
        <p>Content management features coming soon!</p>
      </div>
    </div>
  `;
}

// ==========================
// Helper Functions
// ==========================
function formatDate(dateStr) {
  if (!dateStr) return 'Recent';
  
  const date = new Date(dateStr);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ==========================
// Clean up on page unload
// ==========================
window.addEventListener('beforeunload', () => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});