# Campus Lab Equipment Booking and Maintenance System

A web-based application developed using **Python Flask and MySQL** to manage computer reservations and equipment health monitoring in campus laboratories.

The system provides role-based access for Students, Faculty, Staff, Lab In-charges, and Administrators.

## Features

- User registration and login.
- Role-based access and permissions.
- View laboratory computers and timetable slots.
- Students can book one computer per booking request.
- Faculty can book multiple computers.
- View personal booking history and cancel bookings.
- Staff can view computer health status.
- Lab In-charges can update computer health status and add computers to laboratories.
- Availability checks to help prevent conflicting bookings.
- Maintenance record management.
- SQL procedures, functions, cursors, and triggers.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS |
| Backend | Python, Flask |
| Database | MySQL 8 |
| Database Connectivity | PyMySQL / SQLAlchemy |
| Development Environment | Visual Studio Code |

## Prerequisites

Install the following software before running the project:

1. **Python 3.10 or later** – [Download Python](https://www.python.org/downloads/)
2. **MySQL Server 8.0 or later** – [Download MySQL](https://dev.mysql.com/downloads/mysql/)
3. **Git** – [Download Git](https://git-scm.com/downloads)
4. **Visual Studio Code** (recommended) – [Download VS Code](https://code.visualstudio.com/)

Make sure Python, Git, and MySQL are installed and accessible from your terminal.

## Installation and Setup

### Step 1: Clone the repository

Open Terminal or Command Prompt and execute:

```bash
git clone https://github.com/Aadityaa177/lab_equipment_booking.git
```

Navigate into the project directory:

```bash
cd lab_equipment_booking
```

### Step 2: Create a Python virtual environment

```bash
python -m venv .venv
```

Activate it:

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows:**

```bash
.venv\Scripts\activate
```

### Step 3: Install Python dependencies

If a `requirements.txt` file is present in the project directory, run:

```bash
pip install -r requirements.txt
```

If it is not present, install the required packages:

```bash
pip install Flask PyMySQL Flask-Login Flask-SQLAlchemy python-dotenv
```

### Step 4: Set up the MySQL database

1. Start your MySQL Server.
2. Open MySQL Workbench or the MySQL command-line client.
3. Create the project database:

```sql
CREATE DATABASE campus_lab_booking;
```

4. Select the database:

```sql
USE campus_lab_booking;
```

5. Import the SQL schema provided in the repository.

If the schema file is named `schema.sql` and is located in the project root, you can import it from the terminal using:

```bash
mysql -u root -p campus_lab_booking < schema.sql
```

Replace `schema.sql` with the actual SQL filename in the repository if it has a different name.

The schema must be imported before starting the application.

### Step 5: Configure database connectivity

Open the project in Visual Studio Code.

```bash
code .
```

Configure the MySQL connection settings in the application's database configuration to match your local setup:

- Host: `localhost`
- Port: `3306` (default MySQL port)
- Database: `campus_lab_booking`
- Username: Your MySQL username
- Password: Your MySQL password

Make sure the database credentials match your local MySQL installation. Do not publish personal database passwords or secret configuration files.

### Step 6: Run the Flask application

From the project directory, with the virtual environment activated, execute:

```bash
python -m flask --app app run --debug --port 5002
```

If Flask starts successfully, the terminal will display a local development server address.

### Step 7: Open the application

Open your browser and visit:

**http://127.0.0.1:5002**

The Campus Lab Equipment Booking and Maintenance System should now be accessible locally.

## User Roles

| Role | Permissions |
|---|---|
| Student | View timetable, book one computer, view and cancel own bookings |
| Faculty | Book multiple computers and manage own bookings |
| Staff | View computer health status |
| Lab In-charge | Update computer health and add computers |
| Administrator | Access administrative user-management functions |

Users can register and log in through the application, subject to the configured registration rules.

## Project Structure

```text
lab_equipment_booking/
│
├── app.py
├── schema.sql
├── templates/
├── static/
├── requirements.txt
└── README.md
```

*Note: The structure above is representative. Additional files and folders may be present in the repository.*

## Troubleshooting

**1. MySQL connection error**

- Ensure MySQL Server is running.
- Verify the database name, username, password, and port.
- Confirm that the SQL schema has been imported.

**2. ModuleNotFoundError**

Activate the virtual environment and install the dependencies again:

```bash
pip install -r requirements.txt
```

**3. Flask command or application error**

Make sure you are in the project directory, the virtual environment is activated, and `app.py` is present.

**4. Port already in use**

Try running Flask on another port:

```bash
python -m flask --app app run --debug --port 5003
```

Then open `http://127.0.0.1:5003`.

## Stopping the Application

To stop the local Flask server, press:

```text
CTRL + C
```

## Developer

**Aadityaa Jayamurugan**  
B.Tech – Computer Science and Engineering  
Vellore Institute of Technology (VIT), Vellore

**GitHub Repository:**  
https://github.com/Aadityaa177/lab_equipment_booking

---

*This project was developed as part of the Database Systems course to demonstrate relational database design, SQL implementation, database connectivity, and web-based resource management.*
