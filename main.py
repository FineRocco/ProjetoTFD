import argparse
import socket
import subprocess
import sys
import os
import time
from message import Message

def start_network(num_nodes, total_epochs, delta, base_port):
    """
    Launches each node as a separate process and waits for them to be ready.
    """
    ready_port = 6000  # Port for readiness signaling
    ports = [base_port + i for i in range(num_nodes)]  # Generate a list of ports for nodes

    # Start each node process in a new terminal
    for i in range(num_nodes):
        node_port = ports[i]
        port_list = ",".join(map(str, ports))  # Ports to pass to each node
        if sys.platform == "win32":
            process = subprocess.Popen(
                ["python", "node_script.py", str(i), str(num_nodes), str(total_epochs), str(delta), str(node_port), port_list],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

    # Listen for readiness signals from nodes
    ready_count = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ready_socket:
        ready_socket.bind(('localhost', ready_port))
        ready_socket.listen(num_nodes)
        print("Waiting for nodes to be ready...")

        while ready_count < num_nodes:
            conn, _ = ready_socket.accept()
            with conn:
                data = conn.recv(1024)
                if data == b"READY":
                    ready_count += 1
                    print(f"Node {ready_count} is ready")

    print("All nodes are ready!")
    give_seed(ports)

def give_seed(ports):
    """
    Sends a seed to all nodes to synchronize random leader selection.
    """
    seed = "toleranciaedfaltadeintrusoes"
    seed_message = Message.create_seed_message(seed, -1)
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(('localhost', port))
                sock.sendall(seed_message.serialize())
                print(f"Sent SEED to Node at port {port}")
        except ConnectionRefusedError:
            print(f"Could not connect to Node at port {port} to send seed.")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run the Streamlet Protocol with customizable parameters.")
    parser.add_argument("--num_nodes", type=int, default=5, help="The number of nodes in the network.")
    parser.add_argument("--total_epochs", type=int, default=10, help="The total number of epochs to run.")
    parser.add_argument("--delta", type=int, default=2, help="The network delay parameter (∆).")

    args = parser.parse_args()

    num_nodes = args.num_nodes
    total_epochs = args.total_epochs
    delta = args.delta

    print(f"Starting Streamlet Protocol with {num_nodes} nodes and {total_epochs} epochs.")

    # Start the network
    start_network(num_nodes, total_epochs, delta, 5000)

if __name__ == "__main__":
    main()
