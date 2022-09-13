"""
    Testing control app
"""

import time
from zmq_node import push_msg, ZmqPull
from threading import Thread


def control_main():
    prev_images = ["basler_prev", "arecont_prev", "rs_prev", "depth_prev"]
    server = ZmqPull()
    thread = Thread(target=server.pull_msg)
    first_run = True
    while True:
        label = input("Enter label: ")
        print(f"Sending: {label}")
        if first_run:
            first_run = False
        else:
            print(thread.join(2))
            time.sleep(2)
            thread = Thread(target=server.pull_msg)
            server.clear_images()

        thread.start()
        push_msg(label)

        for ii in range(10):
            for prev_name in prev_images:
                data = getattr(server, prev_name)
                if data is not None:
                    print(ii, prev_name, len(data))
                    if prev_name == "depth_prev":
                        with open("depth_im.jpg", "wb") as f:
                            f.write(data)
            time.sleep(0.5)

if __name__ == "__main__":
    control_main()
