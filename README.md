
# Hostel Complaint Management System

## About the Project

The Hostel Complaint Management System is a web-based
application designed to help hostel students submit
complaints and track their resolution status.

It allows administrators to view complaints and update
their status.

## Technologies Used

- HTML
- CSS
- Python (Flask)
- C Programming
- SQLite Database

## Features

1. Student Registration and Login
2. Submit Hostel Complaints
3. Complaint Categories:
   - Electricity
   - Water
   - Wi-Fi
   - Cleaning
   - Other
4. Complaint Priority Calculation using C
5. View Submitted Complaints
6. Track Complaint Status
7. Admin Dashboard
8. Update Complaint Status
9. SQLite Database Integration
10. Responsive User Interface

## Project Structure

Hostel-Complaint-Management-System/
- app.py
- priority.c
- requirements.txt
- schema.sql
- README.md
- templates/
- static/
- database/

## Installation and Execution

### Step 1: Clone the Repository

git clone YOUR_GITHUB_REPOSITORY_LINK

### Step 2: Open the Project Folder

cd Hostel-Complaint-Management-System

### Step 3: Install Dependencies

pip install -r requirements.txt

### Step 4: Install GCC

Make sure GCC is installed and available in PATH.

### Step 5: Run the Application

python app.py

###Step 6: Open in Browser

https://hostel-complaint-management-system-vuu2.onrender.com

The SQLite database will be created automatically.

a) Default Administrator Login

Username: admin

Password: admin123

b) Database

The application uses SQLite to store:
- Student details
- Login credentials (hashed)
- Complaint descriptions
- Complaint categories
- Complaint priorities
- Complaint statuses

c) C Module

The C program calculates complaint priority
based on complaint category and urgency.

It is compiled and executed by the Python backend.

d) Future Improvements

- Email notifications
- Complaint deletion
- Complaint history
- Admin analytics
- Password reset functionality

e) Author

Radhika Raha
