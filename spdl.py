import re
import time
import os
import yt_dlp
from wakepy import keep  # Importar wakepy para mantener el sistema activo
from difflib import SequenceMatcher
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import tkinter as tk
from tkinter import ttk

def obtenerLista(playlist_text):
    # Your existing code, replace playlist_text assignment with the parameter
    # Configuración de Selenium y opciones de descarga
    dir_path = os.getcwd()
    op = webdriver.ChromeOptions()
    op.add_experimental_option('excludeSwitches', ['enable-logging'], )
    op.enable_downloads = True

    op.add_experimental_option("detach", True)
    op.add_experimental_option("prefs", {
        "download.default_directory": str(dir_path),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    # Inicializar Selenium
    driver = webdriver.Chrome(options=op)
    driver.maximize_window()

    # Espera explícita
    wait = WebDriverWait(driver, 10, poll_frequency=1, ignored_exceptions=[
        ElementNotVisibleException, ElementNotSelectableException])
    # Abrir la página https://www.spotify-backup.com/
    driver.get("https://www.spotify-backup.com/")

    # Use the playlist_text parameter
    playlist_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="playlist_id"]')))
    ActionChains(driver).move_to_element(playlist_input).click(playlist_input).send_keys(
    playlist_text).perform()

    check_terms_path = "/html/body/div[2]/div[1]/form/p/input"
    check_terms = wait.until(EC.element_to_be_clickable((By.XPATH, check_terms_path)))

    ActionChains(driver).move_to_element(check_terms).click(check_terms).perform()

    download_path = "/html/body/div[2]/div[1]/form/input"
    download_button = wait.until(EC.element_to_be_clickable((By.XPATH, download_path)))

    ActionChains(driver).move_to_element(download_button).click(download_button).perform()

    time.sleep(5)
    # Hacer zoom a 70%
    driver.execute_script("document.body.style.zoom='70%'")

    # Espera un tiempo para visualizar los cambios
    time.sleep(5)

    download_path_list = "/html/body/div[2]/div[1]/div[2]/a"
    download_button_list = wait.until(EC.element_to_be_clickable((By.XPATH, download_path_list)))
    ActionChains(driver).move_to_element(download_button_list).click(download_button_list).perform()
    time.sleep(5)

    driver.quit()

# Your existing regex patterns
regex_comillas_primero = r'^[^,]+,"([^"]*)",([^,]+),'  # Canción entre comillas, artista sin comillas
regex_comas_primero = r'^[^,]+,([^,]+),"([^"]*)",'  # Canción sin comillas, artista entre comillas
regex_comillas_ambos = r'^[^,]+,"([^"]*)","([^"]*)",'  # Canción entre comillas, artista también entre comillas
regex_sin_comillas = r'^[^,]+,([^,]+),([^,]+),'  # Canción sin comillas, artista sin comillas (solo separados por comas)

def get_latest_csv():
    files = [f for f in os.listdir() if f.endswith('.csv')]
    if files:
        latest_file = max(files, key=os.path.getctime)
        return latest_file
    return None

def process_csv_to_txt():
    # Your existing code
    csv_file = get_latest_csv()
    if not csv_file:
        print("No se encontró ningún archivo CSV.")
        return

    with open(csv_file, 'r', encoding='utf-8') as file, \
         open('result.txt', 'w', encoding='utf-8') as result_file, \
         open('errores.txt', 'w', encoding='utf-8') as error_file:
        
        lines = file.readlines()
        for index, line in enumerate(lines, start=1):
            match_comillas_ambos = re.search(regex_comillas_ambos, line)
            match_comillas = re.search(regex_comillas_primero, line)
            match_comas = re.search(regex_comas_primero, line)
            match_sin_comillas = re.search(regex_sin_comillas, line)

            if match_comillas_ambos:
                song_name = match_comillas_ambos.group(1)
                artist = match_comillas_ambos.group(2)
                result_file.write(f"{song_name}, {artist}\n")
            elif match_comillas:
                song_name = match_comillas.group(1)
                artist = match_comillas.group(2)
                result_file.write(f"{song_name}, {artist}\n")
            elif match_comas:
                song_name = match_comas.group(1)
                artist = match_comas.group(2)
                result_file.write(f"{song_name}, {artist}\n")
            elif match_sin_comillas:
                song_name = match_sin_comillas.group(1)
                artist = match_sin_comillas.group(2)
                result_file.write(f"{song_name}, {artist}\n")
            else:
                error_file.write(f"Línea {index}: No se pudo procesar -> {line}\n")
                print(f"Línea {index}: No se pudo procesar -> {line}")

    print("Proceso completado. Revisa 'result.txt' para los resultados exitosos y 'errores.txt' para los fallos.")

def downloadSongs(progress_var, status_label, progress_bar):
    # Your existing code, with modifications to update progress
    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    def download_youtube_video(url, output_path="downloads/"):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{output_path}%(title)s.%(ext)s',  # Ruta y formato de salida
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"Descargado: {url}")
            return True
        except Exception as e:
            print(f"Error al descargar {url}: {e}")
            return False

    dir_path = os.getcwd()
    op = webdriver.ChromeOptions()
    op.add_experimental_option('excludeSwitches', ['enable-logging'], )
    op.enable_downloads = True
    op.add_experimental_option("detach", True)
    op.add_experimental_option("prefs", {
      "download.default_directory": str(dir_path),
      "download.prompt_for_download": False,
      "download.directory_upgrade": True,
      "safebrowsing.enabled": True
    })

    with keep.running():
        driver = webdriver.Chrome(options=op)
        driver.maximize_window()

        wait = WebDriverWait(driver, 10, poll_frequency=1, ignored_exceptions=[
            ElementNotVisibleException, ElementNotSelectableException])

        with open('result.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()

        total_songs = len(lines)

        with open('errores.txt', 'w', encoding='utf-8') as error_file:
            for index, line in enumerate(lines):
                line = line.strip()
                if ',' in line:
                    song_name, artist = line.split(',', 1)
                    search_query = f"{song_name.strip()} {artist.strip()}"
                    print(f"Buscando en YouTube: {search_query}")
                    
                    driver.get(f'https://www.youtube.com/results?search_query={search_query}')
                    time.sleep(2)
                    
                    videos = driver.find_elements(By.XPATH, "//a[@id='video-title']")
                    
                    for video in videos:
                        video_title = video.get_attribute("title")
                        video_url = video.get_attribute("href")
                        
                        similitud = similar(video_title, f"{artist.strip()} {song_name.strip()}")
                        
                        print(f"Video encontrado: {video_title}")
                        print(f"URL: {video_url}")
                        print(f"Similitud: {similitud * 100:.2f}%\n")
                        
                        if similitud > 0.7:
                            print(f"¡Match encontrado! Video: {video_title} | URL: {video_url}\n")
                            success = download_youtube_video(video_url)
                            if success:
                                break
                            else:
                                error_file.write(f"Fallo al descargar: {search_query} - {video_url}\n")
                    else:
                        print(f"No se encontró un video para: {search_query}")
                        error_file.write(f"Fallo al encontrar video: {search_query}\n")

                # Update progress bar and status label
                progress = ((index + 1) / total_songs) * 100
                progress_var.set(progress)
                status_label.config(text=f"Downloading song {index + 1} of {total_songs}")

                # Update the GUI elements
                status_label.update()
                progress_bar.update()

def run_download_process(playlist_url, progress_var, status_label, start_button, progress_bar):
    try:
        obtenerLista(playlist_url)
        process_csv_to_txt()
        downloadSongs(progress_var, status_label, progress_bar)
        status_label.config(text="Download completed.")
    except Exception as e:
        status_label.config(text=f"Error: {e}")
    finally:
        start_button.config(state='normal')

def main():
    root = tk.Tk()
    root.title("Spotify Playlist Downloader")
    root.geometry("500x200")

    # Playlist URL Entry
    tk.Label(root, text="Playlist URL:").pack(pady=5)
    playlist_entry = tk.Entry(root, width=60)
    playlist_entry.pack(pady=5)

    # Progress Bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(fill=tk.X, padx=20, pady=10)

    # Status Label
    status_label = tk.Label(root, text="Ready")
    status_label.pack()

    # Start Button
    def start_download():
        playlist_url = playlist_entry.get()
        if playlist_url:
            start_button.config(state='disabled')
            status_label.config(text="Starting download...")
            threading.Thread(target=run_download_process, args=(playlist_url, progress_var, status_label, start_button, progress_bar)).start()
        else:
            status_label.config(text="Please enter a playlist URL.")

    start_button = tk.Button(root, text="Start Download", command=start_download)
    start_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
