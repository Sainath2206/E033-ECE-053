
# ECE-053 – Business Rules
Team: E033
Language: Python 3.12

BR-01: Load test catalogue from CSV.

BR-02: Load chamber details and daily capacity.

BR-03: Load holidays and exclude them from working days.

BR-04: Validate quote requests and test codes.

BR-05: EUT factor: 1 EUT = 1.0, 2–3 = 1.5, 4+ = 2.0.

BR-06: Calculate test hours and round upwards to 0.5 hours.

BR-07: Calculate test cost using hours × hourly rate.

BR-08: Add Rs 8,000 report fee for normal jobs.

BR-09: Retests within 30 days of the failed test's booked day receive 50% test cost and no report fee.

BR-10: Apply 5% discount for 3-4 tests and 10% for 5+ tests.

BR-11: Calculate discounts on gross test costs.

BR-12: Rush jobs receive 40% surcharge on gross test costs.

BR-13: Rush jobs must be fully scheduled within five working days after confirmation.

BR-14: Downgrade rush jobs if all tests cannot fit within the five-day window.

BR-15: Schedule only after confirmation.

BR-16: Schedule tests in catalogue order.

BR-17: Never split a test across multiple days.

BR-18: Add one hour setup per job per chamber per day.

BR-19: A quotation can be confirmed within 30 days, inclusive.

BR-20: Calculate GST at 18% on the final subtotal.

BR-21: Process commands in file order.

BR-22: Generate quotations.csv, quote_lines.csv,
chamber_calendar.csv and errors.csv in the exact required format.
