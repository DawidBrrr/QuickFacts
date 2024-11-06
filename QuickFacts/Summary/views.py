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

    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            submitted_link = form.cleaned_data['link']

            # Try to retrieve the existing summary, if available
            article_summary = ArticleSummary.objects.filter(link=submitted_link).first()

            if article_summary:  # Entry already exists
                summary = article_summary.summary
            else:
                # Proceed with scraping and summarization if new entry
                try:
                    response = requests.get(submitted_link)
                    response.raise_for_status()

                    # Parse the content
                    soup = BeautifulSoup(response.content, 'html.parser')
                    article = soup.find('article')
                    
                    if article:
                        paragraphs = article.find_all('p')
                        article_content = "\n\n".join([p.get_text() for p in paragraphs])
                    else:
                        content_div = soup.find('div', class_='article-content')
                        if content_div:
                            paragraphs = content_div.find_all('p')
                            article_content = "\n\n".join([p.get_text() for p in paragraphs])
                        else:
                            article_content = "No article content found at the provided URL."

                    # Summarize if content is available
                    if not article_content.strip():
                        summary = "No content to summarize."
                    else:
                        summary = summarize_content(article_content)

                        # Save the link and summary in the database
                        article_summary = ArticleSummary(link=submitted_link, summary=summary)
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
                'summary': summary,
            })

    else:
        form = LinkForm()

    return render(request, 'Summary/home.html', {
        'form': form,
    })



#SUMMARIZATION SECTION
def summarize_chunk(chunk, model, tokenizer, device):
    # Tokenize and summarize a chunk of the article
    inputs = tokenizer(chunk, return_tensors="pt", max_length=1024, truncation=True)
    inputs = inputs.to(device)

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

    # Split the article content into chunks (let's use 4000 tokens per chunk for BigBird)
    chunks = split_into_chunks(article_content, max_length=4096)

    # Summarize each chunk separately
    summaries = []
    for chunk in chunks:
        summary = summarize_chunk(chunk, mbart_model, mbart_tokenizer, device)
        summaries.append(summary)

    # Combine all summaries into one final summary
    final_summary = " ".join(summaries)
    
    return final_summary