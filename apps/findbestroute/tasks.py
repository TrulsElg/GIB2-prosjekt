from celery import shared_task
from django.core.files import File
from apps.userregistration.models import PathUser
from apps.findbestroute.models import UploadedFile
from time import sleep
from django.conf import settings
import models
import os
"""
IMPORTANT NOTE:

PASSED FROM views.py: request.user
"""


@shared_task
def local_test(number, username):
    for i in range(number):
        print('hurr durr  ' + str((pow(i, 2))))
    sleep(10)
    UploadedFile.objects.filter(uploader=PathUser.objects.get(username=username)).delete()

    return


# FIXME
@shared_task
def find_best_route(user):
    """
    :param user = request.user, from views.last_opp_filer(request)
    :return:
    """
    files = UploadedFile.objects.filter(uploader=user)
    # fetches ALL the uploads belonging to the user. includes shape, jpg...
    # see valid file__types in models or forms

    print('Finding best route...')
    do_analysis(files, user)

    for i in range(3):
        print('Sleeping for 3 seconds...')
        sleep(1)

    delete_user_uploads(uploader=user)
    print('Filene har blitt slettet. Ferdig med analyse.')


# FIXME return the image file with the optimal path
@shared_task
def do_analysis(files, user):
    print('Doing analysis...')
    # pathen blir:
    # files/bilder/files/testfiles, med dette her.
    path = os.path.join(settings.MEDIA_ROOT, 'test_files', "images.png")
    print(path)
    opening = open(path, 'rb')
    img = File(opening)
    image_object = models.Image()
    image_object.bilde = img
    image_object.uploader = user
    image_object.save()
    img.close()
    opening.close()
"""
    result_object = models.ResultFile()
    result_object.owner = user
    result_object.file = img
    result_object.save()
"""


@shared_task
def delete_user_uploads(uploader):
    UploadedFile.objects.filter(uploader=uploader).delete()
