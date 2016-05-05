#   Username = admin
#   Pass = admin
#   you can change it from login-page class.
from socket import *
import thread
import threading
import time
import MySQLdb
from threading import Thread
from Tkinter import *
import Tkinter as tk
import tkMessageBox
import Queue

BUFF = 1024
# HOST and PORT adresses of server.
HOST = '192.168.0.104'
PORT = 5555
#arraylist to hold connected clients.
list_client = []
#arraylist to hold (un-handled) reply of clients.
reply_buff = []
#globals for database connection.
db=""
cursor=""
TITLE_FONT = ("Helvetica", 18, "bold")

# Main class to initialise all views of application.
class SampleApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (LoginPage, StartPage, PageOne, PageTwo, PageThree,BedroomPage,GaragePage):
            page_name = F.__name__
            frame = F(container, self)
            self.minsize(width=400, height=400)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")
        #self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


# Login Page GUI and operations.
class LoginPage(tk.Frame):

    def __init__(self, parent, controller):

        def validate():

            if(userent.get()=="admin" and passent.get()=="admin"):
                status.config(text="Success Login")
                print "Success login."
                controller.show_frame("StartPage")
            else:
                status.config(text="Invalid username-password combination.")
                print "Fail login"

        tk.Frame.__init__(self, parent)
        self.controller = controller
        LOGIN_FONT = ("Helvetica", 12)
        BUTTON_FONT = ("Helvetica", 14)
        labelframe = LabelFrame(self)
        labelframe.pack(fill="both")
        status = Label(self, text="Getting Started...", bd=2, relief=SUNKEN, anchor=W)
        status.pack(side=BOTTOM, fill=X)

        left = Label(labelframe, text="Automation & Monitoring System", height=3, font=TITLE_FONT)
        left.pack()

        botframe = Frame(self)
        botframe.pack()

        usertag = Label(botframe, text="Username:",padx=15, font=LOGIN_FONT )
        passtag = Label(botframe, text="Password:",padx=15, font=LOGIN_FONT)
        userent = Entry(botframe, bd =5)
        passent = Entry(botframe, bd =5,show="*")

        usertag.grid(row=1, column=0, pady=25)
        userent.grid(row=1, column=1, pady=25)
        passtag.grid(row=2, column=0, pady=5)
        passent.grid(row=2, column=1, pady=5)

        button = Button(botframe, text="Submit", font=BUTTON_FONT, padx=12, bd=5, command=validate)
        button.grid(row=3, column=0, columnspan=2, pady=15)

