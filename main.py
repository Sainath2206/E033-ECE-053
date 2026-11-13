
from engine import (
    load_inputs,
    display_data_summary,
    validate_input_data
)

from processor import run_processor


def main():

    print("Starting EMC Test Lab Management System...")

    data = load_inputs()

    display_data_summary(data)

    validate_input_data(data)

    run_processor(data)


if __name__ == "__main__":
    main()
