
from firebase_admin import credentials, firestore, initialize_app, storage
from datetime import datetime


cred = credentials.Certificate('./podnotes-ai-gcp-service-key.json')
app = initialize_app(cred, {'storageBucket': 'podnotes-ai.appspot.com'})
db = firestore.client()


async def start_summarising(userEmail, url, type):
    print("saving content")
    knowledgebase_ref = db.collection("knowledgebase")
    
    firestore_doc = {
          'title': 'Title is being generated ...',
          'summary': 'Summary is being generated ......',
          'summary_context': '',
          'raw_text' : '',
          'url': url,
          'type': type,
          'userEmail': userEmail,
          'folder': 'inbox',
          'created_at': datetime.now()
    }
    # saving raw text
    update_time, summary_ref = knowledgebase_ref.add(firestore_doc)
    print("raw text saved", summary_ref.id)
    return summary_ref.id

async def save_raw_text(content, document_id, html=''):
    print("saving content", document_id)
    knowledgebase_ref = db.collection("knowledgebase").document(document_id)
    raw_text = content
    firestore_doc = {
          'raw_text' : raw_text,
          'html' : html
    }
    # saving raw text
    knowledgebase_ref.update(firestore_doc)
    return True

async def save_summary(summary, document_id):
    knowledgebase_ref = db.collection("knowledgebase").document(document_id)
    summary_context = summary['intermediate_steps']
    summary = summary['output_text']
    # read summary file
    split_summary = summary.split('\n', 1)  # split the string at the first newline character
    title = split_summary[0]  # the first line is the title
    remaining_summary = split_summary[1] if len(split_summary) > 1 else ""
    
    firestore_doc = {
          'title': title,
          'summary': remaining_summary,
          'summary_context': summary_context,
          'folder': 'inbox',
          'updated_at': datetime.now()
        }
    
    knowledgebase_ref.update(firestore_doc)
    print(f"Successfully added summary")
    return True

async def save_formatted_raw_text(formatted_raw_text, document_id):
    knowledgebase_ref = db.collection("knowledgebase").document(document_id)
     
    firestore_doc = {
          'raw_text' : formatted_raw_text,
    }
    
    response = knowledgebase_ref.update(firestore_doc)
    print(f"Successfully updated  formatted raw text in knowledgebase")
    return response

async def update_new_summary(new_summary, document_id):
    knowledgebase_ref = db.collection("knowledgebase").document(document_id)
    split_summary = new_summary.split('\n', 1)  # split the string at the first newline character
    title = split_summary[0]  # the first line is the title
    remaining_summary = split_summary[1] if len(split_summary) > 1 else ""
    firestore_doc = {
        'title' : title,
        'summary' : remaining_summary,
    }
    
    response = knowledgebase_ref.update(firestore_doc)
    print(f"Successfully updated  formatted raw text in knowledgebase")
    return response
    
def getAllTranscripts(search_keyword):
    bucket = storage.bucket("podnotes-transcripts")
    transcript_files = []

    # Fetch all file blobs from Firebase Storage
    all_blobs = bucket.list_blobs()

    # Check if the blob's name contains 'huberman' and add it to the list
    for blob in all_blobs:
        if search_keyword in blob.name:
            transcript_files.append(blob)
    return transcript_files


async def update_notification(userEmail, summaryType, url, statusObject):
    notifications_ref = db.collection("notifications")
    notification_query = notifications_ref.where('user_email', '==', userEmail).where('url', '==', url)

    docs = notification_query.stream()
    
    try:
        doc = next(docs)
        print(f"Document found with ID: {doc.id}, Data: {doc.to_dict()}")

        firestore_doc = {
          'status':  statusObject,
        }
        update_ref = notifications_ref.document(doc.id)
        update_ref.update(firestore_doc)

    except StopIteration:
        firestore_doc = {
          'date': datetime.now(),
          'fail_message': '',
          'type': summaryType,
          'url' : url,
          'userEmail': userEmail,
          'status':  statusObject,
        }
        notifications_ref.add(firestore_doc)
        print("No such document exists with the given conditions.")

