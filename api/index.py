from flask import Flask, request
import chromaLocal
import scrapeUrl
from TextSummarisation import textSummarisation
from PyPDF2 import PdfReader
from io import BytesIO
from Utils import DBFunctions
import requests
import os
from docx import Document
from werkzeug.utils import secure_filename
from flask_cors import CORS
import subprocess
from dotenv import load_dotenv
from pytube import YouTube
from moviepy.editor import AudioFileClip
import mimetypes
from youtube_dl import YoutubeDL

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024


@app.route('/', methods=['POST'])
async def home():
    print("API request received")
    api_type = request.form.get("apiType")
    print("form api type: %s" % api_type)
    if api_type == "get-query-response":
        query = request.form.get("query")
        userEmail = request.form.get("userEmail")
        collection = userEmail.split("@")[0]
        conversationHistory = request.form.get("conversationHistory")
        print("coll", collection)
        response = chromaLocal.response(query, collection, conversationHistory)
        return response

    elif api_type == "summarise-text-url":
        url = request.form.get("url")
        userEmail = request.form.get("userEmail")
        summary_length = request.form.get("summaryLength")
        summary_format = request.form.get("summaryFormat")
        response = await summarise_text_url(url, userEmail, summary_length, summary_format)
        return response

    elif api_type == "summarise-text-upload":
        file = request.files['file']
        userEmail = request.form.get("userEmail")
        summary_length = request.form.get("summaryLength")
        summary_format = request.form.get("summaryFormat")

        response = await summarise_text_upload(file, userEmail, summary_length, summary_format)
        return response

    elif api_type == "summarise-media-url":
        media_url = request.form.get("url")
        userEmail = request.form.get("userEmail")
        summary_length = request.form.get("summaryLength")
        summary_format = request.form.get("summaryFormat")

        response = await summarise_media_url(media_url, userEmail, summary_length, summary_format)
        return response

    elif api_type == "summarise-media-upload":
        file = request.files['file']
        userEmail = request.form.get("userEmail")
        summary_length = request.form.get("summaryLength")
        summary_format = request.form.get("summaryFormat")

        response = await summarise_media_upload(file, userEmail, summary_length, summary_format)
        return response

    elif api_type == "transcribe-recording-upload":
        file = request.files['file']
        userEmail = request.form.get("userEmail")
        response = await transcribe_recording_upload(file, userEmail)
        return response
    elif api_type == "regenerate-summary":
        docId = request.form.get("docId")
        summaryLength = request.form.get("summaryLength")
        summary_format = request.form.get("summaryFormat")

        summaryContext = request.form.get("summaryContext")
        response = await regenerate_summary(docId, summaryLength, summaryContext, summary_format)
        return response
    else:
        return {"error": "Invalid apiType parameter"}, 400


@app.route('/regenerate-summary', methods=['POST'])
async def regenerate():
    return True

# API functions
#  =================================================================
#  =================================================================
# @app.route("/summarise-text", methods=['GET'])


async def summarise_text_url(url, userEmail, summary_length, summary_format):
    content = ''
    document_id = ''
    summary = ''
    if url:
        content = ''
        document_id = await DBFunctions.start_summarising(userEmail, url, "text")
        if url.lower().endswith('.pdf') is True:
            content = await load_pdf(url)
            await DBFunctions.save_raw_text(content, document_id)
            summary = textSummarisation.summarize_large_text(
                content, summary_length, summary_format)
            # split the string at the first newline character
            split_summary = summary['output_text'].split('\n', 1)
            title = split_summary[0]  # t
            await save_embeddings_to_verctor_store(content, userEmail, title)
            await save_embeddings_to_verctor_store(summary['output_text'], userEmail, title)
        else:
            scrapedText = scrapeUrl.scrape_url(url)
            print("scrappy", scrapedText)
            content = scrapedText["text"]
            await DBFunctions.save_raw_text(content, document_id, scrapedText["html"])
            summary = textSummarisation.summarize_large_text(
                content, summary_length, summary_format)
            # split the string at the first newline character
            split_summary = summary['output_text'].split('\n', 1)
            title = split_summary[0]  # t
            await save_embeddings_to_verctor_store(content, userEmail, title)
            await save_embeddings_to_verctor_store(summary['output_text'], userEmail, title)
        await DBFunctions.save_summary(summary, document_id)

    return summary

