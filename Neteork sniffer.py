import socket
import struct
import textwrap

# Unpack Ethernet frame
def unpack_ethernet_frame(data):
    dest_mac, src_mac, proto = struct.unpack('! 6s 6s H', data[:14])
    return get_mac_addr(dest_mac), get_mac_addr(src_mac), socket.htons(proto), data[14:]

# Return properly formatted MAC address
def get_mac_addr(bytes_addr):
    bytes_str = map('{:02x}'.format, bytes_addr)
    return ':'.join(bytes_str).upper()

# Unpack IPv4 packet
def unpack_ipv4_packet(data):
    version_header_length = data[0]
    version = version_header_length >> 4
    header_length = (version_header_length & 15) * 4
    ttl, proto, src, target = struct.unpack('! 8x B B 2x 4s 4s', data[:20])
    return version, header_length, ttl, proto, ipv4(src), ipv4(target), data[header_length:]

# Return properly formatted IPv4 address
def ipv4(addr):
    return '.'.join(map(str, addr))

# Unpack ICMP packet
def unpack_icmp_packet(data):
    icmp_type, code, checksum = struct.unpack('! B B H', data[:4])
    return icmp_type, code, checksum, data[4:]

# Unpack TCP segment
def unpack_tcp_segment(data):
    (src_port, dest_port, sequence, acknowledgment, offset_reserved_flags) = struct.unpack('! H H L L H', data[:14])
    offset = (offset_reserved_flags >> 12) * 4
    flag_urg = (offset_reserved_flags & 32) >> 5
    flag_ack = (offset_reserved_flags & 16) >> 4
    flag_psh = (offset_reserved_flags & 8) >> 3
    flag_rst = (offset_reserved_flags & 4) >> 2
    flag_syn = (offset_reserved_flags & 2) >> 1
    flag_fin = offset_reserved_flags & 1
    return src_port, dest_port, sequence, acknowledgment, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data[offset:]

# Unpack UDP segment
def unpack_udp_segment(data):
    src_port, dest_port, size = struct.unpack('! H H 2x H', data[:8])
    return src_port, dest_port, size, data[8:]

# Format multi-line data
def format_multi_line(prefix, string, size=80):
    size -= len(prefix)
    if isinstance(string, bytes):
        string = ''.join(r'\x{:02x}'.format(byte) for byte in string)
        if size % 2:
            size -= 1
    return '\n'.join([prefix + line for line in textwrap.wrap(string, size)])

def main():
    # Create a raw socket and bind it to the public interface
    conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))

    while True:
        raw_data, addr = conn.recvfrom(65536)
        dest_mac, src_mac, eth_proto, data = unpack_ethernet_frame(raw_data)
        print('\nEthernet Frame:')
        print(f'Destination: {dest_mac}, Source: {src_mac}, Protocol: {eth_proto}')

        # IPv4
        if eth_proto == 8:
            version, header_length, ttl, proto, src, target, data = unpack_ipv4_packet(data)
            print(f'\tIPv4 Packet:')
            print(f'\t\tVersion: {version}, Header Length: {header_length}, TTL: {ttl}')
            print(f'\t\tProtocol: {proto}, Source: {src}, Target: {target}')

            # ICMP
            if proto == 1:
                icmp_type, code, checksum, data = unpack_icmp_packet(data)
                print(f'\t\tICMP Packet:')
                print(f'\t\t\tType: {icmp_type}, Code: {code}, Checksum: {checksum}')
                print(f'\t\t\tData:')
                print(format_multi_line('\t\t\t\t', data))

            # TCP
            elif proto == 6:
                (src_port, dest_port, sequence, acknowledgment, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data) = unpack_tcp_segment(data)
                print(f'\t\tTCP Segment:')
                print(f'\t\t\tSource Port: {src_port}, Destination Port: {dest_port}')
                print(f'\t\t\tSequence: {sequence}, Acknowledgment: {acknowledgment}')
                print(f'\t\t\tFlags:')
                print(f'\t\t\t\tURG: {flag_urg}, ACK: {flag_ack}, PSH: {flag_psh}, RST: {flag_rst}, SYN: {flag_syn}, FIN: {flag_fin}')
                print(f'\t\t\tData:')
                print(format_multi_line('\t\t\t\t', data))

            # UDP
            elif proto == 17:
                src_port, dest_port, length, data = unpack_udp_segment(data)
                print(f'\t\tUDP Segment:')
                print(f'\t\t\tSource Port: {src_port}, Destination Port: {dest_port}, Length: {length}')

if __name__ == "__main__":
    main()
    
