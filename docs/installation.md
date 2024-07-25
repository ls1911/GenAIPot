# Installation Guide

## Prerequisites

Before installing the software, ensure that your system meets the following prerequisites:

1. **Python Version**: Ensure Python 3.7 or later is installed. You can download it from [python.org](https://www.python.org/downloads/).

2. **pip**: The package installer for Python. It usually comes with Python, but if not, you can install it separately.

3. **Virtual Environment**: It's recommended to use a virtual environment to manage dependencies. You can use `venv` or `virtualenv`.

4. **Git**: If you want to clone the repository, make sure Git is installed. Download from [git-scm.com](https://git-scm.com/).

## Installation Steps

### 1. Clone the Repository

If you haven't done so already, clone the repository to your local machine:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

**2. Set Up a Virtual Environment**

  

Create a virtual environment to manage dependencies:
```
python -m venv venv
```
Activate the virtual environment:

•  On **Windows**:
```
venv\Scripts\activate
```
•  On **macOS and Linux**:
```
source venv/bin/activate
```

**3. Install Dependencies**

Install the required Python packages using pip:

```
pip install -r requirements.txt
```
**4. Configuration**

Create a configuration file or run the app with --config

```
python3 main.py --config
```

> Dont forget to configure OpenAI keys in the config.ini file if you want to use AI
