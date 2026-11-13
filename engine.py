
import csv
from pathlib import Path
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from datetime import date


# ==========================================
# ECE-053 - EMC TEST LAB MANAGEMENT SYSTEM
# CORE PROCESSING ENGINE
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# ==========================================
# 1. READ CSV FILES
# ==========================================

def read_csv_file(filename):

    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {filename}"
        )

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        return list(reader)


# ==========================================
# 2. READ COMMAND FILE
# ==========================================

def read_commands():

    file_path = DATA_DIR / "commands.txt"

    if not file_path.exists():
        raise FileNotFoundError(
            "Required file not found: commands.txt"
        )

    commands = []

    with file_path.open(
        mode="r",
        encoding="utf-8-sig"
    ) as file:

        for line in file:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            commands.append(line.split("|"))

    return commands


# ==========================================
# 3. LOAD PROJECT INPUT DATA
# ==========================================

def load_inputs():

    chambers = read_csv_file("chambers.csv")
    catalogue = read_csv_file("test_catalogue.csv")
    holidays = read_csv_file("holidays.csv")
    commands = read_commands()

    return {
        "chambers": chambers,
        "catalogue": catalogue,
        "holidays": holidays,
        "commands": commands
    }


# ==========================================
# 4. DISPLAY INITIAL DATA SUMMARY
# ==========================================

def display_data_summary(data):

    print("\n===== EMC TEST LAB SYSTEM =====")

    print("Chambers loaded:", len(data["chambers"]))
    print("Tests in catalogue:", len(data["catalogue"]))
    print("Holidays loaded:", len(data["holidays"]))
    print("Commands loaded:", len(data["commands"]))

    print("===============================\n")


# ==========================================
# 5. PREPARE DATA LOOKUPS
# ==========================================

def prepare_lookups(data):

    test_lookup = {
        test["test_code"]: test
        for test in data["catalogue"]
    }

    chamber_lookup = {
        chamber["chamber_id"]: chamber
        for chamber in data["chambers"]
    }

    holiday_dates = {
        holiday["date"]
        for holiday in data["holidays"]
    }

    return {
        "tests": test_lookup,
        "chambers": chamber_lookup,
        "holidays": holiday_dates
    }


# ==========================================
# 6. VALIDATE INPUT DATA
# ==========================================

def validate_input_data(data):

    lookups = prepare_lookups(data)

    errors = []

    if not lookups["tests"]:
        errors.append("Test catalogue is empty.")

    if not lookups["chambers"]:
        errors.append("Chamber list is empty.")

    if not lookups["holidays"]:
        print("Warning: No holidays configured.")

    for test in data["catalogue"]:

        try:
            base_hours = Decimal(test["base_hours"])
            rate = Decimal(test["rate_per_hour_rs"])

            if base_hours <= 0 or rate < 0:
                raise ValueError

        except (ValueError, KeyError):
            errors.append(
                f"Invalid numeric values for test: "
                f"{test.get('test_code', 'UNKNOWN')}"
            )

    for chamber in data["chambers"]:

        try:
            capacity = Decimal(chamber["hours_per_day"])

            if capacity <= 0:
                raise ValueError

        except (ValueError, KeyError):
            errors.append(
                f"Invalid chamber capacity: "
                f"{chamber.get('chamber_id', 'UNKNOWN')}"
            )

    if errors:

        for error in errors:
            print("ERROR:", error)

        raise ValueError("Input validation failed.")

    return lookups


# ==========================================
# 7. EUT FACTOR CALCULATION (BR-05)
# ==========================================

def calculate_eut_factor(eut_count):

    eut_count = int(eut_count)

    if eut_count < 1:
        raise ValueError("EUT count must be at least 1.")

    if eut_count == 1:
        return Decimal("1.0")

    elif eut_count <= 3:
        return Decimal("1.5")

    else:
        return Decimal("2.0")


# ==========================================
# 8. TEST HOURS CALCULATION (BR-06)
# ==========================================

def calculate_test_hours(base_hours, eut_factor):

    raw_hours = (
        Decimal(str(base_hours))
        * Decimal(str(eut_factor))
    )

    rounded_hours = (
        (raw_hours * 2).to_integral_value(
            rounding=ROUND_CEILING
        )
        / Decimal("2")
    )

    return rounded_hours


