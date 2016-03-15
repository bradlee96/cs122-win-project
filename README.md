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
5. Run the server: $python3 manage.py runserver  
6. The website should now be up: http://localhost:8000/  
7. No data on players has been provided here. By typing a summoner name into the search bar, it should be possible to obtain player data from the Riot Games API. In order to avoid long wait times in pulling player data, please experiment first with Greenberries (19 games), The Boojum (19 games), for whom pulling games should not take longer than 20-30 seconds, and then (if you so desire) with people with more games such as Hanazono (200-400 games) and Ghibli Studios (easily 700+ games).  
8. Note that there is a sidebar on the left side of the screen that is used for navigation and also graphing on the stats page.  

For the champion select screen, it is recommended that you use players with more games such as Hanazono and not Greenberries or The Boojum since they do not have enough games to give an accurate recommendation. For instance, if they have only played one champion in a certain lane but lost, the recommendation will still be that champion. However, it is still possible to get a recommendation for someone like Greenberries by not filling in any champion names and trying different roles.  
A list of champions can be found here:  
http://leagueoflegends.wikia.com/wiki/List_of_champions
