import csv

from pathlib import Path

from datetime import date, timedelta

from decimal import Decimal, ROUND_HALF_UP

from engine import (

    calculate_eut_factor,

    calculate_test_hours,

    calculate_test_cost

)

# ==========================================

# ECE-053 - EMC TEST LAB MANAGEMENT SYSTEM

# COMMAND PROCESSOR

# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR = BASE_DIR

# ==========================================

# 1. CONSTANTS AND OUTPUT COLUMNS

# ==========================================

QUOTATION_COLUMNS = [

    "quote_id",

    "quote_date",

    "client",

    "eut_count",

    "test_count",

    "gross_test_cost_rs",

    "bundle_discount_rs",

    "rush_surcharge_rs",

    "report_fee_rs",

    "subtotal_rs",

    "gst_rs",

    "total_rs",

    "status",

    "confirm_date"

]

QUOTE_LINE_COLUMNS = [

    "quote_id",

    "test_code",

    "hours",

    "rate_per_hour_rs",

    "line_cost_rs",

    "retest_50pct"

]

CALENDAR_COLUMNS = [

    "date",

    "chamber_id",

    "quote_id",

    "test_code",

    "test_hours",

    "setup_hours",

    "day_hours_used"

]

ERROR_COLUMNS = [

    "line_no",

    "command",

    "quote_id",

    "reason"

]

ZERO = Decimal("0.00")

REPORT_FEE = Decimal("8000.00")

GST_RATE = Decimal("0.18")

RUSH_RATE = Decimal("0.40")

SETUP_HOURS = Decimal("1.0")

DAY_LIMIT = Decimal("8.0")

# ==========================================

# 2. HELPER FUNCTIONS

# ==========================================

def money(value):

    return Decimal(str(value)).quantize(

        Decimal("0.01"),

        rounding=ROUND_HALF_UP

    )

def decimal_text(value):

    return str(Decimal(str(value)).quantize(

        Decimal("0.01"),

        rounding=ROUND_HALF_UP

    ))

def hour_text(value):

    return str(Decimal(str(value)).quantize(

        Decimal("0.1"),

        rounding=ROUND_HALF_UP

    ))

def is_working_day(day, holidays):

    return (

        day.weekday() < 5

        and day.isoformat() not in holidays

    )

def next_working_day(day, holidays):

    current = day + timedelta(days=1)

    while not is_working_day(current, holidays):

        current += timedelta(days=1)

    return current

def get_working_days(start_day, holidays, count):

    days = []

    current = start_day

    while len(days) < count:

        if is_working_day(current, holidays):

            days.append(current)

        current += timedelta(days=1)

    return days

def read_commands_with_line_numbers():

    path = DATA_DIR / "commands.txt"

    commands = []

    with path.open(

        "r",

        encoding="utf-8-sig"

    ) as file:

        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            if not line or line.startswith("#"):

                continue

            commands.append({

                "line_no": line_number,

                "raw": line,

                "parts": line.split("|")

            })

    return commands

# ==========================================

# 3. INITIALIZE PROCESSING STATE

# ==========================================

def initialize_processor(data):

    catalogue = sorted(

        data["catalogue"],

        key=lambda item: item["test_code"]

    )

    chambers = sorted(

        data["chambers"],

        key=lambda item: item["chamber_id"]

    )

    return {

        "catalogue": catalogue,

        "tests": {

            test["test_code"]: test

            for test in catalogue

        },

        "chambers": chambers,

        "holidays": {

            holiday["date"]

            for holiday in data["holidays"]

        },

        "quotations": {},

        "quote_lines": [],

        "calendar": [],

        "failed_tests": {},

        "test_results": {},

        "confirmed_quotes": set(),

        "errors": [],

        "booking_order": 0

    }

# ==========================================

# 4. CALCULATE QUOTATION PRICING

# ==========================================

def calculate_pricing(gross, test_count, rush, retest):

    gross = money(gross)

    if retest:

        discount = ZERO

        report_fee = ZERO

    elif test_count >= 5:

        discount = money(gross * Decimal("0.10"))

        report_fee = REPORT_FEE

    elif test_count >= 3:

        discount = money(gross * Decimal("0.05"))

        report_fee = REPORT_FEE

    else:

        discount = ZERO

        report_fee = REPORT_FEE

    surcharge = (

        money(gross * RUSH_RATE)

        if rush and not retest

        else ZERO

    )

    subtotal = money(

        gross - discount + surcharge + report_fee

    )

    gst = money(subtotal * GST_RATE)

    total = money(subtotal + gst)

    return {

        "gross_test_cost_rs": gross,

        "bundle_discount_rs": discount,

        "rush_surcharge_rs": surcharge,

        "report_fee_rs": report_fee,

        "subtotal_rs": subtotal,

        "gst_rs": gst,

        "total_rs": total

    }

