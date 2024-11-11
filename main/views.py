from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import random
from django.http import JsonResponse
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum

# Create your views here.

#---------MAIN-------------#
def index(request):
  countDownItem = VotingCountdown.objects.first()
  remainingTime = countDownItem.end_time - timezone.make_aware(datetime.now())

  isVotingEnded = False
  if remainingTime < timedelta(seconds=0):
    isVotingEnded = True
  
  return render(request, 'index.html',{'active': 'index', 'isVotingEnded': isVotingEnded})

def results(request):
    candidates = Candidate.objects.all()
    total_votes = candidates.aggregate(Sum('votesCount'))['votesCount__sum'] or 1  # Avoid division by zero

    # Calculate percentage for each candidate and store in a list
    candidates_with_percentage = []
    for candidate in candidates:
        percentage = round((candidate.votesCount / total_votes) * 100, 2)
        candidates_with_percentage.append({
            'candidate': candidate,
            'percentage': percentage
        })

    # Sort the list by percentage in descending order
    candidates_with_percentage.sort(key=lambda x: x['percentage'], reverse=True)
    top_candidate = candidates_with_percentage[0] if candidates_with_percentage else None
    print(top_candidate)
    return render(request, 'results.html', {
        'active': 'results',
        'candidates': candidates_with_percentage,
        'topCandidate': top_candidate

    })

@login_required
def candidates(request):
  candidates = Candidate.objects.all()
  return render(request, 'candidates.html',{'active': 'candidates', 'candidates': candidates})

def candidate(request, id):
  candidate = Candidate.objects.get(id=id)
  return render(request, 'profile.html',{'active': 'candidates', "candidate": candidate})


#-----------VOTING-------------#
@login_required
def voteList(request):
  if request.method == 'POST':
    candidateId = request.POST.get('vote')
    candidate = Candidate.objects.get(id=candidateId)
    voter = Voter.objects.get(user=request.user)
    if voter.isVoted:
      messages.error(request, "You have already voted")
      return redirect("voteList")

    VoterVotedToItem = VoterVotedTo.objects.create(voter=voter, candidate=candidate)
    candidate.votesCount += 1
    candidate.save()
    voter.isVoted = True
    voter.save()
    messages.success(request, 'You have voted successfully')
    countDownItem = VotingCountdown.objects.first()
    countDown = countDownItem.formatted_end_time()
    candidates = Candidate.objects.all()
    return render(request, 'vote-list.html',{'active': 'vote', 'countDown': countDown, 'candidates': candidates, 'disabled': 'disabled'})


  countDownItem = VotingCountdown.objects.first()
  countDown = countDownItem.formatted_end_time()
  candidates = Candidate.objects.all()
  remainingTime = countDownItem.end_time - timezone.make_aware(datetime.now())

  if remainingTime < timedelta(seconds=0):
    return render(request, 'vote-list.html',{'active': 'vote', 'countDown': countDown, 'candidates': candidates, 'disabled': 'disabled'})
  
  disabled = ''
  voter = Voter.objects.get(user=request.user)
  if voter.isVoted:
    messages.error(request, "You have already voted")
    disabled = 'disabled'
  return render(request, 'vote-list.html',{'active': 'vote', 'countDown': countDown, 'candidates': candidates, 'disabled': disabled})

def vote(request):
  if request.method == "POST":
    cwid = request.POST.get('cwid')
    password = request.POST.get('password')
    # userEnteredOtp = request.POST.get('otp')


    userExists = User.objects.filter(username=cwid.upper()).exists()
    if not userExists:
      messages.error(request, "No user exist with that cwid")
      return redirect('vote')

    # otp = Otp.objects.get(email=email).otp
    # try:
    #   if int(userEnteredOtp) != int(otp):
    #     messages.error(request, "Invalid OTP")
    #     return render(request, 'vote.html',{'active': 'vote'})
    # except:
    #   messages.error(request, "Invalid OTP")
    #   return render(request, 'vote.html',{'active': 'vote'})


    user = authenticate(request, username=cwid.upper(), password=password)
    if user is not None:
      # login(request, user)
      email = Voter.objects.get(cwid=cwid.upper()).mail
      send_otp_register(email, isLogin=True)
      messages.success(request, "OTP sent to your email")
      return redirect(f'/loginOtp?email={email}')
    messages.error(request, "Invalid password")

  return render(request, 'vote.html',{'active': 'vote'})

