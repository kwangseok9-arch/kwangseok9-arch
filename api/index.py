from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Flask, render_template_string, request

from tong_sang_imsugeum_calculator import calculate_wage_breakdown, format_won

app = Flask(__name__)

TETRIS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tetris</title>
  <style>
    :root {
      --bg: #0b1220;
      --panel: #111827;
      --line: #1f2937;
      --text: #e5e7eb;
      --accent: #22c55e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background:
        radial-gradient(circle at 15% 20%, #1e3a8a 0%, rgba(30,58,138,0) 45%),
        radial-gradient(circle at 85% 80%, #14532d 0%, rgba(20,83,45,0) 45%),
        var(--bg);
      color: var(--text);
      font-family: Consolas, Menlo, monospace;
      padding: 20px;
    }
    .wrap {
      display: flex;
      gap: 16px;
      align-items: flex-start;
      width: min(920px, 100%);
    }
    canvas {
      background: #020617;
      border: 2px solid #334155;
      border-radius: 8px;
      width: min(75vw, 300px);
      height: min(150vw, 600px);
      image-rendering: pixelated;
    }
    .side {
      flex: 1;
      background: rgba(17, 24, 39, 0.82);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      backdrop-filter: blur(4px);
    }
    h1 { margin: 0 0 10px; font-size: 26px; letter-spacing: 1px; }
    .meta { line-height: 1.8; margin-bottom: 10px; }
    .btns { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 14px; }
    button, a.link {
      border: 1px solid #334155;
      border-radius: 8px;
      background: #0f172a;
      color: var(--text);
      padding: 8px 10px;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
    }
    button:hover, a.link:hover { border-color: var(--accent); }
    .warn { color: #fca5a5; min-height: 20px; }
    @media (max-width: 760px) {
      .wrap { flex-direction: column; align-items: center; }
      .side { width: min(520px, 100%); }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <canvas id="game" width="300" height="600"></canvas>
    <aside class="side">
      <h1>TETRIS</h1>
      <div class="meta">
        Score: <span id="score">0</span><br />
        Lines: <span id="lines">0</span><br />
        Speed: <span id="speed">450</span>ms
      </div>
      <div class="btns">
        <button id="restart">Restart (R)</button>
        <a class="link" href="/">Wage Calculator</a>
        <a class="link" href="/childcare-calculator">Childcare Calculator</a>
      </div>
      <div>Controls</div>
      <div>
        Left/Right: Move<br />
        Up: Rotate<br />
        Down: Soft drop<br />
        Space: Hard drop
      </div>
      <div class="warn" id="status"></div>
    </aside>
  </div>

  <script>
    const W = 10, H = 20, CELL = 30;
    const SHAPES = {
      I: [[0,1],[1,1],[2,1],[3,1]],
      O: [[1,0],[2,0],[1,1],[2,1]],
      T: [[1,0],[0,1],[1,1],[2,1]],
      S: [[1,0],[2,0],[0,1],[1,1]],
      Z: [[0,0],[1,0],[1,1],[2,1]],
      J: [[0,0],[0,1],[1,1],[2,1]],
      L: [[2,0],[0,1],[1,1],[2,1]],
    };
    const COLORS = {
      I: '#38BDF8', O: '#FACC15', T: '#A78BFA',
      S: '#4ADE80', Z: '#FB7185', J: '#60A5FA', L: '#FB923C'
    };

    const cv = document.getElementById('game');
    const cx = cv.getContext('2d');
    const scoreEl = document.getElementById('score');
    const linesEl = document.getElementById('lines');
    const speedEl = document.getElementById('speed');
    const statusEl = document.getElementById('status');

    let board, piece, score, lines, gameOver, tickMs, timer;

    function newBoard() {
      return Array.from({length: H}, () => Array(W).fill(null));
    }

    function pickPiece() {
      const keys = Object.keys(SHAPES);
      const name = keys[Math.floor(Math.random() * keys.length)];
      return { name, cells: SHAPES[name].map(c => [...c]), x: 3, y: 0 };
    }

    function rotate(cells) {
      const cx = 1.5, cy = 1.5;
      return cells.map(([x, y]) => [Math.round(cx - (y - cy)), Math.round(cy + (x - cx))]);
    }

    function blocks(p) {
      return p.cells.map(([x, y]) => [x + p.x, y + p.y]);
    }

    function collides(p) {
      for (const [x, y] of blocks(p)) {
        if (x < 0 || x >= W || y >= H) return true;
        if (y >= 0 && board[y][x] !== null) return true;
      }
      return false;
    }

    function tryMove(dx=0, dy=0, rot=false) {
      if (gameOver) return false;
      const cand = {
        name: piece.name,
        cells: rot ? rotate(piece.cells) : piece.cells.map(c => [...c]),
        x: piece.x + dx,
        y: piece.y + dy,
      };
      if (!collides(cand)) {
        piece = cand;
        return true;
      }
      return false;
    }

    function lockPiece() {
      for (const [x, y] of blocks(piece)) {
        if (y < 0) {
          gameOver = true;
          statusEl.textContent = 'Game Over - Press R';
          stopTick();
          return;
        }
        board[y][x] = COLORS[piece.name];
      }
      clearLines();
      piece = pickPiece();
      if (collides(piece)) {
        gameOver = true;
        statusEl.textContent = 'Game Over - Press R';
        stopTick();
      }
    }

    function clearLines() {
      const next = board.filter(row => row.some(cell => cell === null));
      const cleared = H - next.length;
      while (next.length < H) next.unshift(Array(W).fill(null));
      board = next;
      if (cleared > 0) {
        lines += cleared;
        const pts = {1:100,2:300,3:500,4:800};
        score += pts[cleared] || cleared * 200;
        tickMs = Math.max(100, 450 - Math.floor(lines / 5) * 30);
        restartTick();
      }
    }

    function drawCell(x, y, color) {
      cx.fillStyle = color;
      cx.fillRect(x * CELL, y * CELL, CELL, CELL);
      cx.strokeStyle = '#1e293b';
      cx.lineWidth = 2;
      cx.strokeRect(x * CELL, y * CELL, CELL, CELL);
    }

    function draw() {
      cx.clearRect(0, 0, cv.width, cv.height);
      for (let y = 0; y < H; y++) {
        for (let x = 0; x < W; x++) {
          const c = board[y][x];
          if (c) drawCell(x, y, c);
          else {
            cx.strokeStyle = '#1e293b';
            cx.lineWidth = 1;
            cx.strokeRect(x * CELL, y * CELL, CELL, CELL);
          }
        }
      }
      for (const [x, y] of blocks(piece)) {
        if (y >= 0) drawCell(x, y, COLORS[piece.name]);
      }
      scoreEl.textContent = score;
      linesEl.textContent = lines;
      speedEl.textContent = tickMs;
    }

    function step() {
      if (!tryMove(0, 1)) lockPiece();
      draw();
    }

    function stopTick() {
      if (timer) clearInterval(timer);
      timer = null;
    }

    function restartTick() {
      stopTick();
      if (!gameOver) timer = setInterval(step, tickMs);
    }

    function hardDrop() {
      while (tryMove(0, 1)) score += 2;
      lockPiece();
      draw();
    }

    function reset() {
      board = newBoard();
      piece = pickPiece();
      score = 0;
      lines = 0;
      gameOver = false;
      tickMs = 450;
      statusEl.textContent = '';
      draw();
      restartTick();
    }

    window.addEventListener('keydown', (e) => {
      const key = e.key.toLowerCase();
      if (key === 'r') return reset();
      if (gameOver) return;
      if (key === 'arrowleft') tryMove(-1, 0);
      else if (key === 'arrowright') tryMove(1, 0);
      else if (key === 'arrowdown') {
        if (tryMove(0, 1)) score += 1;
      }
      else if (key === 'arrowup') tryMove(0, 0, true);
      else if (key === ' ') {
        e.preventDefault();
        hardDrop();
      }
      draw();
    });

    document.getElementById('restart').addEventListener('click', reset);
    reset();
  </script>
</body>
</html>
"""

CALCULATOR_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Wage Calculator</title>
  <style>
    body {
      font-family: "Segoe UI", sans-serif;
      background: #f7f9fc;
      color: #1f2937;
      margin: 0;
      padding: 24px;
    }
    .card {
      max-width: 700px;
      margin: 0 auto;
      background: white;
      border-radius: 14px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      padding: 24px;
    }
    h1 { margin-top: 0; font-size: 24px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    label { font-size: 14px; display: block; margin-bottom: 6px; color: #4b5563; }
    input {
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-size: 14px;
    }
    .actions { margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
    button, a {
      background: #0f766e;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px 14px;
      cursor: pointer;
      font-size: 14px;
      text-decoration: none;
      display: inline-block;
    }
    a { background: #334155; }
    .error {
      margin-top: 12px;
      color: #b91c1c;
      background: #fef2f2;
      border: 1px solid #fecaca;
      padding: 10px;
      border-radius: 8px;
    }
    .result {
      margin-top: 18px;
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 10px;
      padding: 12px 14px;
      line-height: 1.8;
    }
    @media (max-width: 640px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="card">
    <h1>Wage Calculator</h1>
    <form method="post">
      <div class="grid">
        <div>
          <label for="monthly_salary">Monthly Base Salary</label>
          <input id="monthly_salary" name="monthly_salary" type="number" min="1" step="any" value="{{ values.monthly_salary }}" required />
        </div>
        <div>
          <label for="working_days">Working Days per Month</label>
          <input id="working_days" name="working_days" type="number" min="1" step="any" value="{{ values.working_days }}" required />
        </div>
        <div>
          <label for="daily_hours">Regular Daily Hours</label>
          <input id="daily_hours" name="daily_hours" type="number" min="1" step="any" value="{{ values.daily_hours }}" required />
        </div>
        <div>
          <label for="overtime_hours">Overtime Hours</label>
          <input id="overtime_hours" name="overtime_hours" type="number" min="0" step="any" value="{{ values.overtime_hours }}" />
        </div>
        <div>
          <label for="night_hours">Night Hours</label>
          <input id="night_hours" name="night_hours" type="number" min="0" step="any" value="{{ values.night_hours }}" />
        </div>
        <div>
          <label for="holiday_hours">Holiday Hours</label>
          <input id="holiday_hours" name="holiday_hours" type="number" min="0" step="any" value="{{ values.holiday_hours }}" />
        </div>
      </div>
      <div class="actions">
        <button type="submit">Calculate</button>
        <a href="/tetris">Go to Tetris</a>
        <a href="/childcare-calculator">Childcare Calculator</a>
      </div>
    </form>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    {% if result %}
      <div class="result">
        Monthly Base Salary: {{ result.monthly_salary }}<br />
        Daily Wage: {{ result.daily_wage }}<br />
        Hourly Wage: {{ result.hourly_wage }}<br />
        Overtime Pay: {{ result.overtime_pay }}<br />
        Night Pay: {{ result.night_pay }}<br />
        Holiday Pay: {{ result.holiday_pay }}<br />
        Expected Total: <strong>{{ result.total_pay }}</strong>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

CHILDCARE_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>육아휴직/육아기 근로시간 단축 사용일수 계산기</title>
  <style>
    body {
      font-family: "Segoe UI", sans-serif;
      background: #f8fafc;
      color: #0f172a;
      margin: 0;
      padding: 24px;
    }
    .card {
      max-width: 920px;
      margin: 0 auto;
      background: white;
      border-radius: 14px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      padding: 24px;
    }
    h1 { margin: 0 0 8px; font-size: 24px; }
    p.tip { margin: 0 0 14px; color: #475569; font-size: 14px; }
    h2 { font-size: 18px; margin: 18px 0 10px; }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 12px;
      margin-bottom: 10px;
    }
    label { font-size: 13px; color: #475569; display: block; margin-bottom: 6px; }
    input {
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      font-size: 14px;
    }
    .actions {
      margin-top: 12px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    button, a {
      border: none;
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 14px;
      text-decoration: none;
      color: white;
      background: #0f766e;
      cursor: pointer;
    }
    a { background: #334155; }
    .error {
      margin-top: 14px;
      color: #b91c1c;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 8px;
      padding: 10px;
    }
    .result {
      margin-top: 16px;
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 10px;
      padding: 12px 14px;
      line-height: 1.9;
    }
    .muted { color: #64748b; font-size: 13px; margin-top: 8px; }
    @media (max-width: 760px) {
      .row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>육아휴직 / 육아기 근로시간 단축 사용일수 계산기</h1>
    <p class="tip">각 제도별 총 부여일수와 사용기간(시작~종료)을 입력하면 사용일수와 잔여일수를 계산합니다. 시작일과 종료일을 모두 포함해 계산합니다.</p>

    <form method="post">
      <h2>1) 육아휴직</h2>
      <div class="row">
        <div>
          <label for="leave_total_days">총 부여일수(일)</label>
          <input id="leave_total_days" name="leave_total_days" type="number" min="0" step="1" value="{{ values.leave_total_days }}" required />
        </div>
      </div>
      <div class="row">
        <div>
          <label for="leave_1_start">기간1 시작일</label>
          <input id="leave_1_start" name="leave_1_start" type="date" value="{{ values.leave_1_start }}" />
        </div>
        <div>
          <label for="leave_1_end">기간1 종료일</label>
          <input id="leave_1_end" name="leave_1_end" type="date" value="{{ values.leave_1_end }}" />
        </div>
      </div>
      <div class="row">
        <div>
          <label for="leave_2_start">기간2 시작일</label>
          <input id="leave_2_start" name="leave_2_start" type="date" value="{{ values.leave_2_start }}" />
        </div>
        <div>
          <label for="leave_2_end">기간2 종료일</label>
          <input id="leave_2_end" name="leave_2_end" type="date" value="{{ values.leave_2_end }}" />
        </div>
      </div>
      <div class="row">
        <div>
          <label for="leave_3_start">기간3 시작일</label>
          <input id="leave_3_start" name="leave_3_start" type="date" value="{{ values.leave_3_start }}" />
        </div>
        <div>
          <label for="leave_3_end">기간3 종료일</label>
          <input id="leave_3_end" name="leave_3_end" type="date" value="{{ values.leave_3_end }}" />
        </div>
      </div>

      <h2>2) 육아기 근로시간 단축</h2>
      <div class="row">
        <div>
          <label for="short_total_days">총 부여일수(일)</label>
          <input id="short_total_days" name="short_total_days" type="number" min="0" step="1" value="{{ values.short_total_days }}" required />
        </div>
      </div>
      <div class="row">
        <div>
          <label for="short_1_start">기간1 시작일</label>
          <input id="short_1_start" name="short_1_start" type="date" value="{{ values.short_1_start }}" />
        </div>
        <div>
          <label for="short_1_end">기간1 종료일</label>
          <input id="short_1_end" name="short_1_end" type="date" value="{{ values.short_1_end }}" />
        </div>
      </div>
      <div class="row">
        <div>
          <label for="short_2_start">기간2 시작일</label>
          <input id="short_2_start" name="short_2_start" type="date" value="{{ values.short_2_start }}" />
        </div>
        <div>
          <label for="short_2_end">기간2 종료일</label>
          <input id="short_2_end" name="short_2_end" type="date" value="{{ values.short_2_end }}" />
        </div>
      </div>
      <div class="row">
        <div>
          <label for="short_3_start">기간3 시작일</label>
          <input id="short_3_start" name="short_3_start" type="date" value="{{ values.short_3_start }}" />
        </div>
        <div>
          <label for="short_3_end">기간3 종료일</label>
          <input id="short_3_end" name="short_3_end" type="date" value="{{ values.short_3_end }}" />
        </div>
      </div>

      <div class="actions">
        <button type="submit">계산하기</button>
        <a href="/">임금 계산기</a>
        <a href="/tetris">테트리스</a>
      </div>
    </form>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    {% if result %}
      <div class="result">
        [육아휴직] 사용일수: <strong>{{ result.leave_used }}</strong>일 /
        잔여일수: <strong>{{ result.leave_remaining }}</strong>일
        {% if result.leave_exceeded > 0 %}
          (초과 {{ result.leave_exceeded }}일)
        {% endif %}
        <br />
        [육아기 근로시간 단축] 사용일수: <strong>{{ result.short_used }}</strong>일 /
        잔여일수: <strong>{{ result.short_remaining }}</strong>일
        {% if result.short_exceeded > 0 %}
          (초과 {{ result.short_exceeded }}일)
        {% endif %}
        <br />
        [합계] 사용일수: <strong>{{ result.total_used }}</strong>일 /
        잔여일수: <strong>{{ result.total_remaining }}</strong>일
      </div>
      <div class="muted">안내: 이 계산기는 입력한 총 부여일수 기준으로 산술 계산한 참고값입니다.</div>
    {% endif %}
  </div>
</body>
</html>
"""


def _to_float(form_value: str | None, field_name: str, minimum: float) -> float:
    if form_value is None or form_value == "":
        return 0.0 if minimum == 0 else float("nan")

    value = float(form_value)
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    return value


def _to_int(form_value: str | None, field_name: str, minimum: int) -> int:
    if form_value is None or form_value == "":
        raise ValueError(f"{field_name} 값을 입력해주세요.")
    value = int(form_value)
    if value < minimum:
        raise ValueError(f"{field_name} 값은 {minimum} 이상이어야 합니다.")
    return value


def _parse_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} 날짜 형식이 올바르지 않습니다.") from exc


def _extract_periods(values: dict[str, str], prefix: str, title: str) -> list[tuple[date, date]]:
    periods: list[tuple[date, date]] = []
    for idx in range(1, 4):
        start_raw = values.get(f"{prefix}_{idx}_start", "").strip()
        end_raw = values.get(f"{prefix}_{idx}_end", "").strip()

        if not start_raw and not end_raw:
            continue
        if not start_raw or not end_raw:
            raise ValueError(f"{title} 기간{idx}의 시작일/종료일을 모두 입력해주세요.")

        start_date = _parse_date(start_raw, f"{title} 기간{idx} 시작일")
        end_date = _parse_date(end_raw, f"{title} 기간{idx} 종료일")
        if end_date < start_date:
            raise ValueError(f"{title} 기간{idx} 종료일은 시작일보다 빠를 수 없습니다.")

        periods.append((start_date, end_date))
    return periods


def _count_unique_days(periods: list[tuple[date, date]]) -> int:
    if not periods:
        return 0

    sorted_periods = sorted(periods, key=lambda item: item[0])
    merged: list[list[date]] = [[sorted_periods[0][0], sorted_periods[0][1]]]

    for start_date, end_date in sorted_periods[1:]:
        _, last_end = merged[-1]
        if start_date <= last_end + timedelta(days=1):
            merged[-1][1] = max(last_end, end_date)
        else:
            merged.append([start_date, end_date])

    return sum((end_date - start_date).days + 1 for start_date, end_date in merged)


@app.route("/tetris")
def tetris_page():
    return render_template_string(TETRIS_HTML)


@app.route("/", methods=["GET", "POST"])
@app.route("/calculator", methods=["GET", "POST"])
def calculator_page():
    values = {
        "monthly_salary": "",
        "working_days": "",
        "daily_hours": "",
        "overtime_hours": "0",
        "night_hours": "0",
        "holiday_hours": "0",
    }
    error = ""
    result = None

    if request.method == "POST":
        values.update({key: request.form.get(key, "") for key in values.keys()})
        try:
            monthly_salary = _to_float(values["monthly_salary"], "Monthly Base Salary", 1)
            working_days = _to_float(values["working_days"], "Working Days", 1)
            daily_hours = _to_float(values["daily_hours"], "Regular Daily Hours", 1)
            overtime_hours = _to_float(values["overtime_hours"], "Overtime Hours", 0)
            night_hours = _to_float(values["night_hours"], "Night Hours", 0)
            holiday_hours = _to_float(values["holiday_hours"], "Holiday Hours", 0)

            breakdown = calculate_wage_breakdown(
                monthly_salary=monthly_salary,
                working_days=working_days,
                daily_hours=daily_hours,
                overtime_hours=overtime_hours,
                night_hours=night_hours,
                holiday_hours=holiday_hours,
            )
            result = {key: format_won(value) for key, value in breakdown.items()}
        except Exception:
            error = "Please check your input. Salary/days/hours must be >= 1."

    return render_template_string(CALCULATOR_HTML, values=values, error=error, result=result)


@app.route("/childcare-calculator", methods=["GET", "POST"])
def childcare_calculator_page():
    values = {
        "leave_total_days": "0",
        "leave_1_start": "",
        "leave_1_end": "",
        "leave_2_start": "",
        "leave_2_end": "",
        "leave_3_start": "",
        "leave_3_end": "",
        "short_total_days": "0",
        "short_1_start": "",
        "short_1_end": "",
        "short_2_start": "",
        "short_2_end": "",
        "short_3_start": "",
        "short_3_end": "",
    }
    error = ""
    result = None

    if request.method == "POST":
        values.update({key: request.form.get(key, "") for key in values.keys()})
        try:
            leave_total_days = _to_int(values["leave_total_days"], "육아휴직 총 부여일수", 0)
            short_total_days = _to_int(values["short_total_days"], "육아기 근로시간 단축 총 부여일수", 0)

            leave_periods = _extract_periods(values, "leave", "육아휴직")
            short_periods = _extract_periods(values, "short", "육아기 근로시간 단축")

            leave_used = _count_unique_days(leave_periods)
            short_used = _count_unique_days(short_periods)

            leave_remaining = max(leave_total_days - leave_used, 0)
            short_remaining = max(short_total_days - short_used, 0)
            leave_exceeded = max(leave_used - leave_total_days, 0)
            short_exceeded = max(short_used - short_total_days, 0)

            result = {
                "leave_used": leave_used,
                "leave_remaining": leave_remaining,
                "leave_exceeded": leave_exceeded,
                "short_used": short_used,
                "short_remaining": short_remaining,
                "short_exceeded": short_exceeded,
                "total_used": leave_used + short_used,
                "total_remaining": leave_remaining + short_remaining,
            }
        except Exception as exc:
            error = str(exc)

    return render_template_string(CHILDCARE_HTML, values=values, error=error, result=result)


if __name__ == "__main__":
    app.run()
