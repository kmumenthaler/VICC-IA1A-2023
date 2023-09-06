# VICC-IA1A-2023 Flask Web Application

This is a Flask web application for book reviews.

## Setup Instructions

1. Before running the application, ensure that you have set up the database configuration and the Flask secret key in `app/config.py`.
   - Update the `DB_CONFIG` dictionary with your database details.
   - Set the `SECRET_KEY` for Flask. This is used to securely sign the session cookie.

2. Once the configuration is set, you can run the application using:
```
python app/main.py
```

3. Access the web application on `http://localhost:5000/`.

Note: Ensure that the `config.py` file is kept secure and not exposed publicly to protect sensitive information.