def loginOtp(request):
  if request.method == "POST":
    email = request.GET.get('email')
    userEnteredOtp = request.POST.get('otp')
    otp = Otp.objects.get(email=email).otp

    try:
      if int(userEnteredOtp) != int(otp):
        messages.error(request, "Invalid OTP")
        return render(request, 'loginOtp.html', {'email': email})
    except:
      messages.error(request, "Invalid OTP")
      return render(request, 'loginOtp.html', {'email': email})

    user = User.objects.get(email=email)
    login(request, user)
    return redirect('index')

  email = request.GET.get('email')
  return render(request, 'loginOtp.html', {'email': email})

def send_opt_api(request):
  email = request.GET.get('email')
  requestType = request.GET.get('type')
  _type = request.GET.get('type')

  if requestType == "forgot_cwid":
    try:
      voter = Voter.objects.get(mail=email)
    except:
      return JsonResponse({'error': "NoVoterExist"})
    send_otp_register(email)
    return JsonResponse({'success': "sent successfully"})
  if not email:
    cwid = request.GET.get("cwid")
    try:
      voter = Voter.objects.get(cwid=cwid.upper())
    except:
      return JsonResponse({'error': "NoVoterExist"})
    send_otp_register(voter.mail, isLogin=True)
    return JsonResponse({'success': "sent successfully"})
  else:
    # Ontelas1@montclair.edu
    if _type != "login":
      voterExists = Voter.objects.filter(mail=email).exists()
      if voterExists:
        return JsonResponse({'error': "EmailAlreadyExist"})

    if ("@montclair.edu" not in email) and (email != "marioonrage@gmail.com") and (email != "cutezombie0@gmail.com"):
      return JsonResponse({'error': "InvalidEmail"})
    send_otp_register(email)
    return JsonResponse({'success': "sent successfully"})


#-----------REGISTER-------------#
def register(request):
  if request.method == "POST":
    email = request.POST.get('email1')
    firstname = request.POST.get('first_name')
    lastname = request.POST.get('last_name')
    dob = request.POST.get('date_of_birth')
    dob_obj = datetime.strptime(dob, '%m-%d-%Y')  # Parse the original dob format
    dob = dob_obj.strftime('%Y-%m-%d')  # Convert to yyyy-mm-dd
    address = request.POST.get('address')
    country = request.POST.get('country')
    gender = request.POST.get('gender')

    if lastname and firstname and email:
      userEnteredOtp = request.POST.get('otp')      
      otp = Otp.objects.get(email=email).otp
      try:
        if int(userEnteredOtp) != int(otp):
          messages.error(request, "Invalid OTP")
          return render(request, 'register1.html', {'active': 'register'})
      except:
        messages.error(request, "Invalid OTP")
        return render(request, 'register1.html', {'active': 'register'})

      try:
        v = Voter.objects.get(mail=email)
        if v.isVerified:
          messages.error(request, "This email is already has a cw Id linked to it")
          return redirect('vote')
      except: pass
      
      return redirect(f'/verify?email={email}&firstname={firstname}&lastname={lastname}&dob={dob}&address={address}&country={country}&gender={gender}')
    
    messages.error(request, "Enter all details")
    return render(request, 'register1.html',{'active': 'register'})
  
  return render(request, 'register1.html', {'active': 'register'})

def verfiy_otp(request):
  email = request.GET.get('email')
  firstname = request.GET.get('firstname')
  lastname = request.GET.get('lastname')
  dob = request.GET.get('dob')
  address = request.GET.get('address')
  country = request.GET.get('country')
  gender = request.GET.get('gender')

  if request.method == "POST":
    password1 = request.POST.get('password1')
    password2 = request.POST.get('password2')
    email = request.POST.get('email1')
    if password1 != password2:
      messages.error(request, "Passwords do not match")
      return render(request, 'verify.html', {'active': 'register', 'email': email})
    
    while True:
      cwid = "M50" + str(random.randint(000000, 999999))
      try: 
        Voter.objects.get(cwid=cwid.upper())
        continue
      except:
        break
    voter = Voter.objects.create(name=firstname+" "+lastname, mail=email, cwid=cwid.upper(), dateOfBirth=dob, country=country, address=address, gender=gender)
    user = User.objects.create_user(cwid,password=password1, email=email)
    voter.user = user
    voter.isVerified = True
    user.save()
    voter.save()
    send_cwid_register(email)
    return redirect('index')
  return render(request, 'verify.html', {'active': 'register', 'email': email, 'lastname': lastname, 'firstname': firstname})

