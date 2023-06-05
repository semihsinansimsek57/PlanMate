import os


# Set the values of environment variables
os.environ['EMAIL_SENDER'] = 'planmateverify@gmail.com'
os.environ['EMAIL_SENDER_PASSWORD'] = 'ashalyzwkbaktwhg'

print(os.environ.get('EMAIL_SENDER'))
print(os.environ.get('EMAIL_SENDER_PASSWORD'))

