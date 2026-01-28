import sqlite3
import re
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'brainbyte' # Needed for flashing messages

DATABASE = 'brainbyte.db'

def get_xp_required_for_level(level):
    """XP needed to complete this level: 50, 100, 200, 400..."""
    return 50 * (2 ** (level - 1))

def get_total_xp_to_reach_level(level):
    """Total XP needed to reach the start of this level."""
    total = 0
    for l in range(1, level):
        total += get_xp_required_for_level(l)
    return total

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create Tables (Condensed)
    tables = [
        'CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 1, exp INTEGER NOT NULL DEFAULT 0)',
        'CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, difficulty INTEGER NOT NULL, exp_reward INTEGER NOT NULL)',
        'CREATE TABLE IF NOT EXISTS question (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, classes_id INTEGER, FOREIGN KEY (classes_id) REFERENCES classes(id))',
        'CREATE TABLE IF NOT EXISTS answer (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, answer_text TEXT, correct_answer BOOLEAN, FOREIGN KEY (question_id) REFERENCES question(id))',
        'CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, content TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY (user_id) REFERENCES account(id))',
        'CREATE TABLE IF NOT EXISTS news (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, date TEXT NOT NULL, content TEXT NOT NULL, patch_id TEXT);'
    ]
    for table in tables: cursor.execute(table)

    # 2. Bulk Insert Data (Only if the table is empty)
    if cursor.execute("SELECT COUNT(*) FROM classes").fetchone()[0] == 0:
        # 15 Levels (3 tiers for each subject)
        # Updated to match the classes_id used in the questions
        levels = [
            # Subject, Tier, XP Reward
            ("basics", 1, 100), ("basics", 2, 200), ("basics", 3, 300),       # IDs 1, 2, 3
            ("operators", 1, 400), ("operators", 2, 500), ("operators", 3, 600), # IDs 4, 5, 6
            ("sequences", 1, 700), ("sequences", 2, 800), ("sequences", 3, 900), # IDs 7, 8, 9 
            ("statements", 1, 1000), ("statements", 2, 1100), ("statements", 3, 1200) # IDs 10, 11, 12
        ]
        cursor.executemany("INSERT INTO classes (name, difficulty, exp_reward) VALUES (?, ?, ?)", levels)

        # Questions (ID 1-4 for Basics 1, ID 5-8 for Operators 1)
        questions = [
            ("How do you create a comment in Python?", 1),
            ("Which character is used to indicate a block of code in Python?", 1),
            ("What is the correct file extension for Python files?", 1),
            ("How do you create a variable with the numeric value 5?", 1),
            ("Which of these is a valid variable name?", 1),
            ("How do you start a multi-line comment in Python?", 1),
            ("Which function is used to check the data type of a variable?", 1),
            ("What is the output of print(2 + 2)?", 1),
            ("Is Python case-sensitive when dealing with identifiers?", 1),
            ("Which of the following is a string in Python?", 1),

            ("What is the output of type(10.5)?", 2),
            ("How do you convert a string '10' into an integer?", 2),
            ("What does the input() function always return by default?", 2),D
            ("Which function is used to get the length of a string?", 2),
            ("What is the result of 'Python'[0]?", 2),
            ("How do you convert a number to a string?", 2),
            ("What is the result of 10 // 3 in Python?", 2),
            ("Which of these will result in an error?", 2),
            ("What is the correct way to write a string with a new line?", 2),
            ("What does the bool(0) expression return?", 2),

            ("What is the result of 10 % 3?", 3),
            ("What is the output of print(2 ** 3)?", 3),
            ("How do you write 'Hello' in all uppercase?", 3),
            ("What is the correct way to format: 'Age: 25' using a variable a = 25?", 3),
            ("What is the result of 'abc' * 3?", 3),
            ("Which method is used to remove whitespace from the beginning and end of a string?", 3),
            ("How do you check if the string 'apple' contains the letter 'a'?", 3),
            ("What is the output of 'Hello_World'[0:5]?", 3),
            ("How do you convert the string 'HELLO' to lowercase?", 3),
            ("What is the output of bool('False')?", 3),

            ("What is the result of 15 / 3 in Python?", 4),
            ("Which operator is used to find the remainder of a division?", 4),
            ("What is the output of print(10 % 4)?", 4),
            ("How do you calculate 5 to the power of 2 (5 squared)?", 4),
            ("What is the result of 3 ** 2?", 4),
            ("Which comparison operator means 'Not Equal'?", 4),
            ("What is the result of the expression: 10 == 10.0?", 4),
            ("Which of these operators always returns a Float value?", 4),
            ("What does the expression 5 != 3 return?", 4),
            ("What is the output of print(10 > 20)?", 4),

            ("What is the result of (True and False)?", 5),
            ("Which logical operator returns True if at least one statement is true?", 5),
            ("What is the output of (5 > 3 or 10 < 2)?", 5),
            ("What does the 'not' operator do to a Boolean value?", 5),
            ("What is the result of not(5 == 5)?", 5),
            ("How do you join (concatenate) two strings 'Hello' and 'World'?", 5),
            ("What is the output of print('Python' + '3')?", 5),
            ("In the expression (True and True), what is the result?", 5),
            ("What is the result of (False or False)?", 5),
            ("Which operator would you use to check if two conditions are BOTH true?", 5),

            ("What does the operator '+=' do in Python?", 6),
            ("If x = 10, what is the value of x after x += 5?", 6),
            ("Which operator is a shortcut for 'x = x - 2'?", 6),
            ("What is the result of 'a' in 'apple'?", 6),
            ("Which operator checks if a value exists inside a list or string?", 6),
            ("If x = 2, what is the output of print(not(4 is (x += x)))?", 6),
            ("Which operator checks if two variables point to the same object in memory?", 6),
            ("What is the result of 'cat' not in ['dog', 'mouse']?", 6),
            ("If a = [1], b = [1], what does (a is b) return?", 6),
            ("What is the shortcut operator to multiply a variable by itself and save the result?", 6),

            ("Which of the following is used to define a List in Python?", 7),
            ("What does it mean when we say a List is 'Mutable'?", 7),
            ("In the list x = [10, 20, 30], what is the index of the value 10?", 7),
            ("Which function returns the number of items in a list?", 7),
            ("Can a single Python list contain both strings and integers?", 7),
            ("What is the result of print([1, 2] + [3, 4])?", 7),
            ("How do you access the last item of a list without knowing its length?", 7),
            ("What is the output of len([1, 2, 3, 4, 5])?", 7),
            ("Which of these is a correctly defined list?", 7),
            ("What is the result of type([1, 2, 3])?", 7),

            ("Which method is used to add an item to the end of a list?", 8),
            ("How do you add an item at a specific index in a list?", 8),
            ("Which method removes the very last item from a list?", 8),
            ("What happens when you use the .sort() method on a list of numbers?", 8),
            ("How do you remove a specific value (like 'apple') from a list?", 8),
            ("What is the result of [1, 2, 3].pop(0)?", 8),
            ("Which method is used to reverse the order of items in a list?", 8),
            ("How do you empty an entire list so it has 0 items?", 8),
            ("If x = [1, 2], what is the result of x.append([3, 4])?", 8),
            ("Which command is used to create a shallow copy of a list?", 8)
        ]
        cursor.executemany("INSERT INTO question (question, classes_id) VALUES (?, ?)", questions)
    
        # Answers (Using True and False for better readability)
        answers = [
            # Q1: How do you create a comment?
            (1, "// comment", False), (1, "/* comment */", False), (1, "# comment", True), (1, "-- comment", False),
    
            # Q2: Which character indicates a block of code?
            (2, "Brackets { }", False), (2, "Parentheses ( )", False), (2, "Indentation", True), (2, "Semicolons ;", False),
            
            # Q3: Correct file extension?
            (3, ".pyth", False), (3, ".pt", False), (3, ".py", True), (3, ".pyt", False),
            
            # Q4: Create variable with value 5?
            (4, "x = 5", True), (4, "int x = 5", False), (4, "x : 5", False), (4, "variable x = 5", False),
            
            # Q5: Valid variable name?
            (5, "2myvar", False), (5, "my-var", False), (5, "my_var", True), (5, "my var", False),
            
            # Q6: Multi-line comment?
            (6, "###", False), (6, "//", False), (6, "'''", True), (6, "---", False),
            
            # Q7: Check data type?
            (7, "check( )", False), (7, "datatype( )", False), (7, "type( )", True), (7, "kind( )", False),
            
            # Q8: Output of print(2 + 2)?
            (8, "22", False), (8, "4.0", False), (8, "4", True), (8, "Error", False),
            
            # Q9: Case-sensitive?
            (9, "No", False), (9, "Only for numbers", False), (9, "Yes", True), (9, "Only for strings", False),
            
            # Q10: Which is a string?
            (10, "123", False), (10, "True", False), (10, "'123'", True), (10, "1.23", False),
            
            # Q11: type(10.5)
            (11, "class 'int' ", False), (11, " class 'float' ", True), (11, " class 'str' ", False), (11, "10.5", False),
    
            # Q12: Convert '10' to int
            (12, "integer('10')", False), (12, "str(10)", False), (12, "int('10')", True), (12, "to_int('10')", False),
            
            # Q13: input() return type
            (13, "Integer", False), (13, "Float", False), (13, "String", True), (13, "Boolean", False),
            
            # Q14: length of string
            (14, "size()", False), (14, "length()", False), (14, "len()", True), (14, "count()", False),
            
            # Q15: 'Python'[0]
            (15, "P", True), (15, "y", False), (15, "0", False), (15, "Error", False),
            
            # Q16: number to string
            (16, "string(5)", False), (16, "str(5)", True), (16, "to_str(5)", False), (16, "text(5)", False),
            
            # Q17: 10 // 3
            (17, "3.33", False), (17, "3.0", False), (17, "3", True), (17, "1", False),
            
            # Q18: Error result
            (18, "'5' + '5'", False), (18, "5 + 5", False), (18, "'5' + 5", True), (18, "str(5) + '5'", False),
            
            # Q19: New line character
            (19, r"_/_n_", False), (19, r"_\_n_", True), (19, r"_\_\_n_", False), (19, r"_|_n_", False),
            
            # Q20: bool(0)
            (20, "True", False), (20, "0", False), (20, "False", True), (20, "None", False),
            
            # Q21: 10 % 3
            (21, "3", False), (21, "1", True), (21, "0", False), (21, "3.33", False),
    
            # Q22: 2 ** 3
            (22, "6", False), (22, "9", False), (22, "8", True), (22, "16", False),
            
            # Q23: 'Hello' to uppercase
            (23, "upper('Hello')", False), (23, "'Hello'.toUpperCase()", False), (23, "'Hello'.upper()", True), (23, "uppercase('Hello')", False),
            
            # Q24: Formatting 'Age: 25'
            (24, "print('Age: ' + a)", False), (24, "print(f'Age: { a }')", True), (24, "print('Age: { a }')", False), (24, "print(Age: a)", False),
            
            # Q25: 'abc' * 3
            (25, "abcabcabc", True), (25, "abc3", False), (25, "a3b3c3", False), (25, "Error", False),
            
            # Q26: Remove whitespace
            (26, "clean()", False), (26, "trim()", False), (26, "strip()", True), (26, "cut()", False),
            
            # Q27: Check if 'a' in 'apple'
            (27, "'a' in 'apple'", True), (27, "exists('a', 'apple')", False), (27, "'apple'.has('a')", False), (27, "if 'a' == 'apple'", False),
            
            # Q28: 'Hello_World'[0:5]
            (28, "Hello_", False), (28, "Hello", True), (28, "World", False), (28, "H", False),
            
            # Q29: 'HELLO' to lowercase
            (29, "lower('HELLO')", False), (29, "'HELLO'.lower()", True), (29, "'HELLO'.small()", False), (29, "tolower('HELLO')", False),
            
            # Q30: bool('False')
            (30, "False", False), (30, "True", True), (30, "0", False), (30, "Error", False),
            
            # Q31: 15 / 3
            (31, "5", False), (31, "5.0", True), (31, "3", False), (31, "Error", False),
    
            # Q32: Remainder operator
            (32, "/", False), (32, "//", False), (32, "%", True), (32, "**", False),
            
            # Q33: 10 % 4
            (33, "2.5", False), (33, "2", True), (33, "0", False), (33, "4", False),
            
            # Q34: 5 squared
            (34, "5 ^ 2", False), (34, "5 ** 2", True), (34, "5 * 2", False), (34, "sqr(5)", False),
            
            # Q35: 3 ** 2
            (35, "6", False), (35, "9", True), (35, "32", False), (35, "5", False),
            
            # Q36: Not Equal
            (36, "<>", False), (36, "not=", False), (36, "!=", True), (36, "==", False),
            
            # Q37: 10 == 10.0
            (37, "True", True), (37, "False", False), (37, "10", False), (37, "Error", False),
            
            # Q38: Returns a Float
            (38, "/", True), (38, "//", False), (38, "%", False), (38, "+", False),
            
            # Q39: 5 != 3
            (39, "True", True), (39, "False", False), (39, "5", False), (39, "None", False),
            
            # Q40: 10 > 20
            (40, "True", False), (40, "False", True), (40, "Error", False), (40, "20", False),
            
            # Q41: (True and False)
            (41, "True", False), (41, "False", True), (41, "None", False), (41, "Error", False),
    
            # Q42: At least one is true
            (42, "and", False), (42, "not", False), (42, "or", True), (42, "xor", False),
            
            # Q43: (5 > 3 or 10 < 2)
            (43, "True", True), (43, "False", False), (43, "5", False), (43, "10", False),
            
            # Q44: What does 'not' do?
            (44, "It deletes it", False), (44, "It doubles it", False), (44, "It reverses it", True), (44, "It makes it True", False),
            
            # Q45: not(5 == 5)
            (45, "True", False), (45, "False", True), (45, "5", False), (45, "None", False),
            
            # Q46: Join strings
            (46, "Hello . World", False), (46, "Hello + World", True), (46, "Hello & World", False), (46, "join(Hello, World)", False),
            
            # Q47: 'Python' + '3'
            (47, "Python 3", False), (47, "Python3", True), (47, "Python+3", False), (47, "Error", False),
            
            # Q48: (True and True)
            (48, "True", True), (48, "False", False), (48, "None", False), (48, "1", False),
            
            # Q49: (False or False)
            (49, "True", False), (49, "False", True), (49, "None", False), (49, "0", False),
            
            # Q50: Both true operator
            (50, "or", False), (50, "and", True), (50, "not", False), (50, "both", False),
            
            # Q51: What does += do?
            (51, "It adds and assigns", True), (51, "It only adds", False), (51, "It compares values", False), (51, "It deletes a variable", False),
    
            # Q52: x = 10; x += 5
            (52, "10", False), (52, "5", False), (52, "15", True), (52, "Error", False),
            
            # Q53: Shortcut for x = x - 2
            (53, "x = - 2", False), (53, "x -= 2", True), (53, "x - 2 = x", False), (53, "x =-- 2", False),
            
            # Q54: 'a' in 'apple'
            (54, "True", True), (54, "False", False), (54, "a", False), (54, "Error", False),
            
            # Q55: Membership check operator
            (55, "is", False), (55, "exists", False), (55, "in", True), (55, "has", False),
            
            # Q56: 5 in [1, 2, 3, 4]
            (56, "True", False), (56, "False", True), (56, "5", False), (56, "None", False),
            
            # Q57: Identity operator
            (57, "==", False), (57, "is", True), (57, "in", False), (57, "id", False),
            
            # Q58: 'cat' not in ['dog', 'mouse']
            (58, "True", True), (58, "False", False), (58, "Error", False), (58, "None", False),
            
            # Q59: a = [1], b = [1]; a is b
            (59, "True", False), (59, "False", True), (59, "Error", False), (59, "[1]", False),
            
            # Q60: Multiply shortcut
            (60, "x =* x", False), (60, "x **= 1", False), (60, "x *= x", True), (60, "x = x ** x", False),

            # Q61: Define a List
            (61, "Square brackets []", True), (61, "Parentheses ()", False), (61, "Curly brackets {}", False), (61, "Angle brackets <>", False),
            
            # Q62: What is Mutable?
            (62, "It can be changed", True), (62, "It cannot be changed", False), (62, "It only stores numbers", False), (62, "It is encrypted", False),
            
            # Q63: Index of 10 in [10, 20, 30]
            (63, "0", True), (63, "1", False), (63, "2", False), (63, "-1", False),
            
            # Q64: Number of items function
            (64, "len()", True), (64, "count()", False), (64, "size()", False), (64, "length()", False),
            
            # Q65: Mixed types?
            (65, "Yes", True), (65, "No", False), (65, "Only in Tuples", False), (65, "Only in Strings", False),
            
            # Q66: [1, 2] + [3, 4]
            (66, "False", True), (66, "True", False), (66, "4", False), (66, "Error", False),
            
            # Q67: Access last item
            (67, "list[-1]", True), (67, "list[0]", False), (67, "list[last]", False), (67, "list.end()", False),
            
            # Q68: len([1, 2, 3, 4, 5])
            (68, "5", True), (68, "4", False), (68, "6", False), (68, "0", False),
            
            # Q69: Correct list definition
            (69, "x = [1, 2]", True), (69, "x = {1, 2}", False), (69, "x = (1, 2)", False), (69, "x = <1, 2>", False),
            
            # Q70: type([1, 2, 3])
            (70, "<class 'list'>", True), (70, "<class 'tuple'>", False), (70, "<class 'array'>", False), (70, "<class 'seq'>", False),

            # Q71: Add to end
            (71, ".append()", True), (71, ".add()", False), (71, ".insert()", False), (71, ".push()", False),
            
            # Q72: Specific index
            (72, ".insert()", True), (72, ".place()", False), (72, ".append()", False), (72, ".index()", False),
            
            # Q73: Remove last item
            (73, ".pop()", True), (73, ".remove()", False), (73, ".delete()", False), (73, ".last()", False),
            
            # Q74: .sort()
            (74, "Arranges them in ascending order", True), (74, "Shuffles them", False), (74, "Deletes them", False), (74, "Multiplies them", False),
            
            # Q75: Remove specific value
            (75, ".remove()", True), (75, ".pop()", False), (75, ".discard()", False), (75, ".delete()", False),
            
            # Q76: [1, 2, 3].pop(0)
            (76, "1", True), (76, "3", False), (76, "[2, 3]", False), (76, "Error", False),
            
            # Q77: Reverse order
            (77, ".reverse()", True), (77, ".backward()", False), (77, ".flip()", False), (77, ".sort(reverse=False)", False),
            
            # Q78: Empty a list
            (78, ".clear()", True), (78, ".empty()", False), (78, ".remove_all()", False), (78, "del list", False),
            
            # Q79: x.append([3, 4])
            (79, "[1, 2, [3, 4]]", True), (79, "[1, 2, 3, 4]", False), (79, "[3, 4]", False), (79, "Error", False),
            
            # Q80: Shallow copy
            (80, ".copy()", True), (80, ".clone()", False), (80, ".duplicate()", False), (80, ".view()", False)
        ]
        cursor.executemany("INSERT INTO answer (question_id, answer_text, correct_answer) VALUES (?, ?, ?)", answers)
    conn.commit()
    conn.close()

