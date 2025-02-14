# MIT License
# Copyright (c) 2024 Oliver Ribeiro Calazans Jeronimo
# Repository: https://github.com/olivercalazans/DataSeeker
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software...


import ipaddress, random, time, threading, sys
from scapy.layers.inet import TCP
from scapy.sendrecv    import sr1, sr, send
from scapy.all         import conf, Packet
from network           import *
from packets           import *
from arg_parser        import Argument_Parser_Manager
from display           import *


class Port_Scanner:

    def __init__(self, parser_manager:Argument_Parser_Manager, data:list) -> None:
        self._parser_manager   = parser_manager
        self._data             = data
        self._all_ports        = get_ports()
        self._host             = None
        self._flags            = None
        self._ports_to_be_used = None
        self._target_ip        = None
        self._responses        = None
        self._my_ip_address    = None


    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return False


    def _execute(self) -> None:
        try:
            self._get_argument_and_flags()
            self._target_ip = get_ip_by_name(self._host)
            conf.verb       = 0
            self._get_result_by_transmission_method()
            self._process_responses()
        except SystemExit as error: print(invalid_or_missing()) if not error.code == 0 else print()
        except KeyboardInterrupt:   print(red("Process stopped"))
        except Exception as error:  print(unexpected_error(error))


    def _get_argument_and_flags(self) -> None:
        arguments   = self._parser_manager._parse("PortScanner", self._data)
        self._host  = arguments.host
        self._flags = {
            'show':    arguments.show_all,
            'ports':   arguments.port,
            'random':  arguments.random_order,
            'delay':   arguments.delay,
            'decoy':   arguments.decoy,
        }


    def _prepare_ports(self, specified_ports = None) -> None:
        if specified_ports: 
            self._ports_to_be_used = [int(valor) for valor in specified_ports.split(",")]
        else:
            self._ports_to_be_used = list(self._all_ports.keys())

        if self._flags['random']: 
            self._ports_to_be_used = random.sample(self._ports_to_be_used, len(self._ports_to_be_used))


    def _get_result_by_transmission_method(self) -> list:
        if isinstance(self._flags['decoy'], str):
            self._perform_decoy_scan()
        else:
            self._perform_normal_scan()

    
    def _perform_normal_scan(self) -> None:
        self._prepare_ports(self._flags['ports'])
        with Normal_Scan(self._target_ip, self._ports_to_be_used, self._flags) as SCAN:
            self._responses = SCAN._perform_normal_methods()

    
    def _perform_decoy_scan(self) -> None:
        self._prepare_ports(self._flags['decoy'])
        with Decoy(self._target_ip, self._ports_to_be_used[0]) as DECOY:
            self._responses     = DECOY._perform_decoy_methods()
            self._flags['show'] = True


    def _process_responses(self) -> None:
        for sent, received in self._responses:
            port           = sent[TCP].dport
            response_flags = received[TCP].flags if received else None
            description    = self._all_ports[port] if port in self._all_ports else 'Generic Port'
            self._display_result(response_flags, port, description)


    def _display_result(self, response:str|None, port:int, description:str) -> None:
        match response:
            case "SA": status = green('Opened')
            case "S":  status = yellow('Potentially Open')
            case "RA": status = red('Closed')
            case "F":  status = red('Connection Closed')
            case "R":  status = red('Reset')
            case None: status = red('Filtered')
            case _:    status = red('Unknown Status')
        if response == 'SA' or self._flags['show']:
            print(f'Status: {status:>17} -> {port:>5} - {description}')





class Normal_Scan: # =========================================================================================

    def __init__(self, target_ip:str, ports:list|int, flags:dict) -> None:
        self._target_ip   = target_ip
        self._ports       = ports
        self._flags       = flags
        self._packets     = [create_tpc_ip_packet(self._target_ip, port) for port in self._ports]
        self._len_packets = len(self._packets)
        self._delay       = None
        self._lock        = threading.Lock()
        self._responses   = list()


    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return False
    

    def _perform_normal_methods(self) -> None:
        if self._flags['delay']: 
            self._async_sending()
        else:
            self._responses, _ = sr(self._packets, inter=0.1, timeout=3, verbose=0)
        return self._responses


    # DELAY METHODS ------------------------------------------------------------------------------------------
    def _async_sending(self) -> None:
        self._get_delay_time_list()
        threads     = []
        for index ,packet in enumerate(self._packets):
            thread = threading.Thread(target=self._async_send_packet, args=(packet,))
            threads.append(thread)
            thread.start()
            sys.stdout.write(f'\rPacket sent: {index}/{len(self._packets)} - {self._delay[index]:.2}s')
            sys.stdout.flush()
            time.sleep(self._delay[index])
        for thread in threads:
            thread.join()
        print('\n')


    def _get_delay_time_list(self) -> None:
        match self._flags['delay']:
            case True: delay = [random.uniform(1, 3) for _ in range(self._len_packets)]
            case _:    delay = self._create_delay_time_list()
        self._delay = delay


    def _create_delay_time_list(self) -> list:
        values = [float(value) for value in self._flags['delay'].split('-')]
        if len(values) > 1: return [random.uniform(values[0], values[1]) for _ in range(self._len_packets)]
        return [values[0] for _ in range(self._len_packets)]


    def _async_send_packet(self, packet:Packet) -> None:
        response = sr1(packet, timeout=3, verbose=0)
        with self._lock:
            self._responses.append((packet, response))





class Decoy: # ===============================================================================================
    
    def __init__(self, target_ip:str, port:int):
        self._target_ip     = target_ip
        self._port          = port
        self._interface     = get_default_interface()
        self._netmask       = get_subnet_mask(self._interface)
        self._my_ip_address = get_ip_address(self._interface)
        self._decoy_ips     = None
        self._response      = None


    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return False
    

    def _perform_decoy_methods(self) -> Packet:
        self._generate_random_ip_in_subnet()
        self._add_real_packet()        
        self._send_decoy_and_real_packets()
        return self._response


    def _generate_random_ip_in_subnet(self, count = random.randint(4, 6)) -> None:
        network         = ipaddress.IPv4Network(f"{self._my_ip_address}/{self._netmask}", strict=False)
        hosts           = list(network.hosts())
        random_ips      = random.sample(hosts, count)
        self._decoy_ips = [str(ip) for ip in random_ips]


    def _add_real_packet(self) -> list:
        packet_number = len(self._decoy_ips)
        real_ip_index = random.randint(packet_number // 2, packet_number - 1)
        self._decoy_ips.insert(real_ip_index, self._my_ip_address)


    def _send_decoy_and_real_packets(self) -> None:
        for ip in self._decoy_ips:
            delay = random.uniform(1, 3)
            if ip == self._my_ip_address:
                print(f'{green("Real packet")}: {ip:<15}, Delay: {delay:.2}')
                thread = threading.Thread(target=self._send_real_packet)
                thread.start()
            else:
                print(f'{red("Decoy packet")}: {ip:<15}, Delay: {delay:.2}')
                self._send_decoy_packet(ip)
            time.sleep(delay)


    def _send_real_packet(self) -> None:
        real_packet    = create_tpc_ip_packet(self._target_ip, self._port)
        response       = sr1(real_packet, timeout=3, verbose=0)
        self._response = [(real_packet, response)]


    def _send_decoy_packet(self, decoy_ip:str) -> None:
        decoy_packet = create_tpc_ip_packet(self._target_ip, self._port, decoy_ip)
        send(decoy_packet, verbose=0)