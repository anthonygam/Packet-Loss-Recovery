# Packet Loss Recovery Algorithm

Brushing up on my knowledge of TCP by implementing a simplified version of the protocol using UDP.

Implementation is half-duplex and one-way (client downloads from server only) without the three-way handshake in the beginning.

## What it does

Begin by splitting data into chunks. Each chunk gets an index called a sequence number.

```
The Transm ission Con trol Proto col (TCP)  is one of  
|--------| |--------| |--------| |--------| |--------| 
    00         01         02         03         04    

the main p rotocols o f the Inte rnet proto col suite.
|--------| |--------| |--------| |--------| |--------|
    05         06         07         08         09
```

Here is how the server logs appear with simulated packet loss of 50% on the client side

```
[SEND] Sending packet 0
[INFO] Waiting for ACK on packet 0
[SEND] Sending packet 1
[INFO] Waiting for ACK on packet 1
[SEND] Sending packet 2
[INFO] Waiting for ACK on packet 2
[RECV] Received ACK for packet 0 (6 remaining)
[SEND] Sending packet 3
[INFO] Waiting for ACK on packet 3
[SEND] Sending packet 4
[INFO] Waiting for ACK on packet 4
[SEND] Sending packet 5
[INFO] Waiting for ACK on packet 5
[SEND] Sending packet 6
[INFO] Waiting for ACK on packet 6
[RECV] Received ACK for packet 4 (5 remaining)
[INFO] No ACK received on packet 1
[INFO] No ACK received on packet 5
[INFO] No ACK received on packet 2
[INFO] No ACK received on packet 6
[INFO] No ACK received on packet 3
[SEND] Sending packet 1
[INFO] Waiting for ACK on packet 1
[SEND] Sending packet 2
[INFO] Waiting for ACK on packet 2
[SEND] Sending packet 3
[INFO] Waiting for ACK on packet 3
[RECV] Received ACK for packet 1 (4 remaining)
[RECV] Received ACK for packet 3 (3 remaining)
[SEND] Sending packet 5
[INFO] Waiting for ACK on packet 5
[SEND] Sending packet 6
[INFO] Waiting for ACK on packet 6
[RECV] Received ACK for packet 5 (2 remaining)
[RECV] Received ACK for packet 6 (1 remaining)
[INFO] No ACK received on packet 2
[SEND] Sending packet 2
[INFO] Waiting for ACK on packet 2
[INFO] No ACK received on packet 2
[SEND] Sending packet 2
[INFO] Waiting for ACK on packet 2
[INFO] No ACK received on packet 2
[SEND] Sending packet 2
[INFO] Waiting for ACK on packet 2
[RECV] Received ACK for packet 2 (0 remaining)
[INFO] Sent final packet.
```

When the client receives the final packet, they know they have all pieces of the file, so they are able to print it chunk by chunk as follows (100 characters per chunk)

```
The Transmission Control Protocol (TCP) is one of the main protocols of the Internet protocol suite.
It originated in the initial network implementation in which it complemented the Internet Protocol
(IP). Therefore, the entire suite is commonly referred to as TCP/IP. TCP provides reliable, ordered,
and error-checked delivery of a stream of octets (bytes) between applications running on hosts comm
unicating via an IP network. Major internet applications such as the World Wide Web, email, remote a
dministration, and file transfer rely on TCP, which is part of the transport layer of the TCP/IP sui
te. SSL/TLS often run on top of TCP.
```

## How the server works

Started with the example code from this documentation on `asyncio` (bottom of page).

The server uses two hash sets, `seq_numbers_to_send` and `unacknowledged_seq_numbers`, which both start out containing the sequence number of every single packet.

Then, it iterates endlessly over the sequence numbers. For example if there were 3 packets, it would iterate in the pattern of 0, 1, 2, 0, 1, 2, 0, 1, 2, etc. For each sequence number, we check if it is in `seq_numbers_to_send`. If it is, we send the packet to the client (retrieved via a hash map) and we remove the sequence number from `seq_numbers_to_send`. If not, we skip this sequence number.

Also, in between each sequence number we call `await asyncio.sleep(0)`. This allows the scheduler to exit the while loop temporarily to complete other tasks, such as address incoming messages from the client.

Every time the server sends a packet to the client, it starts a timer for 5 seconds. When the 5 second timer is complete, the server will break from the while loop (once again thanks to `await asyncio.sleep(0)`) and check if the sequence number of the packet sent 5 seconds earlier is still contained in the hash set `unacknowledged_seq_numbers`. If it is, we assume that the client did not receive the packet. Thus, we insert the sequence number *back* into `seq_numbers_to_send` so it can be sent once again.

Finally, whenever the server receives a message from the client, if the message is an ACK packet, we will remove the sequence number from `unacknowledged_seq_numbers`.

When the hash set `unacknowledged_seq_numbers` becomes empty, the server will send a final empty packet to the client. This allows the client to know that they have every packet they need to faithfully reconstruct the data.

## How the client works

Similarly started with example code from documentation (bottom of page).

The client is much simpler than the server. The client reconstructs the file sent by the server using a sorted map. Whenever it receives a packet, firstly it simulates packet loss by randomly exiting the function. If it did not exit, it will insert the payload from the packet into the sorted map, sorted by the sequence number. This allows all payloads to remain in the correct order efficiently, even if they are not received in the correct order. After processing the received packet, the client constructs and sends an ACK packet back to the server.

## Utilities

Both the server and client make use of some common utility functions. The main purpose of these functions is to serialise the packet data (payload, packet type and sequence number) using JSON. And also to model this data with a dataclass and enum.

## References

[https://docs.python.org/3/library/asyncio-protocol.html#udp-echo-server](https://docs.python.org/3/library/asyncio-protocol.html#udp-echo-server)

[https://docs.python.org/3/library/asyncio-protocol.html#udp-echo-client](https://docs.python.org/3/library/asyncio-protocol.html#udp-echo-client)
