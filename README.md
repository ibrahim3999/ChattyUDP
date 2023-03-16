# ChattyUDP
This is Python code that defines several functions for sending network messages.

The first function, send_tcp_message, takes an IP address, a port number, and a message as input, and sends the message to the specified IP address and port number using the Transmission Control Protocol (TCP). It sets a timeout for the socket to wait for a response and returns the response if it receives one.

The second function, send_udp_message, is similar to send_tcp_message, but it uses the User Datagram Protocol (UDP) instead of TCP. UDP is a connectionless protocol, meaning that it does not establish a connection before transmitting data, and it does not guarantee reliable delivery of data.

The third function, send_dhcp_request, constructs a Dynamic Host Configuration Protocol (DHCP) discover message and sends it to a DHCP server using UDP. DHCP is a protocol that enables a network server to automatically assign IP addresses and other network configuration settings to devices on a network.

The fourth function, send_dns_query, constructs a Domain Name System (DNS) query message and sends it to a DNS server using UDP. DNS is a protocol that translates human-readable domain names, such as www.example.com, into IP addresses that can be used by network devices to communicate with each other.

The code also includes some constants that define the IP addresses and port numbers for various servers and services. It creates a SQLite database and table for storing data, and defines a cursor object for interacting with the database. Finally, it defines a schema for the data table that includes an ID, a question, and an answer.
