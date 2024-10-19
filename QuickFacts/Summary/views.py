import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from .forms import LinkForm
import torch
from transformers import MBartForConditionalGeneration, MBart50Tokenizer, AutoModelForSeq2SeqLM, AutoTokenizer

def home(request):
    submitted_link = None   
    article_content = None  # To hold the scraped content
    summary = None  # To hold the summary

    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            submitted_link = form.cleaned_data['link']  # Get the link

            # Try to scrape the article content
            try:
                # Fetch the page content
                response = requests.get(submitted_link)
                response.raise_for_status()  # Raise an exception for HTTP errors

                # Parse the page content
                soup = BeautifulSoup(response.content, 'html.parser')

                # Attempt to find the article content
                article = soup.find('article')  # Common tag for articles

                if article:
                    # Extract the paragraphs inside the article
                    paragraphs = article.find_all('p')
                    article_content = "\n\n".join([p.get_text() for p in paragraphs])
                else:
                    # If no <article> tag is found, try other common divs
                    content_div = soup.find('div', class_='article-content')
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        article_content = "\n\n".join([p.get_text() for p in paragraphs])
                    else:
                        article_content = "No article content found at the provided URL."

                # Handle empty content case
                if not article_content or len(article_content.strip()) == 0:
                    summary = "No content to summarize."
                else:
                    # Summarize the article content using Hugging Face Transformers
                    summary = summarize_content(article_content)

            except requests.exceptions.RequestException as e:
                # Handle errors such as invalid URL or network issues
                article_content = f"Error fetching the URL: {str(e)}"
            except ValueError as ve:
                summary = str(ve)
            except Exception as e:
                summary = f"An unexpected error occurred: {str(e)}"

            # Render the form with the submitted link, article content, and summary
            return render(request, 'Summary/home.html', {
                'form': form,
                'submitted_link': submitted_link,
                'article_content': article_content,
                'summary': summary
            })

    else:
        form = LinkForm()

    # Render the form when the request method is GET (initial load)
    return render(request, 'Summary/home.html', {
        'form': form,
    })



#SUMMARIZATION SECTION
def summarize_chunk(chunk, model, tokenizer):
    # Tokenize and summarize a chunk of the article
    inputs = tokenizer(chunk, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model.generate(
        inputs['input_ids'],
        max_length=200,  # Adjust to control summary length for each chunk
        min_length=50,
        num_beams=4,
        length_penalty=2.0,
        early_stopping=True,
        forced_bos_token_id=tokenizer.lang_code_to_id["pl_PL"]
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def split_into_chunks(text, max_length):
    # Function to split the text into chunks of `max_length` tokens
    words = text.split()  # Split text by whitespace
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1  # Account for space between words
        current_chunk.append(word)
        
        if current_length >= max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))  # Add the last chunk
    
    return chunks

def summarize_content(article_content):
    # Load multilingual mBART model and tokenizer for Polish language support
    mbart_model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
    mbart_tokenizer = MBart50Tokenizer.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")

    # Set the source language for Polish
    mbart_tokenizer.src_lang = "pl_PL"

    # Split the article content into chunks (let's use 4000 tokens per chunk for BigBird)
    chunks = split_into_chunks(article_content, max_length=4096)

    # Summarize each chunk separately
    summaries = []
    for chunk in chunks:
        summary = summarize_chunk(chunk, mbart_model, mbart_tokenizer)
        summaries.append(summary)

    # Combine all summaries into one final summary
    final_summary = " ".join(summaries)
    
    return final_summary