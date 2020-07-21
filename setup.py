import os
import psycopg2
import psycopg2.extensions
from gendata import gendata
from psycopg2.extensions import AsIs
from dotenv import load_dotenv


def main():
    # Load environmental variables
    load_dotenv()
    DBNAME = os.getenv('DBNAME')
    DBDFNAME = os.getenv('DBDFNAME')
    DBUSER = os.getenv('DBUSER')
    DBDFUSER = os.getenv('DBDFUSER')
    DBPASS = os.getenv('DBPASS')
    DBDFPASS = os.getenv('DBDFPASS')

    print('Logging in with:')
    print('Database Name: {}\nUser: {}\nPassword: {}\n'.format(DBDFNAME, DBDFUSER, DBDFPASS))

    print('\nGoing to create:')
    print('Database Name: {}\nUser: {}\nPassword: {}\n'.format(DBNAME, DBUSER, DBPASS))

    # Create new user
    conn = psycopg2.connect(dbname=DBDFNAME, user=DBDFUSER, password=DBDFPASS)
    cur = conn.cursor()

    autocommit = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
    conn.set_isolation_level(autocommit)

    # Try to create user account, skip if already exist, end if other error
    try:
        cur.execute("create user %s with password %s createdb", (AsIs(DBUSER), DBPASS))
        print("Successfully created role {}".format(DBUSER))
    except psycopg2.DatabaseError as e:
        print(e)
    except Exception as e:
        print("Error in creation of user account:", e)
        return

    # Try to create database, skip if already exist, end if other error
    try:
        cur.execute("create database %s owner %s", (AsIs(DBNAME), AsIs(DBUSER)))
        print("Successfully created database {}".format(DBNAME))
    except psycopg2.DatabaseError as e:
        print(e)
    except Exception as e:
        print("Error in creation of database:", e)
        return

    cur.close()
    conn.close()

    # Configure new DB
    conn = psycopg2.connect(dbname=DBNAME, user=DBUSER, password=DBPASS)
    cur = conn.cursor()

    autocommit = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
    conn.set_isolation_level(autocommit)

    # Run schema setup
    try:
        cur.execute(open("PostgreSQL/PostgreSQL Workbench Schema/setup.sql", "r").read())
        print("Successfully created schema")
    except psycopg2.DatabaseError as e:
        print(e)
    except Exception as e:
        print("Error in creation of schema:", e)

    # Populate DB
    print("Populating {}...".format(DBNAME))
    gendata.populate(os.getenv('EMPLOYEES'), os.getenv('LOCATIONS'))

    cur.close()
    conn.close()

    print("Setup Complete. Can now launch app.py")


if __name__ == '__main__':
    main()