init_db()

def get_xp_required_for_level(level):
    """How much XP is needed JUST to complete this specific level."""
    # level 1: 50, level 2: 100, level 3: 200, etc.
    return level * 100

def get_total_xp_needed_to_reach_level(level):
    """The total cumulative XP needed to start this level."""
    total = 0
    for l in range(1, level):
        total += get_xp_required_for_level(l)
    return total

# --- Routes ---

@app.route("/")
def home():
    logged_in = 'user_id' in session 
    return render_template('index.html', logged_in=logged_in)
 
@app.route("/about")
def about():
    return render_template("about.html", logged_in='user_id' in session)

@app.route("/news")
def news():
    news_updates = [
        {
            "id": "patch-1.0.4",
            "date": "2026-05-20",
            "title": "Neural Link Stabilization",
            "content": "Fixed a critical bug where replaying lower-tier nodes granted full XP. Replay rewards are now capped at 25 XP to encourage progression."
        },
        {
            "id": "patch-1.0.3",
            "date": "2026-05-15",
            "title": "Database Expansion",
            "content": "Added 15 new logic puzzles to Tier 2 and Tier 3. Operatives are encouraged to sync with the new data packets."
        },
        {
            "id": "announcement",
            "date": "2026-05-10",
            "title": "Welcome to BrainByte",
            "content": "The BrainByte network is officially online. Good luck, Operative."
        }
    ]

    conn = get_db_connection()
    
    # 1. Check if the table is empty
    count = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    
    # 2. If empty, populate it automatically from your list
    if count == 0:
        for update in news_updates:
            conn.execute("""
                INSERT INTO news (title, date, content, patch_id) 
                VALUES (?, ?, ?, ?)
            """, (update['title'], update['date'], update['content'], update['id']))
        conn.commit()

    # 3. Pull the final data from the database
    news_data = conn.execute("SELECT * FROM news ORDER BY date DESC").fetchall()
    conn.close()
    
    return render_template("news.html", 
                           logged_in='user_id' in session, 
                           news_updates=news_data)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    conn = get_db_connection()
    if request.method == "POST":
        if 'user_id' not in session:
            flash("You must be logged in to leave a review.")
            return redirect(url_for('login'))
        
        content = request.form.get("review_content")
        if content:
            conn.execute("INSERT INTO reviews (user_id, content) VALUES (?, ?)", 
                         (session['user_id'], content))
            conn.commit()
            return redirect(url_for('contact'))

    # Fetch reviews and join with account table to get emails (as usernames)
    reviews = conn.execute('''
        SELECT r.content, r.timestamp, a.username 
        FROM reviews r 
        JOIN account a ON r.user_id = a.id 
        ORDER BY r.timestamp DESC
    ''').fetchall()
    conn.close()
    
    logged_in = 'user_id' in session
    return render_template("contact.html", reviews=reviews, logged_in=logged_in)

