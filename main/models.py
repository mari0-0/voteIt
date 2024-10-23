from django.db import models
from django.contrib.auth.models import User
from datetime import date


# Create your models here.
class Voter(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
  name = models.TextField()
  mail = models.EmailField()
  cwid = models.CharField(max_length=15)
  otp = models.PositiveIntegerField(null=True, blank=True)
  isVoted = models.BooleanField(default=False, null=True)
  isVerified = models.BooleanField(default=False, null=True)
  dateOfBirth = models.DateField(null=True)

  def __str__(self):
    return self.name

class Otp(models.Model):
  email = models.EmailField()
  otp = models.PositiveIntegerField(null=True)
  def __str__(self):
    return self.email

class VotingCountdown(models.Model):
  end_time = models.DateTimeField()

  def formatted_end_time(self):
    return self.end_time.strftime("%B %d, %Y %H:%M:%S")

  def __str__(self):
    return self.end_time.strftime("%B %d, %Y %H:%M:%S")

class Candidate(models.Model):
  name = models.CharField(max_length=100)
  dob = models.DateField()
  place = models.CharField(max_length=100)
  political_organization = models.TextField()
  degrees = models.TextField()
  previous_jobs = models.TextField()
  work_experience = models.TextField()
  achivements = models.TextField()
  vison = models.TextField()
  goals = models.TextField()
  description = models.TextField()
  picture = models.ImageField(upload_to ='uploads/profilePics', null=True, blank=True)
  votesCount = models.IntegerField(default=0, blank=True)

  def formatted_dob(self):
    return self.dob.strftime("%B %d, %Y")

  def calculate_age(self):
    today = date.today()
    age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
    return age

  def __str__(self):
    return self.name

class VoterVotedTo(models.Model):
  voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
  candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

  def __str__(self):
    return f"{self.voter.name.capitalize()} voted to {self.candidate.name.capitalize()}"
  