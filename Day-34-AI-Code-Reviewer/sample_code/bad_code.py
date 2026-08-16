# sample_code/bad_code.py
# This file intentionally has many code quality issues for the reviewer to find

import os, sys, json
import requests
from datetime import datetime
import time

# Global mutable state — bad practice
GLOBAL_COUNTER = 0
cache = {}
errors = []

def getUserData(id, db, cache, use_cache=True, retry=True, verbose=False, timeout=None, format=None, transform=None):
    """get user"""
    # No type hints, too many parameters, too long function
    global GLOBAL_COUNTER
    GLOBAL_COUNTER = GLOBAL_COUNTER + 1
    
    if use_cache == True:
        if id in cache:
            return cache[id]
    
    try:
        # Hardcoded credentials — SECURITY ISSUE
        response = requests.get(
            f"http://api.example.com/users/{id}",
            headers={"Authorization": "Bearer hardcoded_secret_token_12345"},
            timeout=timeout
        )
        
        data = response.json()
        
        # SQL injection vulnerability
        query = "SELECT * FROM users WHERE id = " + str(id)
        result = db.execute(query)
        
        x = data
        y = result
        z = x if x else y  # cryptic variable names
        
        if z != None:  # should use 'is not None'
            cache[id] = z
            return z
        else:
            return None
    except:  # bare except — catches everything including SystemExit
        errors.append(id)
        return None

def process_list(items):
    # O(n²) complexity unnecessarily
    result = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in result:
                    result.append(items[i])
    return result

def connect_db():
    # No error handling, no connection pooling
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        user="postgres", 
        password="password123",  # hardcoded password
        database="mydb"
    )
    return conn

class dataProcessor:  # should be DataProcessor (PascalCase)
    def __init__(self):
        self.data = []
        self.processed = False
        self.error = None
        self.timestamp = None
        self.version = None
        self.config = None  # many uninitialized attributes
    
    def Process(self):  # method should be lowercase
        # No return value, modifies state in place
        for i in range(0, len(self.data), 1):
            x = self.data[i]
            self.data[i] = x * 2  # magic operation, unclear intent
        self.processed = True

def divide(a, b):
    # ZeroDivisionError not handled
    return a / b

# Unused imports at top (os, sys, time)
# No module docstring
# Magic numbers
TIMEOUT = 30
MAX_RETRIES = 3
BATCH_SIZE = 100

def fetch_all(ids):
    results = []
    for id in ids:
        time.sleep(0.1)  # blocking sleep in a loop
        result = getUserData(id, None, {})
        results.append(result)
    return results