import json
import pandas as pd
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
from collections import Counter
import requests

def process_text(input_path, output_path):
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nlp = spacy.load("en_core_web_sm")

    df = pd.read_json(input_path)
    # Convert column names to lowercase
    df.columns = map(str.lower, df.columns)
    print(df.columns)
   
    def clean_text_and_extract_entities(text):
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word.lower() for word in tokens if word.lower() not in stop_words]
        cleaned_text = ' '.join(filtered_tokens)
        doc = nlp(cleaned_text)
        entities = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC', 'ORG']]
        return ', '.join(entities)  # Return as a single string

    df['cleaned_text_entities'] = df['messages'].apply(clean_text_and_extract_entities)

    text = df['messages']
    clean_text = []
    for txt in text:
        tokens = word_tokenize(txt)
        relevant_tags = ['NN', 'NNS', 'NNP', 'NNPS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']
        tagged_tokens = nltk.pos_tag(tokens)
        filtered_tokens = [word.lower() for word, tag in tagged_tokens if word.lower() not in stopwords.words('english') and tag in relevant_tags]
        fdist = FreqDist(filtered_tokens)
        most_common_words = fdist.most_common()
        title_words = [word for word, _ in most_common_words if len(word) > 2]
        title = ' '.join(title_words[:3])
        clean_text.append(title)
    df['title'] = clean_text

    cities_by_country = {}
    for place_list in df['cleaned_text_entities']:
        doc = nlp(place_list)
        cities = []
        countries = []
        for ent in doc.ents:
            if ent.label_ == 'GPE':
                if ent.text.lower() not in cities_by_country:
                    cities_by_country[ent.text.lower()] = {"cities": [], "countries": []}
                if ent.text.capitalize() not in cities:
                    if ent.text.capitalize() in place_list.split(', ') and place_list.split(', ').index(ent.text.capitalize()) == 0:
                        cities.append(ent.text.capitalize())
                    else:
                        countries.append(ent.text.capitalize())
        for country in countries:
            if country not in cities_by_country:
                cities_by_country[country] = {"cities": [], "countries": []}
            cities_by_country[country]["countries"].extend(countries)
            cities_by_country[country]["cities"].extend(cities)

    for key in cities_by_country:
        cities_by_country[key]["cities"] = list(set(cities_by_country[key]["cities"]))
        cities_by_country[key]["countries"] = list(set(cities_by_country[key]["countries"]))
    cityList = []
    for city, country in cities_by_country.items():
        cityList.append(city)

    def find_city(text, cities):
        for city in cities:
            if city.lower() in text.lower():
                return city
        return None

    df['matched_city'] = df['cleaned_text_entities'].apply(lambda x: find_city(x, cityList))
    df = df.dropna(subset=['matched_city'])

    def combine_text(row):
        return f"{row['cleaned_text_entities']} {row['title']} {row['matched_city']} {row['messages']}"

    df['combined_text'] = df.apply(combine_text, axis=1)

    def summarize_text(text, max_sentences=8):
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        sentence_scores = {sent: sum(token.vector_norm for token in nlp(sent)) for sent in sentences}
        sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
        summary = ' '.join(sorted_sentences[:max_sentences])
        return summary

    summarized = []
    text = df['combined_text']
    for i in text:
        summary = summarize_text(i)
        summarized.append(summary)
    df['summarized'] = summarized

    df['matched_city2'] = df['summarized'].apply(lambda x: find_city(x, cityList))

    def extract_keywords(text, num_keywords=3):
        doc = nlp(text)
        other_cities = []
        for ent in doc.ents:
            if ent.label_ == 'GPE':
                other_cities.append(ent.text)
        if other_cities:
            return other_cities[:num_keywords]
        else:
            keywords = [token.text for token in doc if token.is_stop == False and token.is_punct == False and (token.pos_ == 'NOUN' or token.pos_ == 'PROPN')]
            keyword_freq = Counter(keywords)
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
            top_keywords = [keyword[0] for keyword in sorted_keywords[:num_keywords]]
            return top_keywords

    cityKeys = []
    text = df['combined_text']
    for i in text:
        keywords = extract_keywords(i)
        cityKeys.append(keywords[0])

    df['city_result'] = cityKeys

    api_key = "AIzaSyBbhiSukoQi6jLozUSGjpt-8wEqf2f2_0k"
    latitudes = []
    longitudes = []

    for city in df['city_result'].to_list():
        city = city.strip().replace(" ", "+")
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={api_key}"
        try:
            response = requests.get(url)
            data = response.json()
            if data['status'] == 'OK':
                lat = data['results'][0]['geometry']['location']['lat']
                lon = data['results'][0]['geometry']['location']['lng']
                latitudes.append(lat)
                longitudes.append(lon)
            else:
                print(f"Error: {data['status']} for city: {city}")
                latitudes.append(None)
                longitudes.append(None)
        except Exception as e:
            print(f"Error fetching data for city: {city}, Error: {e}")
            latitudes.append(None)
            longitudes.append(None)

    df['latitude'] = latitudes
    df['longitude'] = longitudes
    df = df.dropna(subset=['latitude', 'longitude'])
    df['title'] = df['title'].apply(lambda x: x.title())

    # Save the processed data to a new JSON file
    df.to_json(output_path, orient='records', lines=False, force_ascii=False)
   
    print(f"Processed data saved to {output_path}")

if __name__ == "__main__":
    # For testing purposes, you can run the script directly
    input_path = '/home/mhmdghdbn/airflow/zookeeper/airflow/data/output_data.json'
    output_path = '/home/mhmdghdbn/airflow/zookeeper/airflow/data/processed_data_1.json'
    
    process_text(input_path, output_path)
