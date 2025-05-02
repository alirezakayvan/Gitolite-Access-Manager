#!/usr/bin/env python3
# ------------------------
# -- Created by: Alireza Kayvan
# -- Date: 2017-Dec-10
# -- Version: 0.1
# ------------------------

import os
import filecmp
import time
import json
import pwd
from datetime import datetime
from shutil import copyfile
import MySQLdb as mysqldb

# --------------------------------------------------
LOCKFILE = "/tmp/glcreator.lock"
ROOT_PATH = "/home/user"
TEMP_PATH = os.path.join(ROOT_PATH, "tmp")
LOGFILE = os.path.join(ROOT_PATH, "gitolite_creator.log")
DBHOST = 'DBHOST'
DBUSER = 'DBUSER'
DBPASS = 'DBPASS'
DBNAME = 'DBNAME'
DEBUG = 'stdlog'  # or 'stdout'

# --------------------------------------------------
def log(msg):
    cur = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if DEBUG == "stdout":
        print(f'"{cur}" "{msg}"')
    elif DEBUG == "stdlog":
        with open(LOGFILE, 'a') as lf:
            lf.write(f'"{cur}" "{msg}"\n')

def exit_program(exit_code):
    if os.path.isfile(LOCKFILE):
        os.remove(LOCKFILE)
    exit(exit_code)

# --------------------------------------------------
# ---------------- MAIN ----------------------------
# --------------------------------------------------

if os.path.isfile(LOCKFILE):
    print("The program 'glconf-creator' is currently running")
    exit(1)
else:
    with open(LOCKFILE, 'w'):
        pass

try:
    if DEBUG not in ['stdout', 'stdlog']:
        print("Invalid value for the variable 'DEBUG'")
        print("The variable 'DEBUG' must be set to 'stdout' or 'stdlog'")
        exit_program(0)

    log("Starting program...")

    con = mysqldb.connect(DBHOST, DBUSER, DBPASS, DBNAME)
    cur = con.cursor()
    cur.execute("SELECT DISTINCT(RepositoryPath) FROM GIT_repository ORDER BY RepositoryPath ASC")
    rows = cur.fetchall()

    config_path = os.path.join(ROOT_PATH, 'user_permissions.conf')
    open(config_path, 'w').close()

    for row in rows:
        repository = row[0]
        repoText = f"repo {repository}"

        with open(config_path, 'a+') as glconf:
            # Repository-wide permissions
            cur.execute(f"SELECT GROUP_CONCAT(DISTINCT(username) SEPARATOR ' ') FROM GIT_permissions WHERE repository = '{repository}'")
            perm_users = cur.fetchone()[0] or ''
            glconf.write(repoText + "\n")
            glconf.write(f"   RW+  = {perm_users}\n")

            # Directory-specific permissions
            has_vref = False
            cur.execute(f"SELECT directory FROM GIT_permissions WHERE repository = '{repository}' AND directory <> '' GROUP BY directory")
            directories = cur.fetchall()

            for directory_row in directories:
                directory = directory_row[0]
                cur.execute(f"SELECT GROUP_CONCAT(DISTINCT(username) SEPARATOR ' ') FROM GIT_permissions WHERE repository = '{repository}' AND directory = '{directory}'")
                user_text = cur.fetchone()[0] or ''
                glconf.write(f"   RW+  VREF/NAME{directory} = {user_text}\n")
                has_vref = True

            if has_vref:
                cur.execute(f"SELECT GROUP_CONCAT(DISTINCT(username) SEPARATOR ' ') FROM GIT_permissions WHERE repository = '{repository}' AND directory <> ''")
                deny_users = cur.fetchone()[0] or ''
                glconf.write(f"   -    VREF/NAME/     =   {deny_users}\n")
                glconf.write("   R    VREF/NAME/     =   @all\n")
            else:
                glconf.write("   R    VREF/NAME/     =   @all\n")

    gitolite_conf_path = os.path.join(ROOT_PATH, 'gitolite-admin/conf/user_permissions.conf')
    if not filecmp.cmp(config_path, gitolite_conf_path):
        os.system(f'cd {ROOT_PATH}/gitolite-admin && git stash && git pull')
        copyfile(config_path, gitolite_conf_path)
        os.system(f'cd {ROOT_PATH}/gitolite-admin && git add conf/user_permissions.conf && git commit -m "updated by dbmanager.script" && git push')

    exit_program(0)

except Exception as e:
    print(str(e))
    exit_program(1)
