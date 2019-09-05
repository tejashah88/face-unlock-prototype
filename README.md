# face-unlock-prototype
Codebase for face recognition based door unlocking system.

# What's inside?
* `face_unlock_test.py` is the main demo script to run. It'll search for defined faces in the `known-people/` directory and only when it identifies that person for 5 seconds, will it trigger the relay.
* The `experiments/` folder contains a few scripts for testing the face recognition under various environments and configurations and the GrovePi relay. You should `cd` into that folder before trying to run any of the scripts.

## TODO
* Might want to look into KNN: https://github.com/ageitgey/face_recognition/blob/master/examples/face_recognition_knn.py
* MacOS or Linux Setup: https://gist.github.com/ageitgey/629d75c1baac34dfa5ca2a1928a7aeaf
* Raspi setup: https://gist.github.com/ageitgey/1ac8dbe8572f3f533df6269dab35df65