# ==========================================
# 9. TEST COST CALCULATION (BR-07)
# ==========================================

def calculate_test_cost(test_hours, rate_per_hour):

    cost = (
        Decimal(str(test_hours))
        * Decimal(str(rate_per_hour))
    )

    return cost.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ==========================================
# 10. QUOTATION PRICING
# BR-08, BR-09, BR-10, BR-11, BR-12, BR-20
# ==========================================

def calculate_quote_pricing(
    gross_test_cost,
    test_count,
    rush=False,
    is_retest=False
):

    gross = Decimal(str(gross_test_cost))

    if gross < 0 or test_count < 0:
        raise ValueError(
            "Invalid quotation amount or test count."
        )

    # Bundle discount

    if 3 <= test_count <= 4:
        discount_rate = Decimal("0.05")

    elif test_count >= 5:
        discount_rate = Decimal("0.10")

    else:
        discount_rate = Decimal("0.00")

    bundle_discount = gross * discount_rate

    # Retest discount (BR-09)

    if is_retest:

        bundle_discount = Decimal("0.00")
        retest_discount = gross * Decimal("0.50")

    else:

        retest_discount = Decimal("0.00")

    # Rush surcharge (BR-12)

    rush_surcharge = (
        gross * Decimal("0.40")
        if rush and not is_retest
        else Decimal("0.00")
    )

    # Report fee (BR-08)

    report_fee = (
        Decimal("0.00")
        if is_retest
        else Decimal("8000.00")
    )

    # Final subtotal

    subtotal = (
        gross
        - bundle_discount
        - retest_discount
        + rush_surcharge
        + report_fee
    )

    # GST (BR-20)

    gst = subtotal * Decimal("0.18")

    total = subtotal + gst

    def money(value):

        return value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    return {
        "gross_test_cost_rs": money(gross),
        "bundle_discount_rs": money(bundle_discount),
        "retest_discount_rs": money(retest_discount),
        "rush_surcharge_rs": money(rush_surcharge),
        "report_fee_rs": money(report_fee),
        "subtotal_rs": money(subtotal),
        "gst_rs": money(gst),
        "total_rs": money(total)
    }


# ==========================================
# 11. COMMAND PROCESSING STORAGE
# ==========================================

def initialize_state(data):

    return {
        "lookups": prepare_lookups(data),
        "quotations": {},
        "confirmed_quotes": set(),
        "failed_tests": {},
        "quote_lines": [],
        "chamber_calendar": [],
        "errors": [],
        "booking_order": 0
    }


# ==========================================
# 12. COMMAND VALIDATION
# ==========================================

def validate_command(command):

    if not command:
        return False

    command_type = command[0].strip().upper()

    required_arguments = {

        "LOAD_CATALOGUE": 2,
        "LOAD_CHAMBERS": 2,
        "LOAD_HOLIDAYS": 2,
        "QUOTE": 9,
        "CONFIRM": 3,
        "TEST_RESULT": 5,
        "PRINT_QUOTATIONS": 1,
        "PRINT_CALENDAR": 3
    }

    if command_type not in required_arguments:
        return False

    return len(command) == required_arguments[command_type]


# ==========================================
# 13. PROCESS QUOTE COMMAND
# ==========================================

