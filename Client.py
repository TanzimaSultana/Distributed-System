#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Name - Tanzima Sultana
# UTA ID - 1001759430


# In[2]:


import socket
import threading
import os
import tkinter as tk
from tkinter import filedialog
import pickle
from queue import Queue


# In[3]:


# Reserve a port number for connection
SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 12345
POLLING_PORT = 11223
# Backup server port 
BACKUP_SERVER_PORT = 14455
BACKUP_POLLING_PORT = 11112

# File path
FILE_PATH = os.getcwd() + "\Client\\"

# Global variable to keep count of clients
# https://stackoverflow.com/questions/56904280/button-click-counter-in-python
count = 0
root = ''


# In[4]:


# Constants
NORMAL = "normal"
DISABLED = "disabled"
CONNECT = 1
DISCONNECT = 0

CLIENT = "client_"
SUCCESSFUL = "successful"
FAILED = "failed"
DUPLICATE = "duplicate"
CLIENT_DISCONNECT = "disconnect"
CLIENT_CONNECT = "connect"
SERVER_CONNECT = "Server Connected"
SERVER_DISCONNECT = "Server Disconnected"
USERNAME = "username"
MESSAGE = "message"
FILE = "file"
QUEUE = "queue"

# Keys for client messages
KEY_USERNAME = "key_username"
KEY_FILE = "key_file"
KEY_MESSAGE = "key_message"
KEY_FAIL = "key_fail"
KEY_POLL = "key_poll"
REQ_POLL = "req_poll"

PRIMARY_SERVER = "primary_server"
BACKUP_SERVER = "backup_server"
# Server crash message
SERVER_CRASH = "[WinError 10054] An existing connection was forcibly closed by the remote host"


# In[5]:


def initialize():
    # Initialize client count to show
    global count
    count = 0


# In[6]:


def open_client_file(username):
    #Create receive file name with client name
    filename = username + '.txt'
    file = FILE_PATH + filename
    print("open_client_file : ", username, filename)
    return file


# In[7]:


