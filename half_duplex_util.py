
import json
import enum
import random
from dataclasses import asdict, dataclass
import enum

class PacketTypes(enum.Enum):
    ACK = 1
    DATA = 2
    COMPLETE = 3

@dataclass
class Packet:
    packet_type: int
    seq_number: int
    payload: str

def construct_packet(packet_type, seq_number, payload):
    packet = Packet(
        packet_type=packet_type,
        seq_number=seq_number,
        payload=payload
    )
    ret = json.dumps(asdict(packet))
    assert isinstance(ret, str), "Packet should be a string at this point"
    return ret

def deconstruct_packet(packet_string):
    packet_dict = json.loads(packet_string)
    try:
        return Packet(**packet_dict)
    except:
        print(f"[ERROR] Malformed packet: {packet_dict}, returning None. ")
        return None
