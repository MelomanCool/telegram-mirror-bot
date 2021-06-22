import statistics

import face_recognition


class NoFaceError(RuntimeError):
    pass


def find_face_center(image_file):
    image = face_recognition.load_image_file(image_file)
    image_file.seek(0)

    face_landmarks_list = face_recognition.face_landmarks(image)

    if not face_landmarks_list:
        raise NoFaceError

    face_landmarks = face_landmarks_list[0]
    nose_landmarks = face_landmarks['nose_bridge']

    mean_x = statistics.mean(xy[0] for xy in nose_landmarks)
    width = image.shape[1]
    return mean_x / width


if __name__ == '__main__':
    image_file = open('photo.jpg', mode='rb')
    x = find_face_center(image_file)
    print(x)