# Class for each new client
class client:
    def __init__(self, window, clientId, _update_client, _update_server, _get_server): 
        #update_client, _update_server, _get_server = Call back function
        
        print("Client")
        self.window = window
        self.clientId = clientId
        self._update_client = _update_client # To update client count
        self._update_server = _update_server # To update client count
        self._get_server = _get_server # To update client count
        
        self.server_type = self._get_server()
        self.clientSocket = ''
        self.pollingSocket = ''
        
        # Flag = whether a client is connected to server or not
        self.connFlag = DISCONNECT
        # Username
        self.username = ''
        # Uploaded file name
        self.upload_file = ''
        
        # Client GUI
        self.create_client_gui(self.clientId)
        
        # Lexicon words queue
        self.lex_queue = ''
        self.init_queue()
    
    ### -------------------------- GUI --------------------------- ###
    def create_client_gui(self, clientId):
        
        # Initiate GUI for client
        self.window.title("Client " + str(clientId))
        self.window.geometry("400x400")
        
        # Enter user name
        self.userNameLabel = tk.Label(self.window, text = "Enter user name")
        self.userNameLabel.place(x = 50, y = 50)

        # Textbox for input username
        self.userNameEntry = tk.Entry(self.window) 
        self.userNameEntry.place(x = 150, y = 50)
        
        # Connect Button
        self.connButton = tk.Button(self.window, height = 1, width = 8, text = "Connect", command = self.connect_to_server)
        self.connButton.place(x = 50, y = 100)
        
        # Connection status (Connected/Duplicate)
        self.connStatus = tk.Label(self.window, text = "Connection Status, Server")
        self.connStatus.place(x = 150, y = 100)
        
        # Browse files Button
        self.browseButton = tk.Button(self.window, height = 1, width = 8, text = "Browse", command = self.browse_file)
        self.browseButton.place(x = 50, y = 150)
        
        # Broswe file name label
        self.browseLabel = tk.Label(self.window, text = "N/A")
        self.browseLabel.place(x = 150, y = 150)
        
        # Upload Button
        self.uploadButton = tk.Button(self.window, height = 1, width = 8, text = "Upload", command = self.upload_download_file)
        self.uploadButton.place(x = 50, y = 200)
        self.enable_disable_upload_btn(DISABLED)
        
        # Upload file status
        self.uploadLabel = tk.Label(self.window, text = "N/A")
        self.uploadLabel.place(x = 150, y = 200)
        
        # Lexicon Words Label
        self.lexLabel = tk.Label(self.window, text = "Enter Lexicon words : ")
        self.lexLabel.place(x = 50, y = 250)
        
        # Textbox for input Lexicon Words
        self.lexEntry = tk.Entry(self.window) 
        self.lexEntry.place(x = 50, y = 270, width = 300)
        
        # Queue Button
        self.queueButton = tk.Button(self.window, height = 1, width = 8, text = "Queue", command = self.queue_lexicon_words)
        self.queueButton.place(x = 50, y = 300)
        
        # Queue 
        self.queueLabel = tk.Label(self.window, text = "") 
        self.queueLabel.place(x = 120, y = 300)
        
        # Exit Button
        self.exitButton = tk.Button(self.window, height = 1, width = 8, text = "Exit", command = self.close_windows)
        self.exitButton.place(x = 150, y = 350)
    
    ### -------------------------- Button Action --------------------------- ###
    
    # Enable/Disable button
    # https://stackoverflow.com/questions/53580507/disable-enable-button-in-tkinter
    def enable_disable_connect_btn(self, state):
        # Disable connect button
        self.connButton["state"] = state
    
    def enable_disable_upload_btn(self, state):
        # Disable upload button
        self.uploadButton["state"] = state
        
    def connect_to_server(self):
        print("Connect button")
        # Client-Server thread
        thread = threading.Thread(target = self.client_thread)
        thread.start() 
    
    # https://www.geeksforgeeks.org/file-explorer-in-python-using-tkinter/
    # Browse file
    def browse_file(self):
        print("Browse file button")
        self.upload_file = filedialog.askopenfilename(initialdir = FILE_PATH,
                                                      title = "Select a File",
                                                      filetypes = (("Text files",
                                                                    "*.txt*"),
                                                                   ("all files",
                                                                    "*.*")))
      
        # Change label contents
        self.browseLabel.configure(text = "File browse done")                                                 
        # Enable upload button
        self.enable_disable_upload_btn(NORMAL)
    
    # File upload and download from server
    def upload_download_file(self):
        print("Upload-download file")
        # Thread for uploading and downloading file
        thread = threading.Thread(target = self.handle_upload_download_file)
        thread.start()
    
    # Add lexicon words to queue
    def queue_lexicon_words(self):
        print("Add button pressed")
        # When lex_entry texbox is not empty
        if(self.lexEntry != ''):
            # Add wrods to queue
            words = self.lexEntry.get()
            self.add_words_to_queue(words)
            # Show queue
            self.print_queue()
            
            # Clear textbox
            self.lexEntry.delete(0, "end")
        
    def close_windows(self):
        print("Client disconnected : ", self.username)
        
        # Update client count in 'add_client' class
        global count
        count = count - 1
        
        # Call back to update_client
        self._update_client(count)
        # Close connection with server
        self.close_server_connection()
        # Delete received file from server
        self.delete_file()
    
        self.window.destroy()
    
    ### ------------------- Send & Recive ---------------------- ###

    def send_to_server(self, data, key):
        # Send data in a dictionary
        # Value - data(username, message, file)
        data_dict = {}
        data_dict[key] = data
        send_msg = ''
        
        # https://pythonprogramming.net/pickle-objects-sockets-tutorial-python-3/
        send_data = pickle.dumps(data_dict)
        send_data = bytes(f"{len(send_data):<{10}}", 'utf-8')+send_data
       
        try:
            self.clientSocket.send(send_data)
            send_msg = SUCCESSFUL
        
        except Exception as e:
            send_msg = FAILED
            print("send_to_server : Exception :", e)
        
        print("send_to_server : ", data, key, send_msg)
        return send_msg
            
    def recv_from_server(self):
        recv_data = {}
        try:
            # Pickle - for sending-receiving dictionary from/to client
            # https://pythonprogramming.net/pickle-objects-sockets-tutorial-python-3/
            data = self.clientSocket.recv(4096)
            full_msg = b'' + data
            recv_data = pickle.loads(full_msg[10:])
            print("recv_from_server : ", SUCCESSFUL)
        
        except Exception as e:
            msg = str(e)
            if(msg == SERVER_CRASH):
                recv_data[KEY_FAIL] = SERVER_CRASH
            else:
                 recv_data[KEY_MESSAGE] = FAILED
            print("recv_from_server : ", FAILED)
            print("recv_from_server : Exception :", e)
        
        print("recv_from_server : ", recv_data)
        return recv_data
    
    # Client receives 4 types of data from server : Username ack, File, polling request, message
    def handle_recv_data_from_server(self):
        recv_data = self.recv_from_server()
        recv_msg = FAILED
        # 1. Username
        if (KEY_USERNAME in recv_data):
            recv_msg = recv_data[KEY_USERNAME]
        # 2. File
        elif (KEY_FILE in recv_data):
            recv_msg = SUCCESSFUL
        # 3. Polling request & response
        elif (KEY_POLL in recv_data):
            recv_msg = recv_data[KEY_POLL]
        # 4. Message
        elif (KEY_MESSAGE in recv_data):
            recv_msg = recv_data[KEY_MESSAGE] 
        # 5. Server fail
        elif (KEY_FAIL in recv_data):
            recv_msg = recv_data[KEY_FAIL] 
            
        print("handle_recv_data_from_server : ",recv_data, recv_msg)
        return recv_data, recv_msg
            
        
    ### ------------------- File upload & download file ---------------------- ###
    def handle_upload_download_file(self):
        upload_msg = FAILED
        
        ### ------------- Upload
        # Open file, read from it and send to server
        # https://gist.github.com/giefko/2fa22e01ff98e72a5be2
        filename = self.upload_file
        file = open(filename,'rb')
        txt = file.read(1024)
        while (txt):
            # Send data 
            upload_msg = self.send_to_server(txt, KEY_FILE)
            # Read from file
            txt = file.read(1024)
        # Close file
        file.close()
        print("handle_upload_download_file : UPLOAD : ", upload_msg)
        
    ### ------------------- Server Connection ---------------------- ###
    
    #### Client-Server connection thread(one for each client)
    def client_thread(self):
        # 1 - Setup connection
        conn_msg = self.open_server_connection()
        print("client_thread : conn_msg : ", conn_msg)
        
        recv_msg = FAILED
        # Connection successful
        if(conn_msg == SUCCESSFUL):
            
            # Fork a thread to handle polling request
            thread = threading.Thread(target = self.polling_thread)
            thread.start() 
            
            while True:
                ### Receive data from server
                # 4 types of data - username, file, poll req & poll response
                recv_data, recv_msg = self.handle_recv_data_from_server()
                print("client_thread : ", recv_data, recv_msg)
                
                # 1 - Username
                if (KEY_USERNAME in recv_data):
                    self.connStatus.configure(text = "Connection : " + recv_msg + "," + self.server_type)
                    if(recv_msg == SUCCESSFUL):
                        # Disable connect button
                        self.enable_disable_connect_btn(DISABLED)
                        # Set connection flag
                        self.connFlag = CONNECT
                        
                # 2 - File
                elif (KEY_FILE in recv_data):
                    self.uploadLabel.configure(text = "Download : " + recv_msg)
                    # If download successful
                    if(recv_msg == SUCCESSFUL):
                        recv_file = open_client_file(self.username)
                        # Data to write in file
                        data = recv_data[KEY_FILE].decode("utf-8")
                        file = open(recv_file, "w")
                        file.write(data)
                        file.close()
                        
                        # If file not empty, file saved successfully
                        if(os.path.exists(recv_file)):
                            self.uploadLabel.configure(text = "Spell check : " + SUCCESSFUL)
                        
                # 3 - Polling response
                elif(KEY_POLL in recv_data and recv_msg == SUCCESSFUL):
                    print("client_thread : polling response : ", recv_msg)
                    if(self.is_queue_empty() == False):
                        print("client_thread : Clear queue")
                        # Clear queue
                        self.clear_queue()
                
                # 4 - Message
                elif(KEY_MESSAGE in recv_data):
                    print("client_thread : ", recv_msg)
                    if(recv_msg == FAILED):
                        print("client_thread : ", CLIENT_DISCONNECT)
                        break
                        
                # 5 - Server crash
                elif(KEY_FAIL in recv_data):
                    print("client_thread : ", recv_msg)
                    if(recv_msg == SERVER_CRASH):
                        print("client_thread : ", SERVER_CRASH)
                        self.connStatus.configure(text = "Primary server crashed")
                        
                        # Connect to backup server
                        self._update_server(BACKUP_SERVER)
                        self.server_type = BACKUP_SERVER
                        # Connect to backup server
                        # Just like initially, start with connection with server
                        # server_type = backup server
                        self.connect_to_server()
                        print("Backup server connection")
                        break
                        
                # 6 - Exception
                else:
                    print("client_thread : exception")
                    break
    
    ## Polling thread
    def polling_thread(self):
        # Only to receive polling request
        recv_msg = FAILED
        send_msg = FAILED
        while True:
            recv_data = {}
            try:
                # Pickle - for sending-receiving dictionary from/to client
                # https://pythonprogramming.net/pickle-objects-sockets-tutorial-python-3/
                data = self.pollingSocket.recv(4096)
                full_msg = b'' + data
                recv_data = pickle.loads(full_msg[10:])
                print('recv_polling_req :', self.pollingSocket)
                print("polling_thread : ", recv_data)
                
                # If polling request
                if(KEY_POLL in recv_data and recv_data[KEY_POLL] == REQ_POLL):
                    recv_msg = SUCCESSFUL
                    # Send queue words to server
                    send_msg = self.send_to_server(self.get_queue(), KEY_POLL) 
                    print("polling_thread : ", recv_msg, send_msg)
                    
            except Exception as e:
                recv_msg = FAILED
                print("polling_thread : ", recv_msg)
                print("polling_thread : Exception :", e)
                break
        
    #### Method for connecting to server    
    def open_server_connection(self):
        # For new connection
        # It can be primary or backup server
        if(self.server_type == PRIMARY_SERVER):
            server_port = SERVER_PORT
            polling_port = POLLING_PORT
        else:
            server_port = BACKUP_SERVER_PORT
            polling_port = BACKUP_POLLING_PORT
            
        conn_msg = FAILED
        # Create cllient socket
        self.clientSocket = socket.socket() 
        self.pollingSocket = socket.socket()
        try:
            # Connect to the server in both server & polling port
            self.clientSocket.connect((SERVER_ADDR, server_port))
            self.pollingSocket.connect((SERVER_ADDR, polling_port))
            
            # Get username from textbox
            self.username = self.userNameEntry.get()       
            # Check if username is empty or not
            if(self.username != ''):
                print("open_server_connection : username : ", self.username)
                # Send username to server
                conn_msg = self.send_to_server(self.username, KEY_USERNAME)
            else:
                conn_msg = "Empty username"
            
        except Exception as e:
            print("open_server_connection: Exception: ", e)
            conn_msg = FAILED
        
        print("open_server_connection : ", self.server_type, conn_msg)
        return conn_msg
    
    #### Method for closing server connection
    def close_server_connection(self):

        # If server connection exists, then close connection
        if(self.connFlag == CONNECT): 
            # Close client socket
            self.clientSocket.close()
            self.pollingSocket.close()
            # Update connFlag
            self.connFlag = DISCONNECT
    
    #### Delete client files after a client disconnects
    def delete_file(self):
        
        file = FILE_PATH + self.username + ".txt"
        if os.path.exists(file):
            print("File removed : ", file)
            os.remove(file)
        else:
            print("The file does not exist")
        
    ### ------------------- QUEUE ---------------------- ###
    # https://www.geeksforgeeks.org/queue-in-python/
    # Initialize
    def init_queue(self):
        # Initializing a queue
        # A maxsize of zero ‘0’ means an infinite queue
        self.lex_queue = Queue(maxsize = 0)
        
    # Push
    def push_queue(self, word):
        print("push_queue : ", word)
        self.lex_queue.put(word)

    # Queue empty
    def is_queue_empty(self):
        return self.lex_queue.empty()
    
    # Get queue
    def get_queue(self):
        return list(self.lex_queue.queue)
    
    # Clear queue
    # https://stackoverflow.com/questions/6517953/clear-all-items-from-the-queue
    def clear_queue(self):
        self.lex_queue.queue.clear()
        self.queueLabel.configure(text = "Polling complete. Queue cleared.")
        
    # Print Queue
    def print_queue(self):
        print("print_queue : ", self.get_queue())
        self.queueLabel.configure(text = self.get_queue())
        
    # Add words to queue
    def add_words_to_queue(self, words):
        print("add_words_to_queue : ", words)
        # Put the words into list
        # https://www.geeksforgeeks.org/python-spilt-a-sentence-into-list-of-words/
        words_list = words.split()
        for w in words_list:
            self.push_queue(w)


