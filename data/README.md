# ECE-053 – EMC/EMI Test Lab Job Quoting and Scheduling Engine — Sample Data Pack
Prepared by 10 SECONDS for Team E033.

This pack is the input for an EMC test-lab quoting and scheduling engine: a 14-test catalogue on 2 chamber types, 3 chambers, and six weeks (2026-09-07 to 2026-10-16) of 25 quote requests, 19 confirmations and the test results needed for retests. Your engine reads `commands.txt`, prices every quote, books confirmed jobs into chamber-days at confirmation time, and prints the quotations and the chamber calendar.

Pack conventions where the brief is silent: working days are Monday–Friday except holidays.csv. Booking starts on the first working day AFTER the confirmation date; tests are booked one by one in catalogue order (T-01 … T-14) into the earliest working day that has room, trying chambers of the right type in chamber_id order; room = hours_per_day − hours already booked (setup included). Setup (1.0 h) is a scheduling cost, not billed. The rush window is the first 5 working days after confirmation. A quote is valid for 30 days: confirm date − quote date ≤ 30. Money: test cost = hours × rate; bundle discount and rush surcharge are both computed on the gross test costs; total = test costs − discount + surcharge + report fee; GST 18% on that total. A retest (retest_of ≠ NONE) of a test that FAILED is priced at 50% of the test cost with no report fee when its quote date is within 30 days (inclusive) of the failed test's booked day; otherwise it is priced like a normal job. Round every money line half up to 2 decimals.

## Files
| File | What it holds | Rows |
|---|---|---|
| test_catalogue.csv | Test catalogue (catalogue order = booking order) | 14 |
| chambers.csv | Test chambers | 3 |
| holidays.csv | Non-working days | 1 |
| commands.txt | Load commands, then dated QUOTE / CONFIRM / TEST_RESULT commands and the two print commands | 55 |

## Column reference
Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### test_catalogue.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| test_code | string | T-nn | T-01 … T-14 | Primary key; file order is catalogue order |
| test_name | string | - |  |  |
| standard | string | - | CISPR 25, CISPR 32, IEC 61000-x-y | Not used by any rule |
| chamber_type | string | - | SAC, SHIELDED | Which chambers can run it |
| base_hours | decimal | hours, 1 dp | 1.0–3.5 | × EUT factor, rounded up to 0.5 h |
| rate_per_hour_rs | decimal | Rs, 2 dp |  |  |

### chambers.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| chamber_id | string | CH-nn | CH-01 … CH-03 | Primary key |
| chamber_name | string | - |  |  |
| chamber_type | string | - | SAC, SHIELDED |  |
| hours_per_day | decimal | hours | 8.0 | Capacity of one chamber-day |

### holidays.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| date | date | YYYY-MM-DD |  | Not a working day |
| name | string | - |  |  |

