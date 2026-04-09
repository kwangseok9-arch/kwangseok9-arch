#!/usr/bin/env python3
"""통상임금 계산기 (CLI + 웹 공용 계산 함수 포함)."""

from __future__ import annotations


def parse_non_negative_float(prompt: str, default: float | None = None) -> float:
    while True:
        try:
            raw = input(prompt).strip()
            if raw == "" and default is not None:
                return default
            value = float(raw)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("0 이상의 숫자를 입력해주세요.")


def parse_positive_float(prompt: str) -> float:
    while True:
        value = parse_non_negative_float(prompt)
        if value > 0:
            return value
        print("0보다 큰 숫자를 입력해주세요.")


def format_won(value: float) -> str:
    return f"{value:,.0f}원"


def calculate_regular_wage(monthly_salary: float, working_days_per_month: float) -> float:
    return monthly_salary / working_days_per_month


def calculate_hourly_wage(daily_wage: float, daily_hours: float) -> float:
    return daily_wage / daily_hours


def calculate_allowance(hourly_wage: float, hours: float, rate: float) -> float:
    return hourly_wage * hours * rate


def calculate_wage_breakdown(
    monthly_salary: float,
    working_days: float,
    daily_hours: float,
    overtime_hours: float = 0.0,
    night_hours: float = 0.0,
    holiday_hours: float = 0.0,
) -> dict[str, float]:
    daily_wage = calculate_regular_wage(monthly_salary, working_days)
    hourly_wage = calculate_hourly_wage(daily_wage, daily_hours)
    overtime_pay = calculate_allowance(hourly_wage, overtime_hours, 1.5)
    night_pay = calculate_allowance(hourly_wage, night_hours, 1.5)
    holiday_pay = calculate_allowance(hourly_wage, holiday_hours, 2.0)
    total_pay = monthly_salary + overtime_pay + night_pay + holiday_pay

    return {
        "monthly_salary": monthly_salary,
        "daily_wage": daily_wage,
        "hourly_wage": hourly_wage,
        "overtime_pay": overtime_pay,
        "night_pay": night_pay,
        "holiday_pay": holiday_pay,
        "total_pay": total_pay,
    }


def main() -> None:
    print("\n=== 통상임금 계산기 ===\n")
    monthly_salary = parse_positive_float("월 기본급여를 입력하세요 (예: 3000000): ")
    working_days = parse_positive_float("월 근무일수를 입력하세요 (예: 22): ")
    daily_hours = parse_positive_float("1일 소정근로시간을 입력하세요 (예: 8): ")

    print("\n--- 추가 정보 (선택) ---")
    overtime_hours = parse_non_negative_float("월 연장근로 시간을 입력하세요 (없으면 0): ", default=0.0)
    night_hours = parse_non_negative_float("월 야간근로 시간을 입력하세요 (없으면 0): ", default=0.0)
    holiday_hours = parse_non_negative_float("월 휴일근로 시간을 입력하세요 (없으면 0): ", default=0.0)

    result = calculate_wage_breakdown(
        monthly_salary=monthly_salary,
        working_days=working_days,
        daily_hours=daily_hours,
        overtime_hours=overtime_hours,
        night_hours=night_hours,
        holiday_hours=holiday_hours,
    )

    print("\n=== 계산 결과 ===")
    print(f"월 기본급여: {format_won(result['monthly_salary'])}")
    print(f"일 통상임금: {format_won(result['daily_wage'])}")
    print(f"시 통상임금: {format_won(result['hourly_wage'])}")
    print(f"연장근로 수당: {format_won(result['overtime_pay'])}")
    print(f"야간근로 수당: {format_won(result['night_pay'])}")
    print(f"휴일근로 수당: {format_won(result['holiday_pay'])}")
    print(f"총 예상 급여: {format_won(result['total_pay'])}")

    print(
        "\n참고: 통상임금 산정은 회사의 임금 지급 기준과 법 해석에 따라 달라질 수 있습니다. "
        "이 계산기는 일반적인 가정 기반의 참고용입니다."
    )


if __name__ == "__main__":
    main()