@app.route("/signin")
def signin():
    return render_template("signin.html")

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("pswd")

    if not email or not password:
        return render_template("signin.html", error="CRITICAL ERROR: FILL THE FORMS")

    if not is_valid_password(password):
        return render_template("signin.html", error="CRITICAL ERROR: WEAK PASSWORD")

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        # Use 'cur' to capture the new ID created by the database
        cur = conn.execute("INSERT INTO account (username, email, password) VALUES (?, ?, ?)", 
                           (username, email, hashed_password))
        conn.commit()
        
        # Save the new ID in the session to log them in automatically
        session['user_id'] = cur.lastrowid 
        conn.close()
        
        # Redirect to 'home' instead of 'login'
        return redirect(url_for('home'))
    except sqlite3.IntegrityError:
        return render_template("signin.html", error="CRITICAL ERROR: USER ALREADY EXISTS")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pswd")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM account WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            # Save the user's ID in the session
            session['user_id'] = user['id'] 
            return redirect(url_for('home'))
        else:
            return render_template("login.html", error="ACCESS DENIED: INVALID CREDENTIALS")

    return render_template("login.html")

# Add a logout route to clear the session later
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route("/map")
def game_map():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_stats = conn.execute("SELECT level, exp FROM account WHERE id = ?", (session['user_id'],)).fetchone()
    all_levels = conn.execute("SELECT * FROM classes ORDER BY difficulty ASC").fetchall()
    news_items = conn.execute("SELECT * FROM news ORDER BY date DESC").fetchall()
    conn.close()

    if user_stats is None: return redirect(url_for('login'))

    current_level = user_stats['level']
    total_xp = user_stats['exp']
    
    needed_for_this_level = get_xp_required_for_level(current_level)

    # 1. Get the baseline XP needed to even reach the current level
    baseline_xp = get_total_xp_needed_to_reach_level(current_level)
    
    # 2. Progress within this level = Total XP - baseline
    # This automatically includes any leftover XP from the previous level-up
    current_level_progress = total_xp - baseline_xp
    
    # 3. Requirement for the next milestone
    needed_for_this_level = get_xp_required_for_level(current_level)
    
    # 4. Calculate percentage for the front-end bar
    xp_percentage = min((current_level_progress / needed_for_this_level) * 100, 100)

    conn.close()

    return render_template("map.html", 
                           user_stats=user_stats,
                           current_progress=current_level_progress, # Sent to display "X / Y XP"
                           xp_percentage=xp_percentage, 
                           xp_needed=needed_for_this_level, # Sent to display the denominator
                           all_levels=all_levels,
                           news_items=news_items)

