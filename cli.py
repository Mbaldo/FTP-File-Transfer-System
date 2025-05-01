# Client code
# Connecting to the local host server as a client
import socket
import os
import sys

# Command line checks
if len(sys.argv) < 2:
    print("USAGE python " + sys.argv[0] + " <FILE NAME>")
    sys.exit(1)

# Name and port number of the server to want to connect.
serverName = sys.argv[1]
serverPort = int(sys.argv[2])


# Create a socket
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect to the server
clientSocket.connect((serverName, serverPort))
print(clientSocket.recv(17).decode())

def sendAll(clientSocket, encoded_data_):
    # bytes sent
    bytesSent = 0
    # Keep sending bytes until all bytes are sent
    while bytesSent < len(encoded_data_):
        bytesSent += clientSocket.send(encoded_data_[bytesSent:])

def recvAll(sock, numBytes):
    recvBuff = b''

    while len(recvBuff) < numBytes:
        # Receive whatever the newly connected client has to send
        tmpBuff = sock.recv(numBytes - len(recvBuff))

        # When the other side unexpectedly closed its socket.
        if not tmpBuff:
            break

        # Receive whatever the newly connected client has to send
        recvBuff += tmpBuff
    return recvBuff

def sendFile(objFile):
    while True:
        # Read 65536 bytes of data
        fileData = objFile.read(65536)

        # Make sure we did not hit EOF
        if not fileData:
            break

        # The file has been read. We are done
        sendAll(fileData.encode())
    print("Sent file.")

def sendCommand(sock, command):
    encoded = command.encode()
    header = f"{len(encoded):010}".encode()
    sendAll(sock, header)
    sendAll(sock, encoded)

def uploadFile(controlSock, filename):
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist.")
        return

    # Step 1: Create ephemeral data socket
    dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dataSock.bind(('', 0))  # Bind to any available port
    dataSock.listen(1)
    dataPort = dataSock.getsockname()[1]

    # Step 2: Send put command with filename and ephemeral port
    sendCommand(controlSock, f"put {filename} {dataPort}")

    # Step 3: Accept server connection on data port
    conn, addr = dataSock.accept()

    # Step 4: Send file over data channel
    with open(filename, "rb") as f:
        fileData = f.read()

    conn.send(f"{len(fileData):010}".encode())
    sendAll(conn, fileData)
    conn.close()
    dataSock.close()
    print(f"Uploaded '{filename}' ({len(fileData)} bytes)")


def downloadFile(controlSock, filename):
    # Step 1: Create ephemeral data socket
    dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dataSock.bind(('', 0))
    dataSock.listen(1)
    dataPort = dataSock.getsockname()[1]

    # Step 2: Send 'get' command with filename and data port
    sendCommand(controlSock, f"get {filename} {dataPort}")

    # Step 3: Accept connection from server
    conn, addr = dataSock.accept()

    # Step 4: Receive file size and data
    status = conn.recv(2).decode()
    if status == "OK":
        fileSize = int(recvAll(conn, 10).decode())
        fileData = recvAll(conn, fileSize)
        with open(filename, "wb") as f:
            f.write(fileData)
        print(f"Downloaded '{filename}' ({fileSize} bytes)")
    else:
        print(f"File '{filename}' not found on server.")

    conn.close()
    dataSock.close()

def listFiles(controlSock):
    # Step 1: Set up ephemeral data socket
    dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dataSock.bind(('', 0))
    dataSock.listen(1)
    dataPort = dataSock.getsockname()[1]

    # Step 2: Send 'ls' command with data port
    sendCommand(controlSock, f"ls {dataPort}")

    # Step 3: Accept connection from server
    conn, addr = dataSock.accept()

    # Step 4: Receive and print file list
    fileListSize = int(recvAll(conn, 10).decode())
    fileList = recvAll(conn, fileListSize).decode()
    print(fileList)

    conn.close()
    dataSock.close()




try:
    while True:
        command = input("ftp> ").strip()
        if not command:
            continue

        parts = command.split(maxsplit=1)
        action = parts[0]
        argument = parts[1] if len(parts) > 1 else ""

        match action:
            case "put":
                uploadFile(clientSocket, argument)
            case "get":
                downloadFile(clientSocket, argument)
            case "ls":
                listFiles(clientSocket)
            case "quit":
                sendCommand(clientSocket, "quit")
                break
            case _:
                print("Invalid command. Try: get, put, ls, quit.")
except Exception as e:
    print("Error:", e)

clientSocket.close()
