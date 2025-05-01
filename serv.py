# Server code
import socket
import os

# The port on which to listen
serverPort = 12000

# Create a TCP socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to the port
serverSocket.bind(('0.0.0.0', serverPort))
# Start listening for incoming connections
serverSocket.listen(5)

# Receives all data sent by sender/client with n number of bytes
def recvAll(sock, numBytes):
    recvBuff = b''
    while len(recvBuff) < numBytes:
        tmpBuff = sock.recv(numBytes - len(recvBuff))
        if not tmpBuff:
            break
        recvBuff += tmpBuff
    return recvBuff

def handleClient(connectionSocket):
    while True:
        header = recvAll(connectionSocket, 10)
        if not header:
            break
        commandLength = int(header.decode())
        command = recvAll(connectionSocket, commandLength).decode()
        print(f"Command received: {command}")

        parts = command.split(maxsplit=1)
        action = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        match action:
            case "put":
                parts = arg.split()
                filename = parts[0]
                dataPort = int(parts[1])
                clientIP = connectionSocket.getpeername()[0]

                dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dataSock.connect((clientIP, dataPort))

                fileSizeBuffer = recvAll(dataSock, 10)
                fileSize = int(fileSizeBuffer.decode())
                data = recvAll(dataSock, fileSize)

                # ✅ Fix: Strip directory and just save base filename
                baseFilename = os.path.basename(filename)
                savePath = "received_" + baseFilename

                with open(savePath, "wb") as f:
                    f.write(data)

                dataSock.close()
                print(f"Received file: {baseFilename} ({fileSize} bytes)")
                print(f"{baseFilename} data contents: \n{data.decode()}")

            case "get":
                parts = arg.split()
                filename = parts[0]
                dataPort = int(parts[1])
                clientIP = connectionSocket.getpeername()[0]

                dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dataSock.connect((clientIP, dataPort))

                if os.path.exists(filename):
                    dataSock.send("OK".encode())
                    fileSize = os.path.getsize(filename)
                    dataSock.send(f"{fileSize:010}".encode())
                    with open(filename, "rb") as f:
                        dataSock.sendall(f.read())
                else:
                    dataSock.send("NF".encode())  # Not Found

                dataSock.close()

            case "ls":
                dataPort = int(arg.strip())
                clientIP = connectionSocket.getpeername()[0]

                dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dataSock.connect((clientIP, dataPort))

                files = os.listdir()
                listing = "\n".join(files)
                listingBytes = listing.encode()
                dataSock.send(f"{len(listingBytes):010}".encode())
                dataSock.sendall(listingBytes)

                dataSock.close()

            case "quit":
                print("Client requested disconnect.")
                break

            case _:
                print("Unknown command.")

    connectionSocket.close()


print('The server is ready to receive')
try:
    while True:
        print('Waiting for connections...')
        connectionSocket, addr = serverSocket.accept()
        print("Accepted connection from client: ", addr)
        print()
        connectionSocket.send('Hello from server'.encode())
        handleClient(connectionSocket)
except KeyboardInterrupt:
    print("\nServer shutting down...")

# Cleanup
serverSocket.close()