## Command file format
`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored.

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_CATALOGUE / LOAD_CHAMBERS / LOAD_HOLIDAYS | file | Load the masters |
| QUOTE | date \| quote_id \| client \| product \| test_codes (semicolon-separated) \| eut_count \| rush Y/N \| retest_of (quote_id or NONE) | Price a job |
| CONFIRM | date \| quote_id | Book the quoted job (rejected if EXPIRED) |
| TEST_RESULT | date \| quote_id \| test_code \| PASS or FAIL | Record the outcome of a booked test |
| PRINT_QUOTATIONS | (none) | Print all quotations with their final status |
| PRINT_CALENDAR | from_date \| to_date | Print the chamber calendar |

Quote `status` is QUOTED (never confirmed), CONFIRMED, RUSH_CONFIRMED, DOWNGRADED or EXPIRED. For a DOWNGRADED quote, rush_surcharge_rs is 0.00 and the totals are the normal ones. `confirm_date` is NONE when not confirmed. `retest_50pct` is true/false. Error `reason` is EXPIRED or UNKNOWN_QUOTE.

## Planted scenarios
Line numbers count the header row as line 1, so the first data row of a CSV is line 2. For commands.txt the line number is the physical line in the file (comment lines included).

- **Exactly 3 EUTs and exactly 3 tests** — commands.txt line 8 (`QUOTE|2026-09-08|QT-003|Tejas Medical Devices|Infusion pump controller|T-05;T-06;T-08|3|N|NONE`): 3 EUTs → factor 1.5 (2–3 EUTs), 3 tests → 5% bundle discount (3–4 tests) on test costs; the Rs 8,000 report fee is not discounted.
- **Rush job when the window has capacity only on the fifth working day** — Rush commands.txt line 25 (`QUOTE|2026-09-16|QT-010|Kaveri Smart Meters|Single-phase smart energy meter|T-06|1|Y|NONE`) is confirmed at commands.txt line 28 (`CONFIRM|2026-09-17|QT-010`). Just before it, the same day, commands.txt line 23 (`QUOTE|2026-09-14|QT-008|Bharat Rail Electronics|Coach lighting inverter|T-05;T-06;T-07;T-08;T-09;T-10;T-11;T-12;T-13;T-14|4|N|NONE`) (all ten shielded-room tests for 4 EUTs) is confirmed and fills the shielded room for the next four working days (only 1.0 h left on the first). The rush job's single test (T-06, 1.5 h + 1.0 h setup) therefore first fits on 2026-09-24, which is exactly the 5th working day after confirmation (2026-09-18, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-24) → the rush is kept with the 40% surcharge. Compare rush commands.txt line 26 (`QUOTE|2026-09-16|QT-011|Kaveri Smart Meters|Single-phase smart energy meter|T-09;T-11|4|Y|NONE`), confirmed right after it at commands.txt line 29 (`CONFIRM|2026-09-17|QT-011`): T-09 (4.0 h + setup) takes the rest of that 5th day, so T-11 (3.0 h) falls on the 6th working day → not fully inside the window → DOWNGRADED, surcharge removed.
- **Test needing 7.0 hours in an 8-hour chamber day with 1 hour setup** — commands.txt line 17 (`QUOTE|2026-09-10|QT-006|Hampi Audio|Bluetooth soundbar|T-03|4|N|NONE`): T-03 base 3.5 h × 2.0 (4 EUTs) = 7.0 h; with the 1.0 h setup it needs exactly 8.0 h, so it books into an empty 8-hour chamber-day (2026-09-14, CH-02).
- **CONFIRM on the 30th day** — commands.txt line 10 (`QUOTE|2026-09-09|QT-004|Deccan Lighting|Street-light controller|T-01;T-02;T-07;T-10|2|N|NONE`) is confirmed exactly 30 days later at commands.txt line 51 (`CONFIRM|2026-10-09|QT-004`) → accepted. commands.txt line 19 (`QUOTE|2026-09-11|QT-007|Deccan Lighting|Street-light controller|T-12;T-13|1|N|NONE`) is confirmed 31 days later at commands.txt line 54 (`CONFIRM|2026-10-12|QT-007`) → EXPIRED, rejected, nothing booked.
- **Retest exactly 30 days after the original** — The original job commands.txt line 6 (`QUOTE|2026-09-07|QT-001|Bharat Rail Electronics|Coach lighting inverter|T-05;T-06;T-07;T-08;T-09;T-11|1|N|NONE`) has T-06 booked on 2026-09-09 and it FAILS (TEST_RESULT at line 12). The retest commands.txt line 50 (`QUOTE|2026-10-09|QT-024|Bharat Rail Electronics|Coach lighting inverter|T-06|1|N|QT-001`) is quoted exactly 30 days after that test → 50% of the test cost, no report fee.

Extra traps (realistic things your validation should catch):

- **Retest 12 days vs 31 days after the failure** — T-08 of the same job fails on 2026-09-09 (line 13); commands.txt line 31 (`QUOTE|2026-09-21|QT-012|Bharat Rail Electronics|Coach lighting inverter|T-08|1|N|QT-001`) (12 days later) is a 50% retest, while commands.txt line 52 (`QUOTE|2026-10-10|QT-025|Bharat Rail Electronics|Coach lighting inverter|T-08|1|N|QT-001`) (31 days later) is outside the 30-day window → full test cost plus report fee.
- **Unconfirmed quotes** — Five ordinary quotes are never confirmed (and the 31-day retest quote is not confirmed either); they appear in the quotation output but book nothing.
- **Holiday** — 2026-10-02 is in holidays.csv and is not a working day for booking or for the 5-working-day rush window.
- **Setup only once per job per chamber-day** — When two tests of the same job land on the same chamber-day, only the first carries the 1.0 h setup; tests of different jobs on the same day each pay their own setup.

## What is NOT in this pack
Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-07). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation
Produce these files (CSV, header row, same conventions as above). Column order matters.

### quotations.csv
One row per quote, ordered by quote_id.

Columns in order: `quote_id`, `quote_date`, `client`, `eut_count`, `test_count`, `gross_test_cost_rs`, `bundle_discount_rs`, `rush_surcharge_rs`, `report_fee_rs`, `subtotal_rs`, `gst_rs`, `total_rs`, `status`, `confirm_date`

### quote_lines.csv
One row per test per quote, in catalogue order.

Columns in order: `quote_id`, `test_code`, `hours`, `rate_per_hour_rs`, `line_cost_rs`, `retest_50pct`

### chamber_calendar.csv
One row per booked test, ordered by date, chamber_id, booking order.

Columns in order: `date`, `chamber_id`, `quote_id`, `test_code`, `test_hours`, `setup_hours`, `day_hours_used`

### errors.csv
Rejected commands.

Columns in order: `line_no`, `command`, `quote_id`, `reason`
