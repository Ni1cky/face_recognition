import sys
import PIL
from PIL import Image
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from time import sleep
import os
import face_recognition


def except_hook(cls, ex, traceback):
    sys.__excepthook__(cls, ex, traceback)
    if os.path.exists("temp.jpg"):
        os.remove("temp.jpg")


sys.excepthook = except_hook


def load_all_photos():
    global all_photos
    height = 0
    while len(all_photos) != person_photos_count:
        driver.execute_script(f"window.scrollTo(0, {1080 * height})")
        all_photos = driver.find_elements(by=By.CLASS_NAME, value="photos_row ")
        height += 1
    driver.execute_script("window.scrollTo(0, 0)")


def save_parced_pic(photo_link: str):
    time_to_sleep = 1
    while 2 + 2 == 4:
        try:
            pic = requests.get(photo_link)
            break
        except:
            sleep(time_to_sleep)
            time_to_sleep += 1
    pic_file = open("temp.jpg", "wb")
    pic_file.write(pic.content)
    pic_file.close()


def save_progress(pers_id=None, photo_ind=None):
    with open("last_saved.txt", "w") as progress_file:
        progress_file.write(f"id: {pers_id if pers_id else person_id}\nphoto_index: {photo_ind if photo_ind else photo_index}")


def find_and_save_faces(person_photos_path, ind):
    try:
        pic = face_recognition.load_image_file("temp.jpg")
    except PIL.UnidentifiedImageError as ex:
        print(f"Картинка - кака; Ошибка: {ex}")
        os.remove("temp.jpg")
        return ind

    for face in face_recognition.face_locations(pic, model="hog"):
        top, right, bottom, left = face
        the_face = pic[top:bottom, left:right]

        the_face = Image.fromarray(the_face)
        the_face.save("temp.jpg")
        the_face = face_recognition.load_image_file("temp.jpg")

        face_encoding = face_recognition.face_encodings(the_face)
        if len(face_encoding) > 0:
            encodings_values = face_encoding[0]
            Image.fromarray(the_face).save(f"{person_photos_path}/{ind}.jpg")
            encodings_save = open(f"{person_photos_path}/{ind}.txt", "w")
            encodings_save.write(str(encodings_values))
            encodings_save.close()
            ind += 1
            global faces_parced
            faces_parced += 1
    os.remove("temp.jpg")
    save_progress()
    return ind


def reload():
    global driver
    print("_______\nПерезапускаемся...")
    driver.close()
    print("Закрылся первый браузер.")
    driver.quit()
    print("Вышли.")
    print("Пытаемся открыть новый...")
    driver = webdriver.Firefox(executable_path="geckodriver-v0.30.0-linux64/geckodriver")
    print("Открыто!")
    driver.maximize_window()
    global wait
    wait = WebDriverWait(driver, 20)
    print("Продолжаем работу...\n_______")


last_saved_person_id = -1
last_saved_photo_index = -1
if os.path.exists("last_saved.txt"):
    save_file = open("last_saved.txt", "r")
    lines = save_file.readlines()
    last_saved_person_id = int(lines[0].split()[1])
    last_saved_photo_index = int(lines[1].split()[1])


max_iteration = 666
only_for_authorized = list()
photos_parced = 0
faces_parced = 0

driver = webdriver.Firefox(executable_path="geckodriver-v0.30.0-linux64/geckodriver")
driver.maximize_window()
wait = WebDriverWait(driver, 20)

for person_id in range(1, max_iteration + 1):
    if person_id < last_saved_person_id:
        continue
    if person_id % 10 == 0:
        reload()
    person_url = f"https://vk.com/photos{person_id}"
    print(f"#{person_id} id'шник пошёл.")
    driver.get(person_url)
    all_photos = driver.find_elements(by=By.CLASS_NAME, value="photos_row ")
    if len(all_photos) == 0:
        try:
            label = driver.find_element(by=By.CLASS_NAME, value="profile_deleted_text").text
            if label == "Страница доступна только авторизованным пользователям.":
                only_for_authorized.append(person_url)
                print("-Только для авторизованных...\n")
                print("_" * 33)
                continue
        except:
            print("-Мёртвый...\n")
            print("_" * 33)
            continue
        print("-Мёртвый...\n")
        print("_" * 33)
        continue
    person_photos_count = int(driver.find_element(by=By.CLASS_NAME, value="ui_crumb_count").text.replace(" ", "").replace(",", ""))
    print(f"Всего фоток: {[person_photos_count]}")
    load_all_photos()

    directory_for_saves = f"saved/{driver.find_element(by=By.CLASS_NAME, value='ui_crumb').text}_id{person_id}"
    if not os.path.exists("saved/"):
        os.mkdir("saved/")
    if not os.path.exists(directory_for_saves):
        os.mkdir(directory_for_saves)
    person_faces_count = 0

    for photo_index in range(person_photos_count):
        if photo_index <= last_saved_photo_index:
            continue
        if photo_index % 100 == 0:
            print(f"{photo_index} фотографий обработано....")
            reload()
            driver.get(person_url)
            load_all_photos()
        wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "TopHomeLink")))
        all_photos[photo_index].click()
        try:
            wait.until(ec.element_to_be_clickable((By.ID, "pv_author_name")))
        except:
            # os.remove(directory_for_saves)
            # person_id -= 1
            reload()
            driver.get(person_url)
            load_all_photos()
            photo_index -= 1
            print("Всё путём!")
            continue
        # wait.until(ec.element_to_be_clickable((By.ID, "pv_author_name")))
        photo = driver.find_element(by=By.ID, value="pv_photo")
        link = photo.find_element_by_tag_name("img").get_attribute("src")

        photos_parced += 1
        save_parced_pic(link)
        person_faces_count = find_and_save_faces(directory_for_saves, person_faces_count)
        close_btn = driver.find_element(by=By.CLASS_NAME, value="pv_close_btn")
        close_btn.click()
        # driver.find_element(by=By.CLASS_NAME, value="pv_close_btn").click()
    file_with_link = open(f"{directory_for_saves}/link.txt", "w")
    file_with_link.write(f"https://vk.com/id{person_id}")
    file_with_link.close()
    print("_" * 33)

print(f"\n\nФоток спарсено: {photos_parced}\nИз них лиц: {faces_parced}\n")
print(f"Закрытых аккаунтов: {len(only_for_authorized)}")
