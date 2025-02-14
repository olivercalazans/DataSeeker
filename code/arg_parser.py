# MIT License
# Copyright (c) 2024 Oliver Ribeiro Calazans Jeronimo
# Repository: https://github.com/olivercalazans/DataSeeker
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software...


import argparse


class Argument_Parser_Manager: # =============================================================================

    def __init__(self) -> None:
        self._parser         = argparse.ArgumentParser(description="Argument Manager")
        self._subparser      = self._parser.add_subparsers(dest="class")
        self._argument_class = Argument_Definitions()
        self._add_all_commands()


    def _add_all_commands(self) -> None:
        for method_name in dir(self._argument_class):
            method = getattr(self._argument_class, method_name)
            if callable(method) and method_name.endswith('_arguments'):
                arguments = method()
                self._add_arguments(arguments[0], arguments[1])


    def _add_arguments(self, class_name:str, argument_list:list[dict]) -> None:
        class_parser = self._subparser.add_parser(class_name)
        for arg in argument_list:
            match arg[0]:
                case 'bool':  class_parser.add_argument(arg[1], arg[2], action="store_true", help=arg[3])
                case 'value': class_parser.add_argument(arg[1], arg[2], type=arg[3], help=arg[4])
                case 'opt':   class_parser.add_argument(arg[1], arg[2], nargs='?', const=True, default=False, help=arg[3])
                case 'arg':   class_parser.add_argument(arg[1], type=str, help=arg[2])
                case _:       class_parser.add_argument(arg[1], type=str, choices=arg[2], help=arg[3])


    def _parse(self, subparser_id:str, data:list) -> argparse.Namespace:
        data.insert(0, subparser_id)
        return self._parser.parse_args(data)





class Argument_Definitions: # ================================================================================

    @staticmethod
    def _sys_command_arguments():
        return "SysCommand", [("arg", "command", "System command")]


    @staticmethod
    def _portscanner_arguments():
        return "PortScanner", [
            ("arg",   "host", "Target IP/Hostname"),
            ("bool",  "-r", "--random-order", "Use the ports in random order"),
            ("value", "-p", "--port",  str, "Specify a port to scan"),
            ("value", "-D", "--decoy", str, "Uses decoy method"),
            ("opt",   "-d", "--delay", "Add a delay between packet transmissions."),
            ("bool",  "-s", "--show-all", "Display all statuses, both open and closed."),
        ]


    @staticmethod
    def _banner_grabbing_arguments():
        PROTOCOLS = ['http', 'https', 'ssh']
        return "BannerGrabbing", [
            ("arg",    "host",     "Target IP/Hostname"),
            ("choice", "protocol", PROTOCOLS, "Protocol"),
            ("value",  "-p", "--port", str, "Specify a port to grab the banners")
        ]


    @staticmethod
    def _os_fingerprint_arguments():
        return "OSFingerprint", [("arg", "host", "Target IP/Hostname")]