# Main Home page GUI and operations.
# TO make this application non-blocking, we wait for the sent command's reply in different thread. 
# Any tKinter object's on-call method should consume as minimum time as possible.
class StartPage(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        labelframe = LabelFrame(self)
        labelframe.pack(fill="both")
        BUTTON_FONT = ("Helvetica", 14)
        left = Label(labelframe, text="Under control of AMS", height=3, font=TITLE_FONT)
        left.pack()

        topframe = Frame(self)
        topframe.pack()
        status = Label(self, text="Getting Started...", bd=2, relief=SUNKEN, anchor=W)
        status.pack(side=BOTTOM, fill=X)
        button1 = Button(topframe, text="Go to Hall", padx=20, bd=5, font=BUTTON_FONT, command=lambda: controller.show_frame("PageOne"))
        button2 = Button(topframe, text="Go to Kitchen", padx=7, bd=5, font=BUTTON_FONT, command=lambda: controller.show_frame("PageTwo"))
        button3 = Button(topframe, text="Garage", padx=29, bd=5, font=BUTTON_FONT, command=lambda: controller.show_frame("GaragePage"))
        button4 = Button(topframe, text="Bedroom", padx=24, bd=5, font=BUTTON_FONT, command=lambda: controller.show_frame("BedroomPage"))
        button5 = Button(topframe, text="Manual Command", padx=25, bd=5, font=BUTTON_FONT, command=lambda: controller.show_frame("PageThree"))

        button1.grid(row=0, column=0, padx=20, pady=20)
        button2.grid(row=0, column=1, padx=20, pady=20)
        button3.grid(row=1, column=0, padx=20, pady=20)
        button4.grid(row=1, column=1, padx=20, pady=20)
        button5.grid(row=2, column=0, padx=20, pady=20, columnspan=2)

# Hall GUI and operations.
# Hall light 1 = connected on board "12345", pin 13
# Hall check light = conneted on board "12345" pin 7
class PageOne(tk.Frame):
    def __init__(self, parent, controller):
        var1 = IntVar()
        var2 = IntVar()
        def light(event):
            print event.widget.message
            print var1.get()
            try:
                if(var1.get()==0):
                    cmd = "gpdw00130001"
                    client_s=""
                    for i in list_client:
                        if(i[1]=="12345"):
                            client_s=i[0]
                            break
                    client_s.send(cmd)
                    status.config(text="Sent1")
                    thread.start_new_thread(sync_reply,(cmd,))
                    print "sent1"
                else:
                    cmd= "gpdw00130000"
                    client_s=""
                    for i in list_client:
                        if(i[1]=="12345"):
                            client_s=i[0]
                            break
                    client_s.send(cmd)
                    status.config(text="Sent2")
                    thread.start_new_thread(sync_reply,(cmd,))
                    print "sent2"

            except:
                status.config(text="Board Unavailable.")
                print "Board unavailable"

        def check_status():
            try:
                cmd="gpdr0007"
                client_s=""
                for i in list_client:
                    if(i[1]=="12345"):
                        client_s=i[0]
                        break
                client_s.send(cmd)
                status.config(text="Sent")
                thread.start_new_thread(sync_reply,(cmd,))
                print "sent3"
            except:
                status.config(text="Board Unavailable.")
                print "Board unavailable1"

        def sync_reply(cmd):
            # wait for max. 5 seconds for board to reply
            st=time.time()
            et=st+5
            reply="-1"
            while(time.time()<et and reply=="-1" ):
                #find cmd from reply_list
                # print reply_buff
                time.sleep(0.02)
                for i in reply_buff:
                    split=i[0].split(',')
                    if(split[0]==cmd):
                        print "reply found"
                        reply=split[1]
                        print split[1]
                        reply_buff.remove(i)
                        break
                if(reply!="-1"):
                    status.config(text=reply)
                    if(cmd=="gpdr0007"):
                        if(reply[5:6]=="1"):
                            b_light2.select()
                        else:
                            b_light2.deselect()
                    break
                else:
                    status.config(text="Waiting for reply...")
            if(reply=="-1"):
                status.config(text="Board unavailable")

        tk.Frame.__init__(self, parent)
        self.controller = controller
        LOGIN_FONT = ("Helvetica", 12)
        BUTTON_FONT = ("Helvetica", 14)
        small_font = ("Helvetica", 9)
        labelframe = LabelFrame(self)
        labelframe.pack(fill="both")
        left = Label(labelframe, text="This is Hall", height=3, font=TITLE_FONT)
        left.pack()
        botframe = Frame(self)
        status = Label(self, text="Getting Started...", bd=2, relief=SUNKEN, anchor=W)
        status.pack(side=BOTTOM, fill=X)
        b_light1 = tk.Checkbutton(self, text="Hall light1", font=BUTTON_FONT, pady=10, variable=var1, onvalue=1, offvalue=0 )
        b_light_check = tk.Button(botframe,text="Check Status", bd=3, font=small_font, command=check_status)
        b_light2 = tk.Checkbutton(botframe, text="", font=BUTTON_FONT, pady=10, variable=var2, state=DISABLED )
        b_light1.bind('<Button-1>', light)
        #b_light2.bind('<Button-1>', check_status)
        b_light1.message="hl1"
        b_light2.message="hl2"
        button = tk.Button(self, text="Go to the start page", padx=25, bd=5, font=BUTTON_FONT,command=lambda: controller.show_frame("StartPage"))
        b_light1.pack()
        botframe.pack()
        b_light2.grid(row=0,column=0)
        b_light_check.grid(row=0,column=1)
        button.pack(pady = 25)

# KItchen GUI and operations.
# Kitchen temperature sensor = connected on board "12345", analog pin 2
class PageTwo(tk.Frame):

    def __init__(self, parent, controller):

        def Tempreture(event):
            try:
                cmd="gpar0002"
                client_s=""
                for i in list_client:
                    if(i[1]=="12345"):
                        client_s=i[0]
                        break
                client_s.send(cmd)
                status.config(text="Sent")
                thread.start_new_thread(sync_reply,(cmd,))
                print "sent"
            except:
                status.config(text="Board Unavailable.")
                print "board err"
            # listen reply to command in different thread, so applicaton wont block
        def sync_reply(cmd):
            st=time.time()
            et=st+5
            reply="-1"
            while(time.time()<et and reply=="-1" ):
                #find cmd from reply_list
                # print reply_buff
                time.sleep(0.02)
                for i in reply_buff:
                    split=i[0].split(',')
                    if(split[0]==cmd):
                        print "reply found"
                        reply=split[1]
                        print split[1]
                        reply_buff.remove(i)
                        break
                if(reply!="-1"):
                    status.config(text=reply)
                    k_label.config(text="Temperature of kitchen:"+reply[2:])
                    break
                else:
                    status.config(text="Waiting for reply...")
            if(reply=="-1"):
                status.config(text="Board unavailable")
            #k_label.config(text=k_label.cget("text")+"1")

        tk.Frame.__init__(self, parent)
        self.controller = controller
        LOGIN_FONT = ("Helvetica", 12)
        BUTTON_FONT = ("Helvetica", 14)
        small_font = ("Helvetica", 9)
        labelframe = LabelFrame(self)
        labelframe.pack(fill="both")
        left = Label(labelframe, text="This is Kitchen", height=3, font=TITLE_FONT)
        left.pack()
        topframe = Frame(self)
        topframe.pack()
        status = Label(self, text="Getting Started...", bd=2, relief=SUNKEN, anchor=W)
        status.pack(side=BOTTOM, fill=X)
        k_label = tk.Label(topframe, text="Temperature of kitchen:", font=LOGIN_FONT, justify=LEFT)
        k_refresh = tk.Button(topframe, text="Refresh temp.", bd=3, font=small_font)
        k_refresh.bind('<Button-1>', Tempreture)
        k_button = tk.Button(topframe, text="Go to the start page", padx=25, bd=5, font=BUTTON_FONT, command=lambda: controller.show_frame("StartPage"))
        k_label.grid(row=0, column=0, padx=20, pady=20)
        k_refresh.grid(row=0, column=1, padx=25, pady=20)
        k_button.grid(row=1,column=0, columnspan=2, pady=25)

# Manual command GUI and operations.
# Refresh, Select one of the connected boarad, type command in format, Send the command.
class PageThree(tk.Frame):

    def __init__(self, parent, controller):

        def Command(event):
            if(not board_string.get()):
                status.config(text="Board Unavailable.")
            elif(len(k_text.get())==0):
                status.config(text="Please enter command.")
            else:
                for i in list_client:
                    print i
                    if(i[1]==board_string.get()):
                        try:
                            print i[0].send(k_text.get())
                            status.config(text="Command Sent.")
                            thread.start_new_thread(sync_reply,(k_text.get(),))
                            print "sent"
                        except:
                            status.config(text="Board Unavailable.")
                            print "Send err: No board found"
                k_text.delete(0,len(k_text.get()))

        def refresh():
            # Reset var and delete all old options
            board_string.set('')
            board_select['menu'].delete(0, 'end')
            status.config(text="Board list refreshed.")
            for choice in (row[1] for row in list_client):
                board_select['menu'].add_command(label=choice, command=tk._setit(board_string, choice))

        def sync_reply(cmd):
            st=time.time()
            et=st+5
            reply="-1"
            while(time.time()<et and reply=="-1" ):
                #find cmd from reply_list
                # print reply_buff
                time.sleep(0.02)
                for i in reply_buff:
                    split=i[0].split(',')
                    if(split[0]==cmd):
                        print "reply found"
                        reply=split[1]
                        print split[1]
                        reply_buff.remove(i)
                        break
                if(reply!="-1"):
                    status.config(text=reply)
                    break
                else:
                    status.config(text="Waiting for reply...")
            if(reply=="-1"):
                status.config(text="Board unavailable")

        tk.Frame.__init__(self, parent)
        self.controller = controller
        labelframe = LabelFrame(self)
        labelframe.pack(fill="both")
        left = Label(labelframe, text="Enter Command", height=3, font=TITLE_FONT)
        left.pack()
        topframe = Frame (self)
        topframe.pack()
        status = Label(self, text="Getting Started...", bd=2, relief=SUNKEN, anchor=W)
        status.pack(side=BOTTOM, fill=X)
        LOGIN_FONT = ("Helvetica", 12)
        BUTTON_FONT = ("Helvetica", 14)
        boardlabel = Label(topframe, text="Select Board:", font=BUTTON_FONT)
        commandlabel = Label(topframe, text="Command:", font=BUTTON_FONT)
        boards = (" ")
        board_string = StringVar(topframe)
        board_select = OptionMenu(topframe, board_string, *boards)
        refresh = Button(topframe, text='Refresh', command=refresh, font=BUTTON_FONT, padx=12, bd=5)

        k_text = Entry(topframe, bd=5)
        k_text.bind("<Return>", Command)
        k_send = Button(topframe, text="Send", font=BUTTON_FONT, padx=24, bd=5)
        k_send.bind('<Button-1>', Command)
        button = Button(topframe, text="Go to the start page", command=lambda: controller.show_frame("StartPage"), font=BUTTON_FONT, padx=25, bd=5)

        boardlabel.grid(row=0, column=0, padx=10, pady=20)
        board_select.grid(row=0,column=1, padx=10, pady=20)
        refresh.grid(row=0,column=2, padx=10, pady=20)
        commandlabel.grid(row=1, column=0, padx=5, pady=20)
        k_text.grid(row=1,column=1, padx=10, pady=20)
        k_send.grid(row=1,column=2, padx=10, pady=20)
        button.grid(row=2, columnspan=3)

# Bedroom GUI and operations.
# currently these buttons are not working. Handlers are same as Hall light 1.
class BedroomPage(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        labelframe = LabelFrame(self)
        labelframe.pack(fill="both")
        LOGIN_FONT = ("Helvetica", 12)
        BUTTON_FONT = ("Helvetica", 14)
        small_font = ("Helvetica", 9)
        left = Label(labelframe, text="This is Bedroom", height=3, font=TITLE_FONT)
        left.pack()

        topframe = Frame(self)
        topframe.pack()
        status = Label(self, text="Getting Started...", bd=2, relief=SUNKEN, anchor=W)
        status.pack(side=BOTTOM, fill=X)

        Lights = Checkbutton(topframe, text="Lights", font=BUTTON_FONT)
        AC = Checkbutton(topframe, text="A.C.   ", font=BUTTON_FONT)
        button = Button(topframe, text="Go to the start page", command=lambda: controller.show_frame("StartPage"), font=BUTTON_FONT, padx=25, bd=5)

        Lights.grid(row=0, pady=15)
        AC.grid(row=1, pady=10)
        button.grid(row=2, pady=22)

# Garage GUI and operations.
# Take pic of garage, Board no "67890" (BBB), USB camera.
# Open/Close garage, Board no "12345" (Arduino), pin 9 
class GaragePage(tk.Frame):

    def __init__(self, parent, controller):

        def camera(event):
            try:
                cmd = "tp01"
                client_s=""
                for i in list_client:
                    if(i[1]=="67890"):
                        client_s=i[0]
                        break
                client_s.send(cmd)
                status.config(text="Sent1")
                thread.start_new_thread(sync_reply,(cmd,))
                print "sent1"
            except:
                status.config(text="Board Unavailable.")
                print "Board unavailable"

        def garage(event):
            try:
                cmd = "sm090090"
                client_s=""
                for i in list_client:
                    if(i[1]=="12345"):
                        client_s=i[0]
                        break
                client_s.send(cmd)
                status.config(text="Sent1")
                thread.start_new_thread(sync_reply,(cmd,))
                print "sent1"
            except:
                status.config(text="Board Unavailable.")
                print "Board unavailable"


        def sync_reply(cmd):
            st=time.time()
            et=st+7
            reply="-1"
            while(time.time()<et and reply=="-1" ):
                #find cmd from reply_list
                # print reply_buff
                time.sleep(0.02)
                for i in reply_buff:
                    split=i[0].split(',')
                    if(split[0]==cmd):
                        print "reply found"
                        reply=split[1]
                        print split[1]
                        reply_buff.remove(i)
                        break
                if(reply!="-1"):
                    status.config(text=reply)
                    break
                else:
                    status.config(text="Waiting for reply...")
            if(reply=="-1"):
                status.config(text="Board unavailable")

        tk.Frame.__init__(self, parent)
        self.controller = controller
        labelframe = LabelFrame(self)
        labelframe.pack(fill="both")
        LOGIN_FONT = ("Helvetica", 12)
        BUTTON_FONT = ("Helvetica", 14)
        small_font = ("Helvetica", 9)
        left = Label(labelframe, text="This is Garage", height=3, font=TITLE_FONT)
        left.pack()

        topframe = Frame(self)
        topframe.pack()
        status = Label(self, text="Getting Started...", bd=2, relief=SUNKEN, anchor=W)
        status.pack(side=BOTTOM, fill=X)
        Take_Photo = Button(topframe, text="Take Photo of Garage", font=BUTTON_FONT, bd=5)
        Take_Photo.bind('<Button-1>', camera)
        Garage_Door = Button(topframe, text="Open Garage Door", font=BUTTON_FONT, padx=15, bd=5)
        Garage_Door.bind('<Button-1>', garage)
        button = Button(topframe, text="Go to the start page", command=lambda: controller.show_frame("StartPage"), font=BUTTON_FONT, padx=25, bd=5)
        Take_Photo.grid(row=0, pady=15)
        Garage_Door.grid(row=1, pady=10)
        button.grid(row=2, pady=22)

# Just a padding finction.
def response(key):
    return 'Server response: ' + key

# Handler function, get client-board identity string. echo it back. then listens for client's  reply forever.
# Make entry to DB for every client reply.
def handler(clientsock,addr):
        data = clientsock.recv(BUFF)
        new_client=1
        for i in list_client:
            if(i[1]==data):
                i[0]=clientsock
                new_client=0
                break;
        if(new_client==1):
            list_client.append([clientsock,data])
        print repr(addr) + ' recv:' + repr(data)
        clientsock.send(response(data))
        print repr(addr) + ' sent:' + repr(response(data))
        while 1:
            try:
                #recev data from client indefinately
                reply = clientsock.recv(BUFF)
                # put reply to reply buff
                if(len(reply)>=4):
                    reply_buff.append([reply,data])
                    reply_break=reply.split(',')
                    print reply
                    #put appropiate reply to reply to queue
                    #q.put(reply)

                    #print reply_break
                    # insert reply to database log
                    try:
                        sql = "INSERT INTO log_command(command, board_no, reply) VALUES ('%s', '%d', '%s' )" % \
                       (reply_break[0], int(data),reply_break[1])
                        cursor.execute(sql)
                        db.commit()
                    except:
                        try:
                            db.rollback()
                        except:
                            print "db err>>"

            except:
                # client is not responding. so remove the client from list
                del_index=0
                for i in list_client:
                    if(i[0]==clientsock):
                        print i[0]
                        del list_client[del_index]
                        break;
                    del_index+=1
                list_print()
                print "client diconnected:",clientsock
                break
        #thread.exit();-
        #time.sleep(2)
        #while 1:
        #    clientsock.send("1a")
        #    res=clientsock.recv(BUFF)
        #    print clientsock,res
        #    time.sleep(2)


# Create TCP socket waiting for clients to connect
def sock_creator():

    sql = "SELECT * FROM board"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for row in results:
            fname = row[0]
            lname = row[1]
            age = row[2]
            print "fname=%d,lname=%d,age=%s" % \
                  (fname, lname, age)
    except:
        print "db err"

    ADDR = (HOST, PORT)
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind(ADDR)
    serversock.listen(5)
    while 1:
        print 'waiting for connection... listening on port', PORT
        clientsock, addr = serversock.accept()
        print '...connected from:', addr
        thread.start_new_thread(handler, (clientsock, addr))

# Print connected client list.
def list_print():
        print "Clients:"
        for i in list_client:
            print i

if __name__=='__main__':

    try:
        # Try to connect to DB
        db = MySQLdb.connect("localhost","root","","btp" )
        cursor = db.cursor()
    except:
        print "cant connect to db"
    # Start listening connection for clients.
    thread.start_new_thread(sock_creator, ())
    # Start GUI.
    app = SampleApp()
    app.mainloop()
    # while 1:
    #     command=raw_input("Enter sir:")
    #     if(command=="ls"):
    #         list_print()
    #     else:
    #         try:
    #             sql = "INSERT INTO log_command(command, board_no) VALUES ('%s', '%d' )" % \
    #            (command[1:], int(list_client[int(command[0])][1]))
    #             cursor.execute(sql)
    #             db.commit()
    #         except:
    #             try:
    #                 db.rollback()
    #             except:
    #                 print "db err"
    #         try:
    #             print list_client[int(command[0])][0].send(command[1:])
    #             print "sent"
    #         except:
    #             print "invalid syntex"