def send_otp_register(email, isLogin=False):
  try:
    new_otp_obj = Otp.objects.get(email=email)
  except:
    new_otp_obj = Otp.objects.create(email=email)  
  otp = random.randint(10000, 99999)
  new_otp_obj.otp = otp
  new_otp_obj.save()
  if isLogin:
    subject = 'VoteIT | OTP for Login'
  else:
    subject = 'VoteIT | OTP for Register'
  font = "{ font-family: Arial, Helvetica, sans-serif !important; }"
  message = f'''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">

    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Verify your login</title>
      <!--[if mso]><style type="text/css">body, table, td, a { font }</style><![endif]-->
    </head>

    <body style="font-family: Helvetica, Arial, sans-serif; margin: 0px; padding: 0px; background-color: #ffffff;">
      <table role="presentation"
        style="width: 100%; border-collapse: collapse; border: 0px; border-spacing: 0px; font-family: Arial, Helvetica, sans-serif; background-color: rgb(239, 239, 239);">
        <tbody>
          <tr>
            <td align="center" style="padding: 1rem 2rem; vertical-align: top; width: 100%;">
              <table role="presentation" style="max-width: 600px; border-collapse: collapse; border: 0px; border-spacing: 0px; text-align: left;">
                <tbody>
                  <tr>
                    <td style="padding: 40px 0px 0px;">
                      <div style="text-align: left;">
                        <div style="padding-bottom: 20px;"><img src="https://i.ibb.co/Qbnj4mz/logo.png" alt="Company" style="width: 56px;"></div>
                      </div>
                      <div style="padding: 20px; background-color: rgb(255, 255, 255);">
                        <div style="color: rgb(0, 0, 0); text-align: center;">
                          <h1 style="margin: 1rem 0">Verification code</h1>
                          <p style="padding-bottom: 16px">Please use the OTP below to Vote Now.</p>
                          <p style="padding-bottom: 16px; letter-spacing: 1rem; font-size:2rem;"><strong style="font-size: 130%">{otp}</strong></p>
                          <p style="padding-bottom: 16px">If you didn’t request this, you can ignore this email.</p>
                          <p style="padding-bottom: 16px">Thanks,<br>The VoteIT team</p>
                        </div>
                      </div>
                      <div style="padding-top: 20px; color: rgb(153, 153, 153); text-align: center;"></div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>
    </body>

    </html>
  '''
  from_email = settings.EMAIL_HOST_USER
  msg = EmailMultiAlternatives(subject, message, from_email, [email])
  msg.attach_alternative(message, "text/html")
  msg.send()
  print('email sent successfully')

def send_cwid_register(email):
  voter = Voter.objects.get(mail=email)
  cwId = voter.cwid
  subject = 'VoteIT | Your Voter Id'
  font = "{ font-family: Arial, Helvetica, sans-serif !important; }"
  message = f'''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">

    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Verify your login</title>
      <!--[if mso]><style type="text/css">body, table, td, a { font }</style><![endif]-->
    </head>

    <body style="font-family: Helvetica, Arial, sans-serif; margin: 0px; padding: 0px; background-color: #ffffff;">
      <table role="presentation"
        style="width: 100%; border-collapse: collapse; border: 0px; border-spacing: 0px; font-family: Arial, Helvetica, sans-serif; background-color: rgb(239, 239, 239);">
        <tbody>
          <tr>
            <td align="center" style="padding: 1rem 2rem; vertical-align: top; width: 100%;">
              <table role="presentation" style="max-width: 600px; border-collapse: collapse; border: 0px; border-spacing: 0px; text-align: left;">
                <tbody>
                  <tr>
                    <td style="padding: 40px 0px 0px;">
                      <div style="text-align: left;">
                        <div style="padding-bottom: 20px;"><img src="https://i.ibb.co/Qbnj4mz/logo.png" alt="Company" style="width: 56px;"></div>
                      </div>
                      <div style="padding: 20px; background-color: rgb(255, 255, 255);">
                        <div style="color: rgb(0, 0, 0); text-align: center;">
                          <h1 style="margin: 1rem 0">Your CwId</h1>
                          <p style="padding-bottom: 16px">Please use this Voter Id below to Vote Now.</p>
                          <p style="padding-bottom: 16px; letter-spacing: 1rem; font-size:2rem;"><strong style="font-size: 50%">{cwId}</strong></p>
                          <p style="padding-bottom: 16px">If you didn’t request this, you can ignore this email.</p>
                          <p style="padding-bottom: 16px">Thanks,<br>The VoteIT team</p>
                        </div>
                      </div>
                      <div style="padding-top: 20px; color: rgb(153, 153, 153); text-align: center;"></div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>
    </body>

    </html>
  '''
  from_email = settings.EMAIL_HOST_USER
  msg = EmailMultiAlternatives(subject, message, from_email, [email])
  msg.attach_alternative(message, "text/html")
  msg.send()
  print('email sent successfully')

