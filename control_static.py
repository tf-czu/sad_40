"""
    Testing control app
"""

from zmq_node import push_msg


def control_main():
    while True:
        label = input("Enter label: ")
        print(f"Sending: {label}")
        push_msg(label)

if __name__ == "__main__":
    control_main()