#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Name - Tanzima Sultana
# UTA ID - 1001759430 


# In[ ]:


import socket
import threading
import tkinter as tk
import os
import pickle
import time


# In[ ]:


# Reserve a port number for connection
SERVER_ADDR = '127.0.0.1'
BACKUP_SERVER_PORT = 14455
BACKUP_POLLING_PORT = 11112

# File path 
FILE_PATH = os.getcwd() + "\Backup_Server\\"
# Main GUI
root = ''

# Client dictionary
client_dict = {}

# List of misspelled words
words = []
# Polling wait time
WAIT_TIME = 20


# In[ ]:


# Constants
SERVER = "server_"
SUCCESSFUL = "successful"
FAILED = "failed"
DUPLICATE = "duplicate"
CLIENT_DISCONNECT = "disconnect"
CLIENT_CONNECT = "connect"
USERNAME = "username"
MESSAGE = "message"
FILE = "file"
RETURN = "ret_"
DISCONNECT_MSG = "Ran out of input"

# Keys for client messages
KEY_USERNAME = "key_username"
KEY_FILE = "key_file"
KEY_MESSAGE = "key_message"
KEY_FAIL = "key_fail"
KEY_POLL = "key_poll"
REQ_POLL = "req_poll"

ACTIVE = "active"
INACTIVE = "inactive"

BACKUP_LEXICON_WORDS = "lexicon_words"
PRIMARY_SERVER = "primary_server"
BACKUP_SERVER = "backup_server"
# Server crash message
SERVER_CRASH = "[WinError 10054] An existing connection was forcibly closed by the remote host"


# In[ ]:


def initialize():
    # Clear client_dict
    global client_dict
    client_dict.clear()
    
    # https://stackoverflow.com/questions/14676265/how-to-read-a-text-file-into-a-list-or-an-array-with-python
    # Handle lexicon file
    # Create a list with the misspelled words
    global words
    words.clear()
    file = FILE_PATH + "lexicon_file.txt"
    with open(file) as f:
        words = f.read().split(' ')
    
    print("Lexicon Words")
    print(words)


# In[ ]:


# Create scoket object to keep connection and polling socket information together
# To close connection for client disconnect
# https://stackoverflow.com/questions/19985282/how-to-implement-c-type-structures-in-python

class socket_obj(object):
    def __init__(self, conn_socket, poll_socket):
        self.conn_socket = conn_socket
        self.poll_socket = poll_socket


# In[ ]:


def create_socket(conn_socket, poll_socket):
    return socket_obj(conn_socket, poll_socket)


# In[ ]:


# Create client_status class to keep each client information 
# Name, Connection status, File status
# https://stackoverflow.com/questions/19985282/how-to-implement-c-type-structures-in-python

class client_status(object):
    def __init__(self, name, conn, file, thread_id):
        self.name = name
        self.conn = conn
        self.file = file
        self.thread_id = thread_id


# In[ ]:


# Create client_dict dictionary
# Key - name of the client
# Value - client_status class object

def add_client(username, thread_id):
    user = client_status(username, "Connected", "N/A", thread_id)
    
    global client_dict
    client_dict[username] = user 


# In[ ]:


# Check username already exists or not in client_dict dictionary
# Return True = Duplicate
# Return False = Not, New username

# https://www.tutorialspoint.com/python/python_dictionary.htm

def is_duplicate_client(username):
    global client_dict
    
    if username in client_dict:
        check = True
    else:
        check = False
    return check


# In[ ]:


# Input - current running thread
# Output - username associated with the thread
def current_client(thread_id):
    username = ''
    global client_dict
    
    for key in client_dict:
        value = client_dict[key]
        # Find the user associated with the thread
        if(value.thread_id == thread_id):
            username = value.name
            break
    print("current_client : ", thread_id, username)
    return username


# In[ ]:


# After client disconnect, delete client from client_dict & delete files
def delete_client(username):

    print("delete_client : ", username)
    # Pop fron client_dict
    global client_dict
    client_dict.pop(username)
    
    # Delete client files
    delete_client_file(username)


# In[ ]:


# After server disconnect/crash, delete all files of all clients
def delete_all_client_files():
    print("delete_all_client_files")
    global client_dict
    for username in client_dict:
        delete_client_file(username)


# In[ ]:


