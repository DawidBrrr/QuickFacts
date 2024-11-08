import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from .forms import LinkForm
from .models import ArticleSummary
import torch
import torch_directml #For DirectML support
from transformers import MBartForConditionalGeneration, MBart50Tokenizer, AutoModelForSeq2SeqLM, AutoTokenizer

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



#SUMMARIZATION SECTION
def summarize_chunk(chunk, model, tokenizer, device):
    # Tokenize and summarize a chunk of the article
    inputs = tokenizer(chunk, return_tensors="pt", max_length=1024, truncation=True)
    inputs = inputs.to(device)

    summary_ids = model.generate(
        inputs['input_ids'],
        max_length=120,  # Adjust to control summary length for each chunk
        min_length=40,
        num_beams=4,
        length_penalty=2.0,
        early_stopping=True,
        forced_bos_token_id=tokenizer.lang_code_to_id["pl_PL"],
        temperature=1,
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def split_into_chunks(text, max_length, tokenizer):
    # Tokenize the entire text and split based on token length, not characters
    tokens = tokenizer.encode(text, truncation=False)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for token in tokens:
        current_length += 1
        current_chunk.append(token)
        
        if current_length >= max_length:
            chunks.append(tokenizer.decode(current_chunk, skip_special_tokens=True))
            current_chunk = []
            current_length = 0
    
    if current_chunk:
        chunks.append(tokenizer.decode(current_chunk, skip_special_tokens=True))  # Add the last chunk
    
    return chunks

def summarize_content(article_content):
    # Load multilingual mBART model and tokenizer for Polish language support
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print("Using CUDA for GPU acceleration")
    else:

        """
        #MEMORY ISSUE WITH DIRECTML
        try:
            device = torch_directml.device() #DirectML device for AMD GPUs
            _ = torch.ones(1, device=device) #Check if DirectML available
            print("Using DirectML for GPU acceleration")
        except:
        """

        device = torch.device("cpu")
        print("Only CPU available")
    #Initialize mBART model (TO DO FIND BETTER MODEL)
    mbart_model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-many-to-many-mmt").to(device)
    mbart_tokenizer = MBart50Tokenizer.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")

    # Set the source language for Polish
    mbart_tokenizer.src_lang = "pl_PL"

    
    chunks = split_into_chunks(article_content, max_length=1024,tokenizer=mbart_tokenizer)

    # Summarize each chunk separately
    summaries = []
    for chunk in chunks:
        summary = summarize_chunk(chunk, mbart_model, mbart_tokenizer, device)
        summaries.append(summary)

    # Combine all summaries into one final summary
    final_summary = " ".join(summaries)
    
    return final_summary