# @app.route("/summarise-text", methods=['POST'])


async def summarise_text_upload(file, userEmail, summary_length, summary_format):
    summary = ''
    document_id = ''

    if file:
        if file.filename == '':
            return 'No selected file', 400
        if file:
            filename = secure_filename(file.filename)
            print(filename)

            print('\workspace\\' + filename, userEmail)
            document_id = await DBFunctions.start_summarising(userEmail, filename, "text")
            file.save('workspace' + filename)

            file_content = parse_file('workspace' + filename)

            print(file_content)
            await DBFunctions.save_raw_text(file_content, document_id)

            summary = textSummarisation.summarize_large_text(
                file_content, summary_length, summary_format)
            # split the string at the first newline character
            split_summary = summary['output_text'].split('\n', 1)
            title = split_summary[0]
            await save_embeddings_to_verctor_store(file_content, userEmail, title)
            await save_embeddings_to_verctor_store(summary['output_text'], userEmail, title)
            print("uploaded summary", summary)
            await DBFunctions.save_summary(summary, document_id)
    return summary

# @app.route("/summarise-media", methods=['GET'])


async def summarise_media_url(media_url, userEmail, summary_length, summary_format):
    print("url is", media_url)

    # file_name = ''.join(e for e in media_url.split("/")[-1] if e.isalnum())
    # document_id = await DBFunctions.start_summarising(userEmail, media_url, "media")
    # if 'youtube' in media_url or 'youtu.be' in media_url:
    #     download_video(media_url, file_name)
    # else:
    #     audio_file = requests.get(media_url, allow_redirects=True)
    #     print(audio_file.status_code, file_name)
    #     if audio_file.status_code == 200:
    #         with open(f"workspace/{file_name}.mp3", "wb") as file:
    #             file.write(audio_file.content)

    # print('file downloaded')

    # transcribe audio using powershell script
    content = ''
    try:
        url = 'https://query.podnotes.ai'
        response = requests.post(url, files={"url": media_url})
        print(response.status_code)
        print("TRANSCRIPT", response.text)
        content = response.text
        
    except subprocess.CalledProcessError as error:
        print(f"Error occurred: {error}")

    # load transcript and summarise text and save to firestore
    text_summary = ''
    await DBFunctions.save_raw_text(content, document_id)
    text_summary = textSummarisation.summarize_large_text(
        content, summary_length, summary_format)
    # split the string at the first newline character
    split_summary = text_summary['output_text'].split('\n', 1)
    title = split_summary[0]  # t
    await save_embeddings_to_verctor_store(content, userEmail, title)
    await save_embeddings_to_verctor_store(text_summary['output_text'], userEmail, title)
    await DBFunctions.save_summary(text_summary, document_id)
    # delete transcripts if it exists
    delete_if_exists(f"workspace/{file_name}.txt")
    delete_if_exists(f"workspace/{file_name}.ts.txt")
    delete_if_exists(f"workspace/{file_name}.mp3")

    return text_summary

# @app.route("/summarise-media", methods=['POST'])


