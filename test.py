import os

users=[]
for i in os.getenv("RSLB_Users").split(","):
    users.append(i.split("#"))
print(users)

print(users[0][2])
print(users[1][2])
