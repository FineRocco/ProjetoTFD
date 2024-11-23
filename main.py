import argparse
import socket
import subprocess
import sys
import os
import time
from message import Message


def start_network(num_nodes, total_epochs, delta, base_port, start_time):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    node_script_path = os.path.join(script_dir, 'node_script.py')

    ports = [base_port + i for i in range(num_nodes)]

    for i in range(num_nodes):
        node_port = ports[i]
        port_list = ",".join(map(str, ports))
        cmd = ["python3", node_script_path, str(i), str(num_nodes), str(total_epochs), str(delta),
               str(node_port), port_list, str(start_time)]
        command = ' '.join(cmd)

        if sys.platform == "darwin":  # macOS
            subprocess.Popen([
                'osascript', '-e',
                f'tell application "Terminal" to do script "cd {script_dir} && {command}"'
            ])
        elif sys.platform == "win32":  # Windows
            subprocess.Popen([
                "cmd", "/c", f"start cmd /k cd {script_dir} && {command}"
            ])
        else:  # Linux and others
            subprocess.Popen([
                "gnome-terminal", "--", "bash", "-c", f"cd {script_dir} && {command}; exec bash"
            ])

    print("All nodes are ready!")


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run the Streamlet Protocol with customizable parameters.")
    parser.add_argument("--num_nodes", type=int, default=5, help="The number of nodes in the network.")
    parser.add_argument("--total_epochs", type=int, default=2, help="The total number of epochs to run.")
    parser.add_argument("--delta", type=int, default=2, help="The network delay parameter (∆).")
    parser.add_argument("--start_time", type=str, default="00:00", help="The start time in 24-hour format (HH:MM).")

    args = parser.parse_args()

    num_nodes = args.num_nodes
    total_epochs = args.total_epochs
    delta = args.delta
    start_time = args.start_time

    print(f"Starting Streamlet Protocol with {num_nodes} nodes and {total_epochs} epochs.")

    # Start the network
    start_network(num_nodes, total_epochs, delta, 5000, start_time)


if __name__ == "__main__":
    main()
