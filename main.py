import argparse
import json
import subprocess
import sys

def start_network(network_config_file):
    """
    Launches each node in the network using the single network configuration file.

    Parameters:
    - network_config_file: Path to the network configuration file.
    """
    # Load network configuration
    with open(network_config_file, "r") as f:
        network_config = json.load(f)

    num_nodes = network_config["num_nodes"]
    ports = network_config["ports"]

    if len(ports) != num_nodes:
        print("Error: Number of ports does not match num_nodes in the configuration file.")
        sys.exit(1)

    # Start each node process
    for i in range(num_nodes):
        port = ports[i]

        if sys.platform == "win32":
            subprocess.Popen(
                ["python", "node_script.py", str(i), str(port), "False", network_config_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

    print("All nodes are ready!")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run the Streamlet Protocol using a network configuration file.")
    parser.add_argument("--network_config_file", type=str, required=True, help="Path to the network configuration file.")

    args = parser.parse_args()
    network_config_file = args.network_config_file

    print(f"Starting Streamlet Protocol using configuration file: {network_config_file}")

    # Start the network
    start_network(network_config_file)

if __name__ == "__main__":
    main()
