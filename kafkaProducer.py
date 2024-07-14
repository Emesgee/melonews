import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from confluent_kafka import Producer
from datetime import datetime, timezone

# Function to parse time from an element using the provided XPath
def parse_time(element):
    try:
        time_element = element.find_element(By.XPATH, './/span[@class="tgme_widget_message_meta"]/a/time')
        time_text = time_element.get_attribute('datetime')
        if time_text:
            print(f"Extracted time text: {time_text}")  # Debug print
            return datetime.fromisoformat(time_text.replace('Z', '+00:00'))
        else:
            print("Time attribute is empty.")
    except Exception as e:
        print(f"Error parsing time: {e}")
    return None

# Function to parse views from an element using XPath
def parse_views(element):
    try:
        views_element = element.find_element(By.XPATH, './/span[@class="tgme_widget_message_views"]')
        views_text = views_element.text
        if views_text:
            print(f"Extracted views text: {views_text}")  # Debug print
            return parse_views_text(views_text)
        else:
            print("Views attribute is empty.")
    except Exception as e:
        print(f"Error parsing views: {e}")
    return None

def parse_views_text(views_text):
    try:
        if 'K' in views_text:
            return int(float(views_text.replace('K', '').replace(' views', '').replace(',', '')) * 1000)
        elif 'M' in views_text:
            return int(float(views_text.replace('M', '').replace(' views', '').replace(',', '')) * 1000000)
        else:
            return int(views_text.replace(' views', '').replace(',', ''))
    except ValueError as e:
        print(f"Error parsing views: {e}")
        return None

def extract_video_links(element):
    video_links = []
    try:
        video_elements = element.find_elements(By.XPATH, './/video')
        for video in video_elements:
            video_src = video.get_attribute('src')
            if video_src:
                video_links.append(video_src)
    except Exception as e:
        print(f"Error extracting video links: {e}")
    return video_links

def extract_video_durations(element, class_name='message_video_duration'):
    durations = []
    try:
        duration_elements = element.find_elements(By.CLASS_NAME, class_name)
        for duration_element in duration_elements:
            duration_text = duration_element.text.strip()
            if duration_text:
                durations.append(duration_text)
    except Exception as e:
        print(f"Error extracting video durations: {e}")
    return durations

# Function to extract image links
def extract_image_links(element):
    image_links = []
    try:
        # Find all <a> elements
        a_elements = element.find_elements(By.XPATH, './/a')
        for a in a_elements:
            # Check if the href attribute contains "image"
            href = a.get_attribute('href')
            if href and 'image' in href:
                image_links.append(href)
    except Exception as e:
        print(f"Error extracting image links: {e}")
    return image_links

# Function to extract message text
def extract_message_text(element):
    try:
        message_text_element = element.find_element(By.CLASS_NAME, 'tgme_widget_message_text')
        return message_text_element.text
    except Exception as e:
        print(f"Error extracting message text: {e}")
        return ""

# Initialize WebDriver
driver = None
try:
    driver = webdriver.Chrome()
    url = "https://t.me/s/eyeonpal"
    #url = "https://t.me/s/MiddleEastEye_TG"
    #url = "https://t.me/s/QudsNen"
    driver.get(url)
except Exception as e:
    print(f"Error initializing WebDriver: {e}")

if driver:
    messages = []  # Move the messages list definition here
    try:
        # Scroll down until the end as fast as possible using scrollTo
        prev_page_height = driver.execute_script('return document.body.scrollHeight')

        while True:
            # Scroll to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            
            # Check if page height has changed
            current_page_height = driver.execute_script('return document.body.scrollHeight')
            if current_page_height == prev_page_height:
                break  # Break the loop if no new content is loaded
            prev_page_height = current_page_height

        # Scroll up 100 times
        for _ in range(3):
            # Scroll to the top of the page
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)  # Wait for content to load
            
            # Check if page has scrolled to the top
            current_scroll_position = driver.execute_script("return window.pageYOffset;")
            if current_scroll_position == 0:
                break  # Break the loop if scrolled to the top

        # Kafka producer configuration
        bootstrap_servers = '172.25.84.144:9092'  # Update with your Kafka broker(s)
        topic = 'eyesonpalestine'  # Update with your Kafka topic name

        # Create Kafka Producer instance
        producer = Producer({'bootstrap.servers': bootstrap_servers})

        # Locate message elements
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'tgme_widget_message_bubble'))
        )

        for element in elements:
            message_text = extract_message_text(element)
            message_time = parse_time(element)
            total_views = parse_views(element)
            video_links = extract_video_links(element)
            video_durations = extract_video_durations(element)
            image_links = extract_image_links(element)
            
            message_data = {
                'Time': message_time.isoformat() if message_time else None,
                'Total Views': total_views,
                'Message': message_text,
                'Video Links': '|'.join(video_links),
                'Video Durations': '|'.join(video_durations),
                'Image Links': '|'.join(image_links)
            }
            
            messages.append(message_data)
            
            try:
                # Serialize message to JSON and encode to bytes
                json_message = json.dumps(message_data).encode('utf-8')
                
                # Produce message to Kafka topic
                producer.produce(topic, value=json_message)
                producer.flush()  # Ensure message delivery
                print("Message sent to Kafka:", message_data)
            except Exception as e:
                print(f"Error sending message to Kafka: {e}")

        # Close the browser
        time.sleep(5)
        driver.quit()

    except Exception as e:
        print(f"Error: {e}")
        if driver:
            driver.quit()
        if producer:
            producer.flush()
            producer = None
