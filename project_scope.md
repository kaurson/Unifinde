I want to build an app, that can determine, which university or major/minor the user should go study.
The user has an account, kinda like a dating profile, and the univesity also has a profile
The app tries to match the user to the universiy/major which to go study. 
later we will add new criteria for the user and the university.

First we need to gather up info about the highschools, kinda like their stats, i want to do this with browser-use AI tool. with this the app will gather up info and stats about the school. 
The schools do not usually display stats about their school on their website, so the tool needs to be able to be given a queery and the queery is searched up on the internet. The main point is that the tool can go onto a specific website or more preferably search for the answers with a more broad perspective.
The tool would be given a json, which the LLM must fill out. the LLM can do this by searching relevant info about the school.
Once it has found all of the necessary info, the json is commited to the database. 

The users need to able to register a new account, while registering the user is tested with some questions. The answers to these questions will be given to the LLM and a general user profile is determined, kinda like what the personality of the user is. Later the user can add to their profile some important info, like age, name, income, email, phone number. with the questionaire the user can also add a preference of which major or field of study the user wants. 



Frontend: 
Next.js
Shadcn

Backend: 
Fastapi
Python
Alembic
Browser-use

Database:
Supabase