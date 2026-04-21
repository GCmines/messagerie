# Evaluation project

## functions

you are to write a web app alike what'sapp

- users are created from the command line (no admin interface, no registration
  form yet)
- likewise, rooms (channels) are create from the command line
- there is no authentication per se, people entering the system can join the app
  under one of the predefined names
- they can decide to subscribe / unsubscribe any of the known rooms
- once they join a room, they can send messages to the room, and see the
  messages sent by other users in the same room

## technical requirements

- use
  - FastAPI
  - WebSockets
  - sqlite
- the frontend can be done using more advanced tools like react and tailwind;
  other technologies can be considered as well if they are cleared beforehand
  with your teacher

## example session

### start the server

```bash
# optionally wipe the DB
$ rm *.db

# start server and keep it server running ...
$ fastapi dev
...
```

### create users and rooms

then **in another terminal**:

```bash
http POST http://localhost:8000/users name=alice
http POST http://localhost:8000/users name=bob
http POST http://localhost:8000/rooms name=charlie
...

http POST http://localhost:8000/rooms/social
http POST http://localhost:8000/rooms/sports
http POST http://localhost:8000/rooms/bde
...

```

### the UI per se

a new user joins the server; they are asked  to choose a user name; ideally only
names not yet in the system should be allowed, but you can skip this check if
you want

then they are presented with the list of rooms; they can choose to 
- subscribe to rooms they are interested in; or to unsubscribe from rooms they are no longer interested in
- they can also enter a room; in that case they move to a new page
- where they can
  - see the list of messages sent by other users and themselves
  - and write new messages to the room

## bonus

- admin pages to manage users and rooms (warning, this can be tedious to do)
- registration form for new users
- authentication (e.g. using JWT)

## evaluation criteria

- the app should be functional and meet the requirements described above
- use the same technologies as discussed in class (see the notes app in particular)
- write a README file describing how to run the app, and any other relevant information
- the code should be well organized and commented

## how to submit

create an `eval` folder in your homework repository

## submission deadline

 to be defined later, in any case after next course on 21/04/2026
