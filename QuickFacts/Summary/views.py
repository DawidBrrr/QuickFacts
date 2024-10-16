import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from .forms import LinkForm
from transformers import pipeline

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

def summarize_content(article_content):
    # Initialize the summarization pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    # Tokenize the content
    inputs = summarizer.tokenizer(
        article_content, 
        return_tensors="pt", 
        truncation=True, 
        max_length=1024, 
        padding="max_length"
    )

    # Check if input_ids is empty or has an invalid shape
    if inputs['input_ids'].numel() == 0 or inputs['input_ids'].shape[1] > 1024:
        raise ValueError("Input content is empty after tokenization or exceeds the token limit.")
    
    # Generate the summary
    try:
        summary = summarizer(
            article_content,
            max_length=300,
            min_length=30,
            do_sample=False
        )
        return summary[0]['summary_text']
    except Exception as e:
        return f"Error during summarization: {str(e)}"