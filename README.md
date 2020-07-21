# Employee-Assignment-System
Web app for the requesting and placing of employees at locations. <br>
Allows admin users to move employee users to various locations, created by the admins. <br>
Allows location users to request employees at their location.<br>
Allows employees to view their currently assigned location and the last time it was updated.<br>
Built using Flask and PostgreSQL.

#To Run
- Run 'pip install -r requirements.txt' in the project directory to install all dependencies<br>
- Ensure DBDFNAME, DBDFUSER, and DBDFPASS in the env file are assigned valid information for an account<br>
    able to create other users in your PostgreSQL server.<br>
- Run setup.py to create DB, user, and initialize schema (Optionally populates DB with fake data)
- Run app.py (Default root user: u: 'root@admin.com' p: 'root')
