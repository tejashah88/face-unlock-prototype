import face_recognition
import cv2
from multiprocessing import Process, Manager, cpu_count, set_start_method
import time
import numpy
import threading
import platform

# Source: https://github.com/ageitgey/face_recognition/blob/master/examples/facerec_from_webcam_multiprocessing.py

# This is a little bit complicated (but fast) example of running face recognition on live video from your webcam.
# This example is using multiprocess.

# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.
# OpenCV is *not* required to use the face_recognition library. It's only required if you want to run this
# specific demo. If you have trouble installing it, try any of the other demos that don't require it instead.


# Get next worker's id
def next_id(current_id, worker_num):
    if current_id == worker_num:
        return 1
    else:
        return current_id + 1


# Get previous worker's id
def prev_id(current_id, worker_num):
    if current_id == 1:
        return worker_num
    else:
        return current_id - 1


# A subprocess use to capture frames.
def capture(read_frame_list, Global, worker_num):
    # Get a reference to webcam #0 (the default one)
    video_capture = cv2.VideoCapture(0)
    # video_capture.set(3, 640)  # Width of the frames in the video stream.
    # video_capture.set(4, 480)  # Height of the frames in the video stream.
    # video_capture.set(5, 30) # Frame rate.
    print("Width: %d, Height: %d, FPS: %d" % (video_capture.get(3), video_capture.get(4), video_capture.get(5)))

    while not Global.is_exit:
        # If it's time to read a frame
        if Global.buff_num != next_id(Global.read_num, worker_num):
            # Grab a single frame of video
            ret, frame = video_capture.read()
            read_frame_list[Global.buff_num] = frame
            Global.buff_num = next_id(Global.buff_num, worker_num)
        else:
            time.sleep(0.01)

    # Release webcam
    video_capture.release()


# Many subprocess use to process frames.
def process(worker_id, read_frame_list, write_frame_list, Global, worker_num):
    known_face_encodings = Global.known_face_encodings
    known_face_names = Global.known_face_names
    while not Global.is_exit:

        # Wait to read
        while Global.read_num != worker_id or Global.read_num != prev_id(Global.buff_num, worker_num):
            if Global.is_exit:
                break

            time.sleep(0.01)

        # Delay to make the video look smoother
        time.sleep(Global.frame_delay)

        # Read a single frame from frame list
        frame_process = read_frame_list[worker_id]

        # Expect next worker to read frame
        Global.read_num = next_id(Global.read_num, worker_num)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame_process[:, :, ::-1]

        # Find all the faces and face encodings in the frame of video, cost most time
        face_locations = face_recognition.face_locations(rgb_frame)
        print("Found {} faces in image.".format(len(face_locations)))
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Loop through each face in this frame of video
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)

            name = "Unknown"

            # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            print(f"ID {worker_id}: Found {name}'s face at box coordinates {(left, top)}' to {(right, bottom)}")

        # Wait to write
        while Global.write_num != worker_id:
            time.sleep(0.01)

        # Send frame to global
        write_frame_list[worker_id] = frame_process

        # Expect next worker to write frame
        Global.write_num = next_id(Global.write_num, worker_num)


if __name__ == '__main__':
    faces = [
        { 'name': 'Tejas Shah', 'path': 'known-people/tejas.png' }
    ]

    # Fix Bug on MacOS
    if platform.system() == 'Darwin':
        set_start_method('forkserver')

    # Global variables
    Global = Manager().Namespace()
    Global.buff_num = 1
    Global.read_num = 1
    Global.write_num = 1
    Global.frame_delay = 0
    Global.is_exit = False
    read_frame_list = Manager().dict()
    write_frame_list = Manager().dict()

    # Number of workers (subprocess use to process frames)
    if cpu_count() > 2:
        worker_num = cpu_count() - 1  # 1 for capturing frames
    else:
        worker_num = 2

    # Subprocess list
    p = []

    # Create a thread to capture frames (if uses subprocess, it will crash on Mac)
    p.append(threading.Thread(target=capture, args=(read_frame_list, Global, worker_num,)))
    p[0].start()

    # For all images of known people, load each one and learn how to recognize it.
    known_face_encodings = []
    known_face_names = []
    for face in faces:
        person_image = face_recognition.load_image_file(face['path'])
        person_face_encodings = face_recognition.face_encodings(person_image, num_jitters=10)

        if len(person_face_encodings) > 0:
            person_face_encoding = person_face_encodings[0]

            known_face_encodings += [person_face_encoding]
            known_face_names += [face['name']]
        else:
            print(f"Warning: Did not find {face['name']}'s face from {face['path']}")

    # Create arrays of known face encodings and their names
    Global.known_face_encodings = known_face_encodings
    Global.known_face_names = known_face_names

    # Create workers
    for worker_id in range(1, worker_num + 1):
        p.append(Process(target=process, args=(worker_id, read_frame_list, write_frame_list, Global, worker_num,)))
        p[worker_id].start()

    # Start to show video
    last_num = 1
    fps_list = []
    tmp_time = time.time()
    while not Global.is_exit:
        try:
            while Global.write_num != last_num:
                last_num = int(Global.write_num)

                # Calculate fps
                delay = time.time() - tmp_time
                tmp_time = time.time()
                fps_list.append(delay)
                if len(fps_list) > 5 * worker_num:
                    fps_list.pop(0)
                fps = len(fps_list) / numpy.sum(fps_list)
                print("fps: %.2f" % fps)

                # Calculate frame delay, in order to make the video look smoother.
                # When fps is higher, should use a smaller ratio, or fps will be limited in a lower value.
                # Larger ratio can make the video look smoother, but fps will hard to become higher.
                # Smaller ratio can make fps higher, but the video looks not too smoother.
                # The ratios below are tested many times.
                if fps < 6:
                    Global.frame_delay = (1 / fps) * 0.75
                elif fps < 20:
                    Global.frame_delay = (1 / fps) * 0.5
                elif fps < 30:
                    Global.frame_delay = (1 / fps) * 0.25
                else:
                    Global.frame_delay = 0

            time.sleep(0.01)
        except KeyboardInterrupt:
            Global.is_exit = True
            break

    # Quit
    cv2.destroyAllWindows()