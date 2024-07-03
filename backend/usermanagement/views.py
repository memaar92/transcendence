from django.shortcuts import render

# Create your views here.
def json(request):
	# Render the main page
	return render(request, 'json.json')