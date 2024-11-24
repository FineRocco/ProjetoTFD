import argparse
import subprocess
import sys

def start_network(num_nodes, total_epochs, delta, base_port, start_time):
    """
    Launches each node as a separate process.
    """
    ports = [base_port + i for i in range(num_nodes)]  # Generate a list of ports for nodes

    # Start each node process
    for i in range(num_nodes):
        node_port = ports[i]
        port_list = ",".join(map(str, ports))  # Ports to pass to each node
        if sys.platform == "win32":
            subprocess.Popen(
                ["python", "node_script.py", str(i), str(num_nodes), str(total_epochs), str(delta), str(node_port), port_list, str(start_time)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            subprocess.Popen(
                ["python3", "node_script.py", str(i), str(num_nodes), str(total_epochs), str(delta), str(node_port), port_list, str(start_time)],
            )

    print("All nodes are started!")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run the Streamlet Protocol with customizable parameters.")
    parser.add_argument("--num_nodes", type=int, default=5, help="The number of nodes in the network.")
    parser.add_argument("--total_epochs", type=int, default=10, help="The total number of epochs to run.")
    parser.add_argument("--delta", type=int, default=2, help="The network delay parameter (∆).")
    parser.add_argument("--start_time", type=str, default="00:00", help="The start time in 24-hour format (HH:MM).")
    parser.add_argument("--base_port", type=int, default=5000, help="The starting port number for nodes.")

    args = parser.parse_args()

    num_nodes = args.num_nodes
    total_epochs = args.total_epochs
    delta = args.delta
    start_time = args.start_time
    base_port = args.base_port

    print(f"Starting Streamlet Protocol with {num_nodes} nodes and {total_epochs} epochs.")

    # Start the network
    start_network(num_nodes, total_epochs, delta, base_port, start_time)

if __name__ == "__main__":
    main()