def process_quote(command, state):

    if not validate_command(command):
        raise ValueError("Invalid QUOTE command format.")

    (
        command_type,
        quote_date,
        quote_id,
        client,
        product,
        test_codes_raw,
        eut_count,
        rush_flag,
        retest_of
    ) = command

    # Validate quotation date

    quote_day = date.fromisoformat(quote_date)

    # Validate quotation ID

    if not quote_id.strip():
        raise ValueError("Quotation ID cannot be empty.")

    if quote_id in state["quotations"]:
        raise ValueError(
            f"Duplicate quote ID: {quote_id}"
        )

    # Validate client and product

    if not client.strip() or not product.strip():
        raise ValueError(
            "Client and product cannot be empty."
        )

    # Read test codes

    test_codes = [
        code.strip()
        for code in test_codes_raw.split(";")
        if code.strip()
    ]

    if not test_codes:
        raise ValueError(
            "At least one test is required."
        )

    if len(test_codes) != len(set(test_codes)):
        raise ValueError(
            "Duplicate test codes are not allowed."
        )

    # Validate EUT count

    eut_count = int(eut_count)

    if eut_count < 1:
        raise ValueError(
            "EUT count must be at least 1."
        )

    # Validate rush flag

    rush_flag = rush_flag.strip().upper()

    if rush_flag not in ("Y", "N"):
        raise ValueError(
            "Rush flag must be Y or N."
        )

    # Determine retest status

    is_retest = retest_of.strip().upper() != "NONE"

    # Validate test codes against catalogue

    catalogue = state["lookups"]["tests"]

    for code in test_codes:

        if code not in catalogue:
            raise ValueError(
                f"Unknown test code: {code}"
            )

    # Validate retest eligibility (BR-09)

    if is_retest:

        for code in test_codes:

            failed_key = (retest_of, code)

            if failed_key not in state["failed_tests"]:
                raise ValueError(
                    f"No recorded failed test: {code} "
                    f"in quotation {retest_of}"
                )

            failed_day = date.fromisoformat(
                state["failed_tests"][failed_key]
            )

            days_difference = (
                quote_day - failed_day
            ).days

            if not 0 <= days_difference <= 30:
                raise ValueError(
                    f"Retest for {code} is outside "
                    "the 30-day eligibility period."
                )

    # Calculate EUT factor

    eut_factor = calculate_eut_factor(eut_count)

    gross_cost = Decimal("0.00")

    new_quote_lines = []

    # Calculate individual test costs

    for code in test_codes:

        test = catalogue[code]

        hours = calculate_test_hours(
            test["base_hours"],
            eut_factor
        )

        rate = Decimal(
            test["rate_per_hour_rs"]
        )

        line_cost = calculate_test_cost(
            hours,
            rate
        )

        gross_cost += line_cost

        new_quote_lines.append({

            "quote_id": quote_id,
            "test_code": code,
            "hours": hours,
            "rate_per_hour_rs": rate,
            "line_cost_rs": line_cost,
            "retest_50pct": is_retest

        })

    # Calculate quotation pricing

    pricing = calculate_quote_pricing(
        gross_cost,
        len(test_codes),
        rush=(rush_flag == "Y"),
        is_retest=is_retest
    )

    # Store quotation

    quotation = {

        "quote_id": quote_id,
        "quote_date": quote_date,
        "client": client,
        "product": product,
        "test_codes": test_codes,
        "eut_count": eut_count,
        "test_count": len(test_codes),

        "gross_test_cost_rs":
            pricing["gross_test_cost_rs"],

        "bundle_discount_rs":
            pricing["bundle_discount_rs"],

        "retest_discount_rs":
            pricing["retest_discount_rs"],

        "rush_surcharge_rs":
            pricing["rush_surcharge_rs"],

        "report_fee_rs":
            pricing["report_fee_rs"],

        "subtotal_rs":
            pricing["subtotal_rs"],

        "gst_rs":
            pricing["gst_rs"],

        "total_rs":
            pricing["total_rs"],

        "status": "QUOTED",

        "confirm_date": "NONE",

        "rush": rush_flag == "Y",

        "retest_of": retest_of

    }

    state["quotations"][quote_id] = quotation

    state["quote_lines"].extend(new_quote_lines)

    # Display quotation details

    print("\n===== QUOTATION CREATED =====")

    print("Quotation ID:", quote_id)
    print("Client:", client)
    print("Product:", product)
    print("Number of tests:", len(test_codes))

    print(
        "Gross cost:",
        pricing["gross_test_cost_rs"]
    )

    print(
        "Bundle discount:",
        pricing["bundle_discount_rs"]
    )

    print(
        "Retest discount:",
        pricing["retest_discount_rs"]
    )

    print(
        "Rush surcharge:",
        pricing["rush_surcharge_rs"]
    )

    print(
        "Report fee:",
        pricing["report_fee_rs"]
    )

    print(
        "Subtotal:",
        pricing["subtotal_rs"]
    )

    print(
        "GST:",
        pricing["gst_rs"]
    )

    print(
        "Final amount:",
        pricing["total_rs"]
    )

    print("Status: QUOTED")

    print("=============================\n")

    return quotation
