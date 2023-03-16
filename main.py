import socket
import struct
import sqlite3
DHCP_SERVER_IP = "127.0.0.1"
DHCP_SERVER_PORT = 67
DNS_SERVER_IP = "127.0.0.1"
DNS_SERVER_PORT = 53
APPLICATION_SERVER_IP = "127.0.0.1"
APPLICATION_SERVER_PORT = 5000
APPLICATION_SERVER_TCP_PORT = 8000
APPLICATION_SERVER_UDP_PORT = 8001
TCP_TIMEOUT = 5  # in seconds
UDP_MAX_PACKET_SIZE = 65507  # maximum size of a datagram packet for transmission via UDP
APPLICATION_SERVER_TCP_PORT = 8000
APPLICATION_SERVER_UDP_PORT = 8001

# create a connection to the SQLite database
conn = sqlite3.connect('data1.db')
c = conn.cursor()

# create the SQL table to hold the data
c.execute('''CREATE TABLE IF NOT EXISTS data 
             (id INTEGER PRIMARY KEY,
              question TEXT,
              answer TEXT)''')

def send_tcp_message(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(TCP_TIMEOUT)
        s.connect((ip, port))
        s.sendall(message)
        response = s.recv(UDP_MAX_PACKET_SIZE)
    return response

def send_udp_message(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(message, (ip, port))
        response, _ = s.recvfrom(UDP_MAX_PACKET_SIZE)
    return response

def send_dhcp_request(mac_address):
    message = struct.pack("!6s", b'\x00\x0c\x29\x64\x2a\xfc')  # Ethernet header: destination MAC address
    message += struct.pack("!6s", b'\x00\x00\x00\x00\x00\x00')  # Ethernet header: source MAC address
    message += struct.pack("!H", 0x0800)  # Ethernet header: type (IPv4)
    message += struct.pack("!B", 0x45)  # IPv4 header: version and header length
    message += struct.pack("!B", 0x00)  # IPv4 header: differentiated services field
    message += struct.pack("!H", 0x003c)  # IPv4 header: total length (60 bytes)
    message += struct.pack("!H", 0x0000)  # IPv4 header: identification
    message += struct.pack("!H", 0x0000)  # IPv4 header: flags and fragment offset
    message += struct.pack("!B", 0x80)  # IPv4 header: time to live
    message += struct.pack("!B", 0x11)  # IPv4 header: protocol (UDP)
    message += struct.pack("!H", 0x0000)  # IPv4 header: header checksum
    message += socket.inet_aton("0.0.0.0")  # IPv4 header: source IP address
    message += socket.inet_aton("255.255.255.255")  # IPv4 header: destination IP address
    message += struct.pack("!H", 0x0043)  # UDP header: source port (67)
    message += struct.pack("!H", 0x0044)  # UDP header: destination port (68)
    message += struct.pack("!H", 0x001c)  # DHCP header: message type (DHCP discover)
    message += b"\x01"  # DHCP header: hardware type (Ethernet)
    message += b"\x01"  # DHCP header: hardware address length (6 bytes)
    message += b"\x00"  # DHCP header: hops
    message += struct.pack("!I", 0x00000000)  # DHCP header: transaction ID
    message += struct.pack("!H", 0x0000)  # DHCP header: seconds elapsed
    message += struct.pack("!H", 0x0000)  # DHCP header: flags
    message += socket.inet_aton("0.0.0.0")  # DHCP header: client IP address
    message += socket.inet_aton("0.0.0.0")  # DHCP header: your IP address
    message += socket.inet_aton("0.0.0.0")  # DHCP header: server IP address
    message += socket.inet_aton("0.0.0.0")  # DHCP header: gateway IP address
    message += mac_address.encode().replace(b':', b'')  # DHCP header: client hardware address
    message += b'\x00' * (10 + 192)  # DHCP header: padding
    message += b"\x63\x82\x53\x63"  # DHCP header: magic cookie
    message += b"\x35\x01\x01"  # DHCP option: DHCP message type (DHCP discover)
    message += b"\x3d\x06" + mac_address.encode().replace(b':', b'')  # DHCP option: client identifier
    message += b"\x37\x03\x03\x01\x06"  # DHCP option: requested parameters (subnet mask, router)
    message += b"\xff"  # DHCP option: end of options
    response = send_udp_message(DHCP_SERVER_IP, DHCP_SERVER_PORT, message)
    return response

def send_dns_query(hostname):
    message = struct.pack("!H", 0x1234)  # DNS header: ID
    message += struct.pack("!H", 0x0100)  # DNS header: flags (standard query)
    message += struct.pack("!H", 0x0001)  # DNS header: number of questions
    message += struct.pack("!H", 0x0000)  # DNS header: number of answer RRs
    message += struct.pack("!H", 0x0000)  # DNS header: number of authority RRs
    message += struct.pack("!H", 0x0000)  # DNS header: number of additional RRs
    for label in hostname.split('.'):
        message += struct.pack("!B", len(label)) + label.encode()  # DNS question: QNAME
    message += b"\x00"  # DNS question: QNAME terminator
    message += struct.pack("!H", 0x0001)  # DNS question: QTYPE (A)
    message += struct.pack("!H", 0x0001)  # DNS question: QCLASS (IN)
    response = send_udp_message(DNS_SERVER_IP, DNS_SERVER_PORT, message)
    return response


def send_application_query(query):
    try:
        # try sending the query over TCP first
        message = query.encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((APPLICATION_SERVER_IP, APPLICATION_SERVER_TCP_PORT))
        sock.sendall(message)
        response = sock.recv(1024)
        sock.close()
        return response.decode()
    except:
        # if TCP fails, send the query over reliable UDP
        message = struct.pack("!I", 0x00000000)  # reliable UDP header: message ID
        message += struct.pack("!I", len(query))  # reliable UDP header: message length
        message += query.encode()  # reliable UDP data: query
        response = b""
        try_count = 0
        while len(response) == 0 and try_count < 3:
            try_count += 1
            response = send_reliable_udp_message(APPLICATION_SERVER_IP, APPLICATION_SERVER_UDP_PORT, message)
        if len(response) == 0:
            raise Exception("Failed to send query to application server")
        return response[8:].decode()

def send_reliable_udp_message(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    window_size = 1
    sequence_number = 0
    last_acknowledgement_number = 0
    unacknowledged_packets = []
    while len(message) > 0 or len(unacknowledged_packets) > 0:
        # send unacknowledged packets
        while len(unacknowledged_packets) < window_size and len(message) > 0:
            packet = struct.pack("!I", sequence_number)  # reliable UDP header: sequence number
            packet += struct.pack("!I", 0x00000000)  # reliable UDP header: acknowledgement number
            packet += message[:1400]  # reliable UDP data: packet payload
            message = message[1400:]
            unacknowledged_packets.append(packet)
            sequence_number += 1
        for packet in unacknowledged_packets:
            try:
                sock.sendto(packet, (ip, port))
            except socket.error as e:
                print("Failed to send packet: {}".format(e))
                return b""
        # receive acknowledgements
        try:
            packet, _ = sock.recvfrom(1024)
            acknowledgement_number = struct.unpack("!I", packet[4:8])[0]
            if acknowledgement_number > last_acknowledgement_number:
                num_acknowledged_packets = acknowledgement_number - last_acknowledgement_number
                del unacknowledged_packets[:num_acknowledged_packets]
                last_acknowledgement_number = acknowledgement_number
                window_size = min(window_size + num_acknowledged_packets, 32)
        except socket.timeout:
            print("Timeout waiting for acknowledgement")
            return b""
    sock.close()
    return packet


sim_ack_loss = True  # Switch on to simulate loss of first ACK packet during file transfer
sim_packet_order_mix = True  # Causes client to mix up order of packets sent, can be used to test re-ordering at server



conn = sqlite3.connect('data1.db')
c = conn.cursor()

# create the table
c.execute('''CREATE TABLE IF NOT EXISTS answers
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              client_ip TEXT, 
              question_id INTEGER, 
              answer TEXT)''')

# add the initial data to the table
c.execute("INSERT INTO answers (client_ip, question_id, answer) VALUES (?, ?, ?)", ("127.0.0.1", 1, "answer to question 1"))
c.execute("INSERT INTO answers (client_ip, question_id, answer) VALUES (?, ?, ?)", ("127.0.0.1", 2, "answer to question 2"))
# add more initial data here...



conn.commit()
conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

s.bind(("127.0.0.1", 10000))

while 1:
    bytesAddressPair = s.recvfrom(1024)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]
    
    print("WE GOT A MESSAGE!!: ", message)


    a = input("WHAT DO YOU WANT TO SAY?? : ")
    s.sendto(str(a).encode(), address)

