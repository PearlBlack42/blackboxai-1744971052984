
Built by https://www.blackbox.ai

---

```markdown
# Project Overview

This project is a web application built using Flask that allows users to manage data in an MDB (Microsoft Access Database) file. It provides a user-friendly interface for logging in, navigating through tables, and performing CRUD (Create, Read, Update, Delete) operations on the data within those tables. The application organizes and sanitizes database interactions to enhance security and usability.

## Installation

To get started with this project, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   Use `pip` to install the required packages listed in `requirements.txt`. You may need to create this file based on the imports in your code.
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   Create a `.env` file in the root directory of the project and add your secret key:
   ```plaintext
   SECRET_KEY=your_secret_key_here
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   The application will run on `http://127.0.0.1:8000`.

## Usage

- **Login:** Access the login page at `http://127.0.0.1:8000/login`. Use the username `sa` and password `0711321277` to log in.
- **Dashboard:** After logging in, you will be redirected to the dashboard, where you can view the available tables.
- **CRUD Operations:** You can view, add, edit, and delete records from any table by navigating to the respective table page.

## Features

- User authentication with session management.
- Displays available tables and their respective data from an MDB database.
- Ability to add, edit, and delete records in the database.
- Error handling and logging for operations performed by the user.
- Input sanitization to prevent SQL injection.
- Session timeout to enhance security.

## Dependencies

The project requires the following dependencies to be installed:

- Flask
- python-dotenv

These dependencies can be installed using pip. Ensure to list them in a `requirements.txt` file for easy installation. 

```plaintext
Flask
python-dotenv
```

## Project Structure

Here's a brief overview of the project's structure:

```
<project-root>
│
├── app.py             # The main application file containing routes and logic.
├── database.py        # Database interaction functions including sanitization and query execution.
├── config.py          # Configuration settings including environment variables and database paths.
├── requirements.txt    # List of Python package dependencies.
├── .env               # Environment variable configuration for the application.
└── app.log            # Log file for tracking application events and errors.
```

Feel free to contribute or raise issues if you encounter any bugs or need clarification!
```