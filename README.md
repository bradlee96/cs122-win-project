League of Legends Performance Tracker and Champion Recommender Tool
==============
CS122 Winter Project
--------------
Project Members: Brad Lee, Philip Zhou, Johnathan Hsu

To run our project, the user should perform following steps:
1. In the folder containing manage.py, create a virtual environment in the terminal: $virtualenv -p python3 venv
2. Enter the virtual environment: $source venv/bin/activate
3. Install the requirements (django) using pip: $pip3 install -r requirements.txt
4. Make and perform the necessary migrations: $python3 manage.py makemigrations AND $python3 manage.py migrate
5. Run the server (insecure): $python3 manage.py runserver --insecure, since debug mode was turned off (which means static files are not being loaded unless either debug mode is set to True in settings.py or the "insecure" option is added) in order to upload it to pythonanywhere (localhost has been added to the list of allowed hosts).
6. The website should now be up: http://localhost:8000/
7. In order to avoid long wait times in pulling player data, please experiment first with Greenberries (19 games), The Boojum (19 games), and then (if you so desire) with people with more games such as Hanazono (200-400 games) and Ghibli Studios (easily 700+ games).
8. Note that there is a sidebar on the left side of the screen that is used for navigation and also graphing on the stats page.
