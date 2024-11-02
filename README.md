# Agri-modal Setup Guide

This guide will walk you through setting up the Agri-modal project, including downloading and installing PostgreSQL, Python, and required dependencies.

## Prerequisites

Make sure you have the following installed on your system:
- **PostgreSQL**
- **Python 3.x**

---

## Step 1: Download and Install PostgreSQL

1. Download PostgreSQL from the official website: [PostgreSQL Downloads](https://www.postgresql.org/download/)
2. Follow the installation instructions for your operating system (Windows, macOS, or Linux).
3. After installation, open the PostgreSQL terminal (`psql`) or use a GUI tool like pgAdmin to manage your databases.

---

## Step 2: Download and Install Python

1. Download Python from the official website: [Python Downloads](https://www.python.org/downloads/)
2. Ensure that **Python 3.x** is installed by running the following command in your terminal/command prompt:

    ```bash
    python --version
    ```

3. Ensure `pip`, the Python package manager, is installed (usually comes with Python).

---

## Step 3: Create Databases

1. Open PostgreSQL terminal (`psql`) or your preferred database client.
2. Run the following SQL commands to create the development and test databases:

    ```sql
    CREATE DATABASE agri_modal_db;
    CREATE DATABASE agri_modal_test_db;
    ```

---

## Step 4: Clone the Project Repository

1. Clone the Agri-modal project from GitHub:

    ```bash
    git clone https://github.com/AgriModel-AI/agrimodel-backend
    ```

2. Navigate into the project directory:

    ```bash
    cd Agri-modal
    ```

---

## Step 5: Set Up Python Virtual Environment

1. Create a Python virtual environment:

    ```bash
    python -m venv venv
    ```

2. Activate the virtual environment:

    - On **Windows**:

        ```bash
        venv\Scripts\activate
        ```

    - On **macOS/Linux**:

        ```bash
        source venv/bin/activate
        ```

---

## Step 6: Install Project Dependencies

1. Install the required Python packages listed in `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

---

## Step 7: Configure Environment Variables

1. Create a `.env` file in the root directory of the project.
2. Add the following environment variables to the `.env` file:

    ```plaintext
    SQLALCHEMY_DATABASE_URI = 'postgresql://your_postgres_username:your_postgres_password@localhost:5432/agri_modal_db'
    TEST_DATABASE_URL = 'postgresql://your_postgres_username:your_postgres_password@localhost:5432/agri_modal_test_db'
    JWT_SECRET_KEY = "postgres"

    MAIL_USERNAME = "your email"
    MAIL_PASSWORD = "your email password"
    MAIL_DEFAULT_SENDER = "your email"
    ```

    Replace the placeholders with your actual PostgreSQL credentials and email details.

---

## Step 8: Set Up the Database Migrations

1. Initialize Flask-Migrate:

    ```bash
    flask db init
    ```

2. Create an initial migration to set up the database schema:

    ```bash
    flask db migrate -m "Initial migration."
    ```

3. Apply the migration to the database:

    ```bash
    flask db upgrade
    ```

---

## Step 9: Run the Application

1. Start the Flask development server:

    ```bash
    flask run
    ```

2. The app will now be running at: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Step 10: Test the Application Using Postman

1. Use [Postman](https://www.postman.com/downloads/) or any other API client to test the application's endpoints.
2. You can now interact with the API and test its functionality by sending requests to the `http://127.0.0.1:5000` URL.

---

### Additional Notes

- Remember to activate your virtual environment every time you work on the project by running the activation command (as described in **Step 5**).
- For future database schema changes, repeat the `flask db migrate` and `flask db upgrade` commands.
