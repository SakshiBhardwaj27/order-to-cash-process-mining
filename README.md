# Order-to-Cash Process Mining & Operational Bottleneck Analysis

An end-to-end process analytics project that examines how customer orders move through an Order-to-Cash (O2C) workflow. Using Python, SQL, and an interactive Streamlit dashboard, the project analyzes process execution, identifies long-running transitions, compares process variants, and flags cases that may require operational attention.

The objective is to demonstrate how event-log data can be transformed into meaningful process insights that support operational monitoring and process improvement.

---

## Project Overview

In an Order-to-Cash workflow, an order passes through multiple business activities, from order creation and credit checks to payment, fulfillment, shipping, and delivery.

Looking only at the final order status does not explain where delays occur or why different orders follow different paths.

This project uses an event-log-based approach to reconstruct individual order journeys and analyze:

- Process execution and order outcomes
- End-to-end order cycle times
- Waiting times between consecutive activities
- Frequently occurring process variants
- Repeated activities that may indicate rework
- Delayed and cancelled cases requiring further investigation

An interactive dashboard makes these findings easier to explore through filters, KPIs, charts, and detailed case-level information.

## Key Project Highlights

| Component | Implementation |
|---|---|
| Event log | 10,884 synthetic events across 1,500 order cases |
| Data preparation | Validation, sorting, and timestamp handling using Pandas |
| Process analysis | Case-level metrics, process variants, and activity transitions |
| Bottleneck analysis | Average and median waiting-time calculations |
| Rework screening | Identification of repeated activities within cases |
| SQL analysis | PostgreSQL queries using CTEs, window functions, and aggregations |
| Interactive dashboard | Streamlit and Plotly |
| Data filtering | Region and order start-date filters |

## Interactive Dashboard

The Streamlit application provides an interactive view of the Order-to-Cash process.

### 1. Key Performance Indicators

The dashboard displays:

- **Total Cases:** Number of unique orders in the selected dataset.
- **Delivery Rate:** Percentage of cases reaching the Delivered activity.
- **Median Delivered Cycle Time:** Median time taken by delivered orders from their first to last recorded event.
- **Cancellation Rate:** Percentage of cases ending in Order Cancelled.

### 2. Case Outcome Analysis

Visualizes the distribution of final order outcomes, helping distinguish completed orders from cancelled orders.

### 3. Cycle-Time Distribution

Examines the distribution of end-to-end cycle times for delivered orders to understand variation in order completion time.

### 4. Activity Frequency Analysis

Shows how frequently each business activity occurs and how many unique cases contain that activity.

### 5. Process Transitions & Waiting-Time Analysis

Examines consecutive activity transitions within each order case and calculates the average waiting time between them.

This helps identify transitions where a significant amount of elapsed time accumulates.

### 6. Process Variant Analysis

Reconstructs the sequence of activities followed by each order and displays the most frequently occurring process variants.

This helps compare how different orders move through the workflow.

### 7. Cases Requiring Attention

Highlights cases that meet one or more of the following conditions:

- Cycle time exceeds the illustrative 72-hour threshold for delivered cases.
- The final activity indicates order cancellation.
- One or more activities are repeated within the same case.

The dashboard also provides an option to download the filtered event log as a CSV file.

## Dataset Description

The project uses a reproducible synthetic dataset generated using Python.

**Dataset file:** `data/order_to_cash_event_log.csv`

| Column | Description |
|---|---|
| `case_id` | Unique identifier for each order |
| `activity` | Business activity performed during the order lifecycle |
| `timestamp` | Date and time when the activity occurred |
| `customer_id` | Synthetic customer identifier |
| `region` | Sales region associated with the order |
| `order_value` | Synthetic order value |

### Activities Included

The event log represents activities such as:

- Order Created
- Credit Check
- Manual Review
- Payment Received
- Order Approved
- Inventory Replenished
- Pick and Pack
- Shipped
- Delivered
- Order Cancelled

The generated data includes different order paths, manual review scenarios, inventory-related delays, repeated picking activities, and cancelled orders.

**Important:** This is a synthetic dataset created for educational and portfolio purposes. It does not represent real business transactions or customer records.

## Technical Methodology

### 1. Event-Log Preparation

- Loaded the event log using Pandas.
- Validated required columns and checked for missing values in essential event fields.
- Converted timestamps into datetime format.
- Sorted events by case identifier and timestamp.

### 2. Case-Level Analysis

Grouped events by `case_id` to calculate:

- First recorded activity timestamp
- Last recorded activity timestamp
- Total number of events
- Final activity
- End-to-end cycle time
- Delivered and cancelled case indicators

Cycle time is calculated as:

`Cycle Time = Last Event Timestamp - First Event Timestamp`

### 3. Activity and Transition Analysis

