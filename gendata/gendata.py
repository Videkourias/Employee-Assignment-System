import random as rm
import string
from datetime import datetime

import json
import names
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from passlib.hash import sha256_crypt

# Imports env variables and creates DB connection
load_dotenv()
DBNAME = os.getenv('DBNAME')
DBUSER = os.getenv('DBUSER')
DBPASS = os.getenv('DBPASS')

conn = psycopg2.connect(dbname=DBNAME, user=DBUSER, password=DBPASS)

# Fills employees table with random data, satisfies foreign key constraint
def employeeData(num):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Get valid assignedto values
    cur.execute("select id from locations")
    ids = cur.fetchall()
    ids.append([0])  # Allow unassigned to be a possible assignment
    cap = len(ids)

    currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for i in range(num):
        name = names.get_full_name()
        #lname = name.split(' ')[1]
        email = ''.join(rm.choice(string.ascii_letters) for x in range(10)).lower() + "@gmail.com"
        assignedto = ids[rm.randrange(cap)][0]

        # Add to users table first, to satisfy foreign key constraint
        try:
            cur.execute("insert into users(email, password, usertype) values(%s, %s, %s)",
                        (email, sha256_crypt.hash('0000'), 2))
        except psycopg2.DatabaseError:
            print("Error adding row")
            continue

        cur.execute('insert into employees values(%s, %s, %s, %s)',
                    (email, name, assignedto, currentTime))

        if assignedto != 0:
            cur.execute("update locations set numemployees = numemployees + 1 where id = %s", [assignedto])
        print(name, "--", email, "--", assignedto, "--", currentTime)

    conn.commit()
    cur.close()


# Fills locations table with random data
def locationData(num):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Read address data from JSON files
    with open('gendata/addresses-us-500.min.json', 'r') as f:
        data = f.read()
    addresses = json.loads(data)

    with open('gendata/vegetables.json', 'r') as f:
        data = f.read()
    vegetables = json.loads(data)

    # Get length of JSON data
    vlen = len(vegetables["vegetables"])
    alen = len(addresses["addresses"])

    currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for i in range(num):
        # Create farm name
        vegetable = vegetables["vegetables"][rm.randrange(vlen)].title()  # Random vegetable
        suffix = 'Farm' if rm.randint(0, 1) else 'Greenhouse'  # Random type of grower (Farm|Greenhouse)
        lname = names.get_last_name()  # Random owner
        prefix = lname + "'s"

        name = prefix + " " + vegetable + " " + suffix
        address = addresses["addresses"][rm.randrange(alen)]["address1"]
        email = lname + "@gmail.com"

        try:
            # Create user corresponding to the new location
            cur.execute("insert into users(email, password, usertype) values(%s, %s, 3)",
                        (email, sha256_crypt.hash('0000')))
        except psycopg2.DatabaseError:
            print("Error adding row")
            continue

        # Insert location
        cur.execute("insert into locations(address, name, email, lastupdate) values(%s, %s, %s, %s)",
                    (address, name, email, currentTime))
        #print(name, "--", email, "--", currentTime)


    conn.commit()
    cur.close()


# Method to create the root account, if it was deleted
def addRoot():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("insert into users(email, password, usertype) values(%s, %s, 1)", ("root@admin.com", sha256_crypt.hash('root')))
    conn.commit()

    cur.close()

# Clear DB tables and reset sequences
def clearDB():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("delete from requests")
    cur.execute("delete from locations")
    cur.execute("delete from employees")
    cur.execute("delete from users")
    cur.execute("alter sequence locations_id_seq restart with 1")
    cur.execute("alter sequence requests_reqnum_seq restart with 1")
    conn.commit()

    cur.close()


# Customizable Populate Option
def populate(numEmp, numLoc):
    clearDB()
    addRoot()
    locationData(int(numEmp))
    employeeData(int(numLoc))
    conn.close()

if __name__ == "__main__":
    pass
    #conn = psycopg2.connect(dbname='postgres', user='postgres', password='root')
    #clearDB(conn)
    #addRoot(conn)
    #locationData(18, conn)
    #employeeData(50, conn)
    #conn.close()