# ==========================================

# 5. CHECK RETEST ELIGIBILITY

# ==========================================

def is_eligible_retest(

    quote_day,

    retest_of,

    test_code,

    state

):

    if retest_of.upper() == "NONE":

        return False

    key = (retest_of, test_code)

    if key not in state["failed_tests"]:

        return False

    failed_day = state["failed_tests"][key]

    difference = (quote_day - failed_day).days

    return 0 <= difference <= 30

# ==========================================

# 6. PROCESS QUOTE COMMAND

# ==========================================

def process_quote(parts, state):

    if len(parts) != 9:

        return

    (

        command,

        quote_date,

        quote_id,

        client,

        product,

        test_codes_raw,

        eut_count_raw,

        rush_raw,

        retest_of

    ) = parts

    quote_day = date.fromisoformat(quote_date)

    if not quote_id.strip():

        raise ValueError("Empty quotation ID.")

    if quote_id in state["quotations"]:

        raise ValueError("Duplicate quotation ID.")

    eut_count = int(eut_count_raw)

    if eut_count < 1:

        raise ValueError("Invalid EUT count.")

    rush_raw = rush_raw.upper()

    if rush_raw not in ("Y", "N"):

        raise ValueError("Invalid rush flag.")

    test_codes = [

        code.strip()

        for code in test_codes_raw.split(";")

        if code.strip()

    ]

    if not test_codes:

        raise ValueError("No tests specified.")

    if len(test_codes) != len(set(test_codes)):

        raise ValueError("Duplicate test codes.")

    for code in test_codes:

        if code not in state["tests"]:

            raise ValueError(f"Unknown test code: {code}")

    # Always use catalogue order.

    test_codes.sort(

        key=lambda code: next(

            index

            for index, test in enumerate(state["catalogue"])

            if test["test_code"] == code

        )

    )

    eut_factor = calculate_eut_factor(eut_count)

    quote_lines = []

    gross = ZERO

    retest_flags = []

    for code in test_codes:

        test = state["tests"][code]

        hours = calculate_test_hours(

            test["base_hours"],

            eut_factor

        )

        rate = Decimal(test["rate_per_hour_rs"])

        original_cost = calculate_test_cost(

            hours,

            rate

        )

        eligible = is_eligible_retest(

            quote_day,

            retest_of,

            code,

            state

        )

        line_cost = (

            money(original_cost * Decimal("0.50"))

            if eligible

            else original_cost

        )

        gross += line_cost

        retest_flags.append(eligible)

        quote_lines.append({

            "quote_id": quote_id,

            "test_code": code,

            "hours": hours,

            "rate_per_hour_rs": rate,

            "line_cost_rs": line_cost,

            "retest_50pct": eligible

        })

    # A quotation receives retest pricing only when

    # every requested test is an eligible retest.

    is_retest = bool(retest_flags) and all(retest_flags)

    # If only some tests are eligible, keep their

    # individual half-price line costs, but do not

    # remove the report fee for the entire job.

    pricing = calculate_pricing(

        gross,

        len(test_codes),

        rush=(rush_raw == "Y"),

        retest=is_retest

    )

    state["quotations"][quote_id] = {

        "quote_id": quote_id,

        "quote_date": quote_date,

        "client": client,

        "product": product,

        "eut_count": eut_count,

        "test_count": len(test_codes),

        "test_codes": test_codes,

        "retest_of": retest_of,

        "rush": rush_raw == "Y",

        "is_retest": is_retest,

        "confirm_date": "NONE",

        "status": "QUOTED",

        **pricing

    }

    state["quote_lines"].extend(quote_lines)

    print("QUOTE CREATED:", quote_id)

# ==========================================

# 7. GET CHAMBER USAGE

# ==========================================

def get_day_usage(calendar, day, chamber_id):

    return sum(

        (

            item["test_hours"] + item["setup_hours"]

            for item in calendar

            if item["date"] == day

            and item["chamber_id"] == chamber_id

        ),

        ZERO

    )

