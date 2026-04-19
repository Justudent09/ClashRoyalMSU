from flask import Flask, jsonify, render_template_string, request
import sqlite3
import random
from datetime import datetime
import os
import subprocess

app = Flask(__name__)

# HTML для страницы с участниками (исправленный и улучшенный)
PLAYERS_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Участники турнира</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        h1 { color: #667eea; }
        .nav-buttons {
            display: flex;
            gap: 10px;
        }
        .nav-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .nav-btn.active {
            background: #667eea;
            color: white;
        }
        .nav-btn:not(.active) {
            background: #e0e0e0;
            color: #333;
        }
        .nav-btn:not(.active):hover {
            background: #ccc;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .search-box {
            margin-bottom: 20px;
        }
        .search-box input {
            padding: 10px;
            width: 100%;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #667eea;
            color: white;
            cursor: pointer;
        }
        tr:hover { background: #f5f5f5; }
        .refresh-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
        }
        .create-tournament-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        .create-tournament-btn:hover {
            background: #218838;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👥 Участники турнира Clash Royale</h1>
            <div class="nav-buttons">
                <a href="/" class="nav-btn active">📋 Участники</a>
                <a href="/bracket" class="nav-btn">🏆 Турнирная сетка</a>
            </div>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="totalPlayers">-</div>
                <div>Всего игроков</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="totalTrophies">-</div>
                <div>Всего кубков</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avgTrophies">-</div>
                <div>Среднее кубков</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="search" placeholder="🔍 Поиск по имени, нику или ID..." onkeyup="filterTable()">
        </div>

        <div style="overflow-x: auto;">
            <table id="playersTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">#</th>
                        <th onclick="sortTable(1)">ID</th>
                        <th onclick="sortTable(2)">Реальное имя</th>
                        <th onclick="sortTable(3)">Ник в игре</th>
                        <th onclick="sortTable(4)">🏆 Кубки</th>
                        <th onclick="sortTable(5)">Дата регистрации</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr><td colspan="6" style="text-align:center;">Загрузка...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    <button class="refresh-btn" onclick="loadData()">🔄 Обновить</button>

    <script>
        let playersData = [];
        
        async function loadData() {
            try {
                const response = await fetch('/api/players');
                playersData = await response.json();
                
                const statsResponse = await fetch('/api/stats');
                const stats = await statsResponse.json();
                
                document.getElementById('totalPlayers').textContent = stats.total_players;
                document.getElementById('totalTrophies').textContent = stats.total_trophies;
                document.getElementById('avgTrophies').textContent = stats.avg_trophies;
                
                displayTable(playersData);
            } catch(e) {
                console.error('Ошибка:', e);
                document.getElementById('tableBody').innerHTML = '<tr><td colspan="6" style="text-align:center;color:red;">Ошибка загрузки данных</td></tr>';
            }
        }
        
        function displayTable(data) {
            if (!data.length) {
                document.getElementById('tableBody').innerHTML = '<tr><td colspan="6" style="text-align:center;">Нет данных</td></tr>';
                return;
            }
            
            let html = '';
            data.forEach((player, index) => {
                const date = new Date(player.registered_at).toLocaleString('ru-RU');
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${player.user_id}</td>
                        <td><strong>${player.real_name}</strong></td>
                        <td>@${player.nickname}</td>
                        <td style="color:#667eea;font-weight:bold;">${player.trophies} 🏆</td>
                        <td>${date}</td>
                    </tr>
                `;
            });
            document.getElementById('tableBody').innerHTML = html;
        }
        
        function filterTable() {
            const search = document.getElementById('search').value.toLowerCase();
            const filtered = playersData.filter(p => 
                p.real_name.toLowerCase().includes(search) ||
                p.nickname.toLowerCase().includes(search) ||
                p.user_id.toString().includes(search)
            );
            displayTable(filtered);
        }
        
        let sortColumn = 4;
        let sortAsc = false;
        
        function sortTable(col) {
            sortColumn = col;
            sortAsc = !sortAsc;
            
            const sorted = [...playersData];
            sorted.sort((a,b) => {
                let valA, valB;
                if (col === 1) { valA = a.user_id; valB = b.user_id; }
                else if (col === 2) { valA = a.real_name; valB = b.real_name; }
                else if (col === 3) { valA = a.nickname; valB = b.nickname; }
                else if (col === 4) { valA = a.trophies; valB = b.trophies; }
                else if (col === 5) { valA = a.registered_at; valB = b.registered_at; }
                else return 0;
                
                if (valA < valB) return sortAsc ? -1 : 1;
                if (valA > valB) return sortAsc ? 1 : -1;
                return 0;
            });
            displayTable(sorted);
        }
        
        loadData();
        setInterval(loadData, 30000);
    </script>
</body>
</html>
'''

# HTML для страницы с турнирной сеткой
BRACKET_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Турнирная сетка</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        h1 { color: #667eea; }
        .nav-buttons {
            display: flex;
            gap: 10px;
        }
        .nav-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
            display: inline-block;
        }
        .nav-btn.active {
            background: #667eea;
            color: white;
        }
        .nav-btn:not(.active) {
            background: #e0e0e0;
            color: #333;
        }
        .nav-btn:not(.active):hover {
            background: #ccc;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
            transform: translateY(-2px);
        }
        .btn-warning {
            background: #ffc107;
            color: #333;
        }
        .btn-warning:hover {
            background: #e0a800;
            transform: translateY(-2px);
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background: #c82333;
            transform: translateY(-2px);
        }
        .round {
            margin-bottom: 30px;
        }
        .round-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            color: #333;
        }
        .matches {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .match {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            transition: all 0.3s;
        }
        .match:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .match-players {
            display: flex;
            align-items: center;
            gap: 20px;
            flex: 2;
            flex-wrap: wrap;
        }
        .player {
            display: flex;
            align-items: center;
            gap: 10px;
            background: white;
            padding: 8px 15px;
            border-radius: 8px;
            min-width: 200px;
        }
        .player-name {
            font-weight: bold;
        }
        .player-trophies {
            color: #667eea;
            font-size: 12px;
        }
        .vs {
            font-weight: bold;
            color: #dc3545;
            font-size: 18px;
        }
        .match-result {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .result-input {
            width: 60px;
            padding: 8px;
            text-align: center;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        .winner-select {
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 5px;
            background: white;
        }
        .winner-badge {
            background: #28a745;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        .info-text {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .current-round {
            background: #e8f0fe;
            border-left: 4px solid #667eea;
        }
        @media (max-width: 768px) {
            .match-players {
                flex-direction: column;
                align-items: stretch;
            }
            .player {
                justify-content: space-between;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 Турнирная сетка Clash Royale</h1>
            <div class="nav-buttons">
                <a href="/" class="nav-btn">📋 Участники</a>
                <a href="/bracket" class="nav-btn active">🏆 Турнирная сетка</a>
            </div>
        </div>

        <div class="action-buttons">
            <button class="btn btn-primary" onclick="generateBracket()">🎲 Сгенерировать пары</button>
            <button class="btn btn-success" onclick="nextRound()">➡️ Следующий раунд</button>
            <button class="btn btn-warning" onclick="resetTournament()">🔄 Сбросить турнир</button>
        </div>

        <div id="bracket-container">
            <div class="info-text">Нажмите "Сгенерировать пары", чтобы начать турнир</div>
        </div>
    </div>

    <script>
        let tournamentData = null;
        
        async function loadBracket() {
            try {
                const response = await fetch('/api/bracket');
                tournamentData = await response.json();
                renderBracket();
            } catch(e) {
                console.error('Ошибка:', e);
            }
        }
        
        function renderBracket() {
            const container = document.getElementById('bracket-container');
            
            if (!tournamentData || !tournamentData.rounds || tournamentData.rounds.length === 0) {
                container.innerHTML = '<div class="info-text">🏆 Нажмите "Сгенерировать пары", чтобы создать турнирную сетку</div>';
                return;
            }
            
            let html = '';
            
            tournamentData.rounds.forEach((round, roundIndex) => {
                const isCurrentRound = roundIndex === tournamentData.current_round;
                html += `
                    <div class="round ${isCurrentRound ? 'current-round' : ''}">
                        <div class="round-title">
                            ${round.name}
                            ${isCurrentRound ? ' 🔥 ТЕКУЩИЙ РАУНД' : ''}
                        </div>
                        <div class="matches">
                `;
                
                round.matches.forEach((match, matchIndex) => {
                    html += renderMatch(match, roundIndex, matchIndex);
                });
                
                html += `
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function renderMatch(match, roundIndex, matchIndex) {
            if (!match.player1 && !match.player2) {
                return `
                    <div class="match">
                        <div class="match-players">
                            <div class="player">❌ Нет игроков</div>
                        </div>
                    </div>
                `;
            }
            
            const player1Name = match.player1 ? match.player1.real_name : 'Ожидание победителя';
            const player1Trophies = match.player1 ? match.player1.trophies : '';
            const player2Name = match.player2 ? match.player2.real_name : 'Ожидание победителя';
            const player2Trophies = match.player2 ? match.player2.trophies : '';
            
            let resultHtml = '';
            
            if (match.winner_id) {
                resultHtml = `
                    <div class="match-result">
                        <span class="winner-badge">🏆 Победитель: ${match.winner_name}</span>
                    </div>
                `;
            } else if (match.player1 && match.player2) {
                resultHtml = `
                    <div class="match-result">
                        <select class="winner-select" data-round="${roundIndex}" data-match="${matchIndex}" onchange="setWinner(this)">
                            <option value="">Выбрать победителя...</option>
                            <option value="${match.player1.user_id}">🏆 ${match.player1.real_name}</option>
                            <option value="${match.player2.user_id}">🏆 ${match.player2.real_name}</option>
                        </select>
                    </div>
                `;
            } else {
                resultHtml = `
                    <div class="match-result">
                        <span class="winner-badge">⏳ Ожидание...</span>
                    </div>
                `;
            }
            
            return `
                <div class="match">
                    <div class="match-players">
                        <div class="player">
                            <span class="player-name">${player1Name}</span>
                            ${player1Trophies ? `<span class="player-trophies">(${player1Trophies}🏆)</span>` : ''}
                        </div>
                        <div class="vs">VS</div>
                        <div class="player">
                            <span class="player-name">${player2Name}</span>
                            ${player2Trophies ? `<span class="player-trophies">(${player2Trophies}🏆)</span>` : ''}
                        </div>
                    </div>
                    ${resultHtml}
                </div>
            `;
        }
        
        async function generateBracket() {
            const response = await fetch('/api/generate_bracket', { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                await loadBracket();
            } else {
                alert(result.error || 'Ошибка при генерации пар');
            }
        }
        
        async function setWinner(selectElement) {
            const winnerId = selectElement.value;
            if (!winnerId) return;
            
            const roundIndex = parseInt(selectElement.dataset.round);
            const matchIndex = parseInt(selectElement.dataset.match);
            
            const response = await fetch('/api/set_winner', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    round_index: roundIndex,
                    match_index: matchIndex,
                    winner_id: parseInt(winnerId)
                })
            });
            
            const result = await response.json();
            if (result.success) {
                await loadBracket();
            } else {
                alert(result.error || 'Ошибка при установке победителя');
            }
        }
        
        async function nextRound() {
            const response = await fetch('/api/next_round', { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                await loadBracket();
            } else {
                alert(result.error || 'Нельзя перейти к следующему раунду');
            }
        }
        
        async function resetTournament() {
            if (confirm('Вы уверены? Это сбросит весь прогресс турнира.')) {
                const response = await fetch('/api/reset_tournament', { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    await loadBracket();
                } else {
                    alert(result.error || 'Ошибка при сбросе');
                }
            }
        }
        
        function getDbConnection() {
            // Эта функция будет заменена на серверную
            return null;
        }
        
        loadBracket();
        setInterval(loadBracket, 10000);
    </script>
</body>
</html>
'''

def get_db_connection():
    conn = sqlite3.connect('players.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_tournament_table():
    """Создает таблицу для хранения состояния турнира"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_round INTEGER DEFAULT 0,
            rounds_data TEXT DEFAULT '[]'
        )
    ''')
    conn.commit()
    conn.close()

def get_tournament_state():
    """Получает текущее состояние турнира"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT current_round, rounds_data FROM tournament_state WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        import json
        return {
            'current_round': row['current_round'],
            'rounds': json.loads(row['rounds_data']) if row['rounds_data'] else []
        }
    return {'current_round': 0, 'rounds': []}

def save_tournament_state(current_round, rounds):
    """Сохраняет состояние турнира"""
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO tournament_state (id, current_round, rounds_data)
        VALUES (1, ?, ?)
    ''', (current_round, json.dumps(rounds, ensure_ascii=False)))
    conn.commit()
    conn.close()

@app.route('/')
def admin_panel():
    return render_template_string(PLAYERS_PAGE)

@app.route('/bracket')
def bracket_panel():
    return render_template_string(BRACKET_PAGE)

@app.route('/api/players')
def get_players():
    conn = get_db_connection()
    players = conn.execute('''
        SELECT user_id, username, real_name, nickname, trophies, registered_at
        FROM players ORDER BY trophies DESC
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(p) for p in players])

@app.route('/api/stats')
def get_stats():
    conn = get_db_connection()
    total_players = conn.execute('SELECT COUNT(*) as count FROM players').fetchone()['count']
    total_trophies = conn.execute('SELECT SUM(trophies) as sum FROM players').fetchone()['sum'] or 0
    avg_trophies = conn.execute('SELECT AVG(trophies) as avg FROM players').fetchone()['avg'] or 0
    conn.close()
    
    return jsonify({
        'total_players': total_players,
        'total_trophies': total_trophies,
        'avg_trophies': round(avg_trophies, 2)
    })

@app.route('/api/bracket')
def get_bracket():
    """Возвращает текущее состояние турнирной сетки"""
    state = get_tournament_state()
    return jsonify(state)

@app.route('/api/generate_bracket', methods=['POST'])
def generate_bracket():
    """Генерирует пары для первого раунда"""
    try:
        conn = get_db_connection()
        players = conn.execute('''
            SELECT user_id, real_name, nickname, trophies
            FROM players ORDER BY trophies DESC
        ''').fetchall()
        conn.close()
        
        if len(players) < 2:
            return jsonify({'success': False, 'error': 'Нужно минимум 2 игрока для турнира'})
        
        # Перемешиваем игроков (или можно отсортировать по кубкам)
        players_list = [dict(p) for p in players]
        random.shuffle(players_list)
        
        # Создаем пары
        matches = []
        for i in range(0, len(players_list), 2):
            if i + 1 < len(players_list):
                matches.append({
                    'player1': players_list[i],
                    'player2': players_list[i + 1],
                    'winner_id': None,
                    'winner_name': None
                })
            else:
                # Игрок без пары - получает bye (автоматический проход)
                matches.append({
                    'player1': players_list[i],
                    'player2': None,
                    'winner_id': players_list[i]['user_id'],
                    'winner_name': players_list[i]['real_name']
                })
        
        rounds = [{
            'name': '1/8 финала' if len(matches) > 4 else ('1/4 финала' if len(matches) > 2 else 'Финал'),
            'matches': matches
        }]
        
        save_tournament_state(0, rounds)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/set_winner', methods=['POST'])
def set_winner():
    """Устанавливает победителя в матче"""
    try:
        data = request.get_json()
        round_index = data['round_index']
        match_index = data['match_index']
        winner_id = data['winner_id']
        
        state = get_tournament_state()
        
        if round_index >= len(state['rounds']):
            return jsonify({'success': False, 'error': 'Раунд не найден'})
        
        match = state['rounds'][round_index]['matches'][match_index]
        
        # Находим победителя
        winner = None
        if match['player1'] and match['player1']['user_id'] == winner_id:
            winner = match['player1']
        elif match['player2'] and match['player2']['user_id'] == winner_id:
            winner = match['player2']
        
        if winner:
            match['winner_id'] = winner_id
            match['winner_name'] = winner['real_name']
            save_tournament_state(state['current_round'], state['rounds'])
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Победитель не найден'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/next_round', methods=['POST'])
def next_round():
    """Переходит к следующему раунду"""
    try:
        state = get_tournament_state()
        
        if not state['rounds']:
            return jsonify({'success': False, 'error': 'Сначала сгенерируйте пары'})
        
        current_round = state['rounds'][state['current_round']]
        
        # Проверяем, что все матчи текущего раунда завершены
        for match in current_round['matches']:
            if match['player1'] and match['player2'] and not match['winner_id']:
                return jsonify({'success': False, 'error': 'Не все матчи текущего раунда завершены'})
        
        # Собираем победителей текущего раунда
        winners = []
        for match in current_round['matches']:
            if match['winner_id']:
                for player in [match['player1'], match['player2']]:
                    if player and player['user_id'] == match['winner_id']:
                        winners.append(player)
                        break
        
        if len(winners) < 2:
            # Турнир закончен
            if len(winners) == 1:
                return jsonify({'success': True, 'message': f'🏆 Турнир завершен! Победитель: {winners[0]["real_name"]} 🏆'})
            return jsonify({'success': False, 'error': 'Недостаточно победителей для следующего раунда'})
        
        # Создаем пары для следующего раунда
        new_matches = []
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                new_matches.append({
                    'player1': winners[i],
                    'player2': winners[i + 1],
                    'winner_id': None,
                    'winner_name': None
                })
            else:
                # Игрок без пары в следующем раунде
                new_matches.append({
                    'player1': winners[i],
                    'player2': None,
                    'winner_id': winners[i]['user_id'],
                    'winner_name': winners[i]['real_name']
                })
        
        # Определяем название раунда
        round_names = ['Финал', '1/2 финала', '1/4 финала', '1/8 финала', '1/16 финала']
        round_name = round_names[min(len(new_matches), len(round_names) - 1)]
        
        state['rounds'].append({
            'name': round_name,
            'matches': new_matches
        })
        state['current_round'] += 1
        
        save_tournament_state(state['current_round'], state['rounds'])
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reset_tournament', methods=['POST'])
def reset_tournament():
    """Сбрасывает турнир"""
    try:
        save_tournament_state(0, [])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    # Запускаем основной файл бота в фоновом режиме
    subprocess.Popen(["python", "main.py"])
    
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)

