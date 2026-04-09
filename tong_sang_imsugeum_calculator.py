#!/usr/bin/env python3
"""통상임금 계산기

이 스크립트는 월 급여와 근로일수, 1일 근로시간을 입력하면 통상임금과 시급, 연장/야간/휴일 수당을 계산합니다.
"""

from __future__ import annotations


def parse_positive_float(prompt: str, default: float | None = None) -> float:
    while True:
        try:
            raw = input(prompt).strip()
            if raw == "" and default is not None:
                return default
            value = float(raw)
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("값을 다시 입력하세요. 0보다 큰 숫자를 입력해야 합니다.")


def format_won(value: float) -> str:
    return f"{value:,.0f}원"


def calculate_regular_wage(monthly_salary: float, working_days_per_month: float) -> float:
    return monthly_salary / working_days_per_month


def calculate_hourly_wage(daily_wage: float, daily_hours: float) -> float:
    return daily_wage / daily_hours


def calculate_overtime_pay(hourly_wage: float, overtime_hours: float, rate: float = 1.5) -> float:
    return hourly_wage * overtime_hours * rate


def main() -> None:
    print("\n=== 통상임금 계산기 ===\n")
    monthly_salary = parse_positive_float("월 급여를 입력하세요 (예: 3000000): ")
    working_days = parse_positive_float("월 근무일수를 입력하세요 (예: 22): ")
    daily_hours = parse_positive_float("1일 통상 근로시간을 입력하세요 (예: 8): ")

    print("\n--- 추가 정보 (선택) ---")
    overtime_hours = parse_positive_float("이번 달 연장근로 시간을 입력하세요 (없으면 0): ", default=0.0)
    night_hours = parse_positive_float("이번 달 야간근로 시간을 입력하세요 (없으면 0): ", default=0.0)
    holiday_hours = parse_positive_float("이번 달 휴일근로 시간을 입력하세요 (없으면 0): ", default=0.0)

    daily_wage = calculate_regular_wage(monthly_salary, working_days)
    hourly_wage = calculate_hourly_wage(daily_wage, daily_hours)
    overtime_pay = calculate_overtime_pay(hourly_wage, overtime_hours, 1.5)
    night_pay = calculate_overtime_pay(hourly_wage, night_hours, 1.5)
    holiday_pay = calculate_overtime_pay(hourly_wage, holiday_hours, 2.0)
    total_pay = monthly_salary + overtime_pay + night_pay + holiday_pay

    print("\n=== 계산 결과 ===")
    print(f"월 급여: {format_won(monthly_salary)}")
    print(f"통상임금(일평균): {format_won(daily_wage)}")
    print(f"통상임금(시급): {format_won(hourly_wage)}")
    print(f"연장근로 수당: {format_won(overtime_pay)}")
    print(f"야간근로 수당: {format_won(night_pay)}")
    print(f"휴일근로 수당: {format_won(holiday_pay)}")
    print(f"총 예상 급여: {format_won(total_pay)}")

    print("\n참고: 통상임금은 회사의 임금 지급 기준에 따라 달라질 수 있습니다. 이 계산기는 일반적인 한국 노동법 기준을 기반으로 한 예시입니다.")


if __name__ == "__main__":
    main()
