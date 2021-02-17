import argparse
from copy import Error
import logging
import debugpy
from azureml.core import Run
from azdebugrelay import DebugRelay, DebugMode


def remote_debugger_init() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument("--is-debug", type=bool, required=False, default=False)
    parser.add_argument("--debug-relay-connection-name",
                        type=str, required=True)
    parser.add_argument('--debug-port', action='store', type=int,
                        default=5678, required=False)
    parser.add_argument("--debug-relay-connection-string-secret",
                        type=str, required=True)
    options, _ = parser.parse_known_args()

    if not options.is_debug:
        return False

    if options.debug_relay_connection_string_secret == "" or options.debug_relay_connection_name == "":
        err_msg = "Azure Relay connection string secret name or connection name is empty."
        logging.fatal(err_msg)
        raise ValueError(err_msg)
    # get connection string from the workspace Key Vault
    run = Run.get_context()
    connection_string = run.get_secret(
        options.debug_relay_connection_string_secret)
    if connection_string is None or connection_string == "":
        err_msg = "Connection string for Azure Relay Hybrid Connection is missing in Key Vault."
        logging.fatal(err_msg)
        raise ValueError(err_msg)
    
    print("Remote debugging has been activated. Starting Azure Relay Bridge...")
    relay_connection_name = options.debug_relay_connection_name # your Hybrid Connection name
    debug_mode = DebugMode.Connect
    hybrid_connection_url = None # can keep it None because using a connection string
    host = "127.0.0.1"  # local hostname or ip address the debugger starts on
    port = options.debug_port

    debug_relay = DebugRelay(
        connection_string, relay_connection_name, debug_mode, hybrid_connection_url, host, port)
    debug_relay.open(wait_for_connection=False)
    if debug_relay.is_running():
        print(f"Starting debugpy session on {host}:{port}. " +
            "If it's stuck here, make sure your VS Code starts listening before this step starts.")
        debugpy.connect((host, port))
        print(f"Debugpy is connected!")
        return True
    else:
        err_msg = "Cannot connect to a remote debugger"
        print(err_msg)
        logging.fatal(err_msg)
        raise Error(err_msg)