async def summarise_media_upload(file, userEmail, summary_length, summary_format):
    document_id = await DBFunctions.start_summarising(userEmail, file.filename, "media")
    file_name = ''.join(e for e in file.filename.split("/")[-1] if e.isalnum())

    path = os.path.join('workspace', file_name)
    file.save(path)

    # transcribe audio using powershell script
    try:
        result = subprocess.Popen(['powershell.exe',  "-File", "api/Scripts/transcribe.ps1",
                                  f".\{file_name}.mp3"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Output:", result)

        text_summary = ''
        with open(f"workspace/{file_name}.txt", 'r') as file:
            content = file.read()
            await save_embeddings_to_verctor_store(content, userEmail)
            await DBFunctions.save_raw_text(content, document_id)
            text_summary = textSummarisation.summarize_large_text(
                content, summary_length, summary_format)

        await save_embeddings_to_verctor_store(text_summary, userEmail)
        await DBFunctions.save_summary(text_summary, document_id)
        delete_if_exists(f"workspace/{file_name}.txt")
        delete_if_exists(f"workspace/{file_name}.ts.txt")
        delete_if_exists(f"workspace/{file_name}.mp3")

        return text_summary, 200

    except subprocess.CalledProcessError as error:
        print(f"Error occurred: {error}")
        return error

        # load transcript and summarise text and save to firestore


async def transcribe_recording_upload(file, userEmail):
    if file:
        # saving received audio file
        filename = secure_filename(file.filename)
        filepath = os.path.join('workspace', filename)
        file.save(filepath)
        audioclip = AudioFileClip(filepath)

        # converting file to mp3
        audio_filename = 'media' + '.mp3'
        audio_filepath = os.path.join('workspace', audio_filename)
        audioclip.write_audiofile(audio_filepath)

        delete_if_exists('workspace/media.txt')
        delete_if_exists('workspace/media.ts.txt')
        # transcribe audio using powershell script
        try:
            result = subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass",
                    "-File", "api/Scripts/transcribe.ps1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            print("Output:", result)

            transcript = ''
            with open('workspace/media.txt', 'r') as file:
                transcript = file.read()

            print("transcript", transcript)
            # await DBFunctions.save_recording_transcript(transcript, userEmail)

            return transcript, 200

        except subprocess.CalledProcessError as error:
            print(f"Error occurred: {error}")
            return error


async def regenerate_summary(docId, summaryLength, summaryContext, summary_format):
    new_summary = textSummarisation.refineSummary(
        summaryContext, summaryLength, summary_format)
    response = await DBFunctions.update_new_summary(new_summary, docId)
    return new_summary
# Util functions
#  =================================================================
#  =================================================================


async def save_embeddings_to_verctor_store(text, userEmail, title):
    collection_name = userEmail.split('@')[0]
    response = await chromaLocal.saveFiles(text, collection_name, title)
    print(f"Saved to collection {collection_name}", len(text), title)
    return response


def delete_if_exists(file_path):
    """Delete the file at `file_path` if it exists."""
    if os.path.isfile(file_path):
        os.remove(file_path)


def parse_file(filepath):
    file_extension = os.path.splitext(filepath)[1]

    if file_extension == '.txt':
        with open(filepath, 'r') as f:
            return f.read()
    elif file_extension == '.pdf':
        with open(filepath, 'rb') as f:
            pdf = PdfReader(f)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text
    elif file_extension in ['.doc', '.docx']:
        doc = Document(filepath)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text
    else:
        return "Unsupported file type"


async def load_pdf(url):
    response = requests.get(url)

    response.raise_for_status()
    pdf_file = BytesIO(response.content)
    pdf_reader = PdfReader(pdf_file)
    content = ""
    # number _of_pages = len(pdf_reader.pages)  # Use len(pdf.pages) instead of pdf.getNumPages()
    for page in pdf_reader.pages:
        content += page.extract_text()

    print('pdf_content', content)
    return content


def read_file_contents(blob):
    return blob.download_as_text()


def download_video(video_url, filename):
    video = YouTube(video_url)
    stream = video.streams.get_lowest_resolution()
    stream.download(filename=f"{filename}.mp4")
    print('downloaded video, converting to audio')
    # convert video to mp3 using moviepy
    video_clip = AudioFileClip(f"{filename}.mp4")
    video_clip.to_audiofile("workspace/" + filename + '.mp3')
    video_clip.close()
    print('saved audio')


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", use_reloader=False, threaded=True)
