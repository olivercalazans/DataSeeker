# MIT License
# Copyright (c) 2024 Oliver Ribeiro Calazans Jeronimo
# Repository: https://github.com/olivercalazans/DataSeeker
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software...


"""
THIS FILE CONTAINS THE CLASSES THAT EXECUTE SIMPLE COMMANDS.
    -> Command list class;
    -> Interfaces class;
    -> Get IP class;
    -> IP geolocation class;
    -> MAC to device class.
"""


import ipaddress, json, urllib.request, re
from network   import Network
from auxiliary import Color, Argument_Parser_Manager



class Command_List: # ========================================================================================
    """Displays a list of all available commands."""

    @staticmethod
    def _execute(__, _) -> None:
        for command in (
            f'{Color.green("iface")}....: Display interface information',
            f'{Color.green("ip")}.......: Get IP by name',
            f'{Color.green("geoip")}....: Get geolocation of an IP',
            f'{Color.green("dev")}......: Looks up a MAC',
            f'{Color.green("netmap")}...: Network scanner',
            f'{Color.green("pscan")}....: Port scanner',
            f'{Color.green("osfing")}...: OS Fingerprint',
        ): print(command)





class Interfaces: # ==========================================================================================
    """Displays network interfaces information."""

    @staticmethod
    def _execute(__, _):
        for iface in Network._get_interface_information():
            if iface['status'] == 'UP':
                print(f'\n{Color.green("Interface")}: {iface["iface"]} - Status: {Color.green(iface["status"])}')
                print(f'  - IPv4 Address...: {Color.pink(iface["addr"])}')
                print(f'  - Netmask........: {iface["mask"]} - /{Network._convert_mask_to_cidr_ipv4(iface["mask"])}')
                print(f'  - Broadcast IP...: {iface["broad"]}')
            else:
                print(f'\n{Color.green("Interface")}: {iface["iface"]} - Status: {Color.red(iface["status"])}')





class Get_IP: # ==============================================================================================
    """Performs a lookup and displays the IP address of a hostname."""

    @staticmethod
    def _execute(database, data:list) -> None:
        """Executes the process to retrieve the IP address based on the provided hostname."""
        try:   argument = Get_IP._get_argument(database.parser_manager, data)
        except SystemExit as error: print(Color.display_invalid_missing()) if not error.code == 0 else print()
        except Exception  as error: print(Color.display_unexpected_error(error))
        else:  Get_IP._ip(argument)


    @staticmethod
    def _get_argument(parser_manager:Argument_Parser_Manager, argument:list) -> str:
        """Parses and retrieves the hostname argument."""
        arguments = parser_manager._parse("Get_Ip", argument)
        return (arguments.host)


    @staticmethod
    def _ip(host_name:str) -> None:
        """Displays the IP address of the provided hostname."""
        ips = Network._get_ip_by_name(host_name, False)
        Network._display_ips(ips)





class IP_Geolocation: # ======================================================================================
    """This class performs the geolocation of an IP address."""

    @staticmethod
    def _execute(database, data:list) -> None:
        """Executes the geolocation process and handles errors."""
        try:
            host   = IP_Geolocation._get_argument_and_flags(database.parser_manager, data)
            ip     = Network._get_ip_by_name(host, True)
            data   = IP_Geolocation._get_geolocation(ip)
            result = IP_Geolocation._process_data(data)
            IP_Geolocation._display_result(result)
        except SystemExit as error: print(Color.display_invalid_missing()) if not error.code == 0 else print()
        except Exception  as error: print(Color.display_unexpected_error(error))


    @staticmethod
    def _get_argument_and_flags(parser_manager:Argument_Parser_Manager, data:list) -> str:
        """Parses arguments and returns the IP address as a string."""
        arguments = parser_manager._parse("GeoIP", data)
        return (arguments.ip)
    
    
    @staticmethod
    def _get_geolocation(ip:ipaddress.IPv4Address) -> dict:
        """Fetches the geolocation information for the given IP address from a web service."""
        with urllib.request.urlopen(f"https://ipinfo.io/{ip}/json") as response:
            return json.load(response)

    
    @staticmethod
    def _process_data(data:object) -> dict:
        """Processes the geolocation data and extracts specific fields."""
        return {
                "IP":       data.get("ip"),
                "City":     data.get("city"),
                "Region":   data.get("region"),
                "Country":  data.get("country"),
                "Location": data.get("loc"),
                "Postal":   data.get("postal"),
                "Timezone": data.get("timezone")
            }


    @staticmethod
    def _display_result(result:dict) -> None:
        """Displays the processed geolocation results in a formatted manner."""
        for key, value in result.items():
            separator = (8 - len(key)) * '.'
            print(f'{key}{separator}: {value}')





class MAC_To_Device: # =======================================================================================
    """This class displays the manufacturer of devices based on their MAC address."""

    @staticmethod
    def _execute(database, argument:list) -> None:
        """Executes the manufacturer lookup process and handles errors."""
        try: 
            mac    = MAC_To_Device._get_argument_and_flags(database.parser_manager, argument)
            result = MAC_To_Device._lookup_mac(database.mac_dictionary, mac)
            MAC_To_Device._display_result(mac, result)
        except SystemExit as error: print(Color.display_invalid_missing()) if not error.code == 0 else print()
        except ValueError as error: print(Color.display_error(error))
        except Exception  as error: print(Color.display_unexpected_error(error))


    @staticmethod
    def _get_argument_and_flags(parser_manager:Argument_Parser_Manager, data:list) -> str:
        """Parses arguments and returns the normalized MAC address as a string."""
        arguments = parser_manager._parse("MacToDev", data)
        return (arguments.mac)
    

    @staticmethod
    def _normalize_mac(mac):
        """Validates the MAC address and returns it in a normalized format."""
        cleaned_mac = re.sub(r'[^a-fA-F0-9]', '', mac)
        if len(cleaned_mac) < 6: raise ValueError("Invalid MAC address")
        normalized_mac = '-'.join([cleaned_mac[i:i+2] for i in range(0, 6, 2)])
        return normalized_mac.upper()


    @staticmethod
    def _lookup_mac(mac_dictionary:list[dict], mac:str) -> None:
        """Looks up the manufacturer associated with the provided MAC address."""
        mac = MAC_To_Device._normalize_mac(mac)
        return mac_dictionary.get(mac, 'Not found')
        

    @staticmethod
    def _display_result(mac:str, result:str) -> None:
        """Displays the manufacturer information based on the MAC address."""
        print(f'MAC: {mac} - Manufacturer: {result}')
