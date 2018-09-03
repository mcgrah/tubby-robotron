python -m venv robotron\django
robotron\django\Scripts\activate.bat
robotron\django\Scripts\python -m pip install --upgrade pip
robotron\django\scripts\pip install -r robotron\app\requirements.txt
robotron\django\Scripts\python.exe robotron\app\manage.py runserver