def has_job_setup(calendar, day, chamber_id, quote_id):

    return any(

        item["date"] == day

        and item["chamber_id"] == chamber_id

        and item["quote_id"] == quote_id

        for item in calendar

    )

# ==========================================

# 8. SCHEDULE ONE TEST

# ==========================================

def schedule_one_test(

    quote,

    quote_line,

    calendar,

    state,

    allowed_days=None

):

    test = state["tests"][quote_line["test_code"]]

    matching_chambers = [

        chamber

        for chamber in state["chambers"]

        if chamber["chamber_type"] == test["chamber_type"]

    ]

    if not matching_chambers:

        return False

    holidays = state["holidays"]

    if allowed_days is None:

        start_day = next_working_day(

            date.fromisoformat(quote["confirm_date"]),

            holidays

        )

        allowed_days = []

        current = start_day

        for _ in range(3650):

            if is_working_day(current, holidays):

                allowed_days.append(current)

            current += timedelta(days=1)

    for day in allowed_days:

        for chamber in matching_chambers:

            chamber_id = chamber["chamber_id"]

            capacity = Decimal(chamber["hours_per_day"])

            setup = (

                ZERO

                if has_job_setup(

                    calendar,

                    day,

                    chamber_id,

                    quote["quote_id"]

                )

                else SETUP_HOURS

            )

            test_hours = Decimal(str(quote_line["hours"]))

            used = get_day_usage(

                calendar,

                day,

                chamber_id

            )

            required = test_hours + setup

            if used + required <= capacity:

                new_used = used + required

                state["booking_order"] += 1

                calendar.append({

                    "date": day,

                    "chamber_id": chamber_id,

                    "quote_id": quote["quote_id"],

                    "test_code": quote_line["test_code"],

                    "test_hours": test_hours,

                    "setup_hours": setup,

                    "day_hours_used": new_used,

                    "booking_order": state["booking_order"]

                })

                return True

    return False

# ==========================================

# 9. SCHEDULE COMPLETE JOB

# ==========================================

def schedule_job(quote, state, rush_window=False):

    quote_lines = [

        line

        for line in state["quote_lines"]

        if line["quote_id"] == quote["quote_id"]

    ]

    # Sort tests according to the catalogue order

    catalogue_order = {

        test_code: index

        for index, test_code in enumerate(state["tests"])

    }

    quote_lines.sort(

        key=lambda line: catalogue_order.get(

            line["test_code"],

            float("inf")

        )

    )

    holidays = state["holidays"]

    start_day = next_working_day(

        date.fromisoformat(quote["confirm_date"]),

        holidays

    )

    if rush_window:

        allowed_days = get_working_days(

            start_day,

            holidays,

            5

        )

    else:

        allowed_days = None

    temporary_calendar = list(state["calendar"])

    original_order = state["booking_order"]

    for line in quote_lines:

        success = schedule_one_test(

            quote,

            line,

            temporary_calendar,

            state,

            allowed_days

        )

        if not success:

            state["booking_order"] = original_order

            return False

    state["calendar"] = temporary_calendar

    return True

# ==========================================

# 10. PROCESS CONFIRM COMMAND

# ==========================================

def process_confirm(parts, state):

    if len(parts) != 3:

        return

    command, confirm_date, quote_id = parts

    confirmation_day = date.fromisoformat(confirm_date)

    if quote_id not in state["quotations"]:

        raise LookupError("UNKNOWN_QUOTE")

    quote = state["quotations"][quote_id]

    quote_day = date.fromisoformat(quote["quote_date"])

    if (confirmation_day - quote_day).days > 30:

        quote["status"] = "EXPIRED"

        quote["confirm_date"] = "NONE"

        raise ValueError("EXPIRED")

    if confirmation_day < quote_day:

        raise ValueError("Invalid confirmation date.")

    if quote_id in state["confirmed_quotes"]:

        raise ValueError("Quotation already confirmed.")

    quote["confirm_date"] = confirm_date

    state["confirmed_quotes"].add(quote_id)

    if quote["rush"]:

        success = schedule_job(

            quote,

            state,

            rush_window=True

        )

        if success:

            quote["status"] = "RUSH_CONFIRMED"

        else:

            # Remove rush surcharge and recalculate.

            quote["status"] = "DOWNGRADED"

            pricing = calculate_pricing(

                quote["gross_test_cost_rs"],

                quote["test_count"],

                rush=False,

                retest=quote["is_retest"]

            )

            quote.update(pricing)

            if not schedule_job(

                quote,

                state,

                rush_window=False

            ):

                raise RuntimeError(

                    "Unable to schedule downgraded job."

                )

    else:

        if not schedule_job(

            quote,

            state,

            rush_window=False

        ):

            raise RuntimeError(

                "Unable to schedule confirmed job."

            )

        quote["status"] = "CONFIRMED"

    print(

        "CONFIRMATION:",

        quote_id,

        quote["status"]

    )

