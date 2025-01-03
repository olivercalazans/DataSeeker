# MIT License
# Copyright (c) 2024 Oliver Ribeiro Calazans Jeronimo
# Repository: https://github.com/olivercalazans/DataSeeker
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software...


"""
This file contains classes used to manage and interact with the user interface.
It handles input processing and command execution.
"""


import sys
from auxiliary       import Color, DataBase
from port_scanner    import Port_Scanner
from os_fingerprint  import OS_Fingerprint



class Main: # ================================================================================================
    """Handles user interaction by receiving input and verifying if the given command exists."""

    def __init__(self) -> None:
        """Initializes the Main class, setting up the stop flag and auxiliary data."""
        self._stop_flag = False
        self._database  = DataBase()


    @property
    def _stop(self) -> None:
        """Stops the loop that receives user input by setting the stop flag to True."""
        self._stop_flag = True


    def _handle_user(self) -> None:
        """This method is used to do error handling of the loop"""
        try:   self._loop()
        except KeyboardInterrupt:  sys.exit()
        except Exception as error: print(Color.display_unexpected_error(error))


    def _loop(self) -> None:
        """Loop that receives input data from user."""
        print("\nFor more information and detailed documentation, please visit the GitHub repository:")
        print("https://github.com/olivercalazans/DataSeeker")
        while not self._stop_flag:
            print('\nWrite "help" to see the commands ' + '=' * 40)
            input_data         = input('[\033[38;5;202m' + 'DataSeeker' + '\033[0m]# ').split()
            command, arguments = self._separates_command_from_arguments(input_data)
            self._check_if_the_method_exists(command, arguments)


    @staticmethod
    def _separates_command_from_arguments(input_data:list) -> tuple[str, list|None]:
        """Separates the input data into command and arguments."""
        command    = input_data[0]
        arguments  = input_data[1:] or None
        return (command, arguments)


    def _check_if_the_method_exists(self, command:str, arguments:tuple) -> None:
        """Checks if the provided command exists in the strategy dictionary and executes it."""
        if command in self._get_strategy_dictionary():
            self._run_command(command, arguments)
        elif command == 'exit':
            self._stop
        else:
            print(f'{Color.yellow("Unknown command")} "{command}"')


    def _run_command(self, command:str, arguments:str) -> None:
        """Executes the command by calling the corresponding class method."""
        with self._get_strategy_dictionary().get(command) as strategy:
            try:   strategy._execute(self._database, arguments)
            except Exception as error: print(f'{Color.red("Error while trying to execute the command")}.\nERROR: {error}')


    @staticmethod
    def _get_strategy_dictionary() -> dict:
        """Returns the class dictionary."""
        return {
            "help":   Command_List(),
            "pscan":  Port_Scanner(),
            "osfing": OS_Fingerprint(),
        }





class Command_List: # ========================================================================================
    """Displays a list of all available commands."""

    @staticmethod
    def _execute(__, _) -> None:
        for command in (
            f'{Color.green("pscan")}....: Port scanner',
            f'{Color.green("osfing")}...: OS Fingerprint',
        ): print(command)





if __name__ == '__main__':
    user = Main()
    user._handle_user()