#---------LOGOUT-------------#
def logout_view(request):
  logout(request)
  return redirect('index')


#-------Other--------------#
def forgotCwid(request):
  if request.method == "POST":
    email = request.POST.get('cwid1')
    userEnteredOtp = request.POST.get('otp')
    print(email, userEnteredOtp)
    otp = Otp.objects.get(email=email).otp

    try:
      if int(userEnteredOtp) != int(otp):
        messages.error(request, "Invalid OTP")
        return render(request, 'forgotCwid.html')

    except Exception as e:
      print(e)
      messages.error(request, "Invalid OTP")
      return render(request, 'forgotCwid.html')
    
    send_cwid_register(email)
    messages.success(request, "Cwid sent to your email")
    return redirect('vote')
  
  return render(request, 'forgotCwid.html')


#---------API-------------#
# Index View - Show Voting Countdown Status
def index_API(request):
  countDownItem = VotingCountdown.objects.first()
  remainingTime = countDownItem.end_time - timezone.make_aware(datetime.now())

  isVotingEnded = False
  if remainingTime < timedelta(seconds=0):
      isVotingEnded = True

  return JsonResponse({
      'active': 'index',
      'isVotingEnded': isVotingEnded
  })


# Results View - Show Voting Results
def results_API(request):
  candidates = Candidate.objects.all()
  total_votes = candidates.aggregate(Sum('votesCount'))['votesCount__sum'] or 1  # Avoid division by zero

  # Calculate percentage for each candidate
  candidates_with_percentage = []
  for candidate in candidates:
    percentage = round((candidate.votesCount / total_votes) * 100, 2)
    candidates_with_percentage.append({
        'candidate': candidate.name,  # Modify this to return more details
        'percentage': percentage
    })

  # Sort by percentage
  candidates_with_percentage.sort(key=lambda x: x['percentage'], reverse=True)
  top_candidate = candidates_with_percentage[0] if candidates_with_percentage else None

  return JsonResponse({
    'active': 'results',
    'candidates': candidates_with_percentage,
    'topCandidate': top_candidate
  })


# Candidates List View - List All Candidates
def candidates_list_API(request):
  candidates = Candidate.objects.all()
  candidate_data = [{'id': candidate.id, 'name': candidate.name} for candidate in candidates]
  return JsonResponse({'active': 'candidates', 'candidates': candidate_data})


# Single Candidate View - Get Details of a Candidate
def candidate_detail_API(request, id):
  try:
    candidate = Candidate.objects.get(id=id)
  except Candidate.DoesNotExist:
    return JsonResponse({'error': 'Candidate not found'}, status=404)

  return JsonResponse({
    'active': 'candidates',
    'candidate': {
        'id': candidate.id,
        'name': candidate.name,
        'description': candidate.description
    }
  })


# Vote List View - Get Voters for a Candidate
def vote_list_API(request):
  # Assuming we need to authenticate the user or handle logic for voting
  if not request.user.is_authenticated:
    return JsonResponse({'error': 'User not authenticated'}, status=401)

  votes = Voter.objects.filter(user=request.user)
  votes_data = [{'candidate_id': vote.candidate.id, 'candidate_name': vote.candidate.name} for vote in votes]

  return JsonResponse({'active': 'votes', 'votes': votes_data})


# Register User View - User Registration (Assuming username, email, password)
def register_user_API(request):
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')
    email = request.POST.get('email')

    if not username or not password or not email:
      return JsonResponse({'error': 'Missing required fields'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    return JsonResponse({'message': 'User created successfully', 'user': {'id': user.id, 'username': user.username}}, status=201)

  return JsonResponse({'error': 'Invalid request method'}, status=400)


# User Login View - Login User
def login_user_API(request):
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')

    user = authenticate(request, username=username, password=password)
    if user is not None:
      login(request, user)
      return JsonResponse({'message': 'User logged in successfully', 'user': {'id': user.id, 'username': user.username}})
    else:
      return JsonResponse({'error': 'Invalid credentials'}, status=401)

  return JsonResponse({'error': 'Invalid request method'}, status=400)


# OTP Verification (Used for user registration or other processes)
def verify_otp_API(request):
  otp_code = request.POST.get('otp')
  user = request.user  # Assuming user is logged in already

  try:
    otp = Otp.objects.get(user=user, code=otp_code)
    if otp.is_valid():
      return JsonResponse({'message': 'OTP is valid'})
    else:
      return JsonResponse({'error': 'OTP has expired or is invalid'}, status=400)
  except Otp.DoesNotExist:
    return JsonResponse({'error': 'OTP not found'}, status=404)
