import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from .forms import LinkForm
from .models import ArticleSummary
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

def home(request):
    submitted_link = None
    summary = None
    article_title = None

    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            submitted_link = form.cleaned_data['link']

            # Try to retrieve the existing summary, if available
            article_summary = ArticleSummary.objects.filter(link=submitted_link).first()

            if article_summary:  # Entry already exists
                summary = article_summary.summary
                article_title = article_summary.title
            else:
                # Proceed with scraping and summarization if new entry
                try:
                    response = requests.get(submitted_link)
                    response.raise_for_status()

                    # Parse the content
                    soup = BeautifulSoup(response.content, 'html.parser')

                    article_title = extract_article_title(soup)

                    article_content = extract_article_content(soup)                   

                    # Summarize if content is available
                    if not article_content.strip():
                        summary = "No content to summarize."
                    else:
                        summary = summarize_content(article_content)

                        # Save the link and summary in the database
                        article_summary = ArticleSummary(link=submitted_link,title=article_title, summary=summary)
                        article_summary.save()

                except requests.exceptions.RequestException as e:
                    summary = f"Error fetching the URL: {str(e)}"
                except ValueError as ve:
                    summary = str(ve)
                except Exception as e:
                    summary = f"An unexpected error occurred: {str(e)}"

            # Render the form with the submitted link and summary
            return render(request, 'Summary/home.html', {
                'form': form,
                'submitted_link': submitted_link,
                'article_title': article_title,
                'summary': summary,
            })

    else:
        form = LinkForm()

    return render(request, 'Summary/home.html', {
        'form': form,
    })

def extract_article_title(soup):
    #Check for <title>
    if soup.title:
        return soup.title.get_text().strip()
    
    #Check for <h1>
    h1 = soup.find('h1')
    if h1:
        return h1.get_text().strip()
    

    return "Artykuł"

def extract_article_content(soup):
    article = soup.find('article')
    #Try to find <article> tag 
    if article:
        paragraphs = article.find_all('p')
        return "\n\n".join([p.get_text() for p in paragraphs])
    #If not found in <article> try conent inside <div> with specyfic class
    content_div = soup.find('div', class_='article-content')
    if content_div:
        paragraphs = content_div.find_all('p')
        return "\n\n".join([p.get_text() for p in paragraphs])
    
    return "No article content found at the provided URL."

#text summarization - if not working try >>>import nltk >>> nltk.download()
def summarize_content(text):

    #Choose sentences count 
    word_count = len(text.split())
    if word_count < 100:
        sentences_count = 2
    elif word_count < 300:
        sentences_count = 3
    elif word_count < 500:
        sentences_count = 4
    else:
        sentences_count = 5


    #Parser/ tokenize
    parser = PlaintextParser.from_string(text, Tokenizer("polish"))
    
    #summary algorithm
    summarizer = LsaSummarizer()
    
    # Creating Summary choosing amount of sentences
    summary = summarizer(parser.document, sentences_count)
    
    #Joining sentences
    return ' '.join(str(sentence) for sentence in summary)
