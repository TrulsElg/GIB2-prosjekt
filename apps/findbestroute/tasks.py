from celery import shared_task
from django.core.mail import EmailMessage
from ..userregistration.models import PathUser
from models import UploadedFile
from time import sleep
from django.conf import settings

@shared_task
def test(number, user):
    for i in range(number):
        print('hurr durr  ' + str((pow(i, 2))))
    sleep(10)
    UploadedFile.objects.filter(uploader=user).delete()
    return


# FIXME
@shared_task
def find_best_route(user, files):
    """
    :param request:
    :param files:
    :return:
    """
    result = do_analysis(files)
    target_mail = PathUser.objects.get(username=user.username).email
    send_result_email(target_mail, result)
    print('Finding best route...')
    sleep(10)
    UploadedFile.objects.filter(uploader=user).delete()
    return


# FIXME return the image file with the optimal path
def do_analysis(files):
    print('Doing analysis...')
    file_path = settings.MEDIA_ROOT + '/data_files/images.png'
    actual_file = __builtins__.file(file_path)
    return actual_file


@shared_task
def send_result_email(username, file_path):
    """
    SKAL SENDE EN EPOST MED VEDLEGG. Dvs bildet med beste veivalg
    """
    print('Sending email...')
    email = EmailMessage()
    email.subject = 'Path-analyse resultat'
    email.body = 'Hei, \n\nHer er analysens resultater. \n\nTakk for at du bruker Path.'
    email.from_email = 'no-reply@pathErHeltKonge.com'
    email.to = PathUser.objects.get(username=username).email
    email.attach_file(file_path)
    email.send()