# ==========================================

# 11. PROCESS TEST RESULT COMMAND

# ==========================================

def process_test_result(parts, state):

    if len(parts) != 5:

        return

    command, result_date, quote_id, test_code, result = parts

    date.fromisoformat(result_date)

    result = result.upper()

    if result not in ("PASS", "FAIL"):

        raise ValueError("Result must be PASS or FAIL.")

    if quote_id not in state["quotations"]:

        raise LookupError("UNKNOWN_QUOTE")

    if quote_id not in state["confirmed_quotes"]:

        raise ValueError("Quotation is not confirmed.")

    if test_code not in state["quotations"][quote_id]["test_codes"]:

        raise ValueError("Test does not belong to quotation.")

    booking = next(

        (

            item for item in state["calendar"]

            if item["quote_id"] == quote_id

            and item["test_code"] == test_code

        ),

        None

    )

    if booking is None:

        raise ValueError("Test has not been booked.")

    key = (quote_id, test_code)

    if key in state["test_results"]:

        raise ValueError("Test result already recorded.")

    state["test_results"][key] = result

    if result == "FAIL":

        # Eligibility is based on the booked day,

        # not the result-entry date.

        state["failed_tests"][key] = booking["date"]

    print(

        "TEST RESULT:",

        quote_id,

        test_code,

        result

    )

# ==========================================

# 12. PROCESS COMMANDS IN FILE ORDER

# ==========================================

def process_commands(state):

    commands = read_commands_with_line_numbers()

    for entry in commands:

        parts = entry["parts"]

        command_type = parts[0].upper()

        line_no = entry["line_no"]

        raw_command = entry["raw"]

        quote_id = (

            parts[2]

            if command_type in ("QUOTE", "CONFIRM", "TEST_RESULT")

            and len(parts) > 2

            else ""

        )

        try:

            if command_type in (

                "LOAD_CATALOGUE",

                "LOAD_CHAMBERS",

                "LOAD_HOLIDAYS"

            ):

                continue

            elif command_type == "QUOTE":

                process_quote(parts, state)

            elif command_type == "CONFIRM":

                process_confirm(parts, state)

            elif command_type == "TEST_RESULT":

                process_test_result(parts, state)

            elif command_type == "PRINT_QUOTATIONS":

                print_quotations(state)

            elif command_type == "PRINT_CALENDAR":

                if len(parts) == 3:

                    print_calendar(

                        parts[1],

                        parts[2],

                        state

                    )

        except LookupError:

            state["errors"].append({

                "line_no": line_no,

                "command": raw_command,

                "quote_id": quote_id,

                "reason": "UNKNOWN_QUOTE"

            })

        except ValueError as error:

            if str(error) == "EXPIRED":

                reason = "EXPIRED"

            else:

                print(

                    f"Command error at line {line_no}:",

                    error

                )

                continue

            state["errors"].append({

                "line_no": line_no,

                "command": raw_command,

                "quote_id": quote_id,

                "reason": reason

            })

# ==========================================

# 13. PRINT QUOTATIONS

# ==========================================

def print_quotations(state):

    print("\n========== QUOTATIONS ==========")

    for quote_id in sorted(state["quotations"]):

        quote = state["quotations"][quote_id]

        print(

            quote_id,

            quote["status"],

            "Rs.",

            decimal_text(quote["total_rs"])

        )

    print("================================\n")

# ==========================================

# 14. PRINT CHAMBER CALENDAR

# ==========================================

def print_calendar(from_date, to_date, state):

    start = date.fromisoformat(from_date)

    end = date.fromisoformat(to_date)

    print("\n========== CHAMBER CALENDAR ==========")

    bookings = sorted(

        state["calendar"],

        key=lambda item: (

            item["date"],

            item["chamber_id"],

            item["booking_order"]

        )

    )

    for booking in bookings:

        if start <= booking["date"] <= end:

            print(

                booking["date"],

                booking["chamber_id"],

                booking["quote_id"],

                booking["test_code"],

                "Hours:",

                hour_text(booking["test_hours"])

            )

    print("======================================\n")

