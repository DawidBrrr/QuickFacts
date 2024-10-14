from django.shortcuts import render
from .forms import LinkForm

def home(request):
    submitted_link = None  # To hold the submitted link
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            submitted_link = form.cleaned_data['link']  # Get the link
            
            # No need to save it, just render it on the page
            return render(request, 'Summary/home.html', {'form': form, 'submitted_link': submitted_link})
    else:
        form = LinkForm()

    return render(request, 'Summary/home.html', {'form': form})