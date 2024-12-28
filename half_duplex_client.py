import asyncio
import random
from half_duplex_util import construct_packet, deconstruct_packet, PacketTypes
from sortedcontainers import SortedDict
import sys

PACKET_LOSS = False
LOSS_PERCENTAGE = 0.5
DUMMY_DATA = "dummy".encode()

class PacketLossProtectionClient(asyncio.DatagramProtocol):
    def __init__(self, on_con_lost):
        self.on_con_lost = on_con_lost
        self.transport = None
        self.ordered_packets = SortedDict()

    def connection_made(self, transport):
        self.transport = transport
        # Empty message to begin connection, like SYN packet in TCP
        self.transport.sendto(DUMMY_DATA)

    def datagram_received(self, data, addr):
        # Simulate packet loss (lose half packets)
        if PACKET_LOSS:
            if random.random() < LOSS_PERCENTAGE: return
        # Receive Packet
        packet = deconstruct_packet(data.decode())
        if packet.packet_type == PacketTypes.DATA.value:
            self.ordered_packets[packet.seq_number] = packet.payload
            # Send ACK
            packet = construct_packet(
                PacketTypes.ACK.value,
                packet.seq_number,
                ""
            )
            self.transport.sendto(packet.encode())
        # Finished download
        elif packet.packet_type == PacketTypes.COMPLETE.value:
            # Print file and exit
            print("All packets in order:")
            print(list(self.ordered_packets.values()))

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)

async def main():
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: PacketLossProtectionClient(on_con_lost),
        remote_addr=('127.0.0.1', 8888))

    try:
        await on_con_lost
    finally:
        transport.close()

asyncio.run(main())