# ==========================================

# 15. GENERATE CSV FILE

# ==========================================

def write_csv(filename, columns, rows):

    path = OUTPUT_DIR / filename

    with path.open(

        "w",

        encoding="utf-8",

        newline=""

    ) as file:

        writer = csv.DictWriter(

            file,

            fieldnames=columns

        )

        writer.writeheader()

        writer.writerows(rows)

# ==========================================

# 16. GENERATE QUOTATIONS CSV

# ==========================================

def generate_quotations_csv(state):

    rows = []

    for quote_id in sorted(state["quotations"]):

        quote = state["quotations"][quote_id]

        rows.append({

            "quote_id": quote["quote_id"],

            "quote_date": quote["quote_date"],

            "client": quote["client"],

            "eut_count": quote["eut_count"],

            "test_count": quote["test_count"],

            "gross_test_cost_rs":

                decimal_text(quote["gross_test_cost_rs"]),

            "bundle_discount_rs":

                decimal_text(quote["bundle_discount_rs"]),

            "rush_surcharge_rs":

                decimal_text(quote["rush_surcharge_rs"]),

            "report_fee_rs":

                decimal_text(quote["report_fee_rs"]),

            "subtotal_rs":

                decimal_text(quote["subtotal_rs"]),

            "gst_rs":

                decimal_text(quote["gst_rs"]),

            "total_rs":

                decimal_text(quote["total_rs"]),

            "status": quote["status"],

            "confirm_date": quote["confirm_date"]

        })

    write_csv(

        "quotations.csv",

        QUOTATION_COLUMNS,

        rows

    )

# ==========================================

# 17. GENERATE QUOTE LINES CSV

# ==========================================

def generate_quote_lines_csv(state):

    rows = []

    for line in state["quote_lines"]:

        rows.append({

            "quote_id": line["quote_id"],

            "test_code": line["test_code"],

            "hours": hour_text(line["hours"]),

            "rate_per_hour_rs":

                decimal_text(line["rate_per_hour_rs"]),

            "line_cost_rs":

                decimal_text(line["line_cost_rs"]),

            "retest_50pct":

                str(line["retest_50pct"]).lower()

        })

    rows.sort(

        key=lambda row: (

            row["quote_id"],

            row["test_code"]

        )

    )

    write_csv(

        "quote_lines.csv",

        QUOTE_LINE_COLUMNS,

        rows

    )

# ==========================================

# 18. GENERATE CHAMBER CALENDAR CSV

# ==========================================

def generate_chamber_calendar_csv(state):

    bookings = sorted(

        state["calendar"],

        key=lambda item: (

            item["date"],

            item["chamber_id"],

            item["booking_order"]

        )

    )

    rows = []

    for item in bookings:

        rows.append({

            "date": item["date"].isoformat(),

            "chamber_id": item["chamber_id"],

            "quote_id": item["quote_id"],

            "test_code": item["test_code"],

            "test_hours":

                hour_text(item["test_hours"]),

            "setup_hours":

                hour_text(item["setup_hours"]),

            "day_hours_used":

                hour_text(item["day_hours_used"])

        })

    write_csv(

        "chamber_calendar.csv",

        CALENDAR_COLUMNS,

        rows

    )

# ==========================================

# 19. GENERATE ERRORS CSV

# ==========================================

def generate_errors_csv(state):

    rows = sorted(

        state["errors"],

        key=lambda item: item["line_no"]

    )

    write_csv(

        "errors.csv",

        ERROR_COLUMNS,

        rows

    )

# ==========================================

# 20. RUN COMPLETE PROCESSOR

# ==========================================

def run_processor(data):

    print("\n================================")

    print("EMC TEST LAB PROCESSOR STARTED")

    print("================================\n")

    state = initialize_processor(data)

    process_commands(state)

    generate_quotations_csv(state)

    generate_quote_lines_csv(state)

    generate_chamber_calendar_csv(state)

    generate_errors_csv(state)

    print("\n================================")

    print("PROCESSING COMPLETED")

    print("================================")

    print("Total quotations:", len(state["quotations"]))

    print("Total bookings:", len(state["calendar"]))

    print("Rejected commands:", len(state["errors"]))

    print("\nGenerated files:")

    print("1. quotations.csv")

    print("2. quote_lines.csv")

    print("3. chamber_calendar.csv")

    print("4. errors.csv")

    print("\n================================\n")

    return state