# Delete files associated with the client
def delete_client_file(username):
    print("delete_client_file : ", username)
    # Delete client files
    file1 = client_file(username, SERVER)
    file2 = client_file(username, RETURN)
    if os.path.exists(file1):
        os.remove(file1)
        print("File removed : ", file1)
    if os.path.exists(file2):
        print("File removed : ", file2)
        os.remove(file2)
    else:
        print("The file does not exist")


# In[ ]:


# Input - username & type of file (Server/Return)
# Output - return file name
# Server - file sent by client, saved at server side
# Return - after spell check, the file to return

def client_file(username, file_type):
    #Create receive file name with client name
    filename = file_type + username + '.txt'
    file = FILE_PATH + filename
    print("client_file : ", username, filename)
    return file


# In[ ]:


# Spell check method
# Parameter - file received from client and an empty file that will be returned to client(recv_file, ret_file) 
# Words from client received file and server lexicon file are stored in a list
# Compare words from two list & write to 'ret_file'
# Return 'ret_file' with misspelled word as [word]

def process_client_file(username):
    
    # Return file
    recv_file = client_file(username, SERVER)
    ret_file = client_file(username, RETURN)
    
    # Create list with the words received
    recv_words = []
    with open(recv_file) as f:
        recv_words = f.read().split(' ')
    
    global words
    space = ' '
    
    with open(ret_file, 'wb') as f:
        
        for w1 in recv_words: # Client file
            # The word to write in file
            w = w1
            for w2 in words: # Server file
                if(w1.lower() == w2.lower()): # If word matches # https://stackoverflow.com/questions/319426/how-do-i-do-a-case-insensitive-string-comparison
                    w = '[' + w1 + ']'
            
            # Write w in file        
            f.write(w.encode())
            f.write(space.encode())
    
    f.close()
    
    return ret_file


# In[ ]:


# Input - newly added words from client
# Function - find duplicate, merge new words with old ones and save it to Lexicon file
# Output - return duplicate words

def process_new_words(new_words):
    global words
    
    # https://www.programiz.com/python-programming/set
    duplicate_words = set(words) & set(new_words) # AND operation for duplicate words
    lex_words = set(words) | set(new_words) # OR operation for updated words
    
    print("process_new_words : old : ", words)
    print("process_new_words : new : ", new_words)
    print("process_new_words : duplicate : ", list(duplicate_words))
    print("process_new_words : updated : ", list(lex_words))
    
    # Update lexicon file
    # https://www.geeksforgeeks.org/convert-set-to-string-in-python/
    words = list(lex_words)
    
    '''
    # Delete old file
    old_file = FILE_PATH + "lexicon_file.txt"
    if os.path.exists(old_file):
        os.remove(old_file)
        print("process_new_words : File removed : ", old_file)
    '''
    
    # Create new file & write into it
    new_file = FILE_PATH + "lexicon_file.txt"
    file = open(new_file, "w")
    for w in words:
        file.write(w)
        file.write(' ')
    
    file.close()
    
    # Return duplicate words
    return list(duplicate_words)


# In[ ]:


# Print information from client_dict
def client_information():
    print("client_information")
    for key in client_dict:
        value = client_dict[key]
        print(value.name, value.conn, value.thread_id)


# In[ ]:


