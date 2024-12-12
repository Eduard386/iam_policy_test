# IAM Policy Test Automation Framework

## Description

This project is designed to automate the testing of AWS IAM policies that allow viewing users and groups but prohibit their creation, deletion, and modification. The moto library is used for mocking AWS services. Tests are executed using pytest.

## Install

1. **Clone the repo:**

    ```bash
    git clone https://github.com/yourusername/AcademySmart.git
    cd AcademySmart
    ```

2. **Create and activate virtual env:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Linux/Mac
    # For Windows:
    # venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    pip3 install --upgrade -r requirements.txt
    ```

## Run and generate report in "report.html" file in the root directory

1. **Run tests:**

    ```bash
    pytest --html=report.html --self-contained-html
    ```
