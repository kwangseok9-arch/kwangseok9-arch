from __future__ import annotations

from flask import Flask, render_template_string, request

from tong_sang_imsugeum_calculator import calculate_wage_breakdown, format_won

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>통상임금 계산기</title>
  <style>
    body {
      font-family: "Segoe UI", sans-serif;
      background: #f7f9fc;
      color: #1f2937;
      margin: 0;
      padding: 24px;
    }
    .card {
      max-width: 680px;
      margin: 0 auto;
      background: white;
      border-radius: 14px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      padding: 24px;
    }
    h1 { margin-top: 0; font-size: 24px; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    label { font-size: 14px; display: block; margin-bottom: 6px; color: #4b5563; }
    input {
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-size: 14px;
    }
    .actions { margin-top: 16px; }
    button {
      background: #0f766e;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px 14px;
      cursor: pointer;
      font-size: 14px;
    }
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
    @media (max-width: 640px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>통상임금 계산기</h1>
    <form method="post">
      <div class="grid">
        <div>
          <label for="monthly_salary">월 기본급여 (원)</label>
          <input id="monthly_salary" name="monthly_salary" type="number" min="1" step="any" value="{{ values.monthly_salary }}" required />
        </div>
        <div>
          <label for="working_days">월 근무일수</label>
          <input id="working_days" name="working_days" type="number" min="1" step="any" value="{{ values.working_days }}" required />
        </div>
        <div>
          <label for="daily_hours">1일 소정근로시간</label>
          <input id="daily_hours" name="daily_hours" type="number" min="1" step="any" value="{{ values.daily_hours }}" required />
        </div>
        <div>
          <label for="overtime_hours">월 연장근로 시간</label>
          <input id="overtime_hours" name="overtime_hours" type="number" min="0" step="any" value="{{ values.overtime_hours }}" />
        </div>
        <div>
          <label for="night_hours">월 야간근로 시간</label>
          <input id="night_hours" name="night_hours" type="number" min="0" step="any" value="{{ values.night_hours }}" />
        </div>
        <div>
          <label for="holiday_hours">월 휴일근로 시간</label>
          <input id="holiday_hours" name="holiday_hours" type="number" min="0" step="any" value="{{ values.holiday_hours }}" />
        </div>
      </div>
      <div class="actions">
        <button type="submit">계산하기</button>
      </div>
    </form>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    {% if result %}
      <div class="result">
        월 기본급여: {{ result.monthly_salary }}<br />
        일 통상임금: {{ result.daily_wage }}<br />
        시 통상임금: {{ result.hourly_wage }}<br />
        연장근로 수당: {{ result.overtime_pay }}<br />
        야간근로 수당: {{ result.night_pay }}<br />
        휴일근로 수당: {{ result.holiday_pay }}<br />
        총 예상 급여: <strong>{{ result.total_pay }}</strong>
      </div>
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
        raise ValueError(f"{field_name} 값은 {minimum} 이상이어야 합니다.")
    return value


@app.route("/", methods=["GET", "POST"])
def home():
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
            monthly_salary = _to_float(values["monthly_salary"], "월 기본급여", 1)
            working_days = _to_float(values["working_days"], "월 근무일수", 1)
            daily_hours = _to_float(values["daily_hours"], "1일 소정근로시간", 1)
            overtime_hours = _to_float(values["overtime_hours"], "월 연장근로 시간", 0)
            night_hours = _to_float(values["night_hours"], "월 야간근로 시간", 0)
            holiday_hours = _to_float(values["holiday_hours"], "월 휴일근로 시간", 0)

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
            error = "입력값을 다시 확인해주세요. 기본급여/근무일수/근로시간은 1 이상이어야 합니다."

    return render_template_string(HTML, values=values, error=error, result=result)


if __name__ == "__main__":
    app.run()
