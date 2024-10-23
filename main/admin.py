from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Voter)
admin.site.register(Otp)

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'votesCount')  # Display the candidate's name and votes

admin.site.register(Candidate, CandidateAdmin)

admin.site.register(VotingCountdown)
admin.site.register(VoterVotedTo)