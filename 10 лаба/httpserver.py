import asyncore
import asynchat
import socket
import select
import logging
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] (%(processName)-10s) (%(threadName)-10s) %(message)s'
)

class AsyncHTTPRequestHandler(asynchat.async_chat):
    """ Обработчик клиентских запросов """

    def __init__(self, sock):
        super().__init__(sock)

class AsyncHTTPServer(asyncore.dispatcher):

    def __init__(self, host="127.0.0.1", port=9000):
        super().__init__()

        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):

        logging.debug("Incoming connection from {addr}")
        AsyncHTTPRequestHandler(sock)


class AsyncHTTPRequestHandler(asynchat.async_chat):

    def __init__(self, sock):
        super().__init__(sock)
        
        self.set_terminator(b"\r\n\r\n")

    def collect_incoming_data(self, data):
        logging.debug("Incoming data: {data}")

        self._collect_incoming_data(data)
        self.received_data = data
        

    def found_terminator(self):
      
        self.parse_request()

    def parse_request(self):
        self.parse_headers()
        
        


    def parse_headers(self):
        try:
            data = str(self.received_data)
            print(self.received_data)
            data = data[2:len(data)]
            data = data.replace("'","")
            f = data.split(" ")
            c = 0
            for i in f:
                s = i.find("\\r\\n",0)
                if s != -1:
                    f[c] = i[0:s]
                c += 1
                if (c == 4):
                    break
             
            self.method = f[0]
            self.url = str(f[1])
            self.protocol = f[2]
            self.host = f[3]
            s = data.find("User-Agent: ",0)
            d = data.find("\\r\\n",s)
            self.user_agent = data[s+12:d]
            s = data.find("Accept: ",0)
            d = data.find("\\r\\n",s)
            self.accept = data[s+8:d]
            
            
            print(self.method)
            print(self.url)
            print(self.protocol)
            print(self.host)
            print(self.user_agent)
            print(self.accept)

        except:
            self.send_response(400)
        self.handle_request()



    def handle_request(self):
        self.h = False
        self.ispic = False
        method_name = 'do_' + self.method
        if not hasattr(self, method_name):
            self.send_response(405)
            return
        handler = getattr(self, method_name)
        handler()

    def do_POST(self):

        self.send_response(405)


        
        
    def do_HEAD(self):
        self.h = True
        self.url = self.url.replace("%20"," ")
        locurl = self.url
        try:

            if locurl.find("/403/") != -1:
                self.send404()
                self.send_response(403)
            if locurl.find("?") != -1:
                u = locurl.find("?")
                locurl = locurl[0:u]
            file = open(locurl[1:])

        except OSError:
            if (locurl[-1] =="/"):
                locurl = locurl+"index.html"
                self.url = locurl
            try:
                file = open(locurl[1:])  
                self.fileopen(file)
                self.send_response(200)
            except OSError:
                self.send404()
                self.send_response(404)
            
        except IOError:
            self.send404()
            self.send_response(405)
            
        else:
            self.fileopen(file)
            self.send_response(200)


    def do_GET(self):
        
        
        self.url = self.url.replace("%20"," ")
        locurl = self.url
        try:

            if locurl.find("/403/") != -1:
                self.send404()
                self.send_response(403)
            if locurl.find("?") != -1:
                u = locurl.find("?")
                locurl = locurl[0:u]
            file = open(locurl[1:])

        except OSError:
            if (locurl[-1] =="/"):
                locurl = locurl+"index.html"
                self.url = locurl
            try:
                file = open(locurl[1:])  
                self.fileopen(file)
                self.send_response(200)
            except OSError:
                self.send404()
                self.send_response(404)
            
        except IOError:
            self.send404()
            self.send_response(405)
            
        else:
            self.fileopen(file)
            self.send_response(200)

    def fileopen(self, file):
        try:
            self.answer = ""
            self.ispic = False       
            with file:
                lines = file.read()     
                self.answer += lines
                file.close()
        except:
            with open(self.url[1:], 'rb') as file:
                lines = file.read()
                self.answer = lines
                self.ispic = True
                
            file.close()

    def send404(self):
        self.ispic = False
        file = open("404.html")
        self.answer = """<!DOCTYPE html>"""
        with file:
            lines = file.read()
            self.answer += lines  
        file.close()      
                    

    def send_header(self, status):
        now = datetime.now()
        stamp = mktime(now.timetuple())
        t = format_date_time(stamp)
        u = self.url[-5:]
        u = u[u.find(".")+1:]

        try:
            len(self.answer)
        except AttributeError:
            self.answer = ""

        l = "Content-Length: {}".format(len(self.answer))
        self.send(self.protocol.encode("utf-8")+ b" " + status.encode("utf-8") + b"\r\n")
        self.send(b"Date: "+ t.encode("utf-8") + b"\r\n")
        self.send(b"Server: simplehttp\r\n")
        self.send(b"Connection: close\r\n")
        if (self.ispic == True):
            if (u == "jpg"):
                u = "jpeg"
            im = "image/{}".format(u)

            self.send(b"Content-Type: " + im.encode("utf-8") + b"\r\n")
        elif (u == "js"):
            self.send(b"Content-Type: " + b"text/javascript" + b"\r\n")
        elif (u == "css"):
            self.send(b"Content-Type: " + b"text/css" + b"\r\n")    
        else:
            self.send(b"Content-Type: " + b"text/html" + b"\r\n")
        self.send(l.encode("utf-8") + b"\r\n")
        
        self.send(b"\r\n")
        if (not self.h):
            self.ansv()


    def send_response(self, code, message = None):
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = ''
        
        status = str(code) + " " + str(message)
        self.send_header(status)

    def ansv(self): 
        if (self.ispic == False):
            self.answer = self.answer.encode("utf-8")
        self.send(self.answer)
        
        self.close()
        


    responses = {
        200: ('OK', 'Request fulfilled, document follows'),
        400: ('Bad Request',
            'Bad request syntax or unsupported method'),
        403: ('Forbidden',
            'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
            'Specified method is invalid for this resource.'),
    }

server = AsyncHTTPServer()
asyncore.loop()

