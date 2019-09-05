# This is a demo of running face recognition on a Raspberry Pi.
# This program will print out the names of anyone it recognizes to the console.

# To run this, you need a Raspberry Pi 2 (or greater) with face_recognition and
# the picamera[array] module installed.
# You can follow this installation instructions to get your RPi set up:
# https://gist.github.com/ageitgey/1ac8dbe8572f3f533df6269dab35df65

from is_on_raspi import is_raspberry_pi

if not is_raspberry_pi():
    print('Warning: Only Raspberry Pi is supported!')
    exit(-1)


import face_recognition
import picamera
import numpy as np

# Get a reference to the Raspberry Pi camera.
# If this fails, make sure you have a camera connected to the RPi and that you
# enabled your camera in raspi-config and rebooted first.
camera = picamera.PiCamera()

# Various Pi Camera resolutions: https://picamera.readthedocs.io/en/release-1.12/fov.html
camera.resolution = (320, 240)
output = np.empty((240, 320, 3), dtype=np.uint8)

faces = [
    { 'name': 'Tejas Shah', 'path': '../known-people/tejas.png' }
]

# For all images of known people, load each one and learn how to recognize it.
known_face_encodings = []
known_face_names = []
print('Loading known face image(s)')
for face in faces:
    person_image = face_recognition.load_image_file(face['path'])
    person_face_encodings = face_recognition.face_encodings(person_image)

    if len(person_face_encodings) > 0:
        person_face_encoding = person_face_encodings[0]

        known_face_encodings += [person_face_encoding]
        known_face_names += [face['name']]
    else:
        print(f"Warning: Did not find {face['name']}'s face from {face['path']}")

# Initialize some variables
face_locations = []
face_encodings = []

while True:
    print('Capturing image.')
    # Grab a single frame of video from the RPi camera as a numpy array
    camera.capture(output, format='rgb')

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(output)
    print(f'Found {len(face_locations)} faces in image.')
    face_encodings = face_recognition.face_encodings(output, face_locations)

    # Loop over each face found in the frame to see if it's someone we know.
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)

        name = 'Unknown'

        # If a match was found in known_face_encodings, just use the first one.
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

        print(f"Found {name}'s face at box coordinates {(left, top)}' to {(right, bottom)}")