@app.route("/update_xp", methods=["POST"])
def update_xp():
    if 'user_id' not in session:
        return {"status": "error", "message": "Unauthorized"}, 401
    
    data = request.get_json()
    points = data.get('points', 0)
    tier_id_raw = data.get('tier_id') # Raw data from JS
    
    # --- FIX 1: Safe integer conversion to prevent 500 errors ---
    try:
        tier_id = int(tier_id_raw) if tier_id_raw is not None else 0
    except (ValueError, TypeError):
        tier_id = 0

    conn = get_db_connection()
    try:
        # 1. Get current user level
        user = conn.execute("SELECT exp, level FROM account WHERE id = ?", (session['user_id'],)).fetchone()
        if not user:
            return {"status": "error", "message": "User not found"}, 404
            
        current_level = user['level']
        
        # 2. DIMINISHING RETURNS LOGIC
        # Ensure we only cap if a valid tier_id was actually sent
        if tier_id > 0 and current_level > tier_id:
            points = 25
            status_msg = "Redundant data detected: Minimal XP granted."
        else:
            status_msg = "Neural link stable: Full XP granted."

        # 3. Add points
        conn.execute("UPDATE account SET exp = exp + ? WHERE id = ?", (points, session['user_id']))
        
        # 4. Refresh and Level Up Logic
        user = conn.execute("SELECT exp, level FROM account WHERE id = ?", (session['user_id'],)).fetchone()
        current_exp = user['exp']
        old_level = user['level']
        new_level = old_level
        
        # Check for multiple level ups at once
        while current_exp >= get_total_xp_needed_to_reach_level(new_level + 1):
            new_level += 1
        
        level_up = False
        if new_level > old_level:
            conn.execute("UPDATE account SET level = ? WHERE id = ?", (new_level, session['user_id']))
            level_up = True
        
        conn.commit()
        
        return {
            "status": "success", 
            "message": status_msg,
            "new_xp": current_exp, 
            "new_level": new_level,
            "level_up": level_up,
            "points_earned": points 
        }
    except Exception as e:
        conn.rollback() # Undo changes if something goes wrong
        return {"status": "error", "message": str(e)}, 500
    finally:
        conn.close()

@app.route("/api/questions/<int:level_id>")
def get_questions(level_id):
    conn = get_db_connection()
    
    # Find the level name
    level = conn.execute("SELECT name FROM classes WHERE id = ?", (level_id,)).fetchone()
    
    if not level:
        conn.close()
        return {"error": "Level not found"}, 404

    # 1. Get ALL questions for this level from the database
    all_questions = conn.execute("SELECT * FROM question WHERE classes_id = ?", (level_id,)).fetchall()
    
    # 2. Pick up to 10 questions 
    # This gives your frontend enough data to slice its 5 random questions
    selected_questions = random.sample(all_questions, min(len(all_questions), 10))
    
    quiz_data = []
    for q in selected_questions:
        answers = conn.execute("SELECT * FROM answer WHERE question_id = ?", (q['id'],)).fetchall()
        quiz_data.append({
            'text': q['question'],
            'answers': [{'text': a['answer_text'], 'correct': a['correct_answer']} for a in answers]
        })
        
    conn.close()
    
    return {"level_name": level['name'], "questions": quiz_data}


if __name__ == "__main__":
    app.run(debug=True)