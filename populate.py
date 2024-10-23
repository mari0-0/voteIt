# import mysql.connector

# connection = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="root",
#     database="votingApp"
# )
# cursor = connection.cursor()
# # with open('DATA.txt', 'r') as file:
# #   while True:
# #     l = file.readline()
# #     if not l:
# #       break
# #     name, cwid, mail = l.replace('\n','').split(",")

# cursor.execute("INSERT INTO main_voter (name, mail, cwid) VALUES (%s, %s, %s)", ('ADMIN TESTER', 'abhainike@gmail.com', 'A50000001'))
# connection.commit()
# cursor.close()
# connection.close()

import sqlite3

# Connect to SQLite database
connection = sqlite3.connect('db.sqlite3')
cursor = connection.cursor()
with open('DATA.txt', 'r') as file:
  while True:
    l = file.readline()
    if not l:
      break
    name, cwid, mail = l.replace('\n','').split(",")
    cursor.execute("INSERT INTO main_voter (name, mail, cwid) VALUES (?, ?, ?)", (name, mail, cwid))
# Insert data into the table

# Commit the transaction
connection.commit()

# Close the cursor and connection
cursor.close()
connection.close()
