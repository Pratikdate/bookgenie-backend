# BookGenie Backend

Welcome to the BookGenie backend repository! This repository contains the backend code for the BookGenie application, developed using Django. Follow the instructions below to set up and run the backend on your local machine.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Testing](#testing)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- Pip (Python package installer)
- Virtualenv (optional, but recommended)

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/bookgenie-backend.git
   cd bookgenie-backend
2. **Create and Activate a Virtual Environment (optional but recommended):**
   ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use: venv\Scripts\activate

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt

## Running the Server:
In settings.py, update the ALLOWED_HOSTS setting to include your local network IP address:

1. **Start the Django development server with the following command:**
   ```bash
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'your_network_ip']
Replace your_network_ip with your local network IP address.

2. **Start the Django Development Server:**
   ```bash
    python manage.py runserver 0.0.0.0:8000

## Contributing

We welcome contributions to enhance BookGenie! To help you get started, please follow these steps:

1. **Fork the Repository:**
   - Click the "Fork" button at the top-right of the repository page on GitHub to create your own copy.

2. **Create a Feature Branch:**
   - Clone your forked repository to your local machine if you haven’t already:
     ```bash
     git clone https://github.com/yourusername/bookgenie-backend.git
     cd bookgenie-backend
     ```
   - Create a new branch for your feature or bug fix:
     ```bash
     git checkout -b feature/YourFeature
     ```

3. **Commit Your Changes:**
   - Make the necessary changes to the codebase.
   - Add and commit your changes with a meaningful message:
     ```bash
     git add .
     git commit -m 'Add new feature: YourFeature'
     ```

4. **Push to the Branch:**
   - Push your changes to your forked repository on GitHub:
     ```bash
     git push origin feature/YourFeature
     ```

5. **Create a Pull Request:**
   - Navigate to the original repository on GitHub.
   - Click on the "Pull Requests" tab and then "New Pull Request."
   - Select your branch from the dropdown menu and compare it with the base branch (usually `main` or `master`).
   - Provide a clear description of your changes and submit the pull request for review.

Thank you for contributing to BookGenie! We appreciate your efforts to help us improve and grow.
