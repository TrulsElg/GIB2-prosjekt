from celery import shared_task
from django.core.mail import EmailMessage
from ..userregistration.models import PathUser


# FIXME
@shared_task
def find_best_route(username, files):
    result = do_analysis(files)         # please return the result file
    send_result_email(username, result) #
    print('Finding best route...')
    return
    pass


# FIXME
def do_analysis(files):
    print('Doing analysis...')
    pass


@shared_task
def send_result_email(username, file_path):
    print('Sending email...')
    email = EmailMessage()
    email.subject = 'Path-analyse resultat'
    email.body = 'Hei, \n\nHer er analysens resultater. \n\nTakk for at du bruker Path.'
    email.from_email = 'no-reply@pathErHeltKonge.com'
    email.to = PathUser.objects.get(username=username).email
    email.attach_file(file_path)
    email.send()