# Server class
class server:
    def __init__(self, master):
        
        print("Backup Server")
        self.master = master
        self.master.title("Backup Server")
        self.master.geometry("400x400")
        
        #### Server variables
        self.socketList = []
        self.serverStatus = ''
        
        # Create Server GUI
        self.create_server_gui()
        # Start server thread
        self.start_primary_server_thread()
    
    ### -------------------------- GUI --------------------------- ###
    def create_server_gui(self):
        # Text label for server status
        self.serverStatus = tk.Label(self.master, text = "Server Status : " + INACTIVE)
        self.serverStatus.grid(row = 0)

        # Grid for client, connection status and file status
        # Clinet - connected client name
        # Connection status - N/A, connected, disconnected
        # File status - processed & returned

        ## Client
        self.client = tk.Label(self.master, text = "Client")
        self.client.grid(row = 1, column = 0)
        
        # Loop through labels
        # https://stackoverflow.com/questions/42599924/python-tkinter-configure-multiple-labels-with-a-loop
        
        self.clientLabels = [] #creates an empty list for client labels
        for i in range(2,5):
            self.cLabel = tk.Label(self.master, text = "N/A")
            self.cLabel.grid(row = i, column = 0)
            self.clientLabels.append(self.cLabel)

        ## Connection Status
        self.conn = tk.Label(self.master, text = "Conn. Status")
        self.conn.grid(row = 1, column = 1)
        
        self.connLabels = [] #creates an empty list for connection status labels
        for i in range(2,5):
            self.cnLabel = tk.Label(self.master, text = "N/A")
            self.cnLabel.grid(row = i, column = 1)
            self.connLabels.append(self.cnLabel)

        ## File status
        self.file = tk.Label(self.master, text = "File")
        self.file.grid(row = 1, column = 2)
        
        self.fileLabels = [] #creates an empty list for file status labels
        for i in range(2,5):
            self.fLabel = tk.Label(self.master, text = "N/A")
            self.fLabel.grid(row = i, column = 2)
            self.fileLabels.append(self.fLabel)
        
        # Most recent client status
        self.status = tk.Label(self.master, text = "Server Status")
        self.status.grid(row = 8, column = 0)
        
        # New Words 
        self.w1 = tk.Label(self.master, text = "Newly added words : ")
        self.w1.place(x = 20, y = 150)
        self.new_words = tk.Label(self.master, text = "N/A")
        self.new_words.place(x = 20, y = 170)
        
        # Duplicate Words 
        self.w2 = tk.Label(self.master, text = "Duplicate words : ")
        self.w2.place(x = 20, y = 200)
        self.duplicate_words = tk.Label(self.master, text = "N/A")
        self.duplicate_words.place(x = 20, y = 220)
        
        # Exit Button
        self.exitButton = tk.Button(self.master, height = 1, width = 8, text = "Exit", command = self.exit_server)
        self.exitButton.place(x = 150, y = 300)
    
    ### -------------------------- Server Disconnect --------------------------- ###
    def exit_server(self):
        print("Exit button pressed")
        close_server_window()
        
    ### -------------------------- Server Thread --------------------------- ###
    # For not freezing GUI
    # One server thread - three client thread
    
    def start_thread(self):
        # Create server thread
        thread = threading.Thread(target = self.server_thread)
        thread.start() 
        
    def server_thread(self): 
        # Setup server connection
        serverSocket = socket.socket()
        pollingSocket = socket.socket()
        
        try:
            # Bind to the port
            serverSocket.bind(('', BACKUP_SERVER_PORT)) 
            pollingSocket.bind(('', BACKUP_POLLING_PORT)) 
            # Listen for client connection 
            serverSocket.listen(5)
            pollingSocket.listen(5)
            
            # Fork a thread to handle polling request
            thread = threading.Thread(target = self.polling_thread)
            thread.start()

            while True:
                try:
                    print("server_thread : bind successful")
                    # server waits on accept() for incoming requests, new socket created on return
                    connectionSocket, addr1 = serverSocket.accept()
                    pollReqSocket, addr2 = pollingSocket.accept()
                    
                    print(addr1)
                    print(addr2)
                    
                    # Save connection & polling socket into list
                    self.socketList.append(create_socket(connectionSocket, pollReqSocket))
                    # Start client thread
                    thread = threading.Thread(target=self.client_thread, args=(connectionSocket,))
                    thread.start()
                
                except ConnectionResetError as e:
                    self.serverStatus.configure(text = "ConnectionResetError")
                    print("server_thread : ConnectionResetError : ", e)
                    continue
                except socket.error as e:
                    self.serverStatus.configure(text = "Server accept() error")
                    print("server_thread : socket.error : ", e)
                    continue
                    
                except socket.timeout as e:
                    self.serverStatus.configure(text = "Server connection timeout")
                    print("server_thread : socket.timeout : ", e)
                    break
                    
                except Exception as e:
                    self.serverStatus.configure(text = "Server exception")
                    print("server_thread : Exception : ", e)
                    break

        except Exception as e:
            self.serverStatus.configure(text = "Server disconnected")
            print("server_thread : Server disconnected : ", e)
    
    ## -------------------------- Send and Receive data --------------------------- ###
    # Dictionary(key, value)
    # Input - data, key & socket
    # Key - message, file & polling request
    def send_data_to(self, data, key, conn_socket):
        # Send data in a dictionary
        # Value - data(username, message, file)
        data_dict = {}
        data_dict[key] = data
        send_msg = FAILED
        
        # https://pythonprogramming.net/pickle-objects-sockets-tutorial-python-3/
        send_data = pickle.dumps(data_dict)
        send_data = bytes(f"{len(send_data):<{10}}", 'utf-8')+send_data

        try:
            conn_socket.send(send_data)
            send_msg = SUCCESSFUL
            print("send_data_to, data : ", send_data)
        except ConnectionResetError as e:
            print("send_data_to : ConnectionResetError")
            send_msg = CLIENT_DISCONNECT
            print(e)
        except Exception as e:
            print("send_data_to : ", FAILED)
            send_msg = FAILED
            print("send_data_to : Exception : ", e)
            
        return send_msg
    
    # Receive data from client
    # Dictionary(key, value)
    # Key - username, message, file & polling response
    def recv_data_from(self, conn_socket):
        recv_data = {}
        try:
            # Pickle - for sending-receiving dictionary from/to client
            # https://pythonprogramming.net/pickle-objects-sockets-tutorial-python-3/
            data = conn_socket.recv(4096)
            full_msg = b'' + data
            recv_data = pickle.loads(full_msg[10:])
            print("recv_data_from : ", SUCCESSFUL)
        except Exception as e:
            msg = str(e)
            if(msg == SERVER_CRASH):
                recv_data[KEY_FAIL] = SERVER_CRASH
            else:
                 recv_data[KEY_MESSAGE] = FAILED
            print("recv_data_from : ", FAILED)
            print("recv_data_from : Exception :", e)
        
        return recv_data
    
    # Send data & consequent actions
    # Server sends 3 types of data to client - ACK Message, File & Polling request
    def handle_send_data_to_client(self, data, key, conn_socket):
        send_msg = FAILED
        # 1. Username response & Polling request
        if(key == KEY_USERNAME or key == KEY_POLL):
            send_msg = self.send_data_to(data, key, conn_socket)
        # 2. File
        elif(key == KEY_FILE):
            # Open file, read from it and send to server
            # https://gist.github.com/giefko/2fa22e01ff98e72a5be2
            filename = data
            file = open(filename,'rb')
            txt = file.read(1024)
            while (txt):
                # Send data 
                send_msg = self.send_data_to(txt, key, conn_socket)
                # Read from file
                txt = file.read(1024)
            # Close file
            file.close()
        
        print("handle_send_data_to_client : ", data, key, send_msg)
        return send_msg
        
    # Receive data & consequent actions
    # Server receives  3 types of data from client
    # Username, File & lexicon words list from polling
    def handle_recv_data_from_client(self, conn_socket):
        send_msg = FAILED # Sending status to client
        ack_msg = FAILED # The message sent to client
        
        # Receive data from client
        recv_data = self.recv_data_from(conn_socket)
        
        # 1. Username
        if (KEY_USERNAME in recv_data):
            # Check duplicte user
            username = recv_data[KEY_USERNAME]
            if(is_duplicate_client(username)):
                ack_msg = DUPLICATE
            else:
                ack_msg = SUCCESSFUL 
            # Send ack_msg = duplicate/successful to client
            send_msg = self.handle_send_data_to_client(ack_msg, KEY_USERNAME, conn_socket)
            
        # 2. File
        elif (KEY_FILE in recv_data):
            #------------- 1. Receive File ------------- #
            # Create file with username
            username = current_client(threading.current_thread().ident)
            recv_file = client_file(username, SERVER)
            
            # Data to write in file
            data = recv_data[KEY_FILE].decode("utf-8")
            file = open(recv_file, "w")
            file.write(data)
            file.close()
            
            # https://stackoverflow.com/questions/2507808/how-to-check-whether-a-file-is-empty-or-not
            # If file not empty, file received successfully
            if(os.path.exists(recv_file)):
                ack_msg = SUCCESSFUL
            else:
                ack_msg = FAILED
            
            print("handle_recv_data_from_client : File received & saved : ", ack_msg)
            #------------- 2. Send File ------------- #
            # If receive successful
            if(ack_msg == SUCCESSFUL):
                # Process file
                ret_file = process_client_file(username)
                # Return to client
                send_msg = self.handle_send_data_to_client(ret_file, KEY_FILE, conn_socket)
                
            print("handle_recv_data_from_client : File returned : ", send_msg)
                  
        # 3. Polling        
        elif (KEY_POLL in recv_data):
            print("handle_recv_data_from_client : Polling")
            ack_msg = SUCCESSFUL        
            # Send ack_msg = success/fail to client
            send_msg = self.handle_send_data_to_client(ack_msg, KEY_POLL, conn_socket)
            
        # 4. Message
        elif(KEY_MESSAGE in recv_data):
            ack_msg = SUCCESSFUL 
            send_msg = SUCCESSFUL
            
        print("handle_recv_data_from_client : ", recv_data, send_msg, ack_msg)
        return recv_data, send_msg, ack_msg
    
    ### -------------------------- Client Thread --------------------------- ###
    # For each client
    def client_thread(self, conn_socket):
        
        global client_dict             
        # Always listen for client message
        while True:
            try:
                # Receive and Send data to client
                recv_data, send_msg, ack_msg = self.handle_recv_data_from_client(conn_socket)
                print("client_thread, recv_data :", recv_data, send_msg, ack_msg)
                # Successful
                if(send_msg == SUCCESSFUL and ack_msg == SUCCESSFUL):
                    # 1 - Username
                    if(KEY_USERNAME in recv_data):
                        print("client_thread: Username : ", send_msg, ack_msg)
                        # Register client to server
                        username = recv_data[KEY_USERNAME]
                        thread_id = threading.current_thread().ident
                        add_client(username, thread_id)
                        # Connect client
                        client_dict[username].conn = CLIENT_CONNECT
                        # Update client status
                        self.update_client_status(username)
                        
                    # 2 - File
                    elif(KEY_FILE in recv_data):
                        print("client_thread: File operation : ", send_msg, ack_msg)
                        # Update user info in server
                        username = current_client(threading.current_thread().ident)
                        client_dict[username].file = "Processed & Returned"
                        # Update client status
                        self.update_client_status(username)
                    
                    # 3 - Polling
                    elif(KEY_POLL in recv_data):
                        print("client_thread: Polling operation : ", send_msg, ack_msg)
                        # Process words & return duplicate words
                        new_words = recv_data[KEY_POLL]
                        # If received list is not empty
                        if(len(new_words) != 0):
                            duplicate_words = process_new_words(new_words)
                            username = current_client(threading.current_thread().ident)
                            # Update GUI
                            self.status.configure(text = username + " : new words")
                            self.new_words.configure(text = new_words)
                            self.duplicate_words.configure(text = duplicate_words)
                    # 4. Message
                    elif(KEY_MESSAGE in recv_data):
                        msg = recv_data[KEY_MESSAGE]
                        print("client_thread : Message : ", msg)
                        if(msg == BACKUP_SERVER):
                            self.serverStatus.configure(text = "Server Status : " + ACTIVE)
                            self.status.configure(text = "Backup server connected")
                else:
                    print("client_thread : Error : ", send_msg, ack_msg)
                    if(send_msg == FAILED and ack_msg == FAILED):
                        print("client_thread : Disconnect client")
                        self.disconnect_client(conn_socket)
                        break
            except Exception as e:
                print("client_thread : Server exception", e)
                self.disconnect_client(conn_socket)
                break
    
    # Disconnect client
    def disconnect_client(self, conn_socket):
        # Close conenction socket
        # Polling socket & connection socket
        del_socket = ''
        for s in self.socketList:
            if(s.conn_socket == conn_socket):
                del_socket = s
                break
        if(del_socket != ''):
            print("Socket close")
            del_socket.conn_socket.close()
            del_socket.poll_socket.close()
            self.socketList.remove(del_socket)
        
        global client_dict
        username = current_client(threading.current_thread().ident)
        print("disconnect_client : ", username)
        if(username != ""):
            client_dict[username].conn = CLIENT_DISCONNECT
            # Update client status
            self.update_client_status(username)
    
    ### -------------------------- Polling --------------------------- ###
    # https://stackoverflow.com/questions/2398661/schedule-a-repeating-event-in-python-3
    def polling_thread(self):
        print("polling_thread")
        while True:
            time.sleep(WAIT_TIME)
            print("schedule_polling : ", time.ctime())
            self.send_polling_req()
    
    def send_polling_req(self):
        # Send polling request to every connected client
        print("send_polling_req : No of clients :", len(self.socketList))
        print(self.socketList)
        for s in self.socketList:
            print("send_polling_req")
            print(s.poll_socket)
            self.handle_send_data_to_client(REQ_POLL, KEY_POLL, s.poll_socket)
            
    ### -------------------------- Primary Server Thread --------------------------- ###
    def start_primary_server_thread(self):
        # Create server thread
        thread = threading.Thread(target = self.open_primary_server_connection)
        thread.start() 
        
    def open_primary_server_connection(self):
        # Setup server connection
        primarySocket = socket.socket()
        
        try:
            # Bind to the port
            primarySocket.bind((SERVER_ADDR, BACKUP_SERVER_PORT)) 
            # Listen for client connection 
            primarySocket.listen(5)
            
            try:
                print("open_primary_server_connection : bind successful")
                # server waits on accept() for incoming requests, new socket created on return
                primarySocket, addr = primarySocket.accept()
                print(addr)
                
                # Fork a thread to handle receive & send data
                thread = threading.Thread(target=self.primary_server_thread, args=(primarySocket,))
                thread.start()
                    
            except ConnectionResetError as e:
                self.serverStatus.configure(text = "ConnectionResetError")
                print("open_primary_server_connection : ConnectionResetError : ", e)

            except socket.error as e:
                self.serverStatus.configure(text = "Server accept() error")
                print("open_primary_server_connection : socket.error : ", e)

            except socket.timeout as e:
                self.serverStatus.configure(text = "Server connection timeout")
                print("open_primary_server_connection : socket.timeout : ", e)

            except Exception as e:
                self.serverStatus.configure(text = "Server exception")
                print("open_primary_server_connection : Exception : ", e)

        except Exception as e:
            self.serverStatus.configure(text = "Server disconnected")
            print("open_primary_server_connection : Server disconnected : ", e)
    
    def primary_server_thread(self, primary_socket):
        recv_msg = FAILED
        send_msg = FAILED
        
        while True:
            # Receive data from primary
            recv_data = self.recv_data_from(primary_socket)
            
            # 1 - Lexicon words
            if(BACKUP_LEXICON_WORDS in recv_data):
                recv_file = FILE_PATH + "lexicon_file.txt"
                # Data to write in file
                data = recv_data[BACKUP_LEXICON_WORDS].decode("utf-8")
                file = open(recv_file, "w")
                file.write(data)
                file.close()
                recv_msg = SUCCESSFUL
                self.status.configure(text = "Lexicon words received")
                
            # 2 - Server crash
            elif(KEY_FAIL in recv_data):
                crash_msg = recv_data[KEY_FAIL]
                self.status.configure(text = "Primary server crashed")
                # Take primary server's role
                self.start_thread()
                break 
                    
            send_msg = self.send_data_to(recv_msg, KEY_MESSAGE, primary_socket)
            print("primary_server_thread : ", recv_msg, send_msg)
            if(recv_msg == FAILED or send_msg == FAILED):
                break
                
    ### -------------------------- GUI update --------------------------- ###
    # Update client status in server GUI
    # Parameter - username 
    def update_client_status(self, username):
        
        global client_dict
        # Update current client status, connected/disconnected/words received
        msg = client_dict[username].conn
        self.status.configure(text = username + " : " + msg)
        print("update_client_status : name & conn : ", username, msg)
        
        # Print client_dict
        client_information()
        
        # Delete client information
        if(msg == CLIENT_DISCONNECT):
            delete_client(username)
            
        # Loop through labels to update each client information in server
        for i in range(0, 3):
            print("i : client_dict len : ", i , len(client_dict))
            if(i < len(client_dict)):
                value = list(client_dict.values())[i]
                print("i : value : ", i, value.name, value.conn)
                # If client is connected
                if(value.conn == CLIENT_CONNECT):
                    self.clientLabels[i].configure(text = value.name) # Client name
                    self.connLabels[i].configure(text = value.conn) # Connection status
                    self.fileLabels[i].configure(text = value.file) # File Status
            else:
                print("i : No client", i)
                self.clientLabels[i].configure(text = "N/A") 
                self.connLabels[i].configure(text = "N/A")
                self.fileLabels[i].configure(text = "N/A")


# In[ ]:


# https://stackoverflow.com/questions/543309/programmatically-stop-execution-of-python-script
def close_server_window():
    print("Window closed")
    # Delete all client files
    delete_all_client_files()
    
    # Clear client dict
    global client_dict
    client_dict.clear()
    
    # Close window
    global root
    root.destroy()

    # Terminate program
    os._exit(0)


# In[ ]:


def main():
    
    # Initialize server global variables(client_dict & lexicon file)
    initialize()
    
    # Initialize GUI root
    global root
    root = tk.Tk()
    
    # Call server class, start the program
    app = server(root)
    root.mainloop()
    
if __name__ == '__main__':
    main()


# In[ ]:





# In[ ]:





# In[ ]:




