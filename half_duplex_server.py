import asyncio
from half_duplex_util import construct_packet, deconstruct_packet, PacketTypes
import sys

class PacketTracker():
    def __init__(self, data, packet_size=100):
        # Split the data into packets
        packets_list = [
            data[i : i + packet_size] for i in range(0, len(data), packet_size)
        ]

        self.unacknowledged_seq_numbers = set()
        self.packets = {}

        for seq_number, packet in enumerate(packets_list):
            self.packets[seq_number] = packet
            self.unacknowledged_seq_numbers.add(seq_number)
        
        self.largest_seq_number = max(self.unacknowledged_seq_numbers)
        self.seq_numbers_to_send = self.unacknowledged_seq_numbers.copy()

    def not_all_acknowledged(self):
        return len(self.unacknowledged_seq_numbers) > 0


class PacketLossProtectionServer(asyncio.DatagramProtocol):
    def __init__(self, packet_tracker):
        self.transport = None
        self.connected_clients = set()
        self.packet_tracker = packet_tracker

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        # New client
        if addr not in self.connected_clients:
            self.connected_clients.add(addr)
            asyncio.create_task(self.upload_file(addr))
        # Existing client
        else:
            packet = deconstruct_packet(data.decode())
            if packet.packet_type == PacketTypes.ACK.value:
                if packet.seq_number not in \
                    self.packet_tracker.unacknowledged_seq_numbers:
                    print("[INFO] Already received ACK for this packet.")
                else:
                    self.packet_tracker.unacknowledged_seq_numbers.remove(
                        packet.seq_number
                    )
                print(f"[RECV] Received ACK for packet {packet.seq_number}" + \
                    f" ({len(packet_tracker.unacknowledged_seq_numbers)}" + \
                    " remaining)")

    async def upload_file(self, addr):
        current_seq_number = 0
        while self.packet_tracker.not_all_acknowledged():
            if current_seq_number > packet_tracker.largest_seq_number:
                current_seq_number = 0
            if current_seq_number in packet_tracker.seq_numbers_to_send:
                packet = construct_packet(
                    PacketTypes.DATA.value,
                    current_seq_number,
                    packet_tracker.packets[current_seq_number]
                )
                print(f"[SEND] Sending packet {current_seq_number}")
                self.transport.sendto(
                    packet.encode(),
                    addr
                )
                packet_tracker.seq_numbers_to_send.remove(current_seq_number)
                print(f"[INFO] Waiting for ACK on packet {current_seq_number}")
                asyncio.create_task(self.timer_task(current_seq_number))
            current_seq_number += 1
            await asyncio.sleep(0)
        final_packet = construct_packet(
            PacketTypes.COMPLETE.value,
            None,
            None
        )
        self.transport.sendto(final_packet.encode(), addr)
        print("[INFO] Sent final packet.")


    async def timer_task(self, seq_number):
        await asyncio.sleep(5)
        if seq_number in self.packet_tracker.unacknowledged_seq_numbers:
            print(f"[INFO] No ACK received on packet {seq_number}")
            self.packet_tracker.seq_numbers_to_send.add(seq_number)

    def error_received(self, exc):
        print(f"Error received: {exc}")


async def main(packet_tracker):
    print("Starting UDP server")
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: PacketLossProtectionServer(packet_tracker),
        local_addr=('127.0.0.1', 8888))
    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()


if __name__ == '__main__':
    data = """The Transmission Control Protocol (TCP) is one of the main protocols of the Internet protocol suite. It originated in the initial network implementation in which it complemented the Internet Protocol (IP). Therefore, the entire suite is commonly referred to as TCP/IP. TCP provides reliable, ordered, and error-checked delivery of a stream of octets (bytes) between applications running on hosts communicating via an IP network. Major internet applications such as the World Wide Web, email, remote administration, and file transfer rely on TCP, which is part of the transport layer of the TCP/IP suite. SSL/TLS often run on top of TCP."""
    packet_tracker = PacketTracker(data)
    asyncio.run(main(packet_tracker))