Analyzed activity frequency and reconstructed consecutive activity transitions within each case.

Used grouped operations and shift-based calculations to determine:

- Activity frequency
- Number of cases containing each activity
- Next activity in the process
- Time elapsed between consecutive activities
- Average and median transition waiting times

### 4. Process Variant Analysis

Created ordered activity sequences for individual cases and grouped identical sequences to identify frequently occurring process variants.

### 5. Rework Identification

Identified cases where the same activity appeared more than once.

Repeated activities are treated as potential rework indicators rather than confirmed process errors. Their business meaning would need validation with process owners.

### 6. Delay Screening

Flagged delivered cases with a total recorded cycle time exceeding 72 hours.

The 72-hour threshold is an illustrative analytical assumption used for this project, not an industry benchmark or an actual contractual SLA.

## SQL Analysis

The `sql/analysis_queries.sql` file contains PostgreSQL queries demonstrating how event-log data can be analyzed using SQL.

The queries cover:

1. Activity frequency and distinct case counts.
2. Process variant reconstruction using `STRING_AGG`.
3. Consecutive activity analysis using `LEAD()`.
4. Case cycle-time calculation using window functions.
5. Repeated activity identification using `GROUP BY` and `HAVING`.
6. Identification of delivered cases exceeding the illustrative 72-hour threshold.

These SQL queries are provided as a separate analysis component. The Streamlit dashboard currently reads the CSV event log and performs its analysis using Python; it does not execute the SQL queries directly.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Data Manipulation | Pandas, NumPy |
| Data Visualization | Plotly |
| Dashboard Development | Streamlit |
| Database Querying | PostgreSQL |
| SQL Concepts | CTEs, Window Functions, Aggregations, LEAD(), STRING_AGG() |
| Development Tools | VS Code, Git, GitHub |

## Project Structure

```text
celonis_process_mining_project/
│
├── app.py
│
├── data/
│   └── order_to_cash_event_log.csv
│
├── outputs/
│   ├── activity_metrics.csv
│   ├── case_metrics.csv
│   ├── process_variants.csv
│   └── transition_metrics.csv
│
├── sql/
│   └── analysis_queries.sql
│
├── src/
│   ├── __init__.py
│   ├── analyze_process.py
│   └── generate_data.py
│
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Installation & Setup

Follow these steps to run the project locally.

### Prerequisites

- Python 3.10 or later
- pip
- Git (optional, for cloning the repository)

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd celonis_process_mining_project
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Generate the Event Log (Optional)

The repository already includes the generated event log. To regenerate it:

```bash
python -m src.generate_data
```

### 5. Run the Process Analysis

```bash
python -m src.analyze_process
```

This generates the case, activity, transition, and process-variant analysis files inside the `outputs/` directory.

### 6. Launch the Streamlit Dashboard

```bash
python -m streamlit run app.py
```

The application will open in your default browser.

## Key Analytical Considerations

- Cycle time represents the elapsed time between the first and last recorded event for a case.
- Transition waiting time measures elapsed time between consecutive recorded activities; it does not independently establish the cause of a delay.
- Repeated activities may be legitimate business steps and should not automatically be classified as process defects.
- The dataset does not contain resource, department, contractual SLA, or root-cause information.
- The 72-hour threshold is illustrative and should be replaced with a business-approved SLA in a real operational environment.
- Synthetic data demonstrates analytical techniques but cannot support claims about actual business savings or operational improvements.

## Future Enhancements

Potential extensions to this project include:

- Integrating a publicly available, appropriately licensed real-world event-log dataset.
- Applying process discovery and conformance checking using PM4Py.
- Comparing process performance across customer segments and order-value categories.
- Introducing validated SLA targets and business-approved delay measures.
- Connecting the dashboard to PostgreSQL instead of reading a local CSV file.
- Exploring Celonis Studio, Process Query Language (PQL), and the Celonis platform as a separate implementation.

## Skills Demonstrated

Python, SQL, PostgreSQL, Pandas, NumPy, Event-Log Analysis, Process Analytics, Data Cleaning, Data Transformation, Exploratory Data Analysis, Process Variants, Cycle-Time Analysis, Waiting-Time Analysis, Bottleneck Identification, KPI Analysis, Window Functions, Streamlit, and Plotly.

## Project Scope & Disclaimer

This is an independent process analytics portfolio project developed using Python, SQL, and Streamlit.

It demonstrates event-log analysis concepts commonly associated with process mining. It is **not built on the Celonis platform**, does not use PQL, and does not represent an official Celonis implementation.

---

## License

This project is distributed under the MIT License. See the `LICENSE` file for details.

---

**Developed as a portfolio project to demonstrate data analytics, SQL, Python, and process intelligence concepts.**