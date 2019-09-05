from utils.is_on_raspi import is_raspberry_pi

if not is_raspberry_pi():
    print('Warning: Only Raspberry Pi is supported!')
    exit(-1)

import os
from collections import namedtuple

import face_recognition
import numpy as np
import picamera
import grovepi

from utils.progress_print import progress_print

class Person:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.score = 0
        self.MAX_SCORE = 10

    @property
    def verified(self):
        return self.score >= self.MAX_SCORE

    def add_point(self):
        if self.score < self.MAX_SCORE:
            self.score += 1

    def reset(self):
        self.score = 0

class PersonDB:
    def __init__(self):
        self.db = {}

    def add_person(self, person):
        if person.name not in self.db:
            self.db[person.name] = person

    def remove_person(self, person):
        if person.name in self.db:
            del self.db[person.name]

    def get_person(self, name):
        if name in self.db:
            return self.db[name]
        else:
            return None

    def get_all_people(self):
        return list(self.db.values())

    def set_person(self, name, person):
        if name in self.db:
            self.db[name] = person

RELAY_PIN = 4
relay_state = 0
grovepi.pinMode(RELAY_PIN, 'OUTPUT')

camera = picamera.PiCamera()
IMG_WIDTH, IMG_HEIGHT = (320, 240)
camera.resolution = (IMG_WIDTH, IMG_HEIGHT)

KNOWN_PEOPLE_DIR = 'known-people'
UNKNOWN_NAME = 'unknown'
PEOPLE_DB = PersonDB()

@progress_print(msg='Loading people database')
def load_people_db():
    # Load the people DB with known faces.
    for file in os.listdir(KNOWN_PEOPLE_DIR):
        person = Person(name=file.split('.')[0], path=KNOWN_PEOPLE_DIR + file)
        PEOPLE_DB.add_person(person)

@progress_print(msg='Capturing image')
def capture_image():
    # Grab a single frame of video from the RPi camera as a numpy array.
    global IMG_WIDTH, IMG_HEIGHT
    output = np.empty((IMG_HEIGHT, IMG_WIDTH, 3), dtype=np.uint8)
    camera.capture(output, format='rgb')
    return output

@progress_print(msg='Unlocking door')
def unlock_door(should_unlock):
    # Toggle the relay state based on the value of the input parameter.
    try:
        new_relay_state = int(bool(should_unlock))
        if relay_state != new_relay_state:
            relay_state = new_relay_state
            grovepi.digitalWrite(RELAY_PIN, relay_state)
    except KeyboardInterrupt:
        grovepi.digitalWrite(RELAY_PIN, 0)
        break
    except IOError as ioex:
        print(f'Error: {ex}')

@progress_print(msg='Learning known faces')
def train_faces_single(face_dataset):
    # For all images of known people, load each one and learn how to recognize it.
    known_face_encodings = []
    known_face_names = []
    for face in face_dataset:
        person_image = face_recognition.load_image_file(face.path)
        person_face_encodings = face_recognition.face_encodings(person_image)

        if len(person_face_encodings) > 0:
            person_face_encoding = person_face_encodings[0]

            known_face_encodings += [person_face_encoding]
            known_face_names += [face.name]
        else:
            print(f"Warning: Did not find {face.name}'s face from {face.path}")

    return known_face_names, known_face_encodings

@progress_print(msg='Searching for known faces')
def detect_faces(input_img):
    # Find all the faces and face encodings in the current frame of video.
    face_locations = face_recognition.face_locations(input_img)
    face_encodings = face_recognition.face_encodings(input_img, face_locations)
    return face_locations, face_encodings

if __name__ == '__main__':
    load_people_db()
    known_face_names, known_face_encodings = train_faces_single(ALL_FACES)

    is_running = True
    found_person = None

    while is_running:
        try:
            frame = capture_image()
            face_locations, face_encodings = detect_faces(frame)

            # Loop over each face found in the frame to see if it's someone we know.
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)

                name = UNKNOWN_NAME

                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                if name != UNKNOWN_NAME
                    if found_person is None:
                        found_person = PEOPLE_DB.get_person(name)
                    found_person.add_point()
                else:
                    if found_person is not None:
                        found_person = None

                print(f"Found {name}'s face at box coordinates {(left, top)}' to {(right, bottom)}")

                if found_person is not None:
                    print(f'Score for found person is {found_person.score} / {found_person.MAX_SCORE}')

                    if found_person.verified:
                        unlock_door(True)
                else:
                    unlock_door(False)

        except KeyboardInterrupt:
            is_running = False
            camera.close()
        except Exception as ex:
            print(f'An exception occurred during the loop: {ex}')
            is_running = False
            camera.close()
