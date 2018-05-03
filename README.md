# GIB2-prosjekt

... hvor ~~de beste~~ GitHub-konvensjoner praktiseres ~~på ypperste vis~~

_________

Required installations:
1. ArcGIS 10.6
2. Suitable IDE, e.g. PyCharm

Install the following with default settings
1. Erlang
2. RabbitMQ
Get the command line/terminal up (CMD) and enter the following lines:
`    C:\Python27\ArcGIS10.6\python.exe -m pip install django`
`    C:\Python27\ArcGIS10.6\python.exe -m pip install celery`

Now, in PyCharm:
1. Get the repository. Make sure to pull the latest master branch
2. In the terminal, run the following line; it produces a parallel process waiting for tasks.
`C:\Python27\ArcGIS10.6\Scripts\celery.exe worker -A GIB2 --loglevel=info --pool=solo --concurrency=1`

3. Run the GIB2 process from PyCharm. The run window should provide an ip address to the website.
... and now you can play with the website. ~~Or break it beyond recognition.~~

To restart the website properly: restart the GIB2 process.

When changes are made to tasks.py, the parallel process *must* restart.
To restart the parallel process: go to the terminal. Hit CTRL+C. Re-enter the command:
`C:\Python27\ArcGIS10.6\Scripts\celery.exe worker -A GIB2 --loglevel=info --pool=solo --concurrency=1`
