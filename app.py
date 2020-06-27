# Import libraries
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from functools import wraps
from wtforms import Form, StringField, validators, SelectField
from passlib.hash import sha256_crypt
from datetime import datetime
import psycopg2
import psycopg2.extras

# Flask instance
app = Flask(__name__)

# Initialize PostgreSQL
conn = psycopg2.connect(dbname='postgres', user='postgres', password='root')


# Redirects to login page
@app.route('/')
def index():
    return redirect(url_for('login'))


# Login
# Function called for login page. Will test form information against DB information, hashed/salted before comparing
# Will direct user to adminHome if account entered is usertype 1. Otherwise, will redirect to employeeHome
# If account non-existent, password mismatch, or fields empty, will redirect to self (login.html)
# Currently no limit on password entry attempts
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    name: login
    input/output: Accessed through "/login" path by GET or POST. Will direct user to adminHome if account
        entered is usertype 1. Otherwise, will redirect to employeeHome. If account non-existent, password mismatch,
        or fields empty, will redirect to self (login.html)

    """
    if request.method == 'POST':
        # Pull username password info supplied by user
        usernameCandidate = request.form['email']
        passwordCandidate = request.form['password']

        # Disallow empty field entries
        if usernameCandidate == '' or passwordCandidate == '':
            flash('Please fill all fields', 'warning')
            return render_template('login.html')

        # Checks if any entry with the provided email exists
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", [usernameCandidate])

        if cur.rowcount > 0:
            data = cur.fetchone()
            cur.close()

            # Pull data from DB
            password = data['password']
            usertype = data['usertype']

            if sha256_crypt.verify(passwordCandidate, password):
                # Update current session information
                session['logged_in'] = True
                session['username'] = data['email']
                session['user_type'] = usertype

                # Redirect to correct home page
                flash('You are now logged in', 'success')
                if usertype == 1:
                    return redirect(url_for('adminHome'))
                elif usertype == 2:
                    return redirect(url_for('employeeHome'))
                else:
                    return redirect(url_for('locUserHome'))

            # Password mismatch
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)

        # No account with provided email found
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    # GET method
    else:
        return render_template('login.html')


# Is Logged In
# Decorator used to verify if a user is logged in. Uses session data to verify login status
# If user is logged in, function is called as normal. Otherwise, user redirected to login page
def isLoggedIn(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))

    return wrap


# Is Logged In Location User
# Decorator used to verify if user is logged in as a location associated user. Uses session data to verify login status
# If user is admin or locUser, function is called as normal.
# If user is logged in as regular employee, user redirected to employeeHome
# Otherwise, user redirected to login page
def isLoggedLocUser(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            if session['user_type'] == 1 or session['user_type'] == 3:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized, please login as location user', 'danger')
                return redirect(url_for('employeeHome'))
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))

    return wrap


# Is Logged In Admin
# Decorator used to verify if user is logged in as admin. Uses session data to verify login status
# If user is admin, function is called as normal. If user is logged in as regular user, user redirected to employeeHome
# Otherwise, user redirected to login page
def isLoggedAdmin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            if session['user_type'] == 1:
                return f(*args, **kwargs)
            else:
                flash('Unauthorized, please login as admin', 'danger')
                return redirect(url_for('employeeHome'))
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))

    return wrap


# Logout
@app.route('/logout')
@isLoggedIn
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Employer Home
@app.route('/adminHome')
@isLoggedAdmin
def adminHome():
    return render_template('adminHome.html')


# Employee Home
# Displays employees placement data based on username (email)
# pulled from current session data
# If user is using administrative account (admin account)
# they will likely not have a corresponding employees entry
# and this routine will simply flash an error
@app.route('/employeeHome')
@isLoggedIn
def employeeHome():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    username = session['username']

    # Check that account exists in employees
    cur.execute("select * from employees where email=%s", [username])
    if cur.rowcount > 0:
        row = cur.fetchone()
        cur.close()
        return render_template('employeeHome.html', valid=True, employee=row)

    # If placement account does not exist, throw error
    cur.close()
    flash('Error fetching placement information', "warning")
    return render_template('employeeHome.html', valid=False)


# Location User Home
# Displays home page of account associated with location
# Will display current number of employees and allow the user to submit requests to admin users
# If user is using admin account, they will not have a corresponding location entry
# and this routine will simply flash an error
@app.route('/locUserHome')
@isLoggedLocUser
def locUserHome():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    username = session['username']

    # Check that account has associated location entry (checking the user is not admin)
    cur.execute("select * from locations where email=%s", [username])
    if cur.rowcount > 0:
        row = cur.fetchone()
        cur.close()
        return render_template('locUserHome.html', valid=True, location=row)

    # If location account does not exist, throw error
    cur.close()
    flash('Error fetching location information', "warning")
    return render_template('locUserHome.html', valid=False)


# View Employees
# Function redirects to page presenting list of all employees
@app.route('/viewEmployees')
@isLoggedAdmin
def viewEmployees():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from employees where email in (select email from users where usertype=2)")

    # Test if employees exist in DB, if not, exit prematurely
    if cur.rowcount > 0:
        rows = cur.fetchall()

        # Debugging, might flood log if left on when live
        app.logger.info('Fetched employees')
        for row in rows:
            app.logger.info(row['email'])

        # Closing statements
        cur.close()
        return render_template('viewEmployees.html', employees=rows)

    else:
        flash('No employees found', 'info')
        return render_template('adminHome.html')


# View Locations
# Function redirects to page presenting list of all locations
@app.route('/viewLocations')
@isLoggedAdmin
def viewLocations():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from locations")

    # Test if locations exist in DB, if not, exit prematurely
    if cur.rowcount > 0:
        rows = cur.fetchall()

        # Debugging, might flood log if left on when live
        app.logger.info('Fetched locations')
        for row in rows:
            app.logger.info(str(row['id']) + ' ' + row['name'])

        # Closing statements
        cur.close()
        return render_template('viewLocations.html', locations=rows)

    else:
        flash('No locations found', 'info')
        return render_template('adminHome.html')


# Assign Employees to Locations
# Redirects to assignEmployees.html
# Won't redirect if there are no locations
@app.route('/assignEmployees')
@isLoggedAdmin
def assignEmployees():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from locations")

    # Test if locations exist in DB, if not, exit prematurely
    if cur.rowcount > 0:
        rows = cur.fetchall()
        cur.execute("select name, email, assignedto from employees where assignedto = 0")
        urows = cur.fetchall()

        # Logging
        app.logger.info('Fetched locations and unassigned employees')
        for row in rows:
            app.logger.info(row['name'])

        # Closing statements
        cur.close()
        return render_template('assignEmployees.html', locations=rows, employees=urows)

    else:
        flash('No locations found', 'info')
        return render_template('adminHome.html')


# Remove Employees from DB
# Will remove employee from location assignment and drop their users and employees rows from the DB
# Only presents users from employees table, not users table. Therefore some accounts need to be manually deleted
# Contains a button for confirmation just in case :)
@app.route('/deleteEmployee', methods=['GET', 'POST'])
@isLoggedAdmin
def deleteEmployee():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Submitting employee(s) to be deleted
    if request.method == 'POST':

        app.logger.info('In POST')

        # Gets form information from deleteEmployee.html
        delete = request.form.getlist('empDel')

        # Track number of employees deleted
        numDel = 0

        # Deletes all employees in delete list, so long as confirm was selected
        if delete:
            # Get assignedto, if assignedto > 0 lower from location's numEmployee count, then drop employee
            # users and employees
            for email in delete:
                cur.execute("select assignedto from employees where email= %s", [email])
                row = cur.fetchone()

                if row['assignedto'] > 0:
                    cur.execute("update locations set numemployees = numemployees - 1 where id= %s",
                                [row['assignedto']])

                cur.execute("delete from employees where email = %s", [email])
                cur.execute("delete from users where email = %s", [email])
                conn.commit()
                numDel += 1

        flash('Deleted {} employees'.format(numDel), 'info')
        return redirect(url_for('deleteEmployee'))

    # Get request
    else:
        # Grabs all employee info
        cur.execute("select * from employees")

        # Only displays if employees exist in DB
        if cur.rowcount > 0:
            row = cur.fetchall()
            cur.close()
            return render_template('deleteEmployee.html', employees=row)
        else:
            # If the location doesn't exist, user sent back to adminHome.html
            flash('No users found', 'info')
            return redirect(url_for('adminHome'))


# Remove Locations from DB
# Also removes associated user account
# Will remove employees assigned to selected location(s) and change employees assignedto column to 0
# Contains a button for confirmation just in case :)
@app.route('/deleteLocation', methods=['GET', 'POST'])
@isLoggedAdmin
def deleteLocation():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Submitting location(s) to be deleted
    if request.method == 'POST':

        app.logger.info('In POST')

        # Gets form information from deleteLocation.html
        delete = request.form.getlist('locDel')

        # Track number of locations deleted
        numDel = 0

        # TODO: Reduce ID value for each location deleted, so as to have consistent location ids
        # Deletes all locations in delete list, so long as confirm was selected
        if delete:
            for id in delete:
                cur.execute("select email from locations where id = %s", [id])
                email = cur.fetchone()['email']

                cur.execute("update employees set assignedto = 0 where assignedto = %s", [id])

                cur.execute("delete from locations where id = %s", [id])
                cur.execute("delete from users where email = %s", [email])
                conn.commit()
                numDel += 1

        flash('Deleted {} location(s)'.format(numDel), 'info')
        return redirect(url_for('deleteLocation'))

    # Get request
    else:
        # Grabs all employee info
        cur.execute("select * from locations")

        # Only displays if locations exist in DB
        if cur.rowcount > 0:
            row = cur.fetchall()
            cur.close()
            return render_template('deleteLocation.html', locations=row)
        else:
            # If the location doesn't exist, user sent back to adminHome.html
            flash('No locations found', 'info')
            return redirect(url_for('adminHome'))



# FORMS BELOW ARE ONLY NECESSARY IF NEED TO VALIDATE INPUT

# Form to verify/restrict new employee data
class NewEmployeeForm(Form):
    email = StringField('email', [validators.Length(min=1, max=50)])
    name = StringField('name', [validators.Length(min=1, max=50)])
    assignedto = SelectField('assignedto', validate_choice=False)
    usertype = SelectField('usertype', choices=[('1', '1'), ('2', '2')])


# Form to verify/restrict new location data
class NewLocationForm(Form):
    name = StringField('name', [validators.Length(min=6, max=50)])
    email = StringField('name', [validators.Length(min=6, max=50)])
    address = StringField('address', [validators.Length(min=6, max=50)])


# Location Info
# Function redirects to page detailing information on a specific location, as specified in the path
# Also lists the employees assigned to the location
@app.route('/locationInfo/<int:id>', methods=['GET', 'POST'])
@isLoggedAdmin
def locationInfo(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Submitting employee information to be assigned
    if request.method == 'POST':

        app.logger.info('In POST')

        # Form provides email corresponding to name in dropdown, will be "pass" if no employee selected
        emailAdd = request.form.getlist('empAdd')
        emailRemove = request.form.getlist('empRemove')

        currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Removes selected employees from location, lowers num employees column for each employee removed
        if emailRemove:
            for email in emailRemove:
                cur.execute("update employees set assignedto = 0, lastupdate = %s where email = %s",
                            (currentTime, email))
                cur.execute("update locations set numemployees = numemployees - 1, lastupdate = %s where id = %s",
                            (currentTime, id))
                conn.commit()

        # Assign employees to new location, increase num employees column for each employee assigned
        if emailAdd:
            for email in emailAdd:
                cur.execute("update employees set assignedto = %s, lastupdate = %s where email = %s",
                            (id, currentTime, email))
                cur.execute("update locations set numemployees = numemployees + 1, lastupdate = %s where id = %s",
                            (currentTime, id))
                conn.commit()

        # Will reach at end of POST request, redirects to URL as GET request
        return redirect(url_for('locationInfo', id=id))

    # Get request
    else:
        # Grabs location info and employee info (assigned to this location and unassigned)
        cur.execute("select * from locations where id = %s", [id])
        result = cur.rowcount
        row = cur.fetchone()
        cur.execute("select * from employees where assignedto = %s", [id])
        prows = cur.fetchall()
        cur.execute("select * from employees where assignedto = 0")
        urows = cur.fetchall()
        cur.close()

        # locationInfo.html depends on the location existing in the DB
        if result > 0:
            return render_template('locationInfo.html', location=row, assigned=prows, unassigned=urows)
        else:
            # If the location doesn't exist, user sent back to assignEmployees.html
            return redirect(url_for('assignEmployees'))


# Add Employee
# Allows admin to add a new user the the DB
# User needs to input name, email, assignedto, and usertype columns. ID column is auto-filled
# A usertype of 1 indicates an admin user. Admin users aren't added to the employees table
# A usertype of 2 indicates an employee user
@app.route('/newEmployee', methods=['GET', 'POST'])
@isLoggedAdmin
def newEmployee():
    form = NewEmployeeForm(request.form)

    # Fetch all locations from DB for assignment dropdown in form
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select * from locations")
    rows = cur.fetchall()

    if request.method == 'POST' and form.validate():
        app.logger.info('In POST')

        # Get info from form
        name = form.name.data
        email = form.email.data
        assignedto = form.assignedto.data
        usertype = form.usertype.data
        currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if email already in use
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where email=%s", [email])

        if cur.rowcount > 0:
            flash('Email already in use', 'warning')
            return render_template('newEmployee.html')

        # Add new user to DB for logging info
        cur.execute("insert into users(email, password, usertype) values(%s, %s, %s)",
                    (email, sha256_crypt.hash('0000'), usertype))

        # Add new user to DB for placement info, only if user is an employee
        if usertype == '2':
            cur.execute('insert into employees values(%s, %s, %s, %s)',
                        (email, name, assignedto, currentTime))

            # If new user assigned to location (assignedto != 0), update locations numemployees column
            if assignedto != 0:
                cur.execute("update locations set numemployees = numemployees + 1 where id = %s", [assignedto])

        conn.commit()
        cur.close()

        flash('New User has been added to the database', 'success')

        return redirect(url_for('adminHome'))
    else:
        if request.method == 'POST':
            flash('Please fill all blanks', 'warning')
    return render_template('newEmployee.html', form=form, rows=rows)


# Add Location
# Allows admin to add a new location the the DB
# User only needs to input address and name of new location, other columns are auto-filled
@app.route('/newLocation', methods=['GET', 'POST'])
@isLoggedAdmin
def newLocation():
    form = NewLocationForm(request.form)

    if request.method == 'POST' and form.validate():
        # Get data from form
        app.logger.info('In POST')

        name = form.name.data
        address = form.address.data
        email = form.email.data

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Check location account doesn't already exist
        cur.execute("select * from locations where email = %s", [email])

        if cur.rowcount > 0:
            flash('Location with that email already exists', 'warning')
            return render_template('newLocation.html')

        currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create user corresponding to the new location
        cur.execute("insert into users(email, password, usertype) values(%s, %s, 3)",(email, sha256_crypt.hash('0000')))
        # Insert location
        cur.execute("insert into locations(address, name, email, lastupdate) values(%s, %s, %s, %s)",
                    (address, name, email, currentTime))
        conn.commit()

        cur.close()

        flash('New location has been added to the database', 'success')

        return redirect(url_for('adminHome'))

    # Invalid form, still POST
    else:
        if request.method == 'POST':
            flash('Please fill all blanks', 'warning')
    return render_template('newLocation.html', form=form)


# Update Password
# Updates a user's password, old password has to match hashed version stored in DB
# New password is subject to form validators
@app.route('/updatePassword', methods=['GET', 'POST'])
@isLoggedIn
def updatePassword():
    if request.method == 'POST':
        app.logger.info('In POST')
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        passwordCandidate = request.form['currentPassword']
        newPassword = request.form['newPassword']

        # Check that fields aren't empty
        if newPassword == '' or passwordCandidate == '':
            flash('Please fill all fields', 'warning')
            return render_template('updatePassword.html')

        # Pull hashed password from DB to compare
        cur.execute("select password from users where email=%s", [session['username']])
        if cur.rowcount > 0:
            dbPass = cur.fetchone()
        else:
            flash('Error in changing password', 'warning')
            return render_template('updatePassword.html')

        # Verify that entered password is equivalent to DB password
        if sha256_crypt.verify(passwordCandidate, dbPass['password']):
            # Update DB with new hash
            passw = sha256_crypt.hash(newPassword)
            cur.execute("update users set password = %s where email=%s", (passw, session['username']))

            conn.commit()
            cur.close()

            flash('Your password has been updated', 'success')
            return redirect(url_for('logout'))
        else:
            flash('Incorrect password', 'warning')
            return render_template('updatePassword.html')
    else:
        return render_template('updatePassword.html')


if __name__ == '__main__':
    app.secret_key = 'xb8x04xb0x11a$[k;fxc3x1bxafx06xddU'
    app.debug = True
    app.run()
    conn.close()
