import sqlite3
import os
from faker import Faker
import random

def create_academic_db():
    db_path = 'academic.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    fake = Faker()

    # Create tables
    c.execute('''
        CREATE TABLE department (
            dept_id INTEGER PRIMARY KEY,
            dept_name TEXT NOT NULL,
            creation TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE faculty (
            fac_id INTEGER PRIMARY KEY,
            fac_name TEXT NOT NULL,
            dept_id INTEGER,
            FOREIGN KEY (dept_id) REFERENCES department(dept_id)
        )
    ''')

    c.execute('''
        CREATE TABLE publication (
            pub_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            year INTEGER,
            Ptype TEXT,
            fac_id INTEGER,
            FOREIGN KEY (fac_id) REFERENCES faculty(fac_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE writes (
            fac_id INTEGER,
            pub_id INTEGER,
            PRIMARY KEY (fac_id, pub_id),
            FOREIGN KEY (fac_id) REFERENCES faculty(fac_id),
            FOREIGN KEY (pub_id) REFERENCES publication(pub_id)
        )
    ''')

    # --- Populate with 100 rows of sample data ---

    # 1. Departments
    departments = []
    for i in range(1, 101):
        dept_name = fake.bs().title() + " Department"
        creation = fake.year()
        departments.append((i, dept_name, creation))
    c.executemany("INSERT INTO department (dept_id, dept_name, creation) VALUES (?, ?, ?)", departments)

    # 2. Faculty
    faculty = []
    for i in range(1, 101):
        fac_name = fake.name()
        dept_id = random.randint(1, 100)
        faculty.append((i, fac_name, dept_id))
    c.executemany("INSERT INTO faculty (fac_id, fac_name, dept_id) VALUES (?, ?, ?)", faculty)

    # 3. Publications
    publications = []
    pub_types = ['journal', 'conference', 'book']
    for i in range(1, 101):
        title = fake.sentence(nb_words=6).replace('.', '')
        year = random.randint(2000, 2025)
        ptype = random.choice(pub_types)
        author_id = random.randint(1, 100)
        publications.append((i, title, year, ptype, author_id))
    c.executemany("INSERT INTO publication (pub_id, title, year, Ptype, fac_id) VALUES (?, ?, ?, ?, ?)", publications)

    # 4. Writes (linking table)
    writes = set()
    while len(writes) < 100:
        fac_id = random.randint(1, 100)
        pub_id = random.randint(1, 100)
        # Ensure the faculty member is an author of the publication
        c.execute("UPDATE publication SET fac_id = ? WHERE pub_id = ?", (fac_id, pub_id))
        writes.add((fac_id, pub_id))
    c.executemany("INSERT INTO writes (fac_id, pub_id) VALUES (?, ?)", list(writes))

    conn.commit()
    conn.close()
    print(f"Database '{db_path}' created successfully with 100 rows in each table.")

if __name__ == '__main__':
    create_academic_db()
