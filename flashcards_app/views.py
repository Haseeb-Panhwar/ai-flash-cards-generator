from django.shortcuts import render,redirect
from .forms import PDFUploadForm
import io
from pdfminer.high_level import extract_text

from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.urls import reverse_lazy,reverse
import re,os
from dotenv import load_dotenv

# Create your views here.
load_dotenv()
from groq import Groq

client = Groq(api_key=os.getenv('groq_api'))


def extract_cards(llm_response):
    questions_match = re.search(r'questions\s*=\s*\[(.*?)\]', llm_response, re.DOTALL)
    questions_text = questions_match.group(1).strip() if questions_match else ''
    questions = [q.strip().strip('",') for q in re.split(r',\s*(?=[A-Z])', questions_text)]

    # Extract answers
    answers_match = re.search(r'answers\s*=\s*\[(.*?)\]', llm_response, re.DOTALL)
    answers_text = answers_match.group(1).strip() if answers_match else ''
    answers = [a.strip().strip('",') for a in re.split(r',\s*(?=[A-Z])', answers_text)]

    # print("Questions: ",questions)
    # print("Answers: ",answers)

    # Create dictionary of flashcards
    flashcards = {i[0]:i[1] for i in list(zip(questions, answers))}
    return flashcards

def asklama(pdf_text,n):
    prompt = ''' Here is the text from a pdf: {pdf_text}\n Now, follow following instructions:
    1. Your task is to generate {n} questions from this text.
    2. Repond with 2 lists , one for question and other for their respective answers in the same order.
    3. Return Questions' List like "questions = [question1, question2, . . .]"
    4. Return Answers' List like "answers = [answer1,answer2,... ]"
    5. The questions and their respective answers should be short and comprehensive, answer should be one liner.
    6. if {n} number of question answers can not be created, then generate atleast 5 question and answers.
    Ensure the response follows this format exactly and is in plain text with no markdown language symbols.
        '''.format(pdf_text=pdf_text,n=n)

    response = client.chat.completions.create(
        messages = [
            {
                'role':'user',
                'content':prompt
            }
        ],
        model = 'llama-3.1-8b-instant'
    )
    response = response.to_dict()
    response = response['choices'][0]['message']['content']
    # print(response)
    return extract_cards(response)
    
def home(request):
    if request.user.is_authenticated:
        form = PDFUploadForm()
        flashcards = []
        if request.method == 'POST':
            form = PDFUploadForm(request.POST, request.FILES)
            if form.is_valid():
                # Process the PDF file and generate flashcards
                # For simplicity, using sample data here
                pdf_file = request.FILES['pdf']
                pdf_content = pdf_file.read()
                n = form.cleaned_data['cards']
                # Parse the PDF content into a string without saving it to local storage
                pdf_string = extract_text(io.BytesIO(pdf_content))
                print(pdf_string)
                print("\n\n Lama Response: ")
                question_answer_set = asklama(pdf_string,n)
                while ((len(question_answer_set.keys())!=n) and (not (len(question_answer_set.keys())==5 and n>5)) ):
                    question_answer_set = asklama(pdf_string,n)
                for k,v in question_answer_set.items():
                    flashcards.append({"front":k,"back":v})
    else:
        return redirect(reverse_lazy('login'))
    return render(request, 'flashcards_app/home.html', {'form': form, 'flashcards': flashcards})
    


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'flashcards_app/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy('home'))
    else:
        if request.method == 'POST':
            form = CustomAuthenticationForm(data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                return redirect('home')
        else:
            form = CustomAuthenticationForm()
    return render(request, 'flashcards_app/login.html', {'form': form})
