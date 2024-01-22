import json
import socket
import threading
import re
import pymongo
import datetime
from time import sleep

# dababase(mongodb) handler
def init_database():
    print("init database")
    db_client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = db_client["chatroom"]
    users = db["users"]
    messages = db["messages"]
    
    return db
    
def close_database(db):
    print("close database")
    try:
        db.users.drop()
        db.messages.drop()
    except:
        pass
    db.client.close()

def find_user(db, account, password):
    if db.users.count_documents({"account": account, "password": password}, limit = 1) > 0:
        return True 
    else:        
        return False
    
def insert_user(db, account, password):
    db.users.insert_one({"account": account, "password": password})
    
    
def get_messages(db):
    messages = db.messages.find({}).sort("datetime", pymongo.ASCENDING)
    texts = [message["message"] for message in messages]
    return texts
    
def insert_message(db, message):
    db.messages.insert_one({"message": message, "datetime": datetime.datetime.now()})



# http request handler
def get_login(db, request):
    with open("html/login.html", "r") as f:
        response = f.read()
        
    return response

def get_signup(db, request):
    with open("html/signup.html", "r") as f:
        response = f.read()
        
    return response

def get_video(db, request):
    with open("html/video.html", "r") as f:
        response = f.read()
        
    return response

def get_chatroom(db, request):
    with open("html/chatroom.html", "r") as f:
        response = f.read()
    messages = get_messages(db)
    response += f"""<script>
        const postContainer = document.getElementsByClassName("post-container")[0];
        const messages = {messages};

        for (let i = 0; i < {len(messages)}; i++) {{
            const messageContainer = createMessageContainer(messages[i]);
            postContainer.appendChild(messageContainer);
        }}
        setTimeout(() => {{
            postContainer.scrollTop = postContainer.scrollHeight;
        }}, 10);
        </script>"""
        
    return response

def post_signout(db, request):
    set_cookie = None
    with open("html/login.html", "r") as f:
        response = f.read()
    set_cookie = f"Set-Cookie: chatroomlogin=0\r\n expires=Mon, 1 Jan 2024 01:30:00 GMT\r\n;"
    
    return set_cookie, response

def post_chatroom(db, request):
    message = request[-1][8:]
    message = message.replace("+", " ")
    insert_message(db, message)
    with open("html/chatroom.html", "r") as f:
        response = f.read()
    messages = get_messages(db)
    response += f"""<script>
        const postContainer = document.getElementsByClassName("post-container")[0];
        const messages = {messages};

        for (let i = 0; i < {len(messages)}; i++) {{
            const messageContainer = createMessageContainer(messages[i]);
            postContainer.appendChild(messageContainer);
        }}
        setTimeout(() => {{
            postContainer.scrollTop = postContainer.scrollHeight;
        }}, 10);
        </script>"""
        
    return response

def post_signup(db, request):
    request = request[-1]
    pattern = r"Account=(.*)&Password=(.*)"
    match = re.search(pattern, request)
    if match:
        account = match.group(1)
        password = match.group(2)
        with open("html/signup.html", "r") as f:
            response = f.read()
            
        if account == "" or password == "":
            response += """<script>
            document.getElementsByClassName('error')[0].innerHTML = 'invalid account or password';
            document.getElementsByClassName('error')[0].style.visibility = 'visible';
            </script>"""
        else:
            insert_user(db, account, password)
            response += """<script>
            document.getElementsByClassName('error')[0].innerHTML = 'signup succeed';
            document.getElementsByClassName('error')[0].style.visibility = 'visible';
            </script>"""
            
    return response

def post_login(db, request):
    request = request[-1]
    set_cookie = None
    pattern = r"Account=(.*)&Password=(.*)"
    match = re.search(pattern, request)
    if match:
        account = match.group(1)
        password = match.group(2)
        
        if find_user(db, account, password):
            with open("html/chatroom.html", "r") as f:
                response = f.read()
            set_cookie = f"Set-Cookie: chatroomlogin=1\r\n expires=Mon, 1 Jan 2024 01:30:00 GMT\r\n;"
        else:
            with open("html/login.html", "r") as f:
                response = f.read()
            response += "<script>document.getElementsByClassName('error')[0].style.visibility = 'visible';</script>"
    
    return set_cookie, response

def request_handler(db, connection, request):
    print(request)
    request = request.splitlines()
    if len(request) == 0:
        send_msg = "HTTP/1.1 200 OK\r\n\r\n"
        connection.sendall(send_msg.encode())
        return
    method = request[0].split()[0]
    src = request[0].split()[1]
    set_cookie = None
    cookie = None
    
    for i in request:
        if i.startswith("Cookie"):
            cookie_pattern = r"Cookie: chatroomlogin=([^\ ]+)*"
            match = re.search(cookie_pattern, i)
            if match:
                cookie = match.group(1)[0]
            break
        
    if cookie != "1" and not (src == "/signup.html" or src == "/signup" or src == "/login"):
        response = get_login(db, request)
    else:
        if method == "GET" and (src == "/" or src == "/index.html" or src == "/chatroom.html" or src == "/update"):
            response = get_chatroom(db, request)
        
        elif method == "GET" and src == "/signup.html":
            response = get_signup(db, request)
                
        elif method == "GET" and src == "/video.html":
            response = get_video(db, request)
                
        elif method == "GET" and src == "/video.mp4":
            with open("video/cat.mp4", "rb") as f:
                send_msg = f.read()
            
            pattern = r"Range: bytes=(.*?)-(.*?)"
            match = re.search(pattern, request[-2])
            if match:
                start = match.group(1)
                end = match.group(2)
                if start:
                    start = int(start)
                else:
                    start = 0
                if end:
                    end = int(end)
                else:
                    end = len(send_msg)-1
                send_header = f"HTTP/1.1 206 OK\r\nAccept-Ranges: bytes\r\n\Content-Type: video/mp4\r\nContent-Range: bytes {start}-{end}/{len(send_msg)}\r\n\r\n"
                connection.sendall(send_header.encode())
                connection.sendall(send_msg[start:end+1])
                return
        
        elif method == "POST" and src == "/signout":
            set_cookie, response = post_signout(db, request)
            
                
        elif method == "POST" and src == "/chatroom":
            response = post_chatroom(db, request)
            
        elif method == "POST" and src == "/login":
            set_cookie, response = post_login(db, request)
                        
        elif method == "POST" and src == "/signup":
            response = post_signup(db, request)
            
        else:
            response = ""

        
    send_msg = "HTTP/1.1 200 OK\r\n"
    send_msg += "Content-Type: text/html\r\n"
    if set_cookie:
        send_msg += set_cookie
    send_msg += "Content-Length: " + str(len(response)) + "\r\n\r\n"
    send_msg += response
    connection.sendall(send_msg.encode())
        
    return