# In[8]:


# Multiple windows - 
# https://stackoverflow.com/questions/16115378/tkinter-example-code-for-multiple-windows-why-wont-buttons-load-correctly

# GUI for adding clients
class add_client:
    def __init__(self, master):
        
        self.master = master
        self.master.title("Client")
        self.master.geometry("400x400")
        
        # Server type
        self.server_type = PRIMARY_SERVER
    
        # Text label for message to add new client
        self.msgLabel = tk.Label(self.master, text = "Create new client by clicking on add button")
        self.msgLabel.place(x = 20, y = 50)

        # Add button
        self.addBtn = tk.Button(self.master, height = 1, width = 8, text = "Add", command = self.new_client)
        self.addBtn.place(x = 20, y = 100)
        
         # Text label for showing no of clients
        self.clientLabel = tk.Label(self.master, text = "Client : ")
        self.clientLabel.place(x = 120, y = 100)
        
        self.countLabel = tk.Label(self.master, text = str(0))
        self.countLabel.place(x = 200, y = 100)
        
        # Show a warning message
        self.warningLabel = tk.Label(self.master, text = "")
        self.warningLabel.place(x = 20, y = 150)
        
        # Exit Button
        self.exitButton = tk.Button(self.master, height = 1, width = 8, text = "Exit", command = self.close_windows)
        self.exitButton.place(x = 100, y = 200)
    
    # Update server type
    def update_server(self, server_type):
        print("update_server : ", server_type)
        self.server_type = server_type
    
    def get_server(self):
        print("get_server : ",  self.server_type)
        return self.server_type
        
    # Update client count after each connection and disconnection
    def update_client(self, c):
        
        self.countLabel.configure(text = str(c))
        
        # Enable add button
        if(c <= 3):
            self.enable_disable_add_btn(NORMAL)
            # Hide warning message
            self.warningLabel.configure(text = "")
    
    # Enable/Disable add button
    def enable_disable_add_btn(self, state):
        # Disable add button
        # https://stackoverflow.com/questions/53580507/disable-enable-button-in-tkinter
        self.addBtn["state"] = state
            
    # For new client
    def new_client(self):
        
        global count
        
        count += 1
        
        # No of clients does not exceed 3
        if(count <= 3):
            
            # Update client count
            self.update_client(count)
            
            # Launch new window for new client
            self.newWindow = tk.Toplevel(self.master)
            # Add close event
            self.newWindow.protocol("WM_DELETE_WINDOW", self.client_window_close)
            
            self.app = client(self.newWindow, count, self.update_client, self.update_server, self.get_server)
            
        else:
            count = 3
            
            # Show warning message
            self.warningLabel.configure(text = "Can not add more than 3 clients.")
            # Disable add button
            self.enable_disable_add_btn(DISABLED)     
            
    # Close client window & close server connection     
    def client_window_close(self):
        print("Client closed")
        # Call close_windows method in client class
        self.app.close_windows()
        self.newWindow.destroy()
        
    # Exit button
    def close_windows(self):
        root_window_close()


# In[9]:


def root_window_close():
    print("Root closed")
    global root
    root.destroy()
    
    # Terminate program
    os._exit(0)


# In[ ]:


def main():
    
    # Initiate root GUI obj
    global root
    root = tk.Tk()
    app = add_client(root)
    root.protocol("WM_DELETE_WINDOW", root_window_close)
    root.mainloop()
    
if __name__ == '__main__':